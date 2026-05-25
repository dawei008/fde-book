# Ch9 demo — Data engineering end-to-end with AgentCore

This demo materializes Ch9 of the FDE book on the Hesheng Precision Heavy
Industries case. It walks the full path from raw dirty CSVs to an agent that
queries a clean ontology view through AgentCore Runtime + Gateway.

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

See `scripts/01-generate-data.py` through `scripts/09-teardown.sh`.

## Teardown

`bash scripts/09-teardown.sh` removes everything. Run it.
