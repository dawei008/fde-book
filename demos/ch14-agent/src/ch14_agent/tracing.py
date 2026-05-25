"""ch14-agent — tool-call trace correlation from CloudWatch Logs.

When the agent runs in AgentCore Runtime mode, tool calls happen server-side
and the boto3 InvokeAgentRuntime response only carries text deltas. We pull
the OTel logs that AgentCore writes to CloudWatch and reconstruct the
{tool_name, input, ok} list by time window.

Public surface: `fetch_runtime_tool_calls(region, runtime_arn, t_start, t_end)`
returns a list[ToolCallLog].
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

import boto3


@dataclass
class ToolCallLog:
    name: str
    input_preview: str
    latency_ms: int = 0
    ok: bool = True
    error_code: str = ""


def fetch_runtime_tool_calls(
    region: str, runtime_arn: str, t_start: float, t_end: float,
) -> list[ToolCallLog]:
    """Pull tool_use events for the time window from the runtime CWL group.

    AgentCore's OTel logs split tool_calls into bedrock-runtime spans (which
    don't carry session.id) and Strands tracer spans (which do). Since prompts
    in run.py run sequentially, a time-window filter is sufficient and simpler
    than threading session_id through every log line.
    """
    runtime_id = runtime_arn.rsplit("/", 1)[-1]
    log_group = f"/aws/bedrock-agentcore/runtimes/{runtime_id}-DEFAULT"
    logs = boto3.client("logs", region_name=region)
    out: list[ToolCallLog] = []
    try:
        time.sleep(10)  # let CWL ingest the events
        resp = logs.filter_log_events(
            logGroupName=log_group,
            startTime=int(t_start * 1000) - 2000,
            endTime=int(t_end * 1000) + 15000,
            filterPattern='"tool_calls"',
            limit=200,
        )
        seen: set[str] = set()
        for evt in resp.get("events", []):
            msg = evt.get("message", "")
            for m in re.finditer(
                r'"id":"(tooluse_[A-Za-z0-9]+)"[^}]*?"function":\{"name":"([^"]+)","arguments":(\{[^}]*?\})',
                msg,
            ):
                tid, tname, args = m.group(1), m.group(2), m.group(3)
                if tid in seen:
                    continue
                seen.add(tid)
                out.append(ToolCallLog(
                    name=tname, input_preview=args[:120], ok=True,
                ))
    except Exception as e:
        print(f"  (could not fetch trace: {type(e).__name__}: {e})")
    return out
