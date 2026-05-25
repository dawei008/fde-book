"""ch14-agent `make up` — provision Lambda + (optionally) AgentCore Gateway.

Steps (idempotent):
  1. Create IAM role for Lambda execution
  2. Package + deploy alarm_handler.py as Lambda
  3. Try to create AgentCore Gateway with lambda-target → MCP tool exposure
     (best-effort — preview-period SCPs may block CreateGatewayTarget)
  4. If AgentCore Runtime is already deployed (via `agentcore deploy`),
     grant its IAM role permission to invoke the Lambda + Athena
  5. Save state to data/ch14-state.json

The CDK-managed Runtime itself is deployed by `agentcore deploy` — see
the Makefile `up-runtime` target. That step is separate because it uses
CDK and takes 3-5 min.
"""

from __future__ import annotations

import sys
from pathlib import Path

import boto3

DEMO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO_DIR / "src"))
sys.path.insert(0, str(DEMO_DIR.parent / "hesheng-core" / "src"))

from ch14_agent.aws_resources import (  # noqa: E402
    deploy_lambda, ensure_lambda_role, ensure_runtime_role_policy,
    package_zip, try_create_gateway,
)
from ch14_agent.state import State  # noqa: E402
from hesheng_core import config  # noqa: E402

LAMBDA_HANDLER_FILE = DEMO_DIR / "lambda" / "alarm_handler.py"


def main() -> None:
    cfg = config.load()
    print(f"region={cfg.region} account={cfg.account}")
    state = State.load_or_empty()

    iam = boto3.client("iam", region_name=cfg.region)
    lam = boto3.client("lambda", region_name=cfg.region)

    print("[1/3] Lambda role + code")
    state.lambda_role_arn = ensure_lambda_role(iam, cfg.account)
    state.lambda_arn = deploy_lambda(
        lam, state.lambda_role_arn, package_zip(LAMBDA_HANDLER_FILE),
    )

    print("[2/3] AgentCore Gateway (best-effort)")
    try_create_gateway(cfg, state.lambda_arn, state)

    print("[3/3] AgentCore Runtime discovery")
    try:
        ctrl = boto3.client("bedrock-agentcore-control", region_name=cfg.region)
        for rt in ctrl.list_agent_runtimes().get("agentRuntimes", []):
            if rt.get("agentRuntimeName", "").startswith("ch14hesheng_ch14_hesheng_agent"):
                state.runtime_arn = rt.get("agentRuntimeArn", "")
                state.deploy_mode = "agentcore-runtime"
                state.notes.append(f"Found Runtime: {state.runtime_arn}")
                print(f"  found runtime: {state.runtime_arn[:80]}")
                if ensure_runtime_role_policy(cfg, state.lambda_arn):
                    print("  granted runtime role: lambda+athena+s3")
                else:
                    print("  (runtime role not yet visible — re-run after agentcore deploy)")
                break
    except Exception as e:
        state.notes.append(f"Runtime discovery skipped: {type(e).__name__}: {e}")

    if not state.runtime_arn:
        state.deploy_mode = "local"

    state.save()
    print("\nState saved:")
    print(f"  lambda_arn   = {state.lambda_arn}")
    print(f"  gateway_arn  = {state.gateway_arn or '(none)'}")
    print(f"  runtime_arn  = {state.runtime_arn or '(none — local mode)'}")


if __name__ == "__main__":
    main()
