from langchain_core.messages import AIMessage
from fastapi.testclient import TestClient

from target_agent import api, graph as graph_module
from target_agent.detection.injection_detector import DetectionResult


class FakeLLM:
    """Stands in for the Ollama-backed chat model so this test doesn't need Ollama running."""

    def __init__(self, responses):
        self._responses = iter(responses)

    def invoke(self, messages):
        return next(self._responses)


def _stub_injection_classifier(monkeypatch):
    """Keeps these API tests network-free (no live Ollama embedding call)."""
    monkeypatch.setattr(
        graph_module,
        "classify_injection",
        lambda text: DetectionResult(label=False, score=0.0, threshold=0.45),
    )


def test_health():
    client = TestClient(api.app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_chat_calculator_round_trip(monkeypatch):
    responses = [
        AIMessage(
            content="",
            tool_calls=[{"name": "calculator", "args": {"expression": "12 * 7"}, "id": "call1"}],
        ),
        AIMessage(content="12 * 7 is 84."),
    ]
    monkeypatch.setattr(graph_module, "build_llm", lambda: FakeLLM(responses))
    monkeypatch.setattr(api, "_graph", None)
    _stub_injection_classifier(monkeypatch)

    client = TestClient(api.app)
    resp = client.post("/chat", json={"session_id": "test-api", "message": "what's 12 * 7?"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["response"] == "12 * 7 is 84."
    assert any(tc["name"] == "calculator" and tc["content"] == "84" for tc in body["tool_calls"])
    assert body["verification"] == []


def test_attack_endpoint_is_stateless_per_call(monkeypatch):
    def make_responses():
        return [
            AIMessage(
                content="",
                tool_calls=[
                    {"name": "calculator", "args": {"expression": "1 + 1"}, "id": "call1"}
                ],
            ),
            AIMessage(content="1 + 1 is 2."),
        ]

    monkeypatch.setattr(graph_module, "build_llm", lambda: FakeLLM(make_responses()))
    monkeypatch.setattr(api, "_graph", None)
    _stub_injection_classifier(monkeypatch)

    client = TestClient(api.app)
    resp = client.post("/attack", json={"message": "what's 1 + 1?"})

    assert resp.status_code == 200
    assert resp.json() == {"response": "1 + 1 is 2.", "verification": []}
