"""OpenSearch Serverless helpers: policies, collection, vector index."""

from __future__ import annotations

import json
import time

import boto3
from botocore.exceptions import ClientError

from ch7_rag.state import (
    State, COLLECTION_NAME, ENCRYPTION_POLICY, NETWORK_POLICY,
    DATA_ACCESS_POLICY, INDEX_NAME,
)

EMBED_DIM = 1024  # Titan v2 default


def ensure_policies(aoss, role_arn: str, caller_arn: str) -> None:
    """3 policies needed: encryption + network + data access."""
    enc = {"Rules": [{"ResourceType": "collection", "Resource": [f"collection/{COLLECTION_NAME}"]}],
           "AWSOwnedKey": True}
    try:
        aoss.create_security_policy(name=ENCRYPTION_POLICY, type="encryption", policy=json.dumps(enc))
        print(f"  created encryption policy: {ENCRYPTION_POLICY}")
    except ClientError as e:
        if e.response["Error"]["Code"] != "ConflictException":
            raise
        print(f"  encryption policy exists")

    net = [{"Rules": [
        {"ResourceType": "collection", "Resource": [f"collection/{COLLECTION_NAME}"]},
        {"ResourceType": "dashboard", "Resource": [f"collection/{COLLECTION_NAME}"]},
    ], "AllowFromPublic": True}]
    try:
        aoss.create_security_policy(name=NETWORK_POLICY, type="network", policy=json.dumps(net))
        print(f"  created network policy: {NETWORK_POLICY}")
    except ClientError as e:
        if e.response["Error"]["Code"] != "ConflictException":
            raise
        print(f"  network policy exists")

    data = [{"Rules": [
        {"ResourceType": "collection", "Resource": [f"collection/{COLLECTION_NAME}"],
         "Permission": ["aoss:CreateCollectionItems", "aoss:DeleteCollectionItems",
                        "aoss:UpdateCollectionItems", "aoss:DescribeCollectionItems"]},
        {"ResourceType": "index", "Resource": [f"index/{COLLECTION_NAME}/*"],
         "Permission": ["aoss:CreateIndex", "aoss:DeleteIndex", "aoss:UpdateIndex",
                        "aoss:DescribeIndex", "aoss:ReadDocument", "aoss:WriteDocument"]},
    ], "Principal": [role_arn, caller_arn]}]
    try:
        aoss.create_access_policy(name=DATA_ACCESS_POLICY, type="data", policy=json.dumps(data))
        print(f"  created data access policy: {DATA_ACCESS_POLICY}")
    except ClientError as e:
        if e.response["Error"]["Code"] != "ConflictException":
            raise
        # AOSS rejects no-op updates with ValidationException, so diff first
        existing = aoss.get_access_policy(name=DATA_ACCESS_POLICY, type="data")["accessPolicyDetail"]
        if set(existing["policy"][0].get("Principal", [])) != {role_arn, caller_arn}:
            aoss.update_access_policy(name=DATA_ACCESS_POLICY, type="data",
                                      policyVersion=existing["policyVersion"], policy=json.dumps(data))
            print(f"  data access policy updated")
        else:
            print(f"  data access policy exists (principals match)")


def ensure_collection(aoss, state: State) -> State:
    if state.collection_id:
        try:
            d = aoss.batch_get_collection(ids=[state.collection_id])["collectionDetails"][0]
            if d["status"] == "ACTIVE":
                return state
        except (ClientError, IndexError):
            pass
    try:
        r = aoss.create_collection(name=COLLECTION_NAME, type="VECTORSEARCH")
        cid = r["createCollectionDetail"]["id"]
        print(f"  collection creating: {cid} (~5 min)")
    except ClientError as e:
        if e.response["Error"]["Code"] != "ConflictException":
            raise
        cid = aoss.list_collections(collectionFilters={"name": COLLECTION_NAME})["collectionSummaries"][0]["id"]
        print(f"  collection exists: {cid}")

    deadline = time.time() + 900
    while time.time() < deadline:
        d = aoss.batch_get_collection(ids=[cid])["collectionDetails"][0]
        if d["status"] == "ACTIVE":
            state.collection_id = cid
            state.collection_arn = d["arn"]
            state.collection_endpoint = d["collectionEndpoint"]
            print(f"  collection ACTIVE: {state.collection_endpoint}")
            return state
        if d["status"] == "FAILED":
            raise RuntimeError(f"Collection FAILED: {d}")
        print(f"  collection status: {d['status']} ... 30s")
        time.sleep(30)
    raise TimeoutError("Collection did not become ACTIVE within 15 min")


def ensure_index(state: State) -> None:
    """Create vector index inside the collection — KB requires it pre-existing."""
    from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

    creds = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(creds, state.region, "aoss")
    host = state.collection_endpoint.replace("https://", "")
    client = OpenSearch(hosts=[{"host": host, "port": 443}], http_auth=auth,
                        use_ssl=True, verify_certs=True,
                        connection_class=RequestsHttpConnection, timeout=60)

    body = {
        "settings": {"index.knn": True},
        "mappings": {"properties": {
            "vector": {"type": "knn_vector", "dimension": EMBED_DIM,
                       "method": {"name": "hnsw", "engine": "faiss",
                                  "parameters": {"ef_construction": 256, "m": 16}}},
            "text": {"type": "text"}, "metadata": {"type": "text"},
        }},
    }
    # Data access policy can take ~30s to propagate after creation
    for attempt in range(10):
        try:
            if client.indices.exists(index=INDEX_NAME):
                print(f"  index exists: {INDEX_NAME}")
                return
            client.indices.create(index=INDEX_NAME, body=body)
            print(f"  created index: {INDEX_NAME}")
            time.sleep(30)
            return
        except Exception as e:
            print(f"  index create attempt {attempt+1}: {type(e).__name__}: {str(e)[:120]}")
            time.sleep(15)
    raise RuntimeError("Failed to create vector index after 10 attempts")
