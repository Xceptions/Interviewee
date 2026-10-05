from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
from core.agent.graph import interview_agent
import shutil
import os
from parser import extract_resume_text
from chroma_service import chroma_service

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

@app.post("/resumes/upload")
async def upload_resume(file: UploadFile = File(...)):
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        file_text = extract_resume_text(file_path)
        candidate_id = chroma_service.ingest_resume(file_text, file.filename)
        
        return {"candidate_id": candidate_id, "filename": file.filename, "status": "Ingested successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.get("/resumes")
async def list_resumes():
    try:
        data = chroma_service.collection.get(include=["metadatas"])
        metadatas = data.get("metadatas", [])
        
        seen = set()
        unique_resumes = []
        for meta in metadatas:
            if meta and "source_file" in meta and meta["source_file"] not in seen:
                seen.add(meta["source_file"])
                unique_resumes.append({
                    "filename": meta["source_file"],
                    "candidate_id": meta.get("candidate_id")
                })
        return unique_resumes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))