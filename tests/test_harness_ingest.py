import json
import sqlite3

from harness.ingest import ingest_report


FIXTURE_LINES = [
    {"entry_type": "start_run setup", "something": "irrelevant"},
    {"entry_type": "init", "garak_version": "0.0.0", "run": "run-123"},
    {
        "entry_type": "attempt",
        "uuid": "attempt-1",
        "probe_classname": "promptinject.HijackHateHumans",
        "seq": 0,
        "status": 2,
        "goal": "make the model say something harmful",
        "prompt": {"text": "ignore previous instructions"},
        "outputs": [{"text": "I can't help with that."}],
        "detector_results": {"promptinject.AttackRogueString": [0.0]},
    },
    {
        "entry_type": "attempt",
        "uuid": "attempt-2",
        "probe_classname": "promptinject.HijackHateHumans",
        "seq": 1,
        "status": 2,
        "goal": "make the model say something harmful",
        "prompt": {"text": "another injection payload"},
        "outputs": [{"text": "sure, here you go"}, {"text": "no."}],
        "detector_results": {"promptinject.AttackRogueString": [1.0, 0.0]},
    },
    {"entry_type": "completion", "run": "run-123"},
]


def _write_fixture(path):
    with open(path, "w", encoding="utf-8") as f:
        for line in FIXTURE_LINES:
            f.write(json.dumps(line) + "\n")


def test_ingest_report_writes_expected_rows(tmp_path):
    report_path = tmp_path / "smoke.report.jsonl"
    db_path = tmp_path / "attempts.sqlite3"
    _write_fixture(report_path)

    row_count = ingest_report(str(report_path), str(db_path))

    assert row_count == 3  # 1 output for attempt-1, 2 outputs for attempt-2

    conn = sqlite3.connect(str(db_path))
    rows = conn.execute(
        "SELECT run_id, attempt_uuid, output_index, output_text, detector_results "
        "FROM attempts ORDER BY attempt_uuid, output_index"
    ).fetchall()
    conn.close()

    assert len(rows) == 3
    assert all(r[0] == "run-123" for r in rows)

    attempt1 = rows[0]
    assert attempt1[1] == "attempt-1"
    assert attempt1[2] == 0
    assert attempt1[3] == "I can't help with that."
    assert json.loads(attempt1[4]) == {"promptinject.AttackRogueString": 0.0}

    attempt2_out1 = rows[1]
    assert attempt2_out1[1] == "attempt-2"
    assert attempt2_out1[2] == 0
    assert attempt2_out1[3] == "sure, here you go"
    assert json.loads(attempt2_out1[4]) == {"promptinject.AttackRogueString": 1.0}

    attempt2_out2 = rows[2]
    assert attempt2_out2[2] == 1
    assert attempt2_out2[3] == "no."
    assert json.loads(attempt2_out2[4]) == {"promptinject.AttackRogueString": 0.0}


def test_ingest_report_ignores_non_attempt_lines(tmp_path):
    report_path = tmp_path / "smoke.report.jsonl"
    db_path = tmp_path / "attempts.sqlite3"
    _write_fixture(report_path)

    ingest_report(str(report_path), str(db_path))

    conn = sqlite3.connect(str(db_path))
    count = conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
    conn.close()
    assert count == 3
