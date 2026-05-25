"""ch7-rag `make down` — teardown. Idempotent.

Order matters:
  1. Delete KB data sources (they reference the KB)
  2. Delete KB (it references the OpenSearch collection)
  3. Delete OpenSearch collection
  4. Delete OpenSearch policies (after collection is gone)
  5. Delete IAM role
  6. Remove state file
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

from ch7_rag.state import (  # noqa: E402
    State, KB_ROLE, ENCRYPTION_POLICY, NETWORK_POLICY, DATA_ACCESS_POLICY, STATE_FILE,
)
from hesheng_core import config  # noqa: E402


def main() -> None:
    cfg = config.load()
    try:
        state = State.load()
    except FileNotFoundError:
        print("No ch7-state.json — nothing to tear down.")
        return

    print(f"Tearing down ch7-rag in {cfg.region} ...")

    bedrock_agent = boto3.client("bedrock-agent", region_name=cfg.region)
    aoss = boto3.client("opensearchserverless", region_name=cfg.region)
    iam = boto3.client("iam", region_name=cfg.region)

    # 1. Data sources
    # If a data source was created with dataDeletionPolicy=DELETE (older demo
    # runs), delete_data_source races with the OpenSearch collection deletion
    # and the KB can land in DELETE_UNSUCCESSFUL. Flip to RETAIN first so the
    # delete is a no-op vector-side; the collection deletion still wipes the
    # vectors.
    if state.kb_id:
        try:
            for ds_sum in bedrock_agent.list_data_sources(knowledgeBaseId=state.kb_id)["dataSourceSummaries"]:
                ds_id = ds_sum["dataSourceId"]
                try:
                    ds = bedrock_agent.get_data_source(
                        knowledgeBaseId=state.kb_id, dataSourceId=ds_id,
                    )["dataSource"]
                    if ds.get("dataDeletionPolicy") == "DELETE":
                        update_kwargs = {
                            "knowledgeBaseId": state.kb_id,
                            "dataSourceId": ds_id,
                            "name": ds["name"],
                            "dataSourceConfiguration": ds["dataSourceConfiguration"],
                            "dataDeletionPolicy": "RETAIN",
                        }
                        if ds.get("vectorIngestionConfiguration"):
                            update_kwargs["vectorIngestionConfiguration"] = ds["vectorIngestionConfiguration"]
                        bedrock_agent.update_data_source(**update_kwargs)
                        print(f"  flipped {ds_id} dataDeletionPolicy DELETE -> RETAIN")
                        time.sleep(3)  # let state propagate
                except ClientError as e:
                    print(f"  get/update data source {ds_id}: {e.response['Error']['Code']}")

                bedrock_agent.delete_data_source(knowledgeBaseId=state.kb_id, dataSourceId=ds_id)
                print(f"  deleted data source: {ds_id}")
        except ClientError as e:
            print(f"  data sources: {e.response['Error']['Code']}")

    # 2. KB
    if state.kb_id:
        try:
            bedrock_agent.delete_knowledge_base(knowledgeBaseId=state.kb_id)
            print(f"  deleted KB: {state.kb_id}")
            time.sleep(10)  # let KB release its grip on the collection
        except ClientError as e:
            print(f"  KB: {e.response['Error']['Code']}")

    # 3. OpenSearch collection
    if state.collection_id:
        try:
            aoss.delete_collection(id=state.collection_id)
            print(f"  collection deletion submitted: {state.collection_id}")
            # Wait for actual deletion — policies can't be removed while collection exists
            for _ in range(30):
                try:
                    d = aoss.batch_get_collection(ids=[state.collection_id])["collectionDetails"]
                    if not d:
                        break
                    print(f"  collection: {d[0]['status']} ...")
                    time.sleep(10)
                except ClientError:
                    break
            print(f"  collection gone")
        except ClientError as e:
            print(f"  collection: {e.response['Error']['Code']}")

    # 4. OpenSearch policies
    for pname, ptype in [(DATA_ACCESS_POLICY, "data"), (NETWORK_POLICY, "network"),
                         (ENCRYPTION_POLICY, "encryption")]:
        method = aoss.delete_access_policy if ptype == "data" else aoss.delete_security_policy
        try:
            method(name=pname, type=ptype)
            print(f"  deleted {ptype} policy: {pname}")
        except ClientError as e:
            if e.response["Error"]["Code"] != "ResourceNotFoundException":
                print(f"  policy {pname}: {e.response['Error']['Code']}")

    # 5. IAM role
    try:
        for p in iam.list_role_policies(RoleName=KB_ROLE)["PolicyNames"]:
            iam.delete_role_policy(RoleName=KB_ROLE, PolicyName=p)
        for p in iam.list_attached_role_policies(RoleName=KB_ROLE)["AttachedPolicies"]:
            iam.detach_role_policy(RoleName=KB_ROLE, PolicyArn=p["PolicyArn"])
        iam.delete_role(RoleName=KB_ROLE)
        print(f"  deleted role: {KB_ROLE}")
    except ClientError as e:
        if e.response["Error"]["Code"] != "NoSuchEntity":
            print(f"  role: {e.response['Error']['Code']}")

    # 6. State file
    if STATE_FILE.exists():
        STATE_FILE.unlink()
        print(f"  removed: {STATE_FILE.name}")

    print("\nch7-rag torn down. Verify with `make verify-down`.")


if __name__ == "__main__":
    main()
