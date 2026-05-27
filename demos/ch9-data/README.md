# Ch9 demo — Data engineering end-to-end (standalone walkthrough)

This demo materializes Ch9 of the FDE book on the Hesheng Precision Heavy
Industries case. It walks the full path from raw dirty CSVs to an agent that
queries a clean ontology view through AgentCore Runtime + Gateway.

> ⚠️ **关于 hesheng-core**: 本 demo 是早期独立版本，自己合成数据 + 自己建
> S3/Glue。**hesheng-core 是它的精炼版**——后建的 Ch7/8/11/13/14/15 demo
> 都改成了 `from hesheng_core import ...` 复用基础。本 demo 保留为 Ch9 章节
> 的独立完整 walkthrough（"从零到端到端"），新章节 demo 请用 hesheng-core
> 的共享基础。

## What gets built

1. Synthetic raw data (3 CSVs, with both surface and semantic dirt)
2. S3 raw bucket + Glue Crawler + Glue Data Catalog
3. Athena exploratory queries (showing the dirt)
4. dbt-style SQL transforms — building 3 ontology entities (Equipment,
   Ticket, WorkOrder)
5. Lake Formation column-level grants — FDE role can't see customer phone
6. Bedrock Knowledge Base over a small maintenance-manual subset
7. Strands agent deployed on AgentCore Runtime
8. AgentCore Gateway exposing the Athena view as an MCP-compatible tool
9. End-to-end query: agent answers a real Hesheng-style question

## Budget

Target < $50, hard cap $80. Most cost is Athena query + Bedrock invocations.
S3, Glue Catalog, Lake Formation, AgentCore Runtime are essentially free at
this scale.

## Run

See `scripts/01-generate-data.py` through `scripts/09-teardown.py`.

## Teardown

`python3 scripts/09-teardown.py` removes everything. Run it.
