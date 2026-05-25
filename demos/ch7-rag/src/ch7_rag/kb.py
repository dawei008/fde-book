"""Bedrock Knowledge Base helpers: KB creation, data source, ingestion."""

from __future__ import annotations

import time

from botocore.exceptions import ClientError

from ch7_rag.state import State, KB_NAME, INDEX_NAME

EMBED_MODEL = "amazon.titan-embed-text-v2:0"


def ensure_kb(bedrock_agent, state: State, manuals_bucket: str) -> State:
    if state.kb_id:
        try:
            bedrock_agent.get_knowledge_base(knowledgeBaseId=state.kb_id)
            print(f"  KB exists: {state.kb_id}")
        except ClientError:
            state.kb_id = None

    if not state.kb_id:
        # KB creation can fail with "role can't access OpenSearch" right after policy creation
        for attempt in range(6):
            try:
                r = bedrock_agent.create_knowledge_base(
                    name=KB_NAME,
                    roleArn=state.role_arn,
                    knowledgeBaseConfiguration={
                        "type": "VECTOR",
                        "vectorKnowledgeBaseConfiguration": {
                            "embeddingModelArn": f"arn:aws:bedrock:{state.region}::foundation-model/{EMBED_MODEL}",
                        },
                    },
                    storageConfiguration={
                        "type": "OPENSEARCH_SERVERLESS",
                        "opensearchServerlessConfiguration": {
                            "collectionArn": state.collection_arn,
                            "vectorIndexName": INDEX_NAME,
                            "fieldMapping": {"vectorField": "vector", "textField": "text",
                                             "metadataField": "metadata"},
                        },
                    },
                )
                state.kb_id = r["knowledgeBase"]["knowledgeBaseId"]
                print(f"  created KB: {state.kb_id}")
                break
            except ClientError as e:
                code = e.response["Error"]["Code"]
                if code == "ConflictException":
                    state.kb_id = next(k["knowledgeBaseId"]
                                       for k in bedrock_agent.list_knowledge_bases()["knowledgeBaseSummaries"]
                                       if k["name"] == KB_NAME)
                    print(f"  KB found by name: {state.kb_id}")
                    break
                print(f"  create_knowledge_base attempt {attempt+1}: {code}: {str(e)[:100]}")
                time.sleep(20)
        else:
            raise RuntimeError("Failed to create KB after 6 attempts")

    if not state.data_source_id:
        existing = bedrock_agent.list_data_sources(knowledgeBaseId=state.kb_id)["dataSourceSummaries"]
        if existing:
            state.data_source_id = existing[0]["dataSourceId"]
            print(f"  data source exists: {state.data_source_id}")
        else:
            r = bedrock_agent.create_data_source(
                knowledgeBaseId=state.kb_id, name="hesheng-manuals",
                # RETAIN: teardown will delete the whole OpenSearch collection,
                # so we don't need delete_data_source to clean up vectors.
                # Without this, delete_data_source races with collection deletion
                # and the KB can land in DELETE_UNSUCCESSFUL.
                dataDeletionPolicy="RETAIN",
                dataSourceConfiguration={"type": "S3", "s3Configuration": {
                    "bucketArn": f"arn:aws:s3:::{manuals_bucket}",
                    "inclusionPrefixes": ["manuals/"]}},
                vectorIngestionConfiguration={"chunkingConfiguration": {
                    "chunkingStrategy": "HIERARCHICAL",
                    "hierarchicalChunkingConfiguration": {
                        "levelConfigurations": [{"maxTokens": 1500}, {"maxTokens": 300}],
                        "overlapTokens": 60,
                    }}},
            )
            state.data_source_id = r["dataSource"]["dataSourceId"]
            print(f"  created data source: {state.data_source_id}")

    return state


def run_ingestion(bedrock_agent, state: State) -> None:
    r = bedrock_agent.start_ingestion_job(knowledgeBaseId=state.kb_id, dataSourceId=state.data_source_id)
    job_id = r["ingestionJob"]["ingestionJobId"]
    print(f"  ingestion job: {job_id} ... waiting")
    deadline = time.time() + 600
    while time.time() < deadline:
        j = bedrock_agent.get_ingestion_job(knowledgeBaseId=state.kb_id, dataSourceId=state.data_source_id,
                                            ingestionJobId=job_id)["ingestionJob"]
        if j["status"] == "COMPLETE":
            stats = j.get("statistics", {})
            print(f"  ingestion COMPLETE: {stats.get('numberOfDocumentsScanned')} scanned, "
                  f"{stats.get('numberOfNewDocumentsIndexed')} indexed")
            return
        if j["status"] == "FAILED":
            raise RuntimeError(f"Ingestion FAILED: {j.get('failureReasons')}")
        print(f"  ingestion: {j['status']} ... 15s")
        time.sleep(15)
    raise TimeoutError("Ingestion did not complete in 10 min")
