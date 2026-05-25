"""ch14-agent tools — strict-schema, structured-error tool implementations.

Two tools, illustrating Ch14 principles:

  query_tickets(sql)      — read tool, calls Athena ticket_resolution view.
                            SQL is constrained: SELECT-only, must reference
                            ticket_resolution view, max 200 rows.

  lookup_alarm_code(code, dry_run)
                          — read tool with dry_run mode demonstration.
                            dry_run=True returns "what would be looked up"
                            without invoking Lambda.

Both tools return a structured envelope:
  {"ok": true,  "data": {...}}                                  on success
  {"ok": false, "error_code": "...", "message": "...",          on error
   "retriable": false, "suggested_action": "..."}

This is consumed by Strands @tool decorators in agent.py — keeping the
business logic here means we can also call these directly in unit tests
without building an Agent.
"""

from __future__ import annotations

import json
import re
from typing import Any

import boto3
from botocore.exceptions import ClientError

from hesheng_core import config
from hesheng_core.athena import query as athena_query
from hesheng_core.ontology import RESOLUTION_VIEW

# ── query_tickets ──────────────────────────────────────────────────────────

_ALLOWED_VIEW = RESOLUTION_VIEW  # "ticket_resolution"
_FORBIDDEN_RE = re.compile(
    r"\b(insert|update|delete|drop|create|alter|truncate|grant|revoke)\b",
    re.IGNORECASE,
)


def query_tickets_impl(sql: str, max_rows: int = 50) -> dict[str, Any]:
    """SELECT against fde_book_hesheng.ticket_resolution. Read-only."""
    sql_norm = (sql or "").strip().rstrip(";").strip()
    if not sql_norm:
        return _err("EMPTY_SQL", "SQL is empty.", retriable=False,
                   suggest="Provide a SELECT statement against ticket_resolution.")

    if _FORBIDDEN_RE.search(sql_norm):
        return _err("FORBIDDEN_DDL_DML",
                    "Only SELECT statements are allowed.",
                    retriable=False,
                    suggest="Rewrite as SELECT against ticket_resolution.")

    if _ALLOWED_VIEW not in sql_norm.lower() and _ALLOWED_VIEW.lower() not in sql_norm.lower():
        return _err("VIEW_NOT_ALLOWED",
                    f"SQL must reference the {_ALLOWED_VIEW} view.",
                    retriable=False,
                    suggest=f"Add FROM {_ALLOWED_VIEW} to your query.")

    if not sql_norm.lower().startswith("select"):
        return _err("NOT_A_SELECT", "Statement must start with SELECT.",
                    retriable=False, suggest="Rewrite as SELECT.")

    max_rows = max(1, min(int(max_rows or 50), 200))

    try:
        cfg = config.load()
        rows = athena_query(cfg, sql_norm, max_rows=max_rows + 1)
    except FileNotFoundError as e:
        return _err("CORE_NOT_INITIALIZED", str(e), retriable=False,
                    suggest="Run `make up` in demos/hesheng-core first.")
    except RuntimeError as e:
        return _err("ATHENA_QUERY_FAILED", str(e), retriable=False,
                    suggest="Inspect SQL syntax; ticket_resolution columns: "
                            "ticket_no, ts_utc, priority, team, fault_desc, "
                            "alarm_code, equipment_model, site, power_rating_kw, "
                            "resolved_at, total_hours, equipment_found")

    if not rows:
        return {"ok": True, "data": {"columns": [], "rows": [], "row_count": 0}}
    header, *body = rows
    return {
        "ok": True,
        "data": {
            "columns": header,
            "rows": body[:max_rows],
            "row_count": len(body[:max_rows]),
            "truncated": len(body) > max_rows,
        },
    }


# ── lookup_alarm_code ──────────────────────────────────────────────────────

