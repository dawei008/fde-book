"""Verify all ch14-agent resources are gone."""

from __future__ import annotations

import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

DEMO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO_DIR / "src"))
sys.path.insert(0, str(DEMO_DIR.parent / "hesheng-core" / "src"))

from ch14_agent.state import GATEWAY_NAME, LAMBDA_NAME, LAMBDA_ROLE  # noqa: E402
from hesheng_core import config  # noqa: E402

GATEWAY_ROLE = "fde-book-ch14-gateway-role"


def main() -> None:
    cfg = config.load()
    leftover: list[str] = []

    lam = boto3.client("lambda", region_name=cfg.region)
    try:
        lam.get_function(FunctionName=LAMBDA_NAME)
        leftover.append(f"Lambda still present: {LAMBDA_NAME}")
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
            leftover.append(f"Lambda check error: {e}")

    iam = boto3.client("iam", region_name=cfg.region)
    for role in (LAMBDA_ROLE, GATEWAY_ROLE):
        try:
            iam.get_role(RoleName=role)
            leftover.append(f"Role still present: {role}")
        except ClientError as e:
            if e.response["Error"]["Code"] != "NoSuchEntity":
                leftover.append(f"Role check error ({role}): {e}")

    # Gateway: best-effort. Some accounts have an org SCP that blocks
    # DeleteGateway even when CreateGateway is allowed; in that case the
    # gateway stays around as an orphan but it costs ~$0.01/day idle, so
    # we warn rather than fail. down.py preserves GATEWAY_ROLE in this
    # case so the gateway still references a live IAM role.
    gw_orphan = False
    try:
        ctrl = boto3.client("bedrock-agentcore-control", region_name=cfg.region)
        for gw in ctrl.list_gateways().get("items", []):
            if gw.get("name") == GATEWAY_NAME:
                gw_orphan = True
                print(f"  WARN: Gateway still present: {GATEWAY_NAME} "
                      "(probably blocked by org SCP — manual delete needed)")
    except Exception as e:
        print(f"  (gateway API skipped: {type(e).__name__})")

    if gw_orphan:
        # Cross-check: if the gateway is around but GATEWAY_ROLE got
        # deleted somehow, surface it loudly — re-attaching a target
        # later will need the role rebuilt first.
        try:
            iam.get_role(RoleName=GATEWAY_ROLE)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                print(f"  WARN: Gateway still here but {GATEWAY_ROLE} is gone "
                      "— rebuild the role before attaching a target.")

    # AgentCore Runtime
    try:
        ctrl = boto3.client("bedrock-agentcore-control", region_name=cfg.region)
        for rt in ctrl.list_agent_runtimes().get("agentRuntimes", []):
            n = rt.get("agentRuntimeName", "")
            if n.startswith("ch14hesheng_ch14_hesheng_agent"):
                leftover.append(f"Runtime still present: {n}")
    except Exception as e:
        print(f"  (runtime API skipped: {type(e).__name__})")

    # CloudFormation stack
    cf = boto3.client("cloudformation", region_name=cfg.region)
    try:
        s = cf.describe_stacks(StackName="AgentCore-ch14hesheng-default")
        st = s["Stacks"][0]["StackStatus"]
        if st not in ("DELETE_COMPLETE", "DELETE_IN_PROGRESS"):
            leftover.append(f"CDK stack still present: status={st}")
    except ClientError as e:
        if "does not exist" not in str(e):
            print(f"  describe_stacks warn: {e}")

    if leftover:
        print("LEFTOVERS DETECTED:")
        for l in leftover:
            print(f"  - {l}")
        sys.exit(1)
    print("Clean. No ch14-agent resources remain.")


if __name__ == "__main__":
    main()
