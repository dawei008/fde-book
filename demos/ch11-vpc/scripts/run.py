"""ch11-vpc `make run` — fire two real Bedrock calls through the same
VPC endpoint and prove the endpoint policy is the layer doing the
filtering.

Test 1: invoke Lambda with model_id = haiku-4.5  -> expect SUCCESS
Test 2: invoke Lambda with model_id = opus-4.7   -> expect AccessDenied

Both calls go through the same private subnet, the same VPC endpoint,
and the same Lambda IAM role (which allows ALL bedrock:* on *). The
ONLY thing that changes is whether the endpoint policy allows the
target inference profile ARN. That's the Ch11 evidence.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import boto3

DEMO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO_DIR / "src"))
sys.path.insert(0, str(DEMO_DIR.parent / "hesheng-core" / "src"))

from ch11_vpc.state import (  # noqa: E402
    ALLOWED_MODEL, DENIED_MODEL, LAMBDA_NAME, State,
)
from hesheng_core import config  # noqa: E402

RESULTS_DIR = DEMO_DIR / "results"


def invoke(lam, model_id: str) -> dict:
    resp = lam.invoke(
        FunctionName=LAMBDA_NAME,
        InvocationType="RequestResponse",
        Payload=json.dumps({"model_id": model_id}).encode(),
    )
    if "FunctionError" in resp:
        raise RuntimeError(
            f"Lambda crashed: {resp['Payload'].read().decode()}"
        )
    return json.loads(resp["Payload"].read().decode())


def label(test_name: str, payload: dict, expect_ok: bool) -> str:
    if expect_ok:
        return "SUCCESS" if payload.get("ok") else "FAIL_UNEXPECTED"
    # Expect failure — be lenient about the exact code, but it MUST come
    # back AccessDenied / not a generic timeout, otherwise we haven't
    # proved the endpoint policy is the cause.
    if payload.get("ok"):
        return "FAIL_UNEXPECTED_SUCCESS"
    code = (payload.get("error_code") or "").lower()
    msg = (payload.get("error_message") or "").lower()
    if "accessdenied" in code or "accessdenied" in msg or "not authorized" in msg:
        return "EXPECTED_DENIED"
    return f"FAIL_UNEXPECTED_ERROR:{payload.get('error_code')}"


def main() -> None:
    cfg = config.load()
    state = State.load()
    if not state.lambda_arn:
        print("State missing lambda_arn — re-run `make up`.", file=sys.stderr)
        sys.exit(1)

    lam = boto3.client("lambda", region_name=cfg.region)

    print(f"[1/2] Invoking Lambda with ALLOWED model: {ALLOWED_MODEL}")
    t1 = invoke(lam, ALLOWED_MODEL)
    t1_label = label("test1", t1, expect_ok=True)
    print(f"Test 1 (haiku via VPC endpoint): {t1_label}")
    if t1.get("ok"):
        print(f"  response: {t1.get('response_text')!r}  "
              f"(in={t1.get('input_tokens')} out={t1.get('output_tokens')})")
    else:
        print(f"  error: {t1.get('error_code')} | {(t1.get('error_message') or '')[:240]}")

    print(f"\n[2/2] Invoking Lambda with DENIED model: {DENIED_MODEL}")
    t2 = invoke(lam, DENIED_MODEL)
    t2_label = label("test2", t2, expect_ok=False)
    print(f"Test 2 (opus via VPC endpoint): {t2_label}")
    if t2.get("ok"):
        print(f"  response: {t2.get('response_text')!r}")
    else:
        print(f"  error: {t2.get('error_code')} | {(t2.get('error_message') or '')[:240]}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = {
        "endpoint_id": state.endpoint_id,
        "lambda_arn": state.lambda_arn,
        "allowed_model": ALLOWED_MODEL,
        "denied_model": DENIED_MODEL,
        "test1_label": t1_label, "test1_payload": t1,
        "test2_label": t2_label, "test2_payload": t2,
    }
    (RESULTS_DIR / "ch11-results.json").write_text(json.dumps(out, indent=2))

    pass_test1 = (t1_label == "SUCCESS")
    pass_test2 = (t2_label == "EXPECTED_DENIED")
    print("\n=== verdict ===")
    print(f"  haiku via VPC endpoint: {t1_label}")
    print(f"  opus  via VPC endpoint: {t2_label}")
    if pass_test1 and pass_test2:
        print("\nPASS: endpoint policy is the security perimeter, not IAM.")
        return
    print("\nFAIL: see results/ch11-results.json")
    sys.exit(2)


if __name__ == "__main__":
    main()