# Local fallback table — mirrors manuals/01-alarm-codes.md. Used for dry_run
# preview, and as a fallback if the Lambda is not deployed yet.
_ALARM_TABLE: dict[str, dict[str, str]] = {
    "1042": {"meaning": "X 轴伺服电机过热", "team": "电气组"},
    "1043": {"meaning": "Y 轴伺服电机过热", "team": "电气组"},
    "ALM 4501": {"meaning": "冷却液液位低 (传感器)", "team": "电气组"},
    "ALM 4502": {"meaning": "冷却液液位低 (实际)", "team": "机械组"},
    "#2103": {"meaning": "Z 轴回零参考点丢失", "team": "电气组"},
    "#2104": {"meaning": "X 轴回零参考点丢失", "team": "电气组"},
    "E-301": {"meaning": "主轴启动失败", "team": "电气组"},
}


def _normalize_code(code: str) -> str:
    """Match the user's loose input to the canonical key in _ALARM_TABLE."""
    c = (code or "").strip()
    m = re.match(r"^ALM\s*(\d+)$", c, re.IGNORECASE)
    if m:
        return f"ALM {m.group(1)}"
    m = re.match(r"^#?(\d{4,5})#?$", c)
    if m and (c.startswith("#") or c.endswith("#")):
        return f"#{m.group(1)}"
    # 45xx → "ALM 45xx" (matches manuals/01-alarm-codes.md convention)
    if re.match(r"^45\d{2}$", c):
        return f"ALM {c}"
    # 21xx → "#21xx"
    if re.match(r"^21\d{2}$", c):
        return f"#{c}"
    return c


def lookup_alarm_code_impl(
    code: str,
    dry_run: bool = False,
    lambda_arn: str | None = None,
    region: str | None = None,
) -> dict[str, Any]:
    """Look up the alarm code reference table.

    dry_run=True  → return "would look up X" without invoking Lambda.
                    Useful for the agent to preview before committing.
    dry_run=False → invoke Lambda if lambda_arn provided, else local fallback.
    """
    code = (code or "").strip()
    if not code:
        return _err("EMPTY_CODE", "code is required.", retriable=False,
                    suggest="Provide an alarm code like '1042' or 'ALM 4501'.")

    canonical = _normalize_code(code)

    if dry_run:
        return {
            "ok": True,
            "data": {
                "dry_run": True,
                "would_look_up": canonical,
                "preview_source": "local-table" if not lambda_arn else "lambda",
                "preview_known": canonical in _ALARM_TABLE,
                "note": "dry_run=true; no Lambda invoked. "
                        "Call again with dry_run=false to actually fetch.",
            },
        }

    if lambda_arn:
        try:
            client = boto3.client("lambda", region_name=region or "us-east-1")
            resp = client.invoke(
                FunctionName=lambda_arn,
                InvocationType="RequestResponse",
                Payload=json.dumps({"code": canonical}).encode(),
            )
            payload = json.loads(resp["Payload"].read().decode())
            if resp.get("FunctionError"):
                return _err("LAMBDA_ERROR",
                            f"Lambda returned FunctionError: {payload}",
                            retriable=True,
                            suggest="Inspect Lambda logs; retry once.")
            return payload
        except ClientError as e:
            return _err("LAMBDA_INVOKE_FAILED", str(e), retriable=True,
                        suggest="Check Lambda IAM permissions or network.")

    # Local fallback
    hit = _ALARM_TABLE.get(canonical)
    if not hit:
        return _err("ALARM_CODE_UNKNOWN",
                    f"Code {canonical!r} not found in reference table.",
                    retriable=False,
                    suggest="Confirm code with reporter; known prefixes: "
                            "numeric (1042-1099), ALM, #, E-.")
    return {
        "ok": True,
        "data": {"code": canonical, **hit, "source": "local-table"},
    }


# ── helpers ────────────────────────────────────────────────────────────────


def _err(code: str, msg: str, *, retriable: bool, suggest: str = "") -> dict:
    return {
        "ok": False,
        "error_code": code,
        "message": msg,
        "retriable": retriable,
        "suggested_action": suggest,
    }
