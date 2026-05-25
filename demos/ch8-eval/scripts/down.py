"""ch8-eval `make down` — teardown. Idempotent.

Order:
  1. Delete AgentCore evaluator (if registered) — must come before Lambda
     because the evaluator references the Lambda ARN.
  2. Delete Lambda function.
  3. Delete IAM role (detach managed policies first).
  4. Remove state file.
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

from ch8_eval.state import State, LAMBDA_NAME, LAMBDA_ROLE, EVALUATOR_NAME, STATE_FILE  # noqa: E402
from hesheng_core import config  # noqa: E402


def main() -> None:
    cfg = config.load()
    try:
        state = State.load()
    except FileNotFoundError:
        print("No ch8-state.json — nothing to tear down.")
        return

    print(f"Tearing down ch8-eval in {cfg.region} ...")

    # 1. AgentCore evaluator (if any). Even if state thinks we didn't register,
    # do a defensive list_evaluators() in case state diverged.
    try:
        ctl = boto3.client("bedrock-agentcore-control", region_name=cfg.region)
        target_id = state.evaluator_id
        if not target_id:
            try:
                for ev in ctl.list_evaluators().get("evaluatorSummaries", []):
                    if ev.get("evaluatorName") == EVALUATOR_NAME:
                        target_id = ev["evaluatorId"]
                        break
            except ClientError as e:
                print(f"  list_evaluators: {e.response['Error']['Code']}")
        if target_id:
            try:
                ctl.delete_evaluator(evaluatorId=target_id)
                print(f"  deleted AgentCore evaluator: {target_id}")
                # Wait briefly for it to release the Lambda
                time.sleep(5)
            except ClientError as e:
                code = e.response["Error"]["Code"]
                if code != "ResourceNotFoundException":
                    print(f"  evaluator delete: {code}")
        else:
            print("  no AgentCore evaluator to delete")
    except Exception as e:
        print(f"  evaluator cleanup skipped: {type(e).__name__}: {e}")

    # 2. Lambda
    lam = boto3.client("lambda", region_name=cfg.region)
    try:
        lam.delete_function(FunctionName=LAMBDA_NAME)
        print(f"  deleted Lambda: {LAMBDA_NAME}")
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
            print(f"  Lambda delete: {e.response['Error']['Code']}")

    # 3. IAM role
    iam = boto3.client("iam", region_name=cfg.region)
    try:
        for p in iam.list_role_policies(RoleName=LAMBDA_ROLE)["PolicyNames"]:
            iam.delete_role_policy(RoleName=LAMBDA_ROLE, PolicyName=p)
        for p in iam.list_attached_role_policies(RoleName=LAMBDA_ROLE)["AttachedPolicies"]:
            iam.detach_role_policy(RoleName=LAMBDA_ROLE, PolicyArn=p["PolicyArn"])
        iam.delete_role(RoleName=LAMBDA_ROLE)
        print(f"  deleted role: {LAMBDA_ROLE}")
    except ClientError as e:
        if e.response["Error"]["Code"] != "NoSuchEntity":
            print(f"  role delete: {e.response['Error']['Code']}")

    # 4. State file
    if STATE_FILE.exists():
        STATE_FILE.unlink()
        print(f"  removed: {STATE_FILE.name}")

    print("\nch8-eval torn down. Verify with `make verify-down`.")


if __name__ == "__main__":
    main()
