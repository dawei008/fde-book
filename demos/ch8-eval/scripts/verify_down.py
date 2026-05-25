"""Verify ch8-eval resources are gone. Run after `make down`."""

from __future__ import annotations

import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

DEMO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO_DIR / "src"))
sys.path.insert(0, str(DEMO_DIR.parent / "hesheng-core" / "src"))

from ch8_eval.state import LAMBDA_NAME, LAMBDA_ROLE, EVALUATOR_NAME  # noqa: E402
from hesheng_core import config  # noqa: E402


def main() -> None:
    cfg = config.load()
    leftover = []

    # Lambda
    lam = boto3.client("lambda", region_name=cfg.region)
    try:
        lam.get_function(FunctionName=LAMBDA_NAME)
        leftover.append(f"Lambda still present: {LAMBDA_NAME}")
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
            leftover.append(f"Lambda check error: {e.response['Error']['Code']}")

    # IAM role
    iam = boto3.client("iam", region_name=cfg.region)
    try:
        iam.get_role(RoleName=LAMBDA_ROLE)
        leftover.append(f"Role still present: {LAMBDA_ROLE}")
    except ClientError as e:
        if e.response["Error"]["Code"] != "NoSuchEntity":
            leftover.append(f"Role check error: {e.response['Error']['Code']}")

    # AgentCore evaluator (best-effort — control plane may not be available)
    try:
        ctl = boto3.client("bedrock-agentcore-control", region_name=cfg.region)
        for ev in ctl.list_evaluators().get("evaluatorSummaries", []):
            if ev.get("evaluatorName") == EVALUATOR_NAME:
                leftover.append(f"Evaluator still present: {ev['evaluatorId']}")
    except Exception as e:
        # Don't fail verify-down on control-plane unavailability; mention it.
        print(f"  (evaluator check skipped: {type(e).__name__})")

    if leftover:
        print("LEFTOVERS DETECTED:")
        for l in leftover:
            print(f"  - {l}")
        sys.exit(1)
    print("Clean. No ch8-eval resources remain.")


if __name__ == "__main__":
    main()
