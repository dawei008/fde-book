"""Verify all ch15-mcp resources are gone."""

from __future__ import annotations

import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

DEMO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO_DIR / "src"))
sys.path.insert(0, str(DEMO_DIR.parent / "hesheng-core" / "src"))

from ch15_mcp.state import DDB_TABLE  # noqa: E402
from hesheng_core import config  # noqa: E402


def main() -> None:
    cfg = config.load()
    leftover: list[str] = []

    ddb = boto3.client("dynamodb", region_name=cfg.region)
    try:
        ddb.describe_table(TableName=DDB_TABLE)
        leftover.append(f"DynamoDB table still present: {DDB_TABLE}")
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
            leftover.append(f"DDB check error: {e}")

    if leftover:
        print("LEFTOVERS DETECTED:")
        for l in leftover:
            print(f"  - {l}")
        sys.exit(1)
    print("Clean. No ch15-mcp resources remain.")


if __name__ == "__main__":
    main()
