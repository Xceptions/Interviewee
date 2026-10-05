from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
from core.agent.graph import interview_agent

app = FastAPI(title="AI Interviewer Agent API")

class StartInterviewResponse(BaseModel):
    thread_id: str
    message: str
    stage: str

class ChatRequest(BaseModel):
    thread_id: str
    message: str

class ChatResponse(BaseModel):
    message: str
    stage: str
    count: int

@app.post("/interview/start", response_model=StartInterviewResponse)
async def start_interview(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        events = list(interview_agent.stream({}, config, stream_mode="values"))
        if not events or "messages" not in events[-1]:
            raise HTTPException(status_code=500, detail="Failed to initialize agent workflow.")
            
        latest_message = events[-1]["messages"][-1].content
        current_state = interview_agent.get_state(config).values
        
        return StartInterviewResponse(
            thread_id=thread_id,
            message=latest_message,
            stage=current_state.get("stage", "greeting")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/interview/chat", response_model=ChatResponse)
async def chat_interview(payload: ChatRequest):
    config = {"configurable": {"thread_id": payload.thread_id}}
    
    current_state = interview_agent.get_state(config).values
    if not current_state:
        raise HTTPException(status_code=404, detail="Interview session not found. Please start it first.")
        
    if current_state.get("stage") == "goodbye":
        return ChatResponse(
            message="This interview session has already ended.",
            stage="goodbye",
            count=current_state.get("count", 10)
        )
        
    try:
        events = list(interview_agent.stream(
            {"messages": [HumanMessage(content=payload.message)]},
            config,
            stream_mode="values"
        ))
        
        latest_state = interview_agent.get_state(config).values
        
        ai_messages = [msg.content for msg in events[-1]["messages"] if isinstance(msg, AIMessage)]
        response_text = ai_messages[-1] if ai_messages else "Acknowledged."
        
        return ChatResponse(
            message=response_text,
            stage=latest_state.get("stage", "interviewing"),
            count=latest_state.get("count", 0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
