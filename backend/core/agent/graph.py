from typing import Annotated, Literal, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_chroma import Chroma
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from core.config import settings

embedding_function = OllamaEmbeddings(model=settings.ollama_model)
vector_store = Chroma(
    persist_directory=settings.chroma_db_path,
    embedding_function=embedding_function
)
retriever = vector_store.as_retriever(search_kwargs={"k": 2})
llm = ChatOllama(model=settings.ollama_model, temperature=0.7)

class InterviewState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    stage: Literal["greeting", "screening", "interviewing", "goodbye"]
    count: int

def introduce_node(state: InterviewState) -> dict:
    system_prompt = SystemMessage(
        content="You are an expert AI Job Interviewer named Helen Reece. Introduce yourself warmly, "
                "ask the candidate how they are doing today, and ask if they are ready to begin."
    )
    response = llm.invoke([system_prompt] + state["messages"])
    return {"messages": [response], "stage": "greeting", "count": 0}

def chat_node(state: InterviewState) -> dict:
    last_user_message = state["messages"][-1].content.lower()
    is_ready = any(word in last_user_message for word in ["yes", "ready", "sure", "start", "ok", "yep"])
    
    if is_ready:
        return {
            "stage": "interviewing",
            "messages": [AIMessage(content="Excellent! Let's dive into your background. I'll ask you 10 questions related to your experience.")]
        }
    
    system_prompt = SystemMessage(
        content="You are an AI Interviewer. Acknowledge the candidate's response warmly, "
                "maintain good rapport, and politely ask if they are ready to begin the interview."
    )
    response = llm.invoke([system_prompt] + state["messages"])
    return {"messages": [response]}

def interview_node(state: InterviewState) -> dict:
    current_count = state.get("count", 0)
    latest_user_reply = state["messages"][-1].content
    
    docs = retriever.invoke(latest_user_reply)
    context = "\n\n".join([doc.page_content for doc in docs])
    
    system_prompt = SystemMessage(
        content=f"You are a technical interviewer. Here is context from the candidate's resume:\n"
                f"---START RESUME CONTEXT---\n{context}\n---END RESUME CONTEXT---\n\n"
                f"Review their last answer and context. Ask a precise technical follow-up or "
                f"a new question about their resume skills. Keep it brief. Question {current_count + 1} of 10."
    )
    response = llm.invoke([system_prompt] + state["messages"])
    return {"messages": [response], "count": current_count + 1}

def close_node(state: InterviewState) -> dict:
    system_prompt = SystemMessage(
        content="The interview is over. Provide a professional closing remark, "
                "thank them for their time, and say the team will review the details."
    )
    response = llm.invoke([system_prompt] + state["messages"])
    return {"messages": [response], "stage": "goodbye"}

def route_by_stage(state: InterviewState) -> Literal["chat_node", "interview_node", "__end__"]:
    stage = state.get("stage", "greeting")
    if stage in ["greeting", "screening"]:
        return "chat_node"
    return "interview_node" if stage == "interviewing" else END

def route_interview_count(state: InterviewState) -> Literal["interview_node", "close_node"]:
    return END if state["count"] < 10 else "close_node"

builder = StateGraph(InterviewState)
builder.add_node("introduce", introduce_node)
builder.add_node("chat_node", chat_node)
builder.add_node("interview_node", interview_node)
builder.add_node("close_node", close_node)

builder.add_edge(START, "introduce")
builder.add_conditional_edges("introduce", route_by_stage)
builder.add_conditional_edges("chat_node", route_by_stage)
builder.add_conditional_edges("interview_node", route_interview_count)
builder.add_edge("close_node", END)

interview_agent = builder.compile(checkpointer=MemorySaver())
