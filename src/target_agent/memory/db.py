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
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                flagged INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        _migrate_flagged_column(conn)


def _migrate_flagged_column(conn: sqlite3.Connection) -> None:
    columns = {row[1] for row in conn.execute("PRAGMA table_info(notes)")}
    if "flagged" not in columns:
        conn.execute("ALTER TABLE notes ADD COLUMN flagged INTEGER NOT NULL DEFAULT 0")


@contextmanager
def _connect(db_path: str):
    conn = sqlite3.connect(db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def add_note(db_path: str, content: str, flagged: bool = False) -> int:
    init_db(db_path)
    with _connect(db_path) as conn:
        cursor = conn.execute(
            "INSERT INTO notes (content, flagged) VALUES (?, ?)", (content, int(flagged))
        )
        return cursor.lastrowid


def _row_to_dict(row) -> dict:
    return {"id": row[0], "content": row[1], "created_at": row[2], "flagged": bool(row[3])}


def list_notes(db_path: str) -> list[dict]:
    init_db(db_path)
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT id, content, created_at, flagged FROM notes ORDER BY id ASC"
        ).fetchall()
        return [_row_to_dict(r) for r in rows]


def search_notes(db_path: str, query: str) -> list[dict]:
    init_db(db_path)
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT id, content, created_at, flagged FROM notes WHERE content LIKE ? ORDER BY id ASC",
            (f"%{query}%",),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
