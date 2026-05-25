"""Hesheng ticket-context MCP server — stateful.

Designed for AgentCore Runtime stateful MCP (2026-03 GA). For
reproducibility in this Ch15 demo the server runs locally — see README
for the deploy-mode rationale. Production deployment to Runtime
swaps only the host/port wiring; the protocol layer is identical.

Three tools share state through a DynamoDB table keyed by `ticket_no`,
so attachments uploaded in one session are visible in a later session
on a different microVM. That is the cross-session-persistence claim
this Ch15 demo proves.

Tools:
  attach_doc(ticket_no, doc_url, kind=manual|drawing|email)
        — append a doc reference to the ticket's context.
  list_attached_docs(ticket_no)
        — read the current attachments list.
  summarize_ticket_context(ticket_no)
        — render a one-paragraph human summary for business hand-off.

The server is stateful (`stateless_http=False`) so MCP advanced features
(elicitation/sampling/progress) work — the Ch15 demo doesn't exercise
them, but enabling stateful mode is what AgentCore docs call out as the
opt-in for "Mcp-Session-Id maintained across requests in one session".
Cross-session persistence (different Mcp-Session-Id, hours apart) goes
through DynamoDB; per-session liveness goes through the AgentCore-managed
microVM. Both layers are real.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from typing import Literal

import boto3
from botocore.exceptions import ClientError
from mcp.server.fastmcp import FastMCP

DDB_TABLE = os.environ.get("DDB_TABLE", "fde-book-ch15-ticket-context")
REGION = os.environ.get("AWS_REGION", os.environ.get("FDE_BOOK_REGION", "us-east-1"))
HOST = os.environ.get("MCP_HOST", "127.0.0.1")
PORT = int(os.environ.get("MCP_PORT", "8765"))

mcp = FastMCP(host=HOST, port=PORT, stateless_http=False)
_ddb = boto3.client("dynamodb", region_name=REGION)


class _DDBToolError(Exception):
    """Raised inside the data layer; tools translate to structured error."""

    def __init__(self, code: str, msg: str) -> None:
        super().__init__(msg)
        self.code = code
        self.msg = msg


def _ddb_err(e: ClientError) -> _DDBToolError:
    code = e.response.get("Error", {}).get("Code", "DDB_ERROR")
    return _DDBToolError(f"DDB_{code}", str(e))


# ── data layer ─────────────────────────────────────────────────────────────


def _get_item(ticket_no: str) -> dict:
    try:
        resp = _ddb.get_item(
            TableName=DDB_TABLE,
            Key={"ticket_no": {"S": ticket_no}},
            ConsistentRead=True,
        )
    except ClientError as e:
        raise _ddb_err(e) from e
    return resp.get("Item") or {}


def _docs_from_item(item: dict) -> list[dict]:
    raw = item.get("docs", {}).get("S")
    if not raw:
        return []
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return []


def _put_docs(ticket_no: str, docs: list[dict]) -> None:
    try:
        _ddb.update_item(
            TableName=DDB_TABLE,
            Key={"ticket_no": {"S": ticket_no}},
            UpdateExpression="SET docs = :d, updated_at = :t",
            ExpressionAttributeValues={
                ":d": {"S": json.dumps(docs, ensure_ascii=False)},
                ":t": {"S": str(int(time.time()))},
            },
        )
    except ClientError as e:
        raise _ddb_err(e) from e


# ── tools ──────────────────────────────────────────────────────────────────


@mcp.tool()
def attach_doc(
    ticket_no: str,
    doc_url: str,
    kind: Literal["manual", "drawing", "email", "report"] = "manual",
) -> dict:
    """Attach a document URL to a ticket's running context.

    Use when an engineer or customer uploads supporting material (manual
    PDF, machine drawing, customer email) that the agent should remember
    later. The attachment is keyed by `ticket_no` and persists across
    MCP sessions, so a follow-up in a different session sees it.

    Args:
        ticket_no: e.g. "T-2025-Q4-0142" (uppercase letters, digits, hyphens).
        doc_url:   s3:// or https:// URL where the doc lives.
        kind:      manual / drawing / email / report.

    Returns:
        {ok: True, data: {ticket_no, doc_id, doc_count}} on success.
        {ok: False, error_code, message} on validation failure.
    """
    if not ticket_no or len(ticket_no) > 64:
        return {"ok": False, "error_code": "INVALID_TICKET_NO",
                "message": "ticket_no must be 1-64 chars"}
    if not doc_url or not (doc_url.startswith("s3://")
                           or doc_url.startswith("http")):
        return {"ok": False, "error_code": "INVALID_DOC_URL",
                "message": "doc_url must be s3:// or http(s)://"}

    # Note: read-modify-write below has no optimistic concurrency check —
    # demo simplification. Production should use UpdateExpression with
    # list_append + ConditionExpression on updated_at.
    try:
        item = _get_item(ticket_no)
        docs = _docs_from_item(item)
        doc_id = f"d{uuid.uuid4().hex[:8]}"
        docs.append({
            "doc_id": doc_id, "url": doc_url, "kind": kind,
            "attached_at": int(time.time()),
        })
        _put_docs(ticket_no, docs)
    except _DDBToolError as e:
        return {"ok": False, "error_code": e.code, "message": e.msg,
                "retriable": True, "suggested_action": "retry after 2s"}
    return {"ok": True, "data": {
        "ticket_no": ticket_no, "doc_id": doc_id, "doc_count": len(docs),
    }}


@mcp.tool()
def list_attached_docs(ticket_no: str) -> dict:
    """List all documents attached to a ticket.

    Use when the agent needs to know what supporting material is on file.
    Reads through DynamoDB so a doc attached in an earlier MCP session
    on a different microVM is still visible.

    Args:
        ticket_no: e.g. "T-2025-Q4-0142".

    Returns:
        {ok: True, data: {ticket_no, docs: [...], doc_count: N}}.
    """
    if not ticket_no:
        return {"ok": False, "error_code": "INVALID_TICKET_NO",
                "message": "ticket_no required"}
    try:
        item = _get_item(ticket_no)
        docs = _docs_from_item(item)
    except _DDBToolError as e:
        return {"ok": False, "error_code": e.code, "message": e.msg,
                "retriable": True, "suggested_action": "retry after 2s"}
    return {"ok": True, "data": {
        "ticket_no": ticket_no, "docs": docs, "doc_count": len(docs),
        "updated_at": item.get("updated_at", {}).get("S", ""),
    }}


@mcp.tool()
def summarize_ticket_context(ticket_no: str) -> dict:
    """Build a short human-readable summary of a ticket and its attachments.

    Use ONLY when the agent is about to hand a ticket off to a human
    (sales / engineer) and needs a one-paragraph briefing including all
    attached docs. Do not use as a generic ticket lookup — for that,
    use the Ch14 ticket-query tool instead.

    Args:
        ticket_no: e.g. "T-2025-Q4-0142".

    Returns:
        {ok: True, data: {ticket_no, summary: str, doc_count: int}}.
    """
    if not ticket_no:
        return {"ok": False, "error_code": "INVALID_TICKET_NO",
                "message": "ticket_no required"}
    try:
        item = _get_item(ticket_no)
        docs = _docs_from_item(item)
    except _DDBToolError as e:
        return {"ok": False, "error_code": e.code, "message": e.msg,
                "retriable": True, "suggested_action": "retry after 2s"}
    if not docs:
        summary = (f"Ticket {ticket_no} has no attached supporting docs yet. "
                   "Hand-off briefing not ready.")
    else:
        kinds = sorted({d.get("kind", "?") for d in docs})
        summary = (
            f"Ticket {ticket_no}: {len(docs)} attached doc(s) "
            f"(kinds: {', '.join(kinds)}). Latest URL: "
            f"{docs[-1].get('url', '')}. Updated: "
            f"{item.get('updated_at', {}).get('S', '')}."
        )
    return {"ok": True, "data": {
        "ticket_no": ticket_no, "summary": summary, "doc_count": len(docs),
    }}


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
