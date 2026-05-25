"""Run Claude Haiku 4.5 over the 10 work tickets to produce predictions.jsonl.
This file is the *evaluation object* — same predictions feed both evaluators.

Reuses Ch6 prompt verbatim so this demo's predictions are comparable to
Ch6 6.3's "all four models score 40% on fault accuracy" finding.

Idempotent: if predictions.jsonl already exists, skip unless --force.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import boto3

DEMO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO_DIR.parent / "hesheng-core" / "src"))
from hesheng_core import config  # noqa: E402

MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

PROMPT_TEMPLATE = """你是苏州合昇精密重工的工单分诊助手。给定客户报修工单，判断:
1. 应派给哪个团队 (机械组 或 电气组)
2. 故障大类 (从这些选: 伺服系统/主轴/传动/Z 轴/丝杠/传感器/PLC/通信/液压系统/液压/冷却/回零/编码器/电源系统/导轨/润滑)

只输出 JSON,不要解释。格式:
{{"team": "...", "fault_type": "..."}}

工单:
{ticket}
"""


def _parse(text: str) -> dict:
    s = text.strip()
    if s.startswith("```"):
        s = s.strip("`")
        if s.lower().startswith("json"):
            s = s[4:].strip()
    start, end = s.find("{"), s.rfind("}")
    if start == -1 or end == -1:
        return {}
    try:
        return json.loads(s[start:end + 1])
    except json.JSONDecodeError:
        return {}


def predict_one(client, ticket: str) -> tuple[dict, dict]:
    t0 = time.perf_counter()
    resp = client.converse(
        modelId=MODEL_ID,
        messages=[{"role": "user", "content": [{"text": PROMPT_TEMPLATE.format(ticket=ticket)}]}],
        inferenceConfig={"maxTokens": 200, "temperature": 0.0},
    )
    elapsed = (time.perf_counter() - t0) * 1000
    text = resp["output"]["message"]["content"][0]["text"]
    usage = resp.get("usage", {})
    return _parse(text), {
        "raw": text,
        "elapsed_ms": elapsed,
        "input_tokens": usage.get("inputTokens", 0),
        "output_tokens": usage.get("outputTokens", 0),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--force", action="store_true")
    args = p.parse_args()

    cfg = config.load()
    src = DEMO_DIR / "data" / "tickets.jsonl"
    dst = DEMO_DIR / "data" / "predictions.jsonl"

    if dst.exists() and not args.force:
        print(f"Predictions already exist at {dst}. Use --force to regenerate.")
        return 0

    items = [json.loads(l) for l in src.read_text().splitlines() if l.strip()]
    client = boto3.client("bedrock-runtime", region_name=cfg.region)

    out_lines = []
    for it in items:
        pred, meta = predict_one(client, it["ticket"])
        row = {
            "id": it["id"],
            "expected_team": it["expected_team"],
            "expected_fault_type": it["expected_fault_type"],
            "predicted_team": pred.get("team", ""),
            "predicted_fault_type": pred.get("fault_type", ""),
            "elapsed_ms": meta["elapsed_ms"],
            "input_tokens": meta["input_tokens"],
            "output_tokens": meta["output_tokens"],
        }
        out_lines.append(json.dumps(row, ensure_ascii=False))
        print(f"  {it['id']}: predicted={pred} expected_fault={it['expected_fault_type']!r}")

    dst.write_text("\n".join(out_lines) + "\n")
    print(f"\nWrote {len(out_lines)} predictions to {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
