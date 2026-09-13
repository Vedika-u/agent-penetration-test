"""Verification layer: grounding/citation checks and memory-integrity checks.

Phase 1 shipped a stub `check_grounding` that only checked whether the final answer shared any
vocabulary with the last web_search result. Phase 3 extends it into a fuller, still deterministic
heuristic (no ML, no network calls) that also looks for specific unsupported claims — numbers and
proper-noun-like tokens asserted in the final answer that don't appear in any tool output used
that turn — and flags them individually. It also adds `check_memory_integrity`, a heuristic
prompt-injection detector run over content about to be persisted as a note, since persistent
memory (notes survive across turns/sessions) is this agent's distinct attack surface: an
instruction smuggled into a note in one turn can be acted on in a later one.
"""

import re

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "of", "in", "on", "to", "and", "or",
    "for", "with", "that", "this", "it", "as", "at", "by", "from", "be", "has", "have",
}

_GROUNDABLE_TOOLS = {"web_search", "list_notes", "search_notes"}

_NUMBER_RE = re.compile(r"\d[\d,.]*%?")
_PUNCT = ".,!?;:\"'()[]"


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in _STOPWORDS}


def _sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]


def _claim_tokens(text: str) -> set[str]:
    """Numbers and proper-noun-like tokens asserted in `text` that plausibly needed sourcing.

    Numbers are collected wherever they appear. Capitalized words are only treated as
    proper-noun-like if they're not the first word of a sentence, to avoid flagging ordinary
    sentence-initial capitalization.
    """
    tokens: set[str] = set()
    for sentence in _sentences(text):
        words = sentence.split()
        for i, raw in enumerate(words):
            cleaned = raw.strip(_PUNCT)
            if not cleaned:
                continue
            if _NUMBER_RE.search(cleaned):
                tokens.add(cleaned)
            elif i > 0 and cleaned[0].isupper() and cleaned.lower() not in _STOPWORDS:
                tokens.add(cleaned)
    return tokens


def _current_turn_messages(messages: list) -> list:
    last_human_idx = None
    for i, msg in enumerate(messages):
        if isinstance(msg, HumanMessage):
            last_human_idx = i
    if last_human_idx is None:
        return messages
    return messages[last_human_idx:]


def _tool_outputs(messages: list) -> list[str]:
    return [
        msg.content
        for msg in messages
        if isinstance(msg, ToolMessage) and msg.name in _GROUNDABLE_TOOLS
    ]


def check_grounding(messages: list) -> list[str]:
    flags: list[str] = []
    turn = _current_turn_messages(messages)
    tool_outputs = _tool_outputs(turn)
    final = turn[-1] if turn else None

    if not tool_outputs or not isinstance(final, AIMessage) or not final.content:
        return flags

    combined_output = "\n".join(tool_outputs)
    output_words = _words(combined_output)
    answer_words = _words(final.content)

    if answer_words and not (answer_words & output_words):
        flags.append(
            "Final answer shares no vocabulary with this turn's tool output(s) — "
            "possible ungrounded claim."
        )
        return flags

    combined_output_lower = combined_output.lower()
    unsupported = sorted(
        token for token in _claim_tokens(final.content)
        if token.lower() not in combined_output_lower
    )
    if unsupported:
        flags.append(
            "Unsupported claim(s) not found in this turn's tool output: "
            + ", ".join(unsupported)
        )
    return flags


_INJECTION_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("ignore previous instructions",
     re.compile(r"ignore\s+(all\s+)?(the\s+)?(previous|prior|above)\s+instructions", re.I)),
    ("disregard the above",
     re.compile(r"disregard\s+(the\s+)?(above|previous|prior)", re.I)),
    ("role override (\"you are now\")", re.compile(r"\byou are now\b", re.I)),
    ("new instructions:", re.compile(r"new instructions\s*:", re.I)),
    ("system role spoof (\"system:\")", re.compile(r"(^|\n)\s*system\s*:", re.I)),
    ("act as", re.compile(r"\bact as\b", re.I)),
]

_ZERO_WIDTH_RE = re.compile(r"[​‌‍⁠﻿]")


def check_memory_integrity(content: str) -> list[str]:
    """Heuristically flag prompt-injection / instruction-override patterns in note content.

    Deliberately never blocks or mutates content — this is a red-team target, so we want to
    observe attacks landing (and get flagged), not prevent them at write time.
    """
    flags: list[str] = []
    for label, pattern in _INJECTION_PATTERNS:
        if pattern.search(content):
            flags.append(f"Possible prompt-injection pattern detected: {label}.")
    if _ZERO_WIDTH_RE.search(content):
        flags.append("Contains zero-width/invisible unicode characters — possible obfuscated injection.")
    return flags
