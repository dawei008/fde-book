"""ch15-mcp `make run` — prove cross-session state via stateful MCP + DynamoDB.

Pipeline: start FastMCP subprocess → MCP client Session A attaches a doc
and lists → 5s gap → MCP client Session B (NEW Mcp-Session-Id) lists and
summarises → stop server. Verdict: sid_A != sid_B AND both lists return
the same doc_id. The doc survived because it lives in DynamoDB, not in
per-session memory — that is the Ch15 stateful-MCP claim.
"""

from __future__ import annotations

import asyncio
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

DEMO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO_DIR / "src"))
sys.path.insert(0, str(DEMO_DIR.parent / "hesheng-core" / "src"))

from mcp import ClientSession  # noqa: E402
from mcp.client.streamable_http import streamable_http_client  # noqa: E402

from ch15_mcp import results as results_mod  # noqa: E402
from ch15_mcp.state import DDB_TABLE, State  # noqa: E402
from hesheng_core import config  # noqa: E402

TICKET = "T-2025-Q4-0142"
DOC_URL_A = "s3://fde-book-hesheng-manuals/T-2025-Q4-0142/manual-v2.pdf"
HOST = "127.0.0.1"
PORT = int(os.environ.get("MCP_PORT", "8765"))
URL = f"http://{HOST}:{PORT}/mcp"
SLEEP_BETWEEN_SESSIONS = float(os.environ.get("CH15_SLEEP_S", "5"))


def _wait_for_port(host: str, port: int, timeout: float = 30) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError:
            time.sleep(0.3)
    raise RuntimeError(f"server didn't open {host}:{port} within {timeout}s")


def start_server(region: str) -> subprocess.Popen:
    env = os.environ.copy()
    env["AWS_REGION"] = region
    env["DDB_TABLE"] = DDB_TABLE
    env["MCP_HOST"] = HOST
    env["MCP_PORT"] = str(PORT)
    env["PYTHONPATH"] = str(DEMO_DIR / "src")
    log_path = DEMO_DIR / "results" / "server.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_f = log_path.open("w")
    proc = subprocess.Popen(
        [sys.executable, "-u", "-m", "ch15_mcp.mcp_server"],
        stdout=log_f, stderr=subprocess.STDOUT, env=env,
        start_new_session=True,
    )
    print(f"  started MCP server pid={proc.pid} -> {log_path.name}")
    _wait_for_port(HOST, PORT)
    print(f"  port {PORT} open")
    return proc


def stop_server(proc: subprocess.Popen) -> None:
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        proc.wait(timeout=5)


def _tool_payload(result) -> dict:
    """FastMCP returns CallToolResult; extract the JSON dict our tools return."""
    # structured_content path (preferred for typed dict returns)
    sc = getattr(result, "structuredContent", None)
    if isinstance(sc, dict) and ("ok" in sc or "data" in sc or "result" in sc):
        if "result" in sc and isinstance(sc["result"], dict):
            return sc["result"]
        return sc
    # fallback: parse the first text block
    for block in (result.content or []):
        text = getattr(block, "text", None)
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"_text": text}
    return {}


async def session_A() -> dict:
    """Attach a doc, list, return (sid, list_result)."""
    print("\n[Session A] open client")
    async with streamable_http_client(URL) as (read, write, get_sid):
        async with ClientSession(read, write) as sess:
            await sess.initialize()
            sid = get_sid() or "(none-yet)"
            print(f"  Session A sid = {sid}")
            attach = await sess.call_tool("attach_doc", {
                "ticket_no": TICKET, "doc_url": DOC_URL_A, "kind": "manual",
            })
            attach_p = _tool_payload(attach)
            print(f"  attach_doc -> {attach_p}")
            listed = await sess.call_tool("list_attached_docs", {"ticket_no": TICKET})
            listed_p = _tool_payload(listed)
            print(f"  list_attached_docs -> doc_count={listed_p.get('data', {}).get('doc_count')}")
            return {"sid": get_sid(), "attach": attach_p, "list": listed_p}


async def session_B() -> dict:
    """Different Mcp-Session-Id; should still see Session A's doc."""
    print("\n[Session B] open client (NEW Mcp-Session-Id)")
    async with streamable_http_client(URL) as (read, write, get_sid):
        async with ClientSession(read, write) as sess:
            await sess.initialize()
            sid = get_sid() or "(none-yet)"
            print(f"  Session B sid = {sid}")
            listed = await sess.call_tool("list_attached_docs", {"ticket_no": TICKET})
            listed_p = _tool_payload(listed)
            print(f"  list_attached_docs -> doc_count={listed_p.get('data', {}).get('doc_count')}")
            summary = await sess.call_tool("summarize_ticket_context", {"ticket_no": TICKET})
            summary_p = _tool_payload(summary)
            print(f"  summarize_ticket_context -> {summary_p.get('data', {}).get('summary', '')[:120]}")
            return {"sid": get_sid(), "list": listed_p, "summary": summary_p}


def first_doc_id(payload: dict) -> str:
    docs = payload.get("data", {}).get("docs") or []
    return docs[0].get("doc_id", "") if docs else ""


async def main_async(region: str) -> dict:
    proc = start_server(region)
    try:
        a = await session_A()
        print(f"\n... sleeping {SLEEP_BETWEEN_SESSIONS}s (stand-in for hours-later) ...")
        await asyncio.sleep(SLEEP_BETWEEN_SESSIONS)
        b = await session_B()
    finally:
        stop_server(proc)
        print("\n  stopped MCP server")

    sid_a, sid_b = a["sid"] or "", b["sid"] or ""
    same_doc = first_doc_id(a["list"]) == first_doc_id(b["list"]) != ""
    different_sids = bool(sid_a) and bool(sid_b) and sid_a != sid_b
    return {
        "session_a_sid": sid_a, "session_b_sid": sid_b,
        "session_a_list_count": a["list"].get("data", {}).get("doc_count", 0),
        "session_b_list_count": b["list"].get("data", {}).get("doc_count", 0),
        "session_a_doc_id": first_doc_id(a["list"]),
        "session_b_doc_id": first_doc_id(b["list"]),
        "session_a_attach": a["attach"],
        "session_b_summary": b["summary"].get("data", {}).get("summary", ""),
        "different_session_ids": different_sids,
        "same_doc_visible_across_sessions": same_doc,
        "ticket_no": TICKET,
    }


def main() -> None:
    cfg = config.load()
    State.load()  # require `make up` to have run
    out = asyncio.run(main_async(cfg.region))
    results_mod.write(out, DEMO_DIR / "results")
    print("\n=== verdict ===")
    print(f"  different_session_ids:               {out['different_session_ids']}")
    print(f"  same_doc_visible_across_sessions:    {out['same_doc_visible_across_sessions']}")
    if not (out["different_session_ids"] and out["same_doc_visible_across_sessions"]):
        print("\nFAIL: cross-session persistence not proven")
        sys.exit(2)
    print("\nPASS: stateful MCP + DynamoDB delivers cross-session state.")


if __name__ == "__main__":
    main()
