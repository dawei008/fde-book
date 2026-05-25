"""Result-writer for ch15-mcp `make run`.

Pulled into its own module to keep scripts/run.py below the per-file
line cap. The shape of the dict it consumes is documented in run.py.
"""

from __future__ import annotations

import json
from pathlib import Path


def write(out: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "run-summary.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    md = [
        "# ch15-mcp run summary", "",
        f"ticket_no: `{out['ticket_no']}`", "",
        "## Cross-session evidence", "",
        f"- Session A Mcp-Session-Id: `{out['session_a_sid']}`",
        f"- Session B Mcp-Session-Id: `{out['session_b_sid']}`",
        f"- different_session_ids: **{out['different_session_ids']}**",
        f"- Session A list count after attach: **{out['session_a_list_count']}**",
        f"- Session B list count (new session): **{out['session_b_list_count']}**",
        f"- Session A doc_id: `{out['session_a_doc_id']}`",
        f"- Session B doc_id: `{out['session_b_doc_id']}`",
        f"- same_doc_visible_across_sessions: **{out['same_doc_visible_across_sessions']}**",
        "", "## Session B summarize_ticket_context", "",
        f"> {out['session_b_summary']}", "",
    ]
    (out_dir / "summary.md").write_text("\n".join(md), encoding="utf-8")
