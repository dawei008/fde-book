"""Trace summarization + per-test verdict logic for ch13-guardrails.

Kept out of run.py so run.py stays focused on the call flow.
"""

from __future__ import annotations


def summarize_trace(trace: dict) -> dict:
    """Pull the noteworthy bits from the guardrail trace, keep tiny."""
    g = trace.get("guardrail", {})
    summary: dict = {}
    for direction in ("inputAssessment", "outputAssessments"):
        block = g.get(direction)
        if not block:
            continue
        # outputAssessments is dict keyed by guardrail-id with list of
        # assessments; inputAssessment has the same shape.
        for _, assessments in block.items():
            assess_list = (assessments if isinstance(assessments, list)
                           else [assessments])
            for a in assess_list:
                for k in ("topicPolicy", "contentPolicy",
                          "sensitiveInformationPolicy"):
                    pol = a.get(k)
                    if not pol:
                        continue
                    for sub in ("topics", "filters",
                                "piiEntities", "regexes"):
                        for it in pol.get(sub, []):
                            if it.get("action") in ("BLOCKED",
                                                    "ANONYMIZED"):
                                summary.setdefault(
                                    f"{direction}.{k}.{sub}", []
                                ).append({
                                    "name": it.get("name") or it.get("type"),
                                    "action": it.get("action"),
                                })
    return summary


def verdict(test: dict, result: dict) -> str:
    expect = test["expect"]
    if not result["ok"]:
        return f"FAIL_ERROR:{result.get('error_code')}"
    stop = result.get("stopReason")
    text = result.get("output_text", "")
    if expect == "guardrail_intervened":
        return ("PASS" if stop == "guardrail_intervened"
                else f"FAIL_NOT_BLOCKED:{stop}")
    if expect == "pii_anonymized":
        raw_phone = "138-1234-5678"
        has_token = ("{PHONE}" in text or "<PHONE" in text
                     or "{NAME}" in text or "<NAME" in text)
        if raw_phone in text:
            return "FAIL_PHONE_LEAKED"
        if not has_token and stop != "end_turn":
            return f"FAIL_UNEXPECTED:{stop}"
        return "PASS" if has_token else "PASS_NO_LEAK"
    if expect == "passes_through":
        return ("PASS" if stop == "end_turn"
                else f"FAIL_BLOCKED:{stop}")
    return f"UNKNOWN_EXPECT:{expect}"
