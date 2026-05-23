"""Benchmark candidate Bedrock models on the work-ticket triage eval set.

Outputs:
- results/{timestamp}.json — raw runs
- results/latest.json — symlink-or-copy to most recent

Cost guardrail: refuses to run if eval has > 50 items unless --force.
"""

import argparse
import json
import os
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

import boto3

# Bedrock IDs verified in us-east-1 (2026-05-23). Anthropic models require
# cross-region inference profiles ('us.' prefix) — invoking the bare model
# ID returns ValidationException. Nova has both paths; we use the profile
# so all four go through the same call shape.
MODELS = {
    "claude-haiku-4-5":  "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "claude-sonnet-4-6": "us.anthropic.claude-sonnet-4-6",
    "claude-opus-4-7":   "us.anthropic.claude-opus-4-7",
    "nova-pro":          "us.amazon.nova-pro-v1:0",
}

PROMPT_TEMPLATE = """你是苏州合昇精密重工的工单分诊助手。给定客户报修工单，判断:
1. 应派给哪个团队 (机械组 或 电气组)
2. 故障大类 (从这些选: 伺服系统/主轴/传动/Z 轴/丝杠/传感器/PLC/通信/液压系统/液压/冷却/回零/编码器/电源系统/导轨/润滑)

只输出 JSON,不要解释。格式:
{{"team": "...", "fault_type": "..."}}

工单:
{ticket}
"""


def inference_config(model_id: str) -> dict:
    """Per-model inference config. Claude 4.7 family deprecated `temperature`
    on the Converse API — passing it returns ValidationException. Older
    models still accept it.
    """
    cfg: dict = {"maxTokens": 200}
    if "claude-opus-4-7" not in model_id and "claude-sonnet-4-6" not in model_id:
        cfg["temperature"] = 0.0
    return cfg


def call_converse(client, model_id: str, prompt: str) -> tuple[str, dict]:
    """Single Converse API call; returns (text, usage_dict)."""
    t0 = time.perf_counter()
    resp = client.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig=inference_config(model_id),
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000
    text = resp["output"]["message"]["content"][0]["text"]
    usage = resp.get("usage", {})
    return text, {
        "input_tokens": usage.get("inputTokens", 0),
        "output_tokens": usage.get("outputTokens", 0),
        "elapsed_ms": elapsed_ms,
    }


def parse_response(text: str) -> dict:
    """Extract {team, fault_type} JSON; tolerant to markdown fences."""
    s = text.strip()
    if s.startswith("```"):
        s = s.strip("`")
        if s.lower().startswith("json"):
            s = s[4:].strip()
    # Find first { and last } in case of preamble
    start = s.find("{")
    end = s.rfind("}")
    if start == -1 or end == -1:
        return {}
    try:
        return json.loads(s[start:end + 1])
    except json.JSONDecodeError:
        return {}


def score(predicted: dict, expected_team: str, expected_fault: str) -> dict:
    return {
        "team_correct": predicted.get("team") == expected_team,
        "fault_correct": predicted.get("fault_type") == expected_fault,
    }


def run_one_model(client, model_key: str, model_id: str, eval_items: list, runs: int) -> dict:
    """Run all eval items × N runs against one model."""
    per_item = []
    print(f"\n=== {model_key} ({model_id}) ===")
    for item in eval_items:
        prompt = PROMPT_TEMPLATE.format(ticket=item["ticket"])
        item_runs = []
        for r in range(runs):
            try:
                text, meta = call_converse(client, model_id, prompt)
                pred = parse_response(text)
                s = score(pred, item["expected_team"], item["expected_fault_type"])
                item_runs.append({**meta, "predicted": pred, **s, "raw": text[:200]})
            except Exception as e:
                item_runs.append({"error": str(e)})
                print(f"  ERROR on {item['id']} run {r}: {e}")
        avg_latency = statistics.mean(
            [r["elapsed_ms"] for r in item_runs if "elapsed_ms" in r]
        ) if any("elapsed_ms" in r for r in item_runs) else None
        team_acc = sum(r.get("team_correct", False) for r in item_runs) / runs
        fault_acc = sum(r.get("fault_correct", False) for r in item_runs) / runs
        per_item.append({
            "id": item["id"],
            "expected_team": item["expected_team"],
            "expected_fault": item["expected_fault_type"],
            "runs": item_runs,
            "team_acc": team_acc,
            "fault_acc": fault_acc,
            "avg_latency_ms": avg_latency,
        })
        print(f"  {item['id']}: team={team_acc:.0%} fault={fault_acc:.0%} {avg_latency:.0f}ms" if avg_latency else f"  {item['id']}: ERROR")

    overall_team = statistics.mean([x["team_acc"] for x in per_item])
    overall_fault = statistics.mean([x["fault_acc"] for x in per_item])
    latencies = [x["avg_latency_ms"] for x in per_item if x["avg_latency_ms"] is not None]
    in_tok = sum(r.get("input_tokens", 0) for it in per_item for r in it["runs"])
    out_tok = sum(r.get("output_tokens", 0) for it in per_item for r in it["runs"])
    return {
        "model_key": model_key,
        "model_id": model_id,
        "n_items": len(eval_items),
        "n_runs_per_item": runs,
        "per_item": per_item,
        "overall_team_acc": overall_team,
        "overall_fault_acc": overall_fault,
        "p50_latency_ms": statistics.median(latencies) if latencies else None,
        "p90_latency_ms": (sorted(latencies)[int(len(latencies)*0.9)] if latencies else None),
        "total_input_tokens": in_tok,
        "total_output_tokens": out_tok,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--eval", required=True, help="path to eval JSONL")
    p.add_argument("--models", default="all", help="comma list or 'all'")
    p.add_argument("--runs", type=int, default=3)
    p.add_argument("--region", default="us-east-1")
    p.add_argument("--force", action="store_true")
    args = p.parse_args()

    items = [json.loads(l) for l in Path(args.eval).read_text().splitlines() if l.strip()]
    if len(items) > 50 and not args.force:
        print(f"Eval has {len(items)} items — exceeds soft cap of 50. Pass --force.")
        return 2

    if args.models == "all":
        keys = list(MODELS.keys())
    else:
        keys = [k.strip() for k in args.models.split(",")]
        for k in keys:
            if k not in MODELS:
                print(f"Unknown model: {k}. Choices: {list(MODELS)}")
                return 2

    client = boto3.client("bedrock-runtime", region_name=args.region)
    out = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "region": args.region,
        "eval_path": args.eval,
        "results": {},
    }
    for k in keys:
        out["results"][k] = run_one_model(client, k, MODELS[k], items, args.runs)
    out["finished_at"] = datetime.now(timezone.utc).isoformat()

    Path("results").mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = Path(f"results/{ts}.json")
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    latest = Path("results/latest.json")
    if latest.exists():
        latest.unlink()
    latest.write_text(out_path.read_text())
    print(f"\nWrote {out_path} and results/latest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
