"""Verify the ch13-guardrails resources are fully gone."""

from __future__ import annotations

import sys
from pathlib import Path

import boto3

DEMO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO_DIR / "src"))
sys.path.insert(0, str(DEMO_DIR.parent / "hesheng-core" / "src"))

from ch13_guardrails.state import GUARDRAIL_NAME  # noqa: E402
from hesheng_core import config  # noqa: E402


def main() -> None:
    cfg = config.load()
    bedrock = boto3.client("bedrock", region_name=cfg.region)
    leftover: list[str] = []
    paginator = bedrock.get_paginator("list_guardrails")
    for page in paginator.paginate():
        for g in page.get("guardrails", []):
            if g["name"] == GUARDRAIL_NAME:
                leftover.append(f"Guardrail still present: {g['id']}")
    if leftover:
        print("LEFTOVERS DETECTED:")
        for l in leftover:
            print(f"  - {l}")
        sys.exit(1)
    print("Clean. No ch13-guardrails resources remain.")


if __name__ == "__main__":
    main()
