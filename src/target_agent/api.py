import uuid

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from fastapi import FastAPI
from pydantic import BaseModel

from target_agent.graph import build_graph

app = FastAPI(title="target-agent")
_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ToolCallTrace(BaseModel):
    name: str
    content: str


class ChatResponse(BaseModel):
    response: str
    tool_calls: list[ToolCallTrace]
    verification: list[str]


class AttackRequest(BaseModel):
    message: str


class AttackResponse(BaseModel):
    response: str
    verification: list[str]


def _invoke(message: str, thread_id: str) -> dict:
    graph = _get_graph()
    config = {"configurable": {"thread_id": thread_id}}
    return graph.invoke({"messages": [HumanMessage(content=message)]}, config=config)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    result = _invoke(req.message, req.session_id)

    messages = result["messages"]
    final_ai = next(
        (m for m in reversed(messages) if isinstance(m, AIMessage) and m.content), None
    )
    tool_calls = [
        ToolCallTrace(name=m.name, content=m.content)
        for m in messages
        if isinstance(m, ToolMessage)
    ]

    return ChatResponse(
        response=final_ai.content if final_ai else "",
        tool_calls=tool_calls,
        verification=result.get("verification", []),
    )


@app.post("/attack", response_model=AttackResponse)
def attack(req: AttackRequest) -> AttackResponse:
    """Stateless single-turn endpoint for the garak harness (Phase 2): each call gets a
    fresh conversation thread so attack attempts never share message history."""
    result = _invoke(req.message, thread_id=str(uuid.uuid4()))

    final_ai = next(
        (m for m in reversed(result["messages"]) if isinstance(m, AIMessage) and m.content),
        None,
    )
    return AttackResponse(
        response=final_ai.content if final_ai else "",
        verification=result.get("verification", []),
    )
