import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage
from api.main import app

client = TestClient(app)

@pytest.fixture
def mock_agent_state():
    with patch("api.main.interview_agent") as mock_agent:
        mock_state = MagicMock()
        mock_agent.get_state.return_value = mock_state
        yield mock_agent, mock_state

def test_start_interview_success(mock_agent_state):
    mock_agent, mock_state = mock_agent_state
    mock_agent.stream.return_value = [{"messages": [AIMessage(content="Hello, I am Alex.")]}]
    mock_state.values = {"stage": "greeting"}

    response = client.post("/interview/start?thread_id=test_thread_123")
    
    assert response.status_code == 200
    data = response.json()
    assert data["thread_id"] == "test_thread_123"
    assert data["message"] == "Hello, I am Alex."
    assert data["stage"] == "greeting"

def test_chat_interview_session_not_found(mock_agent_state):
    _, mock_state = mock_agent_state
    mock_state.values = {}

    response = client.post(
        "/interview/chat",
        json={"thread_id": "missing_thread", "message": "Hello"}
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Interview session not found. Please start it first."

def test_chat_interview_already_ended(mock_agent_state):
    _, mock_state = mock_agent_state
    mock_state.values = {"stage": "goodbye", "count": 10}

    response = client.post(
        "/interview/chat",
        json={"thread_id": "ended_thread", "message": "Hello"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["stage"] == "goodbye"
    assert data["count"] == 10
    assert "already ended" in data["message"]

def test_chat_interview_processing_success(mock_agent_state):
    mock_agent, mock_state = mock_agent_state
    mock_state.values = {"stage": "interviewing", "count": 2}
    
    mock_agent.stream.return_value = [{
        "messages": [
            HumanMessage(content="My answer"),
            AIMessage(content="Next technical question?")
        ]
    }]

    response = client.post(
        "/interview/chat",
        json={"thread_id": "active_thread", "message": "My answer"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Next technical question?"
    assert data["stage"] == "interviewing"
    assert data["count"] == 2
