"""ch14-agent — AWS resource helpers used by up.py / down.py.

Keeps scripts thin by isolating boto3 boilerplate. IAM policy bodies live
in iam_policies.py.
"""

from __future__ import annotations

import io
import json
import time
import zipfile
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from .iam_policies import (
    gateway_invoke_lambda_policy, gateway_target_schema, gateway_trust_policy,
    lambda_trust_policy, runtime_invoke_tools_policy,
)
from .state import GATEWAY_NAME, LAMBDA_NAME, LAMBDA_ROLE, State

GATEWAY_ROLE = "fde-book-ch14-gateway-role"


def ensure_lambda_role(iam, account: str) -> str:
    arn = f"arn:aws:iam::{account}:role/{LAMBDA_ROLE}"
    try:
        iam.create_role(
            RoleName=LAMBDA_ROLE,
            AssumeRolePolicyDocument=json.dumps(lambda_trust_policy()),
            Description="Ch14 agent demo Lambda execution role.",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] != "EntityAlreadyExists":
            raise
    iam.attach_role_policy(
        RoleName=LAMBDA_ROLE,
        PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    )
    time.sleep(8)
    return arn


def package_zip(source: Path) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("alarm_handler.py", source.read_text(encoding="utf-8"))
    return buf.getvalue()


def deploy_lambda(lam, role_arn: str, zip_bytes: bytes) -> str:
    try:
        resp = lam.create_function(
            FunctionName=LAMBDA_NAME, Runtime="python3.12", Role=role_arn,
            Handler="alarm_handler.handler", Code={"ZipFile": zip_bytes},
            Timeout=10, MemorySize=256,
            Description="Ch14 — alarm-code lookup tool (Hesheng overseas).",
        )
        arn = resp["FunctionArn"]
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceConflictException":
            raise
        lam.update_function_code(FunctionName=LAMBDA_NAME, ZipFile=zip_bytes)
        arn = lam.get_function(FunctionName=LAMBDA_NAME)["Configuration"]["FunctionArn"]
    for _ in range(20):
        cfg_ = lam.get_function(FunctionName=LAMBDA_NAME)["Configuration"]
        if cfg_["State"] == "Active" and cfg_.get("LastUpdateStatus") in (None, "Successful"):
            break
        time.sleep(2)
    return arn


def ensure_gateway_role(cfg) -> str:
    iam = boto3.client("iam", region_name=cfg.region)
    arn = f"arn:aws:iam::{cfg.account}:role/{GATEWAY_ROLE}"
    try:
        iam.create_role(
            RoleName=GATEWAY_ROLE,
            AssumeRolePolicyDocument=json.dumps(gateway_trust_policy()),
            Description="Ch14 AgentCore Gateway service role",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] != "EntityAlreadyExists":
            return ""
    iam.put_role_policy(
        RoleName=GATEWAY_ROLE, PolicyName="invoke-lambda",
        PolicyDocument=json.dumps(
            gateway_invoke_lambda_policy(cfg.region, cfg.account, LAMBDA_NAME)
        ),
    )
    time.sleep(5)
    return arn


def try_create_gateway(cfg, lambda_arn: str, state: State) -> None:
    """Best-effort: create Gateway and attach Lambda target. Records every
    step in state.notes so README explanations stay in sync with run history."""
    ctrl = boto3.client("bedrock-agentcore-control", region_name=cfg.region)
    role_arn = ensure_gateway_role(cfg)
    if not role_arn:
        state.notes.append("Gateway: role creation failed; skipped.")
        return

    gw_arn = ""
    try:
        for gw in ctrl.list_gateways().get("items", []):
            if gw.get("name") == GATEWAY_NAME:
                gw_id = gw.get("gatewayId", "")
                gw_arn = gw.get("gatewayArn") or \
                    f"arn:aws:bedrock-agentcore:{cfg.region}:{cfg.account}:gateway/{gw_id}"
                state.gateway_arn = gw_arn
                state.notes.append(f"Gateway exists: {GATEWAY_NAME}")
                break
    except Exception as e:
        print(f"  list_gateways warn: {type(e).__name__}: {e}")

    if not gw_arn:
        try:
            resp = ctrl.create_gateway(
                name=GATEWAY_NAME,
                description="Hesheng overseas data gateway — alarm + tickets",
                protocolType="MCP", authorizerType="AWS_IAM", roleArn=role_arn,
            )
            gw_arn = resp.get("gatewayArn", "") or resp.get("arn", "")
            state.gateway_arn = gw_arn
            state.gateway_url = resp.get("gatewayUrl", "") or resp.get("url", "")
            state.notes.append(f"Gateway created: {GATEWAY_NAME}")
            print(f"  created gateway: {GATEWAY_NAME}")
        except Exception as e:
            state.notes.append(f"Gateway create skipped: {type(e).__name__}: {e}")
            print(f"  Gateway create skipped: {type(e).__name__}")
            return

    _try_attach_target(ctrl, gw_arn, lambda_arn, state)


def _try_attach_target(ctrl, gw_arn: str, lambda_arn: str, state: State) -> None:
    try:
        for t in ctrl.list_gateway_targets(gatewayIdentifier=gw_arn).get("items", []):
            if t.get("name") == "alarm-lookup":
                state.notes.append("Gateway target alarm-lookup already exists")
                return
    except Exception as e:
        print(f"  list_gateway_targets warn: {type(e).__name__}: {e}")
    try:
        ctrl.create_gateway_target(
            gatewayIdentifier=gw_arn, name="alarm-lookup",
            targetConfiguration=gateway_target_schema(lambda_arn),
            credentialProviderConfigurations=[
                {"credentialProviderType": "GATEWAY_IAM_ROLE"}
            ],
        )
        state.notes.append("Gateway target (lambda) attached.")
        print("  attached gateway target: alarm-lookup")
    except Exception as e:
        state.notes.append(f"Gateway target attach failed: {type(e).__name__}: {e}")
        print(f"  WARN gateway target attach failed: {e}")


def ensure_runtime_role_policy(cfg, lambda_arn: str) -> bool:
    """Attach inline policy to AgentCore Runtime CDK role (Lambda + Athena)."""
    iam = boto3.client("iam", region_name=cfg.region)
    target_role = ""
    for page in iam.get_paginator("list_roles").paginate():
        for r in page.get("Roles", []):
            if r["RoleName"].startswith("AgentCore-ch14hesheng-def-Application"):
                target_role = r["RoleName"]
                break
        if target_role:
            break
    if not target_role:
        return False
    iam.put_role_policy(
        RoleName=target_role, PolicyName="invoke-tools",
        PolicyDocument=json.dumps(runtime_invoke_tools_policy(cfg, lambda_arn)),
    )
    return True
