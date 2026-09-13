from langchain_core.tools import tool

from target_agent.config import settings
from target_agent.memory import db
from target_agent.verification import check_memory_integrity


def _format_note(n: dict) -> str:
    prefix = "[FLAGGED] " if n["flagged"] else ""
    return f"{prefix}#{n['id']}: {n['content']}"


@tool
def add_note(content: str) -> str:
    """Save a note to persistent memory so it can be recalled in later turns or sessions.

    Args:
        content: The text to remember.
    """
    flagged = bool(check_memory_integrity(content))
    note_id = db.add_note(settings.memory_db_path, content, flagged=flagged)
    return f"Saved note #{note_id}."


@tool
def list_notes() -> str:
    """List all notes previously saved to persistent memory."""
    notes = db.list_notes(settings.memory_db_path)
    if not notes:
        return "No notes saved yet."
    return "\n".join(_format_note(n) for n in notes)


@tool
def search_notes(query: str) -> str:
    """Search saved notes for a keyword.

    Args:
        query: Keyword or phrase to search for within saved notes.
    """
    notes = db.search_notes(settings.memory_db_path, query)
    if not notes:
        return f"No notes found matching '{query}'."
    return "\n".join(_format_note(n) for n in notes)
