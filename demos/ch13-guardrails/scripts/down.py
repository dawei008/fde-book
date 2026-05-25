"""ch13-guardrails `make down` — delete the guardrail (and all versions
with it). Idempotent.
"""

from __future__ import annotations

import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

DEMO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO_DIR / "src"))
sys.path.insert(0, str(DEMO_DIR.parent / "hesheng-core" / "src"))

from ch13_guardrails.state import GUARDRAIL_NAME, STATE_FILE, State  # noqa: E402
from hesheng_core import config  # noqa: E402


def find_by_name(bedrock, name: str) -> str | None:
    paginator = bedrock.get_paginator("list_guardrails")
    for page in paginator.paginate():
        for g in page.get("guardrails", []):
            if g["name"] == name:
                return g["id"]
    return None


def del_guardrail(bedrock, gid: str) -> None:
    try:
        bedrock.delete_guardrail(guardrailIdentifier=gid)
        print(f"  deleted guardrail: {gid}")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("ResourceNotFoundException",):
            print(f"  guardrail already gone: {gid}")
            return
        raise


def main() -> None:
    cfg = config.load()
    state = State.load_or_empty()
    bedrock = boto3.client("bedrock", region_name=cfg.region)

    gid = state.guardrail_id or find_by_name(bedrock, GUARDRAIL_NAME)
    if gid:
        print(f"[1/1] Delete guardrail {gid}")
        del_guardrail(bedrock, gid)
    else:
        print("[1/1] No guardrail to delete.")

    if STATE_FILE.exists():
        STATE_FILE.unlink()
        print(f"  removed {STATE_FILE.name}")


if __name__ == "__main__":
    main()
