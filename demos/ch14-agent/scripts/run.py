"""ch14-agent `make run` — invoke the agent on 5 test prompts.

Two execution modes (auto-selected from data/ch14-state.json):

  - "agentcore-runtime": Calls bedrock-agentcore InvokeAgentRuntime against
                        the deployed Runtime ARN. Tool calls happen inside
                        the runtime; we reconstruct them from CloudWatch
                        OTel logs (see ch14_agent.tracing).

  - "local": Runs the Strands agent in-process. Same code/model/tools, just
             no Runtime hop. Lets us instrument tool calls via monkey-patch.

Records per prompt: prompt, answer, mode, total latency, tool_calls.
Writes results/rows.jsonl + results/summary.md.
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import boto3

DEMO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO_DIR / "src"))
sys.path.insert(0, str(DEMO_DIR.parent / "hesheng-core" / "src"))

from ch14_agent import tools as tools_mod  # noqa: E402
from ch14_agent.agent import make_strands_agent  # noqa: E402
from ch14_agent.state import State  # noqa: E402
from ch14_agent.tracing import ToolCallLog, fetch_runtime_tool_calls  # noqa: E402
from hesheng_core import config  # noqa: E402

PROMPTS = [
    "T-2025-Q4-0142 这条工单分给哪个组？",
    "ALM 4501 是什么意思？",
    "如果有人查 ALM 9999 你会怎么做？请用 dry_run 演示一下你会怎么调工具，不要实际查。",
    "Singapore 站点 P1 工单平均解决时间是多少小时？",
    "你能不能帮我写一首诗？",
]


@dataclass
class Row:
    prompt: str
    answer: str
    mode: str = ""
    tool_calls: list[ToolCallLog] = field(default_factory=list)
    total_latency_ms: int = 0
    trace_id: str = ""
    error: str = ""


# ── local mode ─────────────────────────────────────────────────────────────


def _instrument(log: list[ToolCallLog]) -> tuple:
    orig_q, orig_l = tools_mod.query_tickets_impl, tools_mod.lookup_alarm_code_impl

    def wrap_q(sql: str, max_rows: int = 50, **kw):
        t0 = time.time()
        out = orig_q(sql, max_rows=max_rows, **kw)
        log.append(ToolCallLog(
            name="query_tickets", input_preview=(sql or "")[:120],
            latency_ms=int((time.time() - t0) * 1000),
            ok=bool(out.get("ok")), error_code=str(out.get("error_code", "")),
        ))
        return out

    def wrap_l(code: str, dry_run: bool = False, **kw):
        t0 = time.time()
        out = orig_l(code=code, dry_run=dry_run, **kw)
        log.append(ToolCallLog(
            name="lookup_alarm_code",
            input_preview=f"code={code!r} dry_run={dry_run}",
            latency_ms=int((time.time() - t0) * 1000),
            ok=bool(out.get("ok")), error_code=str(out.get("error_code", "")),
        ))
        return out

    tools_mod.query_tickets_impl = wrap_q
    tools_mod.lookup_alarm_code_impl = wrap_l
    return orig_q, orig_l


def _extract_text(result: Any) -> str:
    if isinstance(result, str):
        return result
    msg = getattr(result, "message", None)
    if msg is not None:
        content = getattr(msg, "content", None)
        if content is None and hasattr(msg, "get"):
            content = msg.get("content")
        if isinstance(content, list):
            parts = [b["text"] for b in content
                     if isinstance(b, dict) and "text" in b]
            if parts:
                return "\n".join(parts)
    return str(result)[:2000]


def run_local(prompt: str, state: State, region: str) -> Row:
    log: list[ToolCallLog] = []
    orig_q, orig_l = _instrument(log)
    try:
        agent = make_strands_agent(lambda_arn=state.lambda_arn or None, region=region)
        t0 = time.time()
        result = agent(prompt)
        return Row(
            prompt=prompt, answer=_extract_text(result), mode="local",
            tool_calls=log, total_latency_ms=int((time.time() - t0) * 1000),
            trace_id=str(uuid.uuid4()),
        )
    except Exception as e:
        return Row(prompt=prompt, answer="", mode="local", tool_calls=log,
                   error=f"{type(e).__name__}: {e}")
    finally:
        tools_mod.query_tickets_impl = orig_q
        tools_mod.lookup_alarm_code_impl = orig_l


# ── agentcore-runtime mode ─────────────────────────────────────────────────


def run_runtime(prompt: str, state: State, region: str) -> Row:
    client = boto3.client("bedrock-agentcore", region_name=region)
    session_id = (str(uuid.uuid4()) + "x" * 40)[:40]
    body = {"prompt": prompt}
    t0 = time.time()
    try:
        resp = client.invoke_agent_runtime(
            agentRuntimeArn=state.runtime_arn,
            payload=json.dumps(body).encode("utf-8"),
            contentType="application/json", accept="text/event-stream",
            runtimeSessionId=session_id, runtimeUserId="ch14-demo",
        )
        chunks = []
        for chunk in resp["response"].iter_chunks():
            if isinstance(chunk, (bytes, bytearray)):
                chunks.append(chunk.decode("utf-8", errors="replace"))
            elif isinstance(chunk, str):
                chunks.append(chunk)
        elapsed = int((time.time() - t0) * 1000)
        text = "".join(chunks)
        answer_parts = []
        for line in text.splitlines():
            if not line.startswith("data: "):
                continue
            payload = line[6:].strip()
            try:
                v = json.loads(payload)
                answer_parts.append(v if isinstance(v, str) else payload)
            except Exception:
                answer_parts.append(payload)
        answer = "".join(answer_parts) if answer_parts else text
        tool_calls = fetch_runtime_tool_calls(
            region, state.runtime_arn, t0, time.time(),
        )
        return Row(
            prompt=prompt, answer=answer, mode="agentcore-runtime",
            total_latency_ms=elapsed, tool_calls=tool_calls,
            trace_id=session_id,
        )
    except Exception as e:
        return Row(
            prompt=prompt, answer="", mode="agentcore-runtime",
            total_latency_ms=int((time.time() - t0) * 1000),
            error=f"{type(e).__name__}: {e}",
        )


# ── main ────────────────────────────────────────────────────────────────────


def main() -> None:
    cfg = config.load()
    state = State.load()
    print(f"region={cfg.region} mode={state.deploy_mode}")
    print(f"lambda={state.lambda_arn or '(local fallback)'}")
    print(f"gateway={state.gateway_arn or '(none)'}")
    print(f"runtime={state.runtime_arn or '(none — local Strands)'}\n")

    rows: list[Row] = []
    for i, prompt in enumerate(PROMPTS, 1):
        print(f"[{i}/5] {prompt}")
        if state.deploy_mode == "agentcore-runtime" and state.runtime_arn:
            row = run_runtime(prompt, state, cfg.region)
        else:
            row = run_local(prompt, state, cfg.region)
        rows.append(row)
        if row.error:
            print(f"  ERROR: {row.error}")
        else:
            print(f"  mode={row.mode} latency={row.total_latency_ms}ms tools={[t.name for t in row.tool_calls]}")
        print(f"  ans: {row.answer[:200]!r}\n")

    out_dir = DEMO_DIR / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows_path = out_dir / "rows.jsonl"
    with rows_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")
    _write_summary(out_dir / "summary.md", rows, state)
    print(f"wrote {rows_path}")
    print(f"wrote {out_dir / 'summary.md'}")


def _write_summary(path: Path, rows: list[Row], state: State) -> None:
    lines = [
        "# ch14-agent run summary", "",
        f"deploy_mode: `{state.deploy_mode}`",
        f"lambda_arn: `{state.lambda_arn or '(local)'}`",
        f"gateway_arn: `{state.gateway_arn or '(none)'}`",
        f"runtime_arn: `{state.runtime_arn or '(none)'}`",
        "",
        "| # | prompt | mode | tools | latency_ms | ok |",
        "|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(rows, 1):
        tools_s = ", ".join(t.name + ("✓" if t.ok else "✗") for t in r.tool_calls) or "(opaque)"
        ok = "✓" if not r.error and r.answer else "✗"
        lines.append(f"| {i} | {r.prompt.replace('|', chr(92)+'|')[:36]} | "
                     f"{r.mode} | {tools_s} | {r.total_latency_ms} | {ok} |")
    lines.append("")
    lines.append("## Per-row detail")
    for i, r in enumerate(rows, 1):
        lines.append(f"\n### {i}. {r.prompt}")
        if r.error:
            lines.append(f"\n**error:** `{r.error}`")
        else:
            lines.append(f"\n**answer:** {r.answer}")
        if r.tool_calls:
            lines.append("\n| tool | input | ms | ok | error |")
            lines.append("|---|---|---|---|---|")
            for tc in r.tool_calls:
                lines.append(
                    f"| {tc.name} | `{tc.input_preview.replace('|', chr(92)+'|')}` | "
                    f"{tc.latency_ms} | {'✓' if tc.ok else '✗'} | {tc.error_code or '-'} |"
                )
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
