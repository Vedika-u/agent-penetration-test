"""Minimal grounding-check node.

Phase 1 stub: flags (never blocks) a final answer that follows a web_search call but shares
little vocabulary overlap with that search result, as a naive proxy for "the model may have
answered from its own knowledge/hallucination instead of the tool output." Phase 3 replaces
this heuristic with the full detection layer (attention/embedding classifier +
memory-integrity check) built on the same seam.
"""

import re

from langchain_core.messages import AIMessage, ToolMessage

_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "of", "in", "on", "to", "and", "or",
    "for", "with", "that", "this", "it", "as", "at", "by", "from", "be", "has", "have",
}


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in _STOPWORDS}


def check_grounding(messages: list) -> list[str]:
    flags: list[str] = []
    last_search_result = None
    for msg in messages:
        if isinstance(msg, ToolMessage) and msg.name == "web_search":
            last_search_result = msg.content

    final = messages[-1] if messages else None
    if last_search_result and isinstance(final, AIMessage) and final.content:
        answer_words = _words(final.content)
        result_words = _words(last_search_result)
        if answer_words and not (answer_words & result_words):
            flags.append(
                "Final answer shares no vocabulary with the last web_search result — "
                "possible ungrounded claim."
            )
    return flags
