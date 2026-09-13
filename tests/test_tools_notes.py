from target_agent.config import settings
from target_agent.tools.notes import add_note, list_notes, search_notes


def test_add_and_list_notes(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "memory_db_path", str(tmp_path / "memory.sqlite3"))

    add_note.invoke({"content": "favorite color is blue"})
    add_note.invoke({"content": "buy milk"})

    result = list_notes.invoke({})
    assert "favorite color is blue" in result
    assert "buy milk" in result


def test_search_notes(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "memory_db_path", str(tmp_path / "memory.sqlite3"))

    add_note.invoke({"content": "favorite color is blue"})
    add_note.invoke({"content": "buy milk"})

    result = search_notes.invoke({"query": "color"})
    assert "favorite color is blue" in result
    assert "buy milk" not in result


def test_search_notes_no_match(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "memory_db_path", str(tmp_path / "memory.sqlite3"))

    result = search_notes.invoke({"query": "nonexistent"})
    assert "No notes found" in result
