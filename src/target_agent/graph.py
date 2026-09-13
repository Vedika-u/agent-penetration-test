from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

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


def _verify_node(state: State) -> dict:
    return {"verification": check_grounding(state["messages"])}


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
