"""ch8-eval `make run` — generate predictions (if needed) and run both evaluators.

Outputs:
- data/predictions.jsonl (Bedrock predictions, idempotent)
- results/strict.json (string-equality evaluator)
- results/semantic.json (Lambda evaluator, via AgentCore or direct-invoke)
- results/comparison.md (human-readable head-to-head)
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

DEMO_DIR = Path(__file__).resolve().parent.parent
PY = sys.executable


def run(script: str) -> None:
    print(f"\n=== {script} ===")
    r = subprocess.run([PY, str(DEMO_DIR / "scripts" / script)], cwd=DEMO_DIR)
    if r.returncode != 0:
        sys.exit(r.returncode)


def write_comparison() -> None:
    strict = json.loads((DEMO_DIR / "results" / "strict.json").read_text())
    semantic = json.loads((DEMO_DIR / "results" / "semantic.json").read_text())

    lines: list[str] = []
    lines.append("# Ch8 demo: strict vs semantic evaluator\n")
    lines.append("Same predictions. Two evaluator implementations. Look at the gap.\n")
    lines.append("")
    lines.append("| evaluator | team accuracy | fault accuracy | mode |")
    lines.append("|---|---|---|---|")
    lines.append(
        f"| Strict string match | {strict['team_accuracy']:.0%} "
        f"| {strict['fault_accuracy']:.0%} | local Python |"
    )
    lines.append(
        f"| Semantic equivalence | {semantic['team_accuracy']:.0%} "
        f"| {semantic['fault_accuracy']:.0%} | {semantic['mode']} |"
    )
    lines.append("")
    lines.append("## Per-item disagreement (where the two evaluators differ on fault_type)\n")
    lines.append("| id | predicted | expected | strict | semantic |")
    lines.append("|---|---|---|---|---|")

    s_items = {it["id"]: it for it in strict["per_item"]}
    m_items = {it["id"]: it for it in semantic["per_item"]}
    diffs = 0
    for tid in sorted(s_items.keys()):
        s = s_items[tid]
        m = m_items[tid]
        if s["fault_correct"] != m["fault_correct"]:
            diffs += 1
            lines.append(
                f"| {tid} | {s['predicted_fault_type']} | {s['expected_fault_type']} "
                f"| {'PASS' if s['fault_correct'] else 'FAIL'} "
                f"| {'PASS' if m['fault_correct'] else 'FAIL'} |"
            )
    if diffs == 0:
        lines.append("| _(no disagreements — model already aligned with expected strings)_ | | | | |")

    lines.append("")
    lines.append(f"**Mode**: {semantic['mode']}  ")
    if semantic.get("evaluator_arn"):
        lines.append(f"**Evaluator ARN**: `{semantic['evaluator_arn']}`")
    else:
        lines.append("**Evaluator ARN**: _(direct-invoke mode — no AgentCore evaluator registered)_")

    lines.append("")
    lines.append("## 读出来的工程意义")
    lines.append("")
    lines.append(
        "Ch6 6.3 节里 4 个候选模型在 fault accuracy 上**齐刷刷**拿了一个数字 "
        "（demo 里我们再现的就是这个现象）。先怀疑评估，不怀疑模型。"
        "把 evaluator 从 `predicted == expected` 换成"
        "\"在不在同一个等价类里\"——靠的是**业务知识**（伺服系统 ≡ 伺服电机），"
        "不是模型能力——分立刻往上跳。"
    )

    out = DEMO_DIR / "results" / "comparison.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {out}")


def main() -> None:
    run("predict.py")
    run("eval_strict.py")
    run("eval_semantic.py")
    write_comparison()
    print("\nch8-eval run complete. See results/comparison.md")


if __name__ == "__main__":
    main()
