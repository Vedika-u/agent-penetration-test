import sqlite3
from contextlib import contextmanager
from pathlib import Path


def init_db(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )


@contextmanager
def _connect(db_path: str):
    conn = sqlite3.connect(db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def add_note(db_path: str, content: str) -> int:
    init_db(db_path)
    with _connect(db_path) as conn:
        cursor = conn.execute("INSERT INTO notes (content) VALUES (?)", (content,))
        return cursor.lastrowid


def list_notes(db_path: str) -> list[dict]:
    init_db(db_path)
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT id, content, created_at FROM notes ORDER BY id ASC"
        ).fetchall()
        return [{"id": r[0], "content": r[1], "created_at": r[2]} for r in rows]


def search_notes(db_path: str, query: str) -> list[dict]:
    init_db(db_path)
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT id, content, created_at FROM notes WHERE content LIKE ? ORDER BY id ASC",
            (f"%{query}%",),
        ).fetchall()
        return [{"id": r[0], "content": r[1], "created_at": r[2]} for r in rows]
