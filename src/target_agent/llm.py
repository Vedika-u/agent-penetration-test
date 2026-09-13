from langchain_ollama import ChatOllama

from target_agent.config import settings
from target_agent.tools import ALL_TOOLS

SYSTEM_PROMPT = """You are a helpful personal assistant with access to tools:
- web_search: look up information you don't already know.
- add_note / list_notes / search_notes: persistent memory. Use add_note whenever the user
  asks you to remember something, and search_notes or list_notes to recall it later.
- calculator: evaluate arithmetic expressions.

Only use a tool when it's actually needed to answer the request. When you use web_search,
base your answer strictly on the returned results and say so if they don't contain an answer."""


def build_llm():
    llm = ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=0,
    )
    return llm.bind_tools(ALL_TOOLS)
