"""ch13-guardrails `make up` — create the Bedrock Guardrail and publish a
version. Idempotent via data/ch13-state.json.

Why a published version: Converse's `guardrailConfig` requires a numeric
version. DRAFT can be tested via `apply_guardrail` directly, but Converse
attachment needs a version like "1".
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

DEMO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO_DIR / "src"))
sys.path.insert(0, str(DEMO_DIR.parent / "hesheng-core" / "src"))

from ch13_guardrails.state import (  # noqa: E402
    BLOCKED_INPUT_MSG, BLOCKED_OUTPUT_MSG, GUARDRAIL_NAME, State,
    guardrail_config,
)
from hesheng_core import config  # noqa: E402

TAGS = [{"key": "Project", "value": "fde-book"},
        {"key": "Demo", "value": "ch13-guardrails"}]


def find_existing(bedrock) -> dict | None:
    paginator = bedrock.get_paginator("list_guardrails")
    for page in paginator.paginate():
        for g in page.get("guardrails", []):
            if g["name"] == GUARDRAIL_NAME:
                return g
    return None


def ensure_guardrail(bedrock, state: State) -> None:
    existing = find_existing(bedrock)
    if existing:
        state.guardrail_id = existing["id"]
        state.guardrail_arn = existing["arn"]
        print(f"  guardrail already present: {state.guardrail_id}")
        return
    cfg = guardrail_config()
    resp = bedrock.create_guardrail(
        name=GUARDRAIL_NAME,
        description="Ch13 demo: PII anonymize, denied topic, prompt attack, grounding",
        blockedInputMessaging=BLOCKED_INPUT_MSG,
        blockedOutputsMessaging=BLOCKED_OUTPUT_MSG,
        tags=TAGS,
        **cfg,
    )
    state.guardrail_id = resp["guardrailId"]
    state.guardrail_arn = resp["guardrailArn"]
    print(f"  created guardrail: {state.guardrail_id}")


def wait_ready(bedrock, gid: str) -> None:
    for _ in range(40):
        g = bedrock.get_guardrail(guardrailIdentifier=gid)
        st = g.get("status")
        if st == "READY":
            return
        if st in ("FAILED",):
            raise RuntimeError(f"guardrail FAILED: {g}")
        time.sleep(3)
    raise RuntimeError("guardrail not READY in 120s")


def ensure_version(bedrock, state: State) -> None:
    if state.guardrail_version:
        try:
            bedrock.get_guardrail(
                guardrailIdentifier=state.guardrail_id,
                guardrailVersion=state.guardrail_version,
            )
            print(f"  version already present: {state.guardrail_version}")
            return
        except ClientError:
            state.guardrail_version = ""
    resp = bedrock.create_guardrail_version(
        guardrailIdentifier=state.guardrail_id,
        description="ch13 v1",
    )
    state.guardrail_version = resp["version"]
    print(f"  published version: {state.guardrail_version}")


def main() -> None:
    cfg = config.load()
    print(f"region={cfg.region} account={cfg.account}")
    state = State.load_or_empty()
    bedrock = boto3.client("bedrock", region_name=cfg.region)

    print("[1/3] Create guardrail")
    ensure_guardrail(bedrock, state); state.save()
    print("[2/3] Wait READY")
    wait_ready(bedrock, state.guardrail_id)
    print("[3/3] Publish version")
    ensure_version(bedrock, state); state.save()

    print("\nState saved:")
    for k, v in state.__dict__.items():
        if v:
            print(f"  {k:20s} = {v}")


if __name__ == "__main__":
    main()
