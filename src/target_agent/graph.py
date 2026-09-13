from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from target_agent.detection.injection_detector import classify as classify_injection
from target_agent.llm import SYSTEM_PROMPT, build_llm
from target_agent.state import State
from target_agent.tools import ALL_TOOLS
from target_agent.verification import check_grounding


def _agent_node(state: State, llm) -> dict:
    messages = state["messages"]
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT), *messages]
    response = llm.invoke(messages)
    return {"messages": [response]}


def _last_human_message(messages: list) -> str | None:
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            return msg.content
    return None


def _check_injection(messages: list) -> list[str]:
    content = _last_human_message(messages)
    if not content:
        return []
    result = classify_injection(content)
    if not result.label:
        return []
    return [
        f"Input flagged as possible prompt injection/jailbreak (score={result.score:.3f} "
        f">= threshold={result.threshold:.3f}, closest to: \"{result.matched_reference}\")."
    ]


def _verify_node(state: State) -> dict:
    messages = state["messages"]
    return {"verification": check_grounding(messages) + _check_injection(messages)}


def build_graph():
    llm = build_llm()
    graph = StateGraph(State)

    graph.add_node("agent", lambda state: _agent_node(state, llm))
    graph.add_node("tools", ToolNode(ALL_TOOLS))
    graph.add_node("verify", _verify_node)

    graph.set_entry_point("agent")
    graph.add_conditional_edges(
        "agent",
        tools_condition,
        {"tools": "tools", END: "verify"},
    )
    graph.add_edge("tools", "agent")
    graph.add_edge("verify", END)

    return graph.compile(checkpointer=MemorySaver())
