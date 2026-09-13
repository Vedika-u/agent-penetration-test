import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path


def init_db(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                attempt_uuid TEXT NOT NULL,
                probe_classname TEXT,
                seq INTEGER,
                status INTEGER,
                goal TEXT,
                prompt_text TEXT,
                output_index INTEGER,
                output_text TEXT,
                detector_results TEXT,
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


def insert_attempts(db_path: str, rows: list[dict]) -> int:
    """Each row: run_id, attempt_uuid, probe_classname, seq, status, goal, prompt_text,
    output_index, output_text, detector_results (a dict, JSON-encoded here)."""
    init_db(db_path)
    with _connect(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO attempts (
                run_id, attempt_uuid, probe_classname, seq, status, goal,
                prompt_text, output_index, output_text, detector_results
            ) VALUES (:run_id, :attempt_uuid, :probe_classname, :seq, :status, :goal,
                      :prompt_text, :output_index, :output_text, :detector_results)
            """,
            [
                {**row, "detector_results": json.dumps(row["detector_results"])}
                for row in rows
            ],
        )
        return len(rows)
