"""Pretty-print bench.py results into the table the book uses."""

import argparse
import json
import sys
from pathlib import Path

# us-east-1 on-demand pricing (USD per 1M tokens), as of 2026-05-23.
# Sources: Bedrock pricing page; pin if anything diverges.
PRICING = {
    "claude-haiku-4-5":  {"input": 1.00,  "output":  5.00},
    "claude-sonnet-4-6": {"input": 3.00,  "output": 15.00},
    "claude-opus-4-7":   {"input": 15.00, "output": 75.00},
    "nova-pro":          {"input": 0.80,  "output":  3.20},
}


def fmt_pct(v):
    return f"{v*100:.1f}%" if v is not None else "—"


def fmt_ms(v):
    return f"{v:.0f}ms" if v is not None else "—"


def estimate_cost_per_1k_tickets(in_tok, out_tok, n_calls, pricing):
    """Scale the observed token usage to 1k tickets and price it."""
    in_per_call = in_tok / max(n_calls, 1)
    out_per_call = out_tok / max(n_calls, 1)
    cost_1k = (in_per_call * 1000 * pricing["input"] / 1_000_000 +
               out_per_call * 1000 * pricing["output"] / 1_000_000)
    return cost_1k, in_per_call, out_per_call


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("results", help="path to results JSON")
    args = p.parse_args()

    data = json.loads(Path(args.results).read_text())
    rows = []
    for key, r in data["results"].items():
        n_calls = r["n_items"] * r["n_runs_per_item"]
        cost_1k, in_per, out_per = estimate_cost_per_1k_tickets(
            r["total_input_tokens"], r["total_output_tokens"], n_calls,
            PRICING.get(key, {"input": 0, "output": 0})
        )
        rows.append({
            "model": key,
            "team_acc": r["overall_team_acc"],
            "fault_acc": r["overall_fault_acc"],
            "p50": r["p50_latency_ms"],
            "p90": r["p90_latency_ms"],
            "in_per": in_per,
            "out_per": out_per,
            "cost_1k": cost_1k,
        })

    print(f"\nEval: {data['eval_path']}")
    print(f"Region: {data['region']} · Started: {data['started_at']}\n")
    print(f"{'Model':<22}{'Team':>10}{'Fault':>10}{'P50':>10}{'P90':>10}"
          f"{'In/call':>10}{'Out/call':>10}{'$/1k':>10}")
    print("─" * 92)
    for row in rows:
        print(f"{row['model']:<22}"
              f"{fmt_pct(row['team_acc']):>10}"
              f"{fmt_pct(row['fault_acc']):>10}"
              f"{fmt_ms(row['p50']):>10}"
              f"{fmt_ms(row['p90']):>10}"
              f"{row['in_per']:>10.0f}"
              f"{row['out_per']:>10.0f}"
              f"{'$'+format(row['cost_1k'],'.2f'):>10}")
    print()

    # Markdown version for pasting into the chapter
    print("\nMarkdown (paste into chapter):\n")
    print("| 模型 | 派工准确率 | 故障类型准确率 | P50 延迟 | P90 延迟 | $/1k 工单 |")
    print("|---|---|---|---|---|---|")
    for row in rows:
        print(f"| {row['model']} | {fmt_pct(row['team_acc'])} | {fmt_pct(row['fault_acc'])} | "
              f"{fmt_ms(row['p50'])} | {fmt_ms(row['p90'])} | ${row['cost_1k']:.2f} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
