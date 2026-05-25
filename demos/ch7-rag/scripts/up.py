"""ch7-rag `make up` — create Bedrock Knowledge Base over hesheng manuals.

Order of operations matters:
  1. IAM role (KB execution role)
  2. OpenSearch Serverless: 3 policies + collection (~5 min wait)
  3. Vector index inside the collection (KB requires it pre-existing)
  4. Knowledge Base + S3 data source
  5. Ingestion job (sync from manuals bucket)

Each step is idempotent — re-running picks up where it left off.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

DEMO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO_DIR / "src"))
sys.path.insert(0, str(DEMO_DIR.parent / "hesheng-core" / "src"))

from ch7_rag.state import State, KB_ROLE  # noqa: E402
from ch7_rag.aoss import ensure_policies, ensure_collection, ensure_index  # noqa: E402
from ch7_rag.kb import ensure_kb, run_ingestion, EMBED_MODEL  # noqa: E402
from hesheng_core import config  # noqa: E402


def ensure_role(iam, account: str, manuals_bucket: str) -> str:
    """KB execution role: trusted by bedrock, can read S3 + invoke embed model + use OpenSearch."""
    role_arn = f"arn:aws:iam::{account}:role/{KB_ROLE}"
    trust = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "bedrock.amazonaws.com"},
            "Action": "sts:AssumeRole",
            "Condition": {"StringEquals": {"aws:SourceAccount": account}},
        }],
    }
    try:
        iam.create_role(
            RoleName=KB_ROLE,
            AssumeRolePolicyDocument=json.dumps(trust),
            Description="Ch7 RAG demo KB execution role",
        )
        print(f"  created role: {KB_ROLE}")
    except ClientError as e:
        if e.response["Error"]["Code"] != "EntityAlreadyExists":
            raise
        print(f"  role exists: {KB_ROLE}")

    inline = {
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow", "Action": ["s3:ListBucket"],
             "Resource": [f"arn:aws:s3:::{manuals_bucket}"]},
            {"Effect": "Allow", "Action": ["s3:GetObject"],
             "Resource": [f"arn:aws:s3:::{manuals_bucket}/*"]},
            {"Effect": "Allow", "Action": ["bedrock:InvokeModel"],
             "Resource": [f"arn:aws:bedrock:*::foundation-model/{EMBED_MODEL}"]},
            {"Effect": "Allow", "Action": ["aoss:APIAccessAll"], "Resource": ["*"]},
        ],
    }
    iam.put_role_policy(RoleName=KB_ROLE, PolicyName="ch7-kb-inline", PolicyDocument=json.dumps(inline))
    return role_arn


def main() -> None:
    cfg = config.load()
    print(f"Bringing up ch7-rag in {cfg.region} / account {cfg.account}")

    iam = boto3.client("iam", region_name=cfg.region)
    aoss = boto3.client("opensearchserverless", region_name=cfg.region)
    bedrock_agent = boto3.client("bedrock-agent", region_name=cfg.region)
    sts = boto3.client("sts", region_name=cfg.region)
    caller_arn = sts.get_caller_identity()["Arn"]

    state = State.load_or_empty(region=cfg.region, account=cfg.account)

    print("\n[1/5] IAM role ...")
    state.role_arn = ensure_role(iam, cfg.account, cfg.manuals_bucket)
    state.save()
    time.sleep(8)  # IAM propagation

    print("\n[2/5] OpenSearch Serverless policies ...")
    ensure_policies(aoss, state.role_arn, caller_arn)

    print("\n[3/5] OpenSearch Serverless collection ...")
    state = ensure_collection(aoss, state)
    state.save()

    print("\n[4/5] Vector index ...")
    ensure_index(state)

    print("\n[5/5] Knowledge Base + ingestion ...")
    state = ensure_kb(bedrock_agent, state, cfg.manuals_bucket)
    state.save()
    run_ingestion(bedrock_agent, state)

    print(f"\nch7-rag is up. KB={state.kb_id}  Collection={state.collection_id}")
    print(f"Run `make run` to execute the eval. Run `make down` IMMEDIATELY after to stop the meter.")


if __name__ == "__main__":
    main()
