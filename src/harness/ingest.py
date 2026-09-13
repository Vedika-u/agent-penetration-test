"""Parses a garak `*.report.jsonl` and loads its attack/response pairs into our own storage.

garak already logs everything we need per attempt (see `garak/attempt.py::Attempt.as_dict`):
probe name, prompt, outputs, and detector scores. This module just flattens that into rows
for `harness.storage`, one row per (attempt, output) pair, rather than re-implementing logging.
"""

import json

from harness import storage


def _iter_rows(record: dict, run_id: str | None):
    prompt = record.get("prompt") or {}
    prompt_text = prompt.get("text") if isinstance(prompt, dict) else None
    outputs = record.get("outputs") or []
    detector_results = record.get("detector_results") or {}

    for index, output in enumerate(outputs):
        output_text = output.get("text") if isinstance(output, dict) else None
        per_output_scores = {
            detector: scores[index] if index < len(scores) else None
            for detector, scores in detector_results.items()
        }
        yield {
            "run_id": run_id,
            "attempt_uuid": record.get("uuid"),
            "probe_classname": record.get("probe_classname"),
            "seq": record.get("seq"),
            "status": record.get("status"),
            "goal": record.get("goal"),
            "prompt_text": prompt_text,
            "output_index": index,
            "output_text": output_text,
            "detector_results": per_output_scores,
        }


def ingest_report(report_path: str, db_path: str) -> int:
    run_id = None
    rows = []

    with open(report_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            entry_type = record.get("entry_type")

            if entry_type == "init":
                run_id = record.get("run")
            elif entry_type == "attempt":
                rows.extend(_iter_rows(record, run_id))

    return storage.insert_attempts(db_path, rows)
