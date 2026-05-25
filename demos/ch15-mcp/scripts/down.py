"""ch15-mcp `make down` — delete the DynamoDB table and clear state.

Idempotent. Also tries to kill any leftover MCP server subprocess that
may still be holding port 8765 (in case `make run` was interrupted).
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

DEMO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO_DIR / "src"))
sys.path.insert(0, str(DEMO_DIR.parent / "hesheng-core" / "src"))

from ch15_mcp.state import DDB_TABLE, STATE_FILE, State  # noqa: E402
from hesheng_core import config  # noqa: E402

PORT = int(os.environ.get("MCP_PORT", "8765"))


def kill_leftover_server() -> None:
    try:
        out = subprocess.check_output(
            ["lsof", "-ti", f"tcp:{PORT}"], stderr=subprocess.DEVNULL,
        ).decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return
    if not out:
        return
    for pid_str in out.split():
        try:
            pid = int(pid_str)
            os.kill(pid, signal.SIGTERM)
            print(f"  killed leftover server pid={pid} on port {PORT}")
        except (ValueError, ProcessLookupError):
            pass


def delete_table(region: str) -> None:
    ddb = boto3.client("dynamodb", region_name=region)
    try:
        ddb.delete_table(TableName=DDB_TABLE)
        print(f"  deleting table: {DDB_TABLE}")
        waiter = ddb.get_waiter("table_not_exists")
        waiter.wait(TableName=DDB_TABLE,
                    WaiterConfig={"Delay": 3, "MaxAttempts": 40})
        print(f"  table gone: {DDB_TABLE}")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "ResourceNotFoundException":
            print(f"  table already gone: {DDB_TABLE}")
        elif code == "ResourceInUseException":
            print(f"  table busy (probably mid-create); rerun `make down`")
        else:
            print(f"  delete_table warn: {e}")


def main() -> None:
    cfg = config.load()
    State.load_or_empty()

    print("[1/2] Leftover server")
    kill_leftover_server()

    print("[2/2] DynamoDB table")
    delete_table(cfg.region)

    if STATE_FILE.exists():
        STATE_FILE.unlink()
        print(f"  removed {STATE_FILE.name}")


if __name__ == "__main__":
    main()
