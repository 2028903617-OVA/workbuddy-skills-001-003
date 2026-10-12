#!/usr/bin/env python3
"""Append one validated flow runtime ledger entry as JSONL."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = (
    "run_id",
    "goal",
    "status",
    "target",
    "command",
    "confirmation",
    "started_at",
    "ended_at",
    "attempts",
    "errors",
)

VALID_STATUSES = {"succeeded", "failed", "blocked", "skipped"}
VALID_CONFIRMATIONS = {"approved", "declined", "not_required", "skipped"}


def load_entry(raw: str) -> dict[str, Any]:
    if raw.startswith("@"):
        raw = Path(raw[1:]).expanduser().read_text(encoding="utf-8")
    try:
        entry = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"entry is not valid JSON: {exc}") from exc
    if not isinstance(entry, dict):
        raise ValueError("entry must be a JSON object")
    return entry


def validate_entry(entry: dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_FIELDS if field not in entry]
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")
    if entry["status"] not in VALID_STATUSES:
        raise ValueError(f"status must be one of: {', '.join(sorted(VALID_STATUSES))}")
    if entry["confirmation"] not in VALID_CONFIRMATIONS:
        raise ValueError(
            f"confirmation must be one of: {', '.join(sorted(VALID_CONFIRMATIONS))}"
        )
    if not isinstance(entry["attempts"], int) or entry["attempts"] < 1:
        raise ValueError("attempts must be a positive integer")
    if not isinstance(entry["errors"], list):
        raise ValueError("errors must be a list")


def default_ledger(workspace: Path) -> Path:
    return workspace / "tempfile" / "flow-runtime-ledger.jsonl"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Workspace root used for the default tempfile ledger path.",
    )
    parser.add_argument(
        "--ledger",
        type=Path,
        help="Override ledger path. Defaults to <workspace>/tempfile/flow-runtime-ledger.jsonl.",
    )
    parser.add_argument(
        "--entry",
        required=True,
        help="Ledger JSON object, or @path/to/entry.json.",
    )
    args = parser.parse_args()

    try:
        workspace = args.workspace.expanduser().resolve()
        ledger = args.ledger.expanduser() if args.ledger else default_ledger(workspace)
        entry = load_entry(args.entry)
        validate_entry(entry)
        ledger.parent.mkdir(parents=True, exist_ok=True)
        with ledger.open("a", encoding="utf-8") as output:
            output.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    except Exception as exc:  # noqa: BLE001 - CLI should print a concise validation error.
        print(f"append ledger failed: {exc}", file=sys.stderr)
        return 1

    print(f"ledger_appended: {ledger}")
    print(f"run_id: {entry['run_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
