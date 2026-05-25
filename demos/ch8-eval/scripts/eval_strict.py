"""Strict string-match evaluator (Ch6 6.3 节那个 40% evaluator).

Reads data/predictions.jsonl, scores each row by exact string equality,
writes results/strict.json.

This is the *naive* evaluator the book argues against — when 4 different
models all score 40% on fault accuracy, this is who's lying.
"""

from __future__ import annotations

import json
from pathlib import Path

DEMO_DIR = Path(__file__).resolve().parent.parent


def main() -> int:
    src = DEMO_DIR / "data" / "predictions.jsonl"
    dst = DEMO_DIR / "results" / "strict.json"
    dst.parent.mkdir(exist_ok=True)

    rows = [json.loads(l) for l in src.read_text().splitlines() if l.strip()]

    per_item = []
    team_correct = 0
    fault_correct = 0
    for r in rows:
        team_ok = r["predicted_team"] == r["expected_team"]
        fault_ok = r["predicted_fault_type"] == r["expected_fault_type"]
        team_correct += int(team_ok)
        fault_correct += int(fault_ok)
        per_item.append({
            "id": r["id"],
            "predicted_team": r["predicted_team"],
            "expected_team": r["expected_team"],
            "team_correct": team_ok,
            "predicted_fault_type": r["predicted_fault_type"],
            "expected_fault_type": r["expected_fault_type"],
            "fault_correct": fault_ok,
        })

    n = len(rows)
    summary = {
        "evaluator": "strict_string_match",
        "n_items": n,
        "team_accuracy": team_correct / n if n else 0.0,
        "fault_accuracy": fault_correct / n if n else 0.0,
        "per_item": per_item,
    }
    dst.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"strict: team={summary['team_accuracy']:.0%} fault={summary['fault_accuracy']:.0%}")
    print(f"  wrote {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
