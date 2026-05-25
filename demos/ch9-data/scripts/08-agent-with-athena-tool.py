"""End-to-end demo: agent answers Hesheng questions by querying Athena.

This is what the data engineering work in steps 1-6 enables. The agent:
- has 5 maintenance manuals stuffed into its system prompt (KB
  alternative — see step 07 for why)
- has ONE tool: query_tickets(sql) which executes against the cleaned
  ontology view ticket_resolution
- gets asked 4 Hesheng-style questions and answers them by composing
  SQL → Athena → analysis → response

This deliberately uses Bedrock Converse + tool use instead of full
AgentCore Runtime + Gateway, because:
1. AgentCore Runtime requires container build + deploy (10+ min, $)
2. Gateway requires OpenAPI spec + auth setup
3. The CONCEPTS we want to demo (data → tool → agent) are identical
   in both paths
4. For a single-agent single-tool demo on a small budget, Converse
   tool use IS the right answer (Ch6 6.5.3 signal A/B/C aren't met)

A note in the chapter explains when to graduate from this to
AgentCore Runtime + Gateway.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import boto3

OUT = Path(__file__).resolve().parent.parent / "data" / "stack-outputs.json"
cfg = json.loads(OUT.read_text())

REGION = cfg["region"]
DB = cfg["database"]

bedrock = boto3.client("bedrock-runtime", region_name=REGION)
athena = boto3.client("athena", region_name=REGION)


# Manuals stuffed into system prompt
MANUALS_DIR = Path(__file__).resolve().parent.parent / "data" / "manuals"
MANUALS = "\n\n".join(p.read_text() for p in sorted(MANUALS_DIR.glob("*.md")))


SYSTEM_PROMPT = f"""你是合昇精密重工海外服务部的工单分诊和分析助手。

你能调用一个 SQL 工具 query_tickets(sql) 来查询 ticket_resolution 视图。
这个视图的 schema:
- ticket_no, ts_utc, priority (P1/P2/P3), team (机械组/电气组)
- fault_desc, alarm_code
- equipment_model, site (singapore/kuala_lumpur/bangkok/jakarta/ho_chi_minh)
- power_rating_kw
- resolved_at, total_hours
- equipment_found (boolean — false 表示工单引用的设备不在主数据里, 是数据问题)

你也熟悉以下维修手册和派工策略:

{MANUALS}

回答问题时:
1. 先用 query_tickets 查相关数据
2. 结合手册的派工策略给出业务结论
3. 用一段中文回答, 不超过 100 字
"""


# Tool spec for Converse API
TOOL_SPEC: dict[str, Any] = {
    "toolSpec": {
        "name": "query_tickets",
        "description": "Run a read-only SQL query against the ticket_resolution view. Use this to look up ticket counts, distributions, averages, etc.",
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": f"A SELECT statement against {DB}.ticket_resolution. Must be read-only.",
                    }
                },
                "required": ["sql"],
            }
        },
    }
}


def run_athena_sql(sql: str) -> list[list[str]]:
    """Execute SQL against Athena and return rows."""
    sql = sql.strip().rstrip(";").strip()
    if not sql.lower().startswith("select") and not sql.lower().startswith("with"):
        return [["ERROR: only SELECT or CTE (WITH) allowed"]]

    try:
        qid = athena.start_query_execution(
            QueryString=sql,
            QueryExecutionContext={"Database": DB},
            ResultConfiguration={"OutputLocation": f"s3://{cfg['athena_bucket']}/results/"},
        )["QueryExecutionId"]
    except Exception as e:
        return [[f"ERROR (start): {e!r} | SQL was: {sql[:300]}"]]

    while True:
        st = athena.get_query_execution(QueryExecutionId=qid)["QueryExecution"]
        state = st["Status"]["State"]
        if state in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        time.sleep(1)

    if state != "SUCCEEDED":
        return [[f"ERROR: {st['Status'].get('StateChangeReason', 'unknown')}"]]

    rows = athena.get_query_results(QueryExecutionId=qid, MaxResults=50)["ResultSet"]["Rows"]
    return [[d.get("VarCharValue", "") for d in r["Data"]] for r in rows]


def ask(question: str, model_id: str = "us.anthropic.claude-haiku-4-5-20251001-v1:0") -> str:
    """Ask the agent a question. Loops on tool_use until the agent finalizes."""
    print(f"\n{'='*70}\nUSER: {question}\n")
    messages: list[dict[str, Any]] = [{"role": "user", "content": [{"text": question}]}]

    for hop in range(5):  # safety: max 5 tool hops
        resp = bedrock.converse(
            modelId=model_id,
            system=[{"text": SYSTEM_PROMPT}],
            messages=messages,
            toolConfig={"tools": [TOOL_SPEC]},
            inferenceConfig={"maxTokens": 800},
        )

        content = resp["output"]["message"]["content"]
        stop = resp.get("stopReason")
        messages.append({"role": "assistant", "content": content})

        # Check for tool_use blocks
        tool_uses = [b for b in content if "toolUse" in b]
        if not tool_uses:
            # Done — emit text and exit loop
            for b in content:
                if "text" in b:
                    print(f"AGENT: {b['text']}")
            return "".join(b.get("text", "") for b in content)

        # Execute each tool call
        tool_results = []
        for tu in tool_uses:
            tool = tu["toolUse"]
            name = tool["name"]
            sql = tool["input"]["sql"]
            print(f"  TOOL CALL: {name}({sql[:80]}{'...' if len(sql) > 80 else ''})")
            rows = run_athena_sql(sql)
            preview = "\n".join("  ".join(r) for r in rows[:5])
            if len(rows) > 5:
                preview += f"\n  ... ({len(rows) - 5} more rows)"
            print(f"  TOOL RESULT (first 5 rows):\n    {preview.replace(chr(10), chr(10) + '    ')}")

            tool_results.append({
                "toolResult": {
                    "toolUseId": tool["toolUseId"],
                    "content": [{"text": json.dumps(rows[:30])}],
                }
            })

        messages.append({"role": "user", "content": tool_results})

        if stop != "tool_use":
            break

    return "(no answer after 5 hops)"


QUESTIONS = [
    "过去 90 天里 Singapore 站点 P1 工单的平均解决时间是多少?",
    "ALM 4501 报警在不同站点的分布如何, 哪个站点最多?",
    "我们有多少工单引用了不存在的设备 ID? 这是个数据质量问题吗?",
    "Jakarta 站点本月机械组工单, 哪些超过了 SLA 上门时间 (P3=5天)?",
]


def main() -> None:
    print("Starting Ch9 end-to-end agent demo.")
    print(f"Model: claude-haiku-4-5 (cross-region inference profile)")
    print(f"Database: {DB}")
    print(f"Manuals stuffed in system prompt: {len(MANUALS)} chars\n")
    for q in QUESTIONS:
        ask(q)


if __name__ == "__main__":
    main()
