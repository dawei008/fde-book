"""Ch14 alarm-code lookup tool — Lambda backend.

Two invocation contracts supported:

  1. Direct invoke / Gateway lambda-target:
        event = {"code": "ALM 4501"}
        return {"ok": True, "data": {"code": "ALM 4501", ...}}

  2. AgentCore Gateway lambda-target with tool-call envelope:
        event = {"toolName": "...", "toolUseId": "...",
                 "input": {"code": "ALM 4501"}}
        return {"ok": True, "data": {...}}  # Gateway re-wraps for the agent

The handler accepts either shape — the demo's local fallback path uses (1),
and the Gateway-routed path uses (2). All responses use the same
{"ok": bool, "error_code": ...} envelope as the in-process tool stub so
the agent's branching logic is identical regardless of transport.
"""

from __future__ import annotations

import re
from typing import Any

# Mirrors manuals/01-alarm-codes.md. In a real deployment this would read
# from DynamoDB or a manuals KB; the table is small enough to inline.
ALARM_TABLE: dict[str, dict[str, str]] = {
    "1042": {"meaning": "X 轴伺服电机过热", "team": "电气组"},
    "1043": {"meaning": "Y 轴伺服电机过热", "team": "电气组"},
    "ALM 4501": {"meaning": "冷却液液位低 (传感器)", "team": "电气组"},
    "ALM 4502": {"meaning": "冷却液液位低 (实际)", "team": "机械组"},
    "#2103": {"meaning": "Z 轴回零参考点丢失", "team": "电气组"},
    "#2104": {"meaning": "X 轴回零参考点丢失", "team": "电气组"},
    "E-301": {"meaning": "主轴启动失败", "team": "电气组"},
}


def _normalize(code: str) -> str:
    c = (code or "").strip()
    # "ALM4501" / "ALM 4501" / "alm 4501" -> "ALM 4501"
    m = re.match(r"^ALM\s*(\d+)$", c, re.IGNORECASE)
    if m:
        return f"ALM {m.group(1)}"
    # "#2103" / "2103#" -> "#2103"
    m = re.match(r"^#?(\d{4,5})#?$", c)
    if m and (c.startswith("#") or c.endswith("#")):
        return f"#{m.group(1)}"
    # Bare 4-5 digit numeric in the ALM range (45xx) -> assume ALM prefix
    # since 45xx codes only exist as "ALM 45xx" in our table.
    if re.match(r"^45\d{2}$", c):
        return f"ALM {c}"
    # Bare numeric in 21xx range -> assume # prefix (Z/X axis homing).
    if re.match(r"^21\d{2}$", c):
        return f"#{c}"
    return c


def _err(code: str, msg: str, *, retriable: bool, suggest: str = "") -> dict:
    return {
        "ok": False,
        "error_code": code,
        "message": msg,
        "retriable": retriable,
        "suggested_action": suggest,
    }


def lookup(code: str) -> dict[str, Any]:
    if not code or not str(code).strip():
        return _err("EMPTY_CODE", "code is required.", retriable=False,
                    suggest="Provide an alarm code like '1042' or 'ALM 4501'.")

    canonical = _normalize(code)
    hit = ALARM_TABLE.get(canonical)
    if not hit:
        return _err("ALARM_CODE_UNKNOWN",
                    f"Code {canonical!r} not found in reference table.",
                    retriable=False,
                    suggest="Confirm code with reporter; known prefixes: "
                            "numeric, ALM, #, E-.")
    return {"ok": True, "data": {"code": canonical, **hit, "source": "lambda"}}


def handler(event: dict, _context=None) -> dict:
    # AgentCore Gateway lambda-target wraps the call as {"input": {...}, "toolName": ...}.
    body = event.get("input") if isinstance(event.get("input"), dict) else event
    code = body.get("code") if isinstance(body, dict) else None
    return lookup(code)
