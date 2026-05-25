"""ch7-rag `make run` — execute eval set across 3 approaches and produce comparison.

Each question runs once per approach. Records: text, keyword hit ratio,
latency (ms), input/output tokens. Output: rows.jsonl + summary.json + summary.md.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import boto3

DEMO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO_DIR / "src"))
sys.path.insert(0, str(DEMO_DIR.parent / "hesheng-core" / "src"))

from ch7_rag.state import State  # noqa: E402
from ch7_rag.approaches import approach_a, approach_b, approach_c  # noqa: E402
from hesheng_core import config  # noqa: E402

EVAL_FILE = DEMO_DIR / "data" / "eval-v0.jsonl"
RESULTS_DIR = DEMO_DIR / "results"

# Claude Haiku 4.5 us-east-1 on-demand pricing (per million tokens)
PRICE_IN_PER_M = 1.00
PRICE_OUT_PER_M = 5.00
PRICE_RERANK_PER_CALL = 0.001  # Cohere Rerank v3.5 ~$1/1k searches


def hit_ratio(text: str, keywords: list[str]) -> float:
    if not keywords:
        return 0.0
    return sum(1 for k in keywords if k.lower() in text.lower()) / len(keywords)


def percentile(xs: list[float], p: float) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    idx = max(0, min(len(s) - 1, int(round(p / 100 * (len(s) - 1)))))
    return s[idx]


def cost_per_1k(rows: list[dict], add_per_call: float = 0.0) -> float:
    if not rows:
        return 0.0
    avg_in = sum(r["input_tokens"] for r in rows) / len(rows)
    avg_out = sum(r["output_tokens"] for r in rows) / len(rows)
    per_call = (avg_in / 1_000_000 * PRICE_IN_PER_M
                + avg_out / 1_000_000 * PRICE_OUT_PER_M
                + add_per_call)
    return per_call * 1000


def run_one(q: dict, br_runtime, br_agent_runtime, kb_id: str, region: str, account: str) -> list[dict]:
    rows = []
    for approach, fn in [
        ("A_prompting", lambda: approach_a(br_runtime, q["question"])),
        ("B_rag", lambda: approach_b(br_agent_runtime, kb_id, q["question"], region, account)),
        ("C_rag_rerank", lambda: approach_c(br_agent_runtime, br_runtime, kb_id, q["question"])),
    ]:
        try:
            res = fn()
            hit = hit_ratio(res["text"], q["expected_answer_keywords"])
            row = {"qid": q["id"], "category": q["category"], "approach": approach,
                   "hit_ratio": hit, **{k: v for k, v in res.items() if k != "text"},
                   "answer": res["text"][:300]}
            print(f"  {approach}: hit={hit:.2f}  lat={res['latency_ms']:.0f}ms  "
                  f"in={res['input_tokens']} out={res['output_tokens']}")
        except Exception as e:
            print(f"  {approach}: ERROR {type(e).__name__}: {str(e)[:120]}")
            row = {"qid": q["id"], "category": q["category"], "approach": approach,
                   "error": f"{type(e).__name__}: {str(e)[:200]}", "hit_ratio": 0.0,
                   "latency_ms": 0, "input_tokens": 0, "output_tokens": 0, "answer": ""}
        rows.append(row)
    return rows


def build_summary(rows: list[dict]) -> dict:
    summary = {}
    for ap in ("A_prompting", "B_rag", "C_rag_rerank"):
        sub = [r for r in rows if r["approach"] == ap and "error" not in r]
        all_sub = [r for r in rows if r["approach"] == ap]
        lats = [r["latency_ms"] for r in sub]
        add = PRICE_RERANK_PER_CALL if ap == "C_rag_rerank" else 0.0
        summary[ap] = {
            "n": len(all_sub), "errors": len(all_sub) - len(sub),
            "accuracy_avg": sum(r["hit_ratio"] for r in all_sub) / max(1, len(all_sub)),
            "p50_latency_ms": percentile(lats, 50),
            "p95_latency_ms": percentile(lats, 95),
            "cost_per_1k_calls_usd": round(cost_per_1k(sub, add), 4),
            "by_category": {
                cat: round(sum(r["hit_ratio"] for r in all_sub if r["category"] == cat)
                           / max(1, sum(1 for r in all_sub if r["category"] == cat)), 3)
                for cat in ("simple", "rag", "multi-doc", "refusal")},
        }
    return summary


def write_outputs(rows: list[dict], summary: dict) -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "rows.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows))
    (RESULTS_DIR / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    md = ["# Ch7 RAG comparison\n", "## Headline\n",
          "| approach | accuracy | P50 latency | P95 latency | $/1k calls | errors |",
          "|---|---|---|---|---|---|"]
    for ap, s in summary.items():
        md.append(f"| {ap} | {s['accuracy_avg']:.2%} | {s['p50_latency_ms']:.0f} ms | "
                  f"{s['p95_latency_ms']:.0f} ms | ${s['cost_per_1k_calls_usd']:.4f} | {s['errors']} |")
    md.append("\n## By category (accuracy)\n")
    md.append("| approach | simple | rag | multi-doc | refusal |")
    md.append("|---|---|---|---|---|")
    for ap, s in summary.items():
        c = s["by_category"]
        md.append(f"| {ap} | {c['simple']:.2f} | {c['rag']:.2f} | {c['multi-doc']:.2f} | {c['refusal']:.2f} |")
    (RESULTS_DIR / "summary.md").write_text("\n".join(md) + "\n")


def main() -> None:
    cfg = config.load()
    state = State.load()
    eval_set = [json.loads(l) for l in EVAL_FILE.read_text().splitlines() if l.strip()]
    print(f"Running eval: {len(eval_set)} questions x 3 approaches")

    br_runtime = boto3.client("bedrock-runtime", region_name=cfg.region)
    br_agent_runtime = boto3.client("bedrock-agent-runtime", region_name=cfg.region)

    rows = []
    for i, q in enumerate(eval_set, 1):
        print(f"\n[{i}/{len(eval_set)}] {q['id']} ({q['category']}): {q['question'][:60]}...")
        rows.extend(run_one(q, br_runtime, br_agent_runtime, state.kb_id, cfg.region, cfg.account))

    summary = build_summary(rows)
    write_outputs(rows, summary)

    print(f"\nResults written to {RESULTS_DIR}/")
    print("\n=== Headline ===")
    for ap, s in summary.items():
        print(f"  {ap}: acc={s['accuracy_avg']:.2%}  p50={s['p50_latency_ms']:.0f}ms  "
              f"${s['cost_per_1k_calls_usd']:.4f}/1k  errors={s['errors']}")


if __name__ == "__main__":
    main()
