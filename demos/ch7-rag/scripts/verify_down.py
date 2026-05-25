"""Verify all ch7-rag resources are gone. Run after `make down`."""

from __future__ import annotations

import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

DEMO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO_DIR / "src"))
sys.path.insert(0, str(DEMO_DIR.parent / "hesheng-core" / "src"))

from ch7_rag.state import KB_NAME, COLLECTION_NAME, KB_ROLE  # noqa: E402
from hesheng_core import config  # noqa: E402


def main() -> None:
    cfg = config.load()
    bedrock_agent = boto3.client("bedrock-agent", region_name=cfg.region)
    aoss = boto3.client("opensearchserverless", region_name=cfg.region)
    iam = boto3.client("iam", region_name=cfg.region)

    leftover = []

    # KB in DELETING state is fine — it's async cleanup and free of charge.
    # Only ACTIVE / FAILED KBs count as leftovers.
    kbs = [k for k in bedrock_agent.list_knowledge_bases()["knowledgeBaseSummaries"]
           if k["name"] == KB_NAME and k["status"] not in ("DELETING",)]
    if kbs:
        leftover.append(f"KB still present (non-DELETING): {kbs}")

    cols = aoss.list_collections(collectionFilters={"name": COLLECTION_NAME})["collectionSummaries"]
    if cols:
        leftover.append(f"Collection still present: {cols}")

    try:
        iam.get_role(RoleName=KB_ROLE)
        leftover.append(f"Role still present: {KB_ROLE}")
    except ClientError as e:
        if e.response["Error"]["Code"] != "NoSuchEntity":
            leftover.append(f"Role check error: {e}")

    if leftover:
        print("LEFTOVERS DETECTED:")
        for l in leftover:
            print(f"  - {l}")
        sys.exit(1)
    print("Clean. No ch7-rag resources remain.")


if __name__ == "__main__":
    main()
