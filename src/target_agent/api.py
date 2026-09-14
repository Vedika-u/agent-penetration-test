import logging
import uuid

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from target_agent.config import settings
from target_agent.graph import build_graph

logger = logging.getLogger("target_agent.api")

app = FastAPI(title="target-agent")
_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def require_auth(request: Request) -> None:
    """No-op when API_AUTH_TOKEN is unset (the default) -- see config.py: this service is a
    red-team target meant to receive attack traffic from the harness/garak with no friction.
    Only enforced if a deployer explicitly sets the token (e.g. exposing beyond localhost)."""
    if not settings.api_auth_token:
        return
    header = request.headers.get("authorization", "")
    token = header.removeprefix("Bearer ").strip()
    if token != settings.api_auth_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid or missing bearer token")


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Avoids leaking stack traces to the client (e.g. if Ollama is unreachable mid-turn) --
    the failure is still logged server-side with full detail."""
    logger.exception("unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=502, content={"detail": "target agent failed to respond"})


class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(min_length=1, max_length=8000)


class ToolCallTrace(BaseModel):
    name: str
    content: str


class ChatResponse(BaseModel):
    response: str
    tool_calls: list[ToolCallTrace]
    verification: list[str]


class AttackRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)


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


@app.post("/chat", response_model=ChatResponse, dependencies=[Depends(require_auth)])
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


@app.post("/attack", response_model=AttackResponse, dependencies=[Depends(require_auth)])
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
