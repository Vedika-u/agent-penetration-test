"""CLI: run garak against the target agent's /attack endpoint, then ingest the report.

Usage:
    uv run python -m harness.run [--spec probes.promptinject] [--report_prefix agent-redteam]

Assumes the target agent is already running (see target_agent.main) and reachable at the URI
configured in configs/rest_generator.json.
"""

import argparse
from pathlib import Path

import garak._config as garak_config
import garak.cli

from harness.ingest import ingest_report

CONFIG_PATH = Path(__file__).parent / "configs" / "rest_generator.json"
DEFAULT_DB_PATH = "data/attempts.sqlite3"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--spec",
        default="probes.promptinject",
        help="garak probe selection spec (see `garak --help` for syntax)",
    )
    parser.add_argument(
        "--report_prefix",
        default="agent-redteam",
        help="prefix for garak's report.jsonl file",
    )
    parser.add_argument(
        "--db_path",
        default=DEFAULT_DB_PATH,
        help="sqlite db to ingest attempt rows into",
    )
    args = parser.parse_args()

    garak.cli.main(
        [
            "--target_type",
            "rest",
            "--generator_option_file",
            str(CONFIG_PATH),
            "--spec",
            args.spec,
            "--report_prefix",
            args.report_prefix,
        ]
    )

    report_path = garak_config.transient.report_filename
    row_count = ingest_report(report_path, args.db_path)
    print(f"Ingested {row_count} attempt rows from {report_path} into {args.db_path}")


if __name__ == "__main__":
    main()
