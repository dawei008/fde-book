"""ch8-eval `make up` — deploy the code-based evaluator.

Steps:
  1. IAM role for Lambda execution
  2. Package + deploy Lambda (handler.py)
  3. Try to register the Lambda as an AgentCore code-based evaluator
     via `bedrock-agentcore-control` CreateEvaluator. If the API is
     unavailable in this region or the call fails, fall back to
     direct-invoke mode and record the reason in state.

Idempotent — safe to re-run.
"""

from __future__ import annotations

import io
import json
import sys
import time
import zipfile
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

DEMO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO_DIR / "src"))
sys.path.insert(0, str(DEMO_DIR.parent / "hesheng-core" / "src"))

from ch8_eval.state import State, LAMBDA_NAME, LAMBDA_ROLE, EVALUATOR_NAME  # noqa: E402
from hesheng_core import config  # noqa: E402

LAMBDA_HANDLER_FILE = DEMO_DIR / "lambda" / "handler.py"


def ensure_lambda_role(iam, account: str) -> str:
    role_arn = f"arn:aws:iam::{account}:role/{LAMBDA_ROLE}"
    trust = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }],
    }
    try:
        iam.create_role(
            RoleName=LAMBDA_ROLE,
            AssumeRolePolicyDocument=json.dumps(trust),
            Description="Ch8 eval demo Lambda execution role for code-based evaluator",
        )
        print(f"  created role: {LAMBDA_ROLE}")
    except ClientError as e:
        if e.response["Error"]["Code"] != "EntityAlreadyExists":
            raise
        print(f"  role exists: {LAMBDA_ROLE}")

    iam.attach_role_policy(
        RoleName=LAMBDA_ROLE,
        PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    )
    return role_arn


def package_lambda() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("handler.py", LAMBDA_HANDLER_FILE.read_text(encoding="utf-8"))
    return buf.getvalue()


def ensure_lambda(lam, role_arn: str) -> str:
    code = package_lambda()
    try:
        resp = lam.create_function(
            FunctionName=LAMBDA_NAME,
            Runtime="python3.12",
            Role=role_arn,
            Handler="handler.lambda_handler",
            Code={"ZipFile": code},
            Timeout=10,
            MemorySize=128,
            Description="Ch8 eval fault-type semantic equivalence evaluator",
        )
        print(f"  created Lambda: {LAMBDA_NAME}")
        return resp["FunctionArn"]
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceConflictException":
            raise
        # Update code if function exists
        for _ in range(8):
            try:
                resp = lam.update_function_code(FunctionName=LAMBDA_NAME, ZipFile=code)
                print(f"  updated Lambda code: {LAMBDA_NAME}")
                return resp["FunctionArn"]
            except ClientError as e2:
                if e2.response["Error"]["Code"] in ("ResourceConflictException", "InvalidParameterValueException"):
                    time.sleep(3)
                    continue
                raise
        raise RuntimeError("Lambda update_function_code never settled")


def wait_lambda_active(lam) -> None:
    for _ in range(20):
        cfg = lam.get_function_configuration(FunctionName=LAMBDA_NAME)
        if cfg["State"] == "Active" and cfg.get("LastUpdateStatus") == "Successful":
            return
        time.sleep(2)


def try_register_evaluator(state: State) -> State:
    """Best-effort registration. If anything goes wrong (API not available,
    permission, schema), fall back to direct-invoke and remember why.
    """
    try:
        ctl = boto3.client("bedrock-agentcore-control", region_name=state.region)
    except Exception as e:
        state.used_agentcore_register = False
        state.register_failure_reason = f"client init: {e}"
        return state

    # Idempotency: if an evaluator with our name exists, reuse it
    try:
        for ev in ctl.list_evaluators().get("evaluatorSummaries", []):
            if ev.get("evaluatorName") == EVALUATOR_NAME:
                state.evaluator_id = ev["evaluatorId"]
                state.evaluator_arn = ev["evaluatorArn"]
                state.used_agentcore_register = True
                print(f"  evaluator exists: {EVALUATOR_NAME} ({state.evaluator_id})")
                return state
    except ClientError as e:
        # If list fails, surface and try to create anyway
        print(f"  list_evaluators: {e.response['Error']['Code']} (continuing)")

    try:
        resp = ctl.create_evaluator(
            evaluatorName=EVALUATOR_NAME,
            level="TRACE",
            evaluatorConfig={
                "codeBased": {
                    "lambdaConfig": {
                        "lambdaArn": state.lambda_arn,
                        "lambdaTimeoutInSeconds": 30,
                    }
                }
            },
            description="Ch8 demo: fault-type semantic equivalence (Hesheng triage)",
        )
        state.evaluator_id = resp["evaluatorId"]
        state.evaluator_arn = resp["evaluatorArn"]
        state.used_agentcore_register = True
        print(f"  registered AgentCore evaluator: {state.evaluator_id}")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        state.used_agentcore_register = False
        state.register_failure_reason = f"{code}: {e.response['Error'].get('Message', '')[:200]}"
        print(f"  AgentCore register FAILED ({code}); falling back to direct-invoke mode")
    except Exception as e:
        state.used_agentcore_register = False
        state.register_failure_reason = f"{type(e).__name__}: {e}"
        print(f"  AgentCore register failed ({type(e).__name__}); falling back to direct-invoke mode")
    return state


def main() -> None:
    cfg = config.load()
    print(f"Bringing up ch8-eval in {cfg.region} / account {cfg.account}")

    iam = boto3.client("iam", region_name=cfg.region)
    lam = boto3.client("lambda", region_name=cfg.region)

    state = State.load_or_empty(region=cfg.region, account=cfg.account)

    print("\n[1/3] IAM role for Lambda ...")
    state.lambda_role_arn = ensure_lambda_role(iam, cfg.account)
    state.save()
    time.sleep(8)  # IAM propagation

    print("\n[2/3] Lambda function ...")
    state.lambda_arn = ensure_lambda(lam, state.lambda_role_arn)
    wait_lambda_active(lam)
    # Explicit invoke grant for AgentCore Evaluations. Preview tier seems to
    # auto-grant via service-linked role today, but stricter accounts can
    # see AccessDenied on Evaluate without this. Cheap insurance.
    try:
        lam.add_permission(
            FunctionName=LAMBDA_NAME,
            StatementId="agentcore-invoke",
            Action="lambda:InvokeFunction",
            Principal="bedrock-agentcore.amazonaws.com",
            SourceArn=f"arn:aws:bedrock-agentcore:{cfg.region}:{cfg.account}:evaluator/*",
        )
        print("  added invoke permission for bedrock-agentcore.amazonaws.com")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceConflictException":
            pass  # already granted
        else:
            raise
    state.save()

    print("\n[3/3] AgentCore evaluator (best-effort register) ...")
    state = try_register_evaluator(state)
    state.save()

    if state.used_agentcore_register:
        print(f"\nch8-eval is up. Evaluator={state.evaluator_id}  Lambda={LAMBDA_NAME}")
    else:
        print(f"\nch8-eval is up in DIRECT-INVOKE mode. Lambda={LAMBDA_NAME}")
        print(f"  reason AgentCore register skipped: {state.register_failure_reason}")
    print(f"Run `make run` next.")


if __name__ == "__main__":
    main()
