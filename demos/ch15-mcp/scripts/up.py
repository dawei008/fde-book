"""ch15-mcp `make up` — provision DynamoDB table for the stateful MCP server.

Idempotent. Creates a single PAY_PER_REQUEST table keyed by `ticket_no`.
That table is the persistence layer that lets a doc attached in MCP
session A still be visible from a different MCP session B (different
Mcp-Session-Id, hours apart, possibly on a different microVM).

Deploy mode is recorded as "local" — the MCP server itself runs as a
local Python process during `make run`. The README explains why we
chose the local-server path over the AgentCore Runtime stateful-MCP
path for this demo (the latter is GA but the deploy step is heavier
and out-of-budget for a 30-min demo).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

DEMO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO_DIR / "src"))
sys.path.insert(0, str(DEMO_DIR.parent / "hesheng-core" / "src"))

from ch15_mcp.state import DDB_TABLE, State  # noqa: E402
from hesheng_core import config  # noqa: E402


def ensure_table(region: str) -> str:
    ddb = boto3.client("dynamodb", region_name=region)
    try:
        d = ddb.describe_table(TableName=DDB_TABLE)
        arn = d["Table"]["TableArn"]
        print(f"  table already present: {DDB_TABLE}")
        return arn
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
            raise
    ddb.create_table(
        TableName=DDB_TABLE,
        AttributeDefinitions=[{"AttributeName": "ticket_no", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "ticket_no", "KeyType": "HASH"}],
        BillingMode="PAY_PER_REQUEST",
        Tags=[
            {"Key": "Project", "Value": "fde-book"},
            {"Key": "Demo", "Value": "ch15-mcp"},
        ],
    )
    print(f"  creating table: {DDB_TABLE}")
    waiter = ddb.get_waiter("table_exists")
    waiter.wait(TableName=DDB_TABLE,
                WaiterConfig={"Delay": 2, "MaxAttempts": 30})
    # Need ACTIVE (not just present) before reads/writes work
    d = None
    for _ in range(30):
        d = ddb.describe_table(TableName=DDB_TABLE)
        if d["Table"]["TableStatus"] == "ACTIVE":
            break
        time.sleep(2)
    if d is None or d["Table"]["TableStatus"] != "ACTIVE":
        raise RuntimeError(f"Table {DDB_TABLE} did not reach ACTIVE within 60s")
    arn = d["Table"]["TableArn"]
    print(f"  table ACTIVE: {arn}")
    return arn


def main() -> None:
    cfg = config.load()
    print(f"region={cfg.region} account={cfg.account}")
    state = State.load_or_empty()

    print("[1/1] DynamoDB table")
    state.ddb_table_arn = ensure_table(cfg.region)
    state.deploy_mode = "local"
    state.notes.append("MCP server runs locally (subprocess); DynamoDB persists state.")

    state.save()
    print("\nState saved:")
    print(f"  ddb_table_arn = {state.ddb_table_arn}")
    print(f"  deploy_mode   = {state.deploy_mode}")


if __name__ == "__main__":
    main()
