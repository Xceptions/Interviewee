from langchain_core.messages import HumanMessage, AIMessage
from core.agent.graph import interview_agent

def run_interview():
    config = {"configurable": {"thread_id": "interview_session_001"}}
    print("--- Starting Agentic Interview Loop ---\n")
    
    events = interview_agent.stream({}, config, stream_mode="values")
    for event in events:
        if event.get("messages"):
            print(f"Agent: {event['messages'][-1].content}\n")
            
    while True:
        current_state = interview_agent.get_state(config).values
        if current_state.get("stage") == "goodbye":
            print("--- Interview Ended Safely ---")
            break
            
        user_input = input("You: ")
        if user_input.strip().lower() in ["exit", "quit"]:
            break
            
        events = interview_agent.stream(
            {"messages": [HumanMessage(content=user_input)]}, 
            config, 
            stream_mode="values"
        )
        for event in events:
            if event.get("messages") and isinstance(event["messages"][-1], AIMessage):
                print(f"\nAgent: {event['messages'][-1].content}\n")

if __name__ == "__main__":
    run_interview()
