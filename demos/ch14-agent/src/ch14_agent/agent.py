"""ch14-agent — Strands agent factory for Hesheng overseas ticket triage.

Two tools, schema-strict descriptions per Ch14.4 conventions:

  - query_tickets: read-only Athena SELECT against ticket_resolution view
  - lookup_alarm_code: alarm-code lookup with dry_run preview mode

System prompt is the routing policy from manuals/02-routing-policy.md plus
hard refusal rules ("不写诗，不闲聊"). Both tools return structured envelopes
({"ok": ..., "data": ...} on success; {"ok": false, "error_code": ...} on
error) so the agent can branch on error_code instead of parsing free text.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from strands import Agent, tool
from strands.models.bedrock import BedrockModel

from .tools import lookup_alarm_code_impl, query_tickets_impl

MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

# Fallback embedded policy (used when this file is bundled into a Runtime
# zip and the manuals/ tree isn't available on disk).
_EMBEDDED_ROUTING_POLICY = """\
1. 含数字报警代码 (1042, 1043, 4501-4599) → 电气组
2. 含 # 开头报警 (#2103, #2104) → 电气组
3. 无报警代码 + 描述包含"异响"/"卡顿"/"渗油"/"磨损" → 机械组
4. 无报警代码 + 描述包含"通信"/"电源"/"PLC" → 电气组
5. 描述模糊或包含方言 → 升级 P1, 转资深工程师

站点工程师覆盖：
- Singapore: 电气 4 / 机械 3 (覆盖 Singapore + KL)
- Bangkok: 电气 2 / 机械 2
- Jakarta: 电气 2 / 机械 1 (机械组工时不足, 复杂机械故障转 KL)
- Ho Chi Minh: 电气 1 / 机械 1
"""

_CANDIDATE_MANUAL_DIRS = [
    Path(__file__).resolve().parents[3] / "hesheng-core" / "manuals",
    Path("/var/task/manuals"),
    Path(__file__).resolve().parent / "_manuals",  # vendored fallback
]


def _load_routing_policy() -> str:
    for d in _CANDIDATE_MANUAL_DIRS:
        p = d / "02-routing-policy.md"
        if p.exists():
            return p.read_text(encoding="utf-8")
    return _EMBEDDED_ROUTING_POLICY


SYSTEM_PROMPT = f"""你是合昇精密重工海外业务部的工单分诊助手。
只回答与工单分诊、报警代码、站点 SLA、备件相关的问题。
不写诗，不闲聊，不假装专家。如果用户问与工单无关的事，礼貌拒答并给一句"建议直接问工程师"。

## 派工策略 (来自 manuals/02-routing-policy.md)

{_load_routing_policy()}

## 工具使用约定

- query_tickets: SQL SELECT 查 ticket_resolution view。只允许 SELECT, 必须 FROM ticket_resolution。
  - **site 列是 snake_case 小写**：Singapore 在数据里是 'singapore'，"Ho Chi Minh" 是 'ho_chi_minh'，"Kuala Lumpur" 是 'kuala_lumpur'。WHERE site = 时务必小写。
  - **priority** 是 'P1' / 'P2' / 'P3'（大写带 P）。**team** 是 '机械组' 或 '电气组'。
- lookup_alarm_code: 查报警代码归属。
  - 当用户说"如果你查 X"、"假设要查 X"、"演示一下查 X"——用 dry_run=true 预览，不实际执行。
  - 否则 dry_run=false 实际查询。

## 错误处理约定

工具返回 {{"ok": false, "error_code": ..., "suggested_action": ...}} 时：
- 不要重复同样的调用
- 读 suggested_action，决定改参数 / 升级 / 问用户
- 不要把 error_message 原样返给用户，改成中文工程师能读懂的描述

## 回答风格

- 简短，直接给结论 + 一句依据
- 引用工具数据时只引用关键字段，不要把整张表贴出来
"""


def make_strands_agent(
    *,
    lambda_arn: str | None = None,
    region: str = "us-east-1",
    model_id: str = MODEL_ID,
) -> Agent:
    """Build a Strands Agent with the two tools bound to this account's resources."""

    @tool
    def query_tickets(sql: str, max_rows: int = 50) -> dict[str, Any]:
        """Run a SELECT against the Hesheng ticket_resolution Athena view.

        Use this for any "which tickets / how many tickets / average resolution
        time / who handled ticket X" question. Read-only; SQL is rejected if it
        is not a SELECT or does not reference ticket_resolution.

        Args:
            sql: SELECT statement against fde_book_hesheng.ticket_resolution.
                 Available columns: ticket_no, ts_utc, priority (P1/P2/P3),
                 team (机械组/电气组), fault_desc, alarm_code, equipment_model,
                 site (Singapore/Bangkok/Jakarta/Ho Chi Minh/KL),
                 power_rating_kw, resolved_at, total_hours, equipment_found.
            max_rows: cap on returned rows (1-200, default 50).

        Returns:
            {"ok": True, "data": {"columns": [...], "rows": [[...]],
            "row_count": N, "truncated": bool}} on success, or
            {"ok": False, "error_code": ..., "message": ...,
            "suggested_action": ...} on error.
        """
        return query_tickets_impl(sql, max_rows=max_rows)

    @tool
    def lookup_alarm_code(code: str, dry_run: bool = False) -> dict[str, Any]:
        """Look up the meaning and owning team of a Hesheng alarm code.

        Use ONLY when the user asks "what does ALM 4501 mean" or "which team
        owns code 1042". Do NOT use as a fallback for free-text fault
        descriptions — for those, use query_tickets instead.

        Args:
            code: alarm code with the EXACT prefix the user provided. Examples:
                  "1042", "ALM 4501", "#2103", "E-301". Do NOT strip prefixes:
                  if the user said "ALM 4501" pass "ALM 4501", NOT "4501".
                  Loose forms like "ALM4501" or "2103#" will be normalized.
            dry_run: when True, return a preview of what would be looked up
                     without invoking the backend. Use this for hypothetical
                     questions ("if you were to look up X, what would you
                     do"); use False for actual fetch.

        Returns:
            On success (dry_run=False): {"ok": True, "data": {"code": ...,
            "meaning": ..., "team": ..., "source": ...}}.
            On dry_run=True: {"ok": True, "data": {"dry_run": True,
            "would_look_up": ..., "preview_known": bool}}.
            On error: {"ok": False, "error_code": ..., "suggested_action": ...}.
        """
        return lookup_alarm_code_impl(
            code=code, dry_run=dry_run, lambda_arn=lambda_arn, region=region,
        )

    model = BedrockModel(model_id=model_id, region_name=region)
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[query_tickets, lookup_alarm_code],
    )
