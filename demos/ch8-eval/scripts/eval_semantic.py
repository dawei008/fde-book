"""Semantic-equivalence evaluator backed by Lambda.

Two execution modes, picked by `state.used_agentcore_register`:
1. AgentCore mode: call `bedrock-agentcore Evaluate` with the registered
   evaluator ID. AgentCore invokes the Lambda for us.
2. Direct-invoke mode: call `lambda.Invoke` ourselves. Fallback for when
   AgentCore registration was unavailable. Same Lambda code either way.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import boto3


def _otel_trace_id(seed: str) -> str:
    """OTel trace IDs are 32 lowercase hex. Deterministic from seed."""
    return hashlib.sha256(seed.encode()).hexdigest()[:32]


def _otel_span_id(seed: str) -> str:
    return hashlib.sha256(("span:" + seed).encode()).hexdigest()[:16]

DEMO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO_DIR / "src"))
sys.path.insert(0, str(DEMO_DIR.parent / "hesheng-core" / "src"))

from ch8_eval.state import State, LAMBDA_NAME  # noqa: E402
from hesheng_core import config  # noqa: E402


def _build_agentcore_call(predicted: str, expected: str, item_id: str) -> dict:
    """Pack a single (predicted, expected) pair into an AgentCore Evaluate
    request shaped like an OTel span dump.

    AgentCore validates the span schema strictly: it wants OTel-style
    trace_id / span_id (lower hex), `scope`, `start_time`, `end_time`,
    plus `attributes` as a list of `{key, value}` items (not a dict).
    """
    trace_id = _otel_trace_id(item_id)
    span_id = _otel_span_id(item_id)
    session_id = _otel_trace_id("session:" + item_id)
    completion_json = json.dumps({"fault_type": predicted}, ensure_ascii=False)
    # OTel "unix nano" timestamps. Use a fixed offset so re-runs are stable.
    start_ns = 1_700_000_000_000_000_000
    end_ns = start_ns + 1_000_000_000  # +1s
    return {
        "evaluationInput": {
            "sessionSpans": [{
                "trace_id": trace_id,
                "span_id": span_id,
                "name": "Agent.invoke",
                "scope": {"name": "ch8-eval-demo", "version": "1.0"},
                "kind": "SPAN_KIND_INTERNAL",
                "status": {"status_code": "STATUS_CODE_OK"},
                "start_time": start_ns,
                "end_time": end_ns,
                # AgentCore's parser wants attributes as a dict (despite OTel
                # protobuf-shaped span fields elsewhere). Confirmed by trial.
                "attributes": {
                    "gen_ai.completion": completion_json,
                    "session.id": session_id,
                },
            }],
        },
        "evaluationTarget": {"traceIds": [trace_id]},
        "evaluationReferenceInputs": [
            {
                "context": {
                    "spanContext": {
                        "sessionId": session_id,
                        "traceId": trace_id,
                    },
                },
                "expectedResponse": {"text": expected},
            },
        ],
    }


def _via_agentcore(state: State, predicted: str, expected: str, item_id: str) -> dict:
    """Returns {label,value,explanation} or {error*}."""
    client = boto3.client("bedrock-agentcore", region_name=state.region)
    payload = _build_agentcore_call(predicted, expected, item_id)
    resp = client.evaluate(evaluatorId=state.evaluator_id, **payload)
    results = resp.get("evaluationResults", [])
    if not results:
        return {"errorCode": "NO_RESULT", "errorMessage": "Evaluate returned empty results"}
    r = results[0]
    if r.get("errorCode"):
        return {"errorCode": r["errorCode"], "errorMessage": r.get("errorMessage", "")}
    return {
        "label": r.get("label"),
        "value": r.get("value"),
        "explanation": r.get("explanation"),
    }


def _via_direct_invoke(state: State, predicted: str, expected: str) -> dict:
    client = boto3.client("lambda", region_name=state.region)
    resp = client.invoke(
        FunctionName=LAMBDA_NAME,
        InvocationType="RequestResponse",
        Payload=json.dumps({"predicted": predicted, "expected": expected}).encode("utf-8"),
    )
    body = json.loads(resp["Payload"].read())
    if resp.get("FunctionError"):
        return {"errorCode": "LAMBDA_ERROR", "errorMessage": json.dumps(body)[:500]}
    return body


def main() -> int:
    state = State.load()

    src = DEMO_DIR / "data" / "predictions.jsonl"
    dst = DEMO_DIR / "results" / "semantic.json"
    dst.parent.mkdir(exist_ok=True)

    rows = [json.loads(l) for l in src.read_text().splitlines() if l.strip()]
    use_agentcore = state.used_agentcore_register and bool(state.evaluator_id)
    mode = "agentcore" if use_agentcore else "direct-invoke"
    print(f"semantic eval via {mode} (Lambda={LAMBDA_NAME})")

    per_item = []
    fault_correct = 0
    team_correct = 0
    errors = 0
    for r in rows:
        # Fault-type via Lambda (the demo's hero path)
        if use_agentcore:
            res = _via_agentcore(state, r["predicted_fault_type"], r["expected_fault_type"], item_id=r["id"])
            # If AgentCore call itself fails (e.g. quota/preview gap), degrade
            # to direct-invoke for this item — the book's point is the *eval
            # logic*, not the control plane plumbing.
            if "errorCode" in res:
                print(f"  {r['id']}: AgentCore Evaluate errored ({res['errorCode']}); falling back direct-invoke")
                res = _via_direct_invoke(state, r["predicted_fault_type"], r["expected_fault_type"])
        else:
            res = _via_direct_invoke(state, r["predicted_fault_type"], r["expected_fault_type"])

        if "errorCode" in res:
            fault_ok = False
            errors += 1
        else:
            fault_ok = res.get("label") == "PASS"
            fault_correct += int(fault_ok)

        # Team accuracy stays a simple equality check — the book's argument is
        # specifically about fault-type strings; team is binary 机械组/电气组.
        team_ok = r["predicted_team"] == r["expected_team"]
        team_correct += int(team_ok)

        per_item.append({
            "id": r["id"],
            "predicted_team": r["predicted_team"],
            "expected_team": r["expected_team"],
            "team_correct": team_ok,
            "predicted_fault_type": r["predicted_fault_type"],
            "expected_fault_type": r["expected_fault_type"],
            "fault_correct": fault_ok,
            "lambda_response": res,
        })
        time.sleep(0.05)  # gentle pacing

    n = len(rows)
    summary = {
        "evaluator": "semantic_equivalence_lambda",
        "mode": mode,
        "evaluator_arn": state.evaluator_arn or None,
        "lambda_name": LAMBDA_NAME,
        "n_items": n,
        "team_accuracy": team_correct / n if n else 0.0,
        "fault_accuracy": fault_correct / n if n else 0.0,
        "errors": errors,
        "per_item": per_item,
    }
    dst.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"semantic ({mode}): team={summary['team_accuracy']:.0%} fault={summary['fault_accuracy']:.0%} errors={errors}")
    print(f"  wrote {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
