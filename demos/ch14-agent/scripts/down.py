"""ch14-agent `make down` — teardown.

Order:
  1. Tear down AgentCore Runtime CDK stack (if deployed)
  2. Delete Gateway target(s) and Gateway (if present)
  3. Delete Lambda function
  4. Detach + delete IAM roles
  5. Drop state file

All steps idempotent.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

DEMO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO_DIR / "src"))
sys.path.insert(0, str(DEMO_DIR.parent / "hesheng-core" / "src"))

from ch14_agent.state import (  # noqa: E402
    GATEWAY_NAME, LAMBDA_NAME, LAMBDA_ROLE, STATE_FILE, State,
)
from hesheng_core import config  # noqa: E402

GATEWAY_ROLE = "fde-book-ch14-gateway-role"
AGENTCORE_PROJECT = DEMO_DIR / "agentcore_project" / "ch14hesheng"


def delete_gateway(cfg, gw_arn: str) -> bool:
    """Returns True if gateway deleted (or never existed), False if SCP blocked."""
    if not gw_arn:
        # Try to find by name in case state was lost
        try:
            ctrl = boto3.client("bedrock-agentcore-control", region_name=cfg.region)
            for gw in ctrl.list_gateways().get("items", []):
                if gw.get("name") == GATEWAY_NAME:
                    gw_arn = gw.get("gatewayArn") or gw.get("arn", "")
                    break
        except Exception as e:
            print(f"  list_gateways skipped: {type(e).__name__}: {e}")
            return True  # nothing we can do; treat as clean for role-cleanup purposes

    if not gw_arn:
        print("  no gateway to delete")
        return True

    try:
        ctrl = boto3.client("bedrock-agentcore-control", region_name=cfg.region)
        # Delete targets first
        try:
            for t in ctrl.list_gateway_targets(gatewayIdentifier=gw_arn).get("items", []):
                tid = t.get("targetId") or t.get("name")
                ctrl.delete_gateway_target(gatewayIdentifier=gw_arn, targetId=tid)
                print(f"  deleted gateway target: {tid}")
        except Exception as e:
            print(f"  list/delete targets warn: {type(e).__name__}: {e}")
        ctrl.delete_gateway(gatewayIdentifier=gw_arn)
        print(f"  deleted gateway: {gw_arn[:80]}")
        return True
    except Exception as e:
        print(f"  delete_gateway warn: {type(e).__name__}: {e}")
        return False


def delete_lambda(cfg) -> None:
    lam = boto3.client("lambda", region_name=cfg.region)
    try:
        lam.delete_function(FunctionName=LAMBDA_NAME)
        print(f"  deleted lambda: {LAMBDA_NAME}")
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
            print(f"  delete_function warn: {e}")
        else:
            print("  lambda already gone")


def delete_role(cfg, role_name: str) -> None:
    iam = boto3.client("iam", region_name=cfg.region)
    try:
        # Detach managed policies
        for p in iam.list_attached_role_policies(RoleName=role_name).get("AttachedPolicies", []):
            iam.detach_role_policy(RoleName=role_name, PolicyArn=p["PolicyArn"])
        # Delete inline policies
        for n in iam.list_role_policies(RoleName=role_name).get("PolicyNames", []):
            iam.delete_role_policy(RoleName=role_name, PolicyName=n)
        iam.delete_role(RoleName=role_name)
        print(f"  deleted role: {role_name}")
    except ClientError as e:
        if e.response["Error"]["Code"] != "NoSuchEntity":
            print(f"  delete_role warn: {e}")
        else:
            print(f"  role already gone: {role_name}")


def teardown_runtime(cfg) -> None:
    """Tear down the AgentCore Runtime CDK stack if it exists."""
    cf = boto3.client("cloudformation", region_name=cfg.region)
    stack = "AgentCore-ch14hesheng-default"
    try:
        cf.describe_stacks(StackName=stack)
    except ClientError as e:
        if "does not exist" in str(e):
            print("  no CDK stack to delete")
            return
        print(f"  describe_stacks warn: {e}")
        return
    try:
        cf.delete_stack(StackName=stack)
        print(f"  initiated CDK stack deletion: {stack}")
        # Wait for deletion (fire-and-forget if it takes too long)
        waiter = cf.get_waiter("stack_delete_complete")
        try:
            waiter.wait(StackName=stack,
                        WaiterConfig={"Delay": 10, "MaxAttempts": 60})
            print(f"  CDK stack deleted: {stack}")
        except Exception as e:
            print(f"  stack delete timeout (still in progress): {e}")
    except ClientError as e:
        print(f"  delete_stack warn: {e}")


def main() -> None:
    cfg = config.load()
    state = State.load_or_empty()

    print("[1/4] AgentCore Runtime (CDK stack)")
    teardown_runtime(cfg)

    print("[2/4] AgentCore Gateway")
    gw_gone = delete_gateway(cfg, state.gateway_arn)

    print("[3/4] Lambda")
    delete_lambda(cfg)

    print("[4/4] IAM roles")
    delete_role(cfg, LAMBDA_ROLE)
    if gw_gone:
        delete_role(cfg, GATEWAY_ROLE)
    else:
        # Gateway delete blocked (likely SCP). Keep GATEWAY_ROLE so the
        # user can re-attach a target once SCP is loosened — otherwise
        # the orphan gateway would reference a deleted role.
        print(f"  KEEPING role: {GATEWAY_ROLE} (gateway still present; SCP?)")

    if STATE_FILE.exists():
        STATE_FILE.unlink()
        print(f"  removed {STATE_FILE.name}")


if __name__ == "__main__":
    main()
