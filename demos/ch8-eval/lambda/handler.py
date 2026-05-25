"""AgentCore code-based evaluator Lambda — fault-type semantic match.

Conforms to the AgentCore Evaluations input/output contract documented at
https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/code-based-evaluators.html

Input event shape (we only use a subset):
{
  "schemaVersion": "1.0",
  "evaluatorId": "...",
  "evaluatorName": "hesheng_fault_type_v1",
  "evaluationLevel": "TRACE",
  "evaluationInput": {"sessionSpans": [...]},
  "evaluationReferenceInputs": [...],
  "evaluationTarget": {"traceIds": [...], "spanIds": [...]}
}

Returns:
  Success: {"label": "PASS"|"FAIL", "value": 0.0|1.0, "explanation": "..."}
  Error:   {"errorCode": "...", "errorMessage": "..."}

For this demo we also support a *direct-invoke fallback shape* that lets
the demo's run.py call the Lambda directly when AgentCore evaluator
registration is unavailable. In that mode the event has a flat shape:
{"predicted": "...", "expected": "..."}  → same response shape.
"""

from __future__ import annotations

import json
from typing import Any

# Equivalence classes — duplicated from src/ch8_eval/equivalence.py because
# the Lambda zip is self-contained (no shared layer). Keep these in sync
# with src/ch8_eval/equivalence.py — Ch8 README notes the duplication.
EQUIVALENCE_CLASSES: list[list[str]] = [
    ["伺服系统", "伺服电机", "伺服", "伺服驱动"],
    ["回零/编码器", "回零", "编码器", "参考点"],
    ["主轴/传动", "主轴", "传动"],
    ["Z 轴/丝杠", "Z轴/丝杠", "Z 轴", "Z轴", "丝杠"],
    ["传感器", "感应器", "探头", "限位"],
    ["PLC/通信", "PLC", "通信", "网络", "上位机"],
    ["液压系统", "液压"],
    ["液压/冷却", "冷却", "切削液"],
    ["电源系统", "电源", "供电"],
    ["导轨/润滑", "导轨", "润滑"],
]


def _canonical(label: str) -> str | None:
    if not label:
        return None
    for cls in EQUIVALENCE_CLASSES:
        if label in cls:
            return cls[0]
    return None


def _semantic_equal(predicted: str, expected: str) -> bool:
    if predicted == expected:
        return True
    cp = _canonical(predicted)
    ce = _canonical(expected)
    if cp is None or ce is None:
        return False
    return cp == ce


def _score(predicted: str, expected: str) -> dict:
    if not predicted or not expected:
        return {
            "label": "FAIL",
            "value": 0.0,
            "explanation": f"missing field (predicted={predicted!r} expected={expected!r})",
        }
    if _semantic_equal(predicted, expected):
        cp = _canonical(predicted) or predicted
        return {
            "label": "PASS",
            "value": 1.0,
            "explanation": f"semantic match (canonical={cp!r}; predicted={predicted!r}, expected={expected!r})",
        }
    return {
        "label": "FAIL",
        "value": 0.0,
        "explanation": f"no equivalence class match (predicted={predicted!r}, expected={expected!r})",
    }


def _extract_pred_expected_from_agentcore_event(event: dict) -> tuple[str, str]:
    """Pull predicted + expected fault types out of an AgentCore TRACE-level event.

    The agent's prediction lives in a span attribute named `gen_ai.completion`
    (matches OpenInference convention). The expected (ground-truth) value
    comes from `evaluationReferenceInputs` keyed by `expected_fault_type`.
    """
    spans = event.get("evaluationInput", {}).get("sessionSpans", []) or []
    target_traces = (event.get("evaluationTarget") or {}).get("traceIds", []) or []

    def _get_span_trace_id(span: dict) -> str:
        # AgentCore normalises OTel ids onto camelCase keys when the Lambda
        # receives them. Accept both shapes for safety.
        return span.get("traceId") or span.get("trace_id") or ""

    def _get_attr(span: dict, key: str) -> str:
        attrs = span.get("attributes")
        if isinstance(attrs, dict):
            return attrs.get(key) or ""
        if isinstance(attrs, list):
            for a in attrs:
                if a.get("key") != key:
                    continue
                v = a.get("value", {})
                # OTel anyValue: {string_value|stringValue: "..."}
                return v.get("string_value") or v.get("stringValue") or ""
        return ""

    predicted = ""
    for span in spans:
        if target_traces and _get_span_trace_id(span) not in target_traces:
            continue
        completion = _get_attr(span, "gen_ai.completion")
        if not completion:
            continue
        try:
            parsed = json.loads(completion)
            predicted = parsed.get("fault_type", "") or predicted
        except (ValueError, TypeError):
            pass

    expected = ""
    for ref in event.get("evaluationReferenceInputs", []) or []:
        # AgentCore shape: {"context":{...}, "expectedResponse":{"text":"..."}}
        er = ref.get("expectedResponse")
        if er and er.get("text"):
            expected = er["text"]
            break
        # Fallback shape (some preview builds): {"key":..., "value":...}
        if ref.get("key") == "expected_fault_type":
            expected = ref.get("value", "") or expected

    return predicted, expected


def lambda_handler(event: dict, context: Any) -> dict:
    """Two shapes supported:
    1. AgentCore TRACE-level event (schemaVersion present)
    2. Demo direct-invoke flat event {"predicted": "...", "expected": "..."}
    """
    try:
        if "schemaVersion" in event:
            predicted, expected = _extract_pred_expected_from_agentcore_event(event)
        else:
            predicted = event.get("predicted", "")
            expected = event.get("expected", "")
        return _score(predicted, expected)
    except Exception as e:  # never let evaluator throw — return error envelope
        return {
            "errorCode": "EVALUATOR_INTERNAL",
            "errorMessage": f"{type(e).__name__}: {e}",
        }
