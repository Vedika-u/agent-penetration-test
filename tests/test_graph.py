from langchain_core.messages import AIMessage, HumanMessage

from target_agent import graph as graph_module


class FakeLLM:
    """Stands in for the Ollama-backed chat model so graph tests don't need Ollama running."""

    def __init__(self, responses):
        self._responses = iter(responses)

    def invoke(self, messages):
        return next(self._responses)


def _build_graph_with_responses(monkeypatch, responses):
    monkeypatch.setattr(graph_module, "build_llm", lambda: FakeLLM(responses))
    return graph_module.build_graph()


def test_calculator_tool_call_round_trip(monkeypatch):
    responses = [
        AIMessage(
            content="",
            tool_calls=[{"name": "calculator", "args": {"expression": "12 * 7"}, "id": "call1"}],
        ),
        AIMessage(content="12 * 7 is 84."),
    ]
    compiled = _build_graph_with_responses(monkeypatch, responses)

    result = compiled.invoke(
        {"messages": [HumanMessage(content="what's 12 * 7?")], "verification": []},
        config={"configurable": {"thread_id": "test-calc"}},
    )

    contents = [m.content for m in result["messages"]]
    assert "84" in contents
    assert "12 * 7 is 84." in contents
    assert result["verification"] == []


def test_verification_flags_ungrounded_answer(monkeypatch):
    responses = [
        AIMessage(
            content="",
            tool_calls=[
                {"name": "web_search", "args": {"query": "langgraph"}, "id": "call1"}
            ],
        ),
        AIMessage(content="The capital of France is Paris."),
    ]
    compiled = _build_graph_with_responses(monkeypatch, responses)

    result = compiled.invoke(
        {"messages": [HumanMessage(content="tell me about langgraph")], "verification": []},
        config={"configurable": {"thread_id": "test-verify"}},
    )

    assert result["verification"], "expected a grounding flag for an unrelated final answer"
