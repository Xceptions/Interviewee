import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage, HumanMessage

import core
from core.agent.graph import introduce_node, chat_node, interview_node, close_node, route_by_stage, route_interview_count


@pytest.fixture
def mock_dependencies():
    with patch("core.agent.graph.llm") as mock_llm, patch("core.agent.graph.retriever") as mock_retriever:
        mock_llm.invoke.return_value = AIMessage(content="Mocked response")
        mock_retriever.invoke.return_value = [MagicMock(page_content="Python, LangChain")]
        yield mock_llm, mock_retriever

def test_introduce_node(mock_dependencies):
    state = {"messages": [], "stage": "greeting", "count": 0}
    res = introduce_node(state)
    assert res["stage"] == "greeting"
    assert res["count"] == 0
    assert len(res["messages"]) == 1

def test_chat_node_user_not_ready(mock_dependencies):
    state = {"messages": [HumanMessage(content="Hello")], "stage": "greeting", "count": 0}
    res = chat_node(state)
    assert "stage" not in res
    assert len(res["messages"]) == 1

def test_chat_node_user_ready():
    state = {"messages": [HumanMessage(content="Yes, let's start")], "stage": "greeting", "count": 0}
    res = chat_node(state)
    assert res["stage"] == "interviewing"
    assert "10 questions" in res["messages"][0].content

def test_interview_node(mock_dependencies):
    state = {"messages": [HumanMessage(content="My experience")], "stage": "interviewing", "count": 2}
    res = interview_node(state)
    assert res["count"] == 3
    assert len(res["messages"]) == 1

def test_close_node(mock_dependencies):
    state = {"messages": [HumanMessage(content="Final answer")], "stage": "interviewing", "count": 10}
    res = close_node(state)
    assert res["stage"] == "goodbye"

@pytest.mark.parametrize("stage, expected", [
    ("greeting", "chat_node"),
    ("screening", "chat_node"),
    ("interviewing", "interview_node"),
    ("goodbye", "__end__")
])
def test_route_by_stage(stage, expected):
    state = {"messages": [], "stage": stage, "count": 0}
    assert route_by_stage(state) == expected

@pytest.mark.parametrize("count, expected", [
    (0, "__end__"),
    (9, "__end__"),
    (10, "close_node")
])
def test_route_interview_count(count, expected):
    state = {"messages": [], "stage": "interviewing", "count": count}
    assert route_interview_count(state) == expected
