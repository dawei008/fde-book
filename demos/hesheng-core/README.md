# hesheng-core — shared substrate for chapter demos

This is the shared code library that chapter demos build on. It owns:

- **Synthetic Hesheng data** — 3 CSV tables (equipment / tickets / work_orders)
  with both surface and semantic dirt, as designed in Ch9
- **AWS substrate** — S3 raw bucket, Glue Catalog database, IAM roles
- **Cleaned ontology** — 4 Athena SQL views (equipment_clean,
  ticket_clean, work_order_clean, ticket_resolution)
- **Maintenance manuals** — 5 short documents (alarm codes, routing
  policy, SLA) used by Ch7 (KB) and Ch9.7 (prompt-stuff baseline)
- **Helper SDK** — `hesheng_core` Python package: thin wrappers around
  Athena / Bedrock / common config

## Architecture

```
                  ┌──────────────────────┐
                  │   hesheng-core       │  ← this directory
                  │   data + ontology    │
                  │   manuals + helpers  │
                  └──────────┬───────────┘
                             │ imported by
        ┌────────┬───────────┼───────────┬──────────┐
        │        │           │           │          │
       Ch7      Ch8        Ch11        Ch13      Ch14/15
       RAG     Eval       VPC/SSO    Guardrails  Agent/MCP
```

Each chapter demo `import`s from `hesheng_core` instead of re-creating
synthetic data or re-writing the ontology.

## Bring it up

```bash
cd demos/hesheng-core
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make up      # generates data, sets up S3 + Glue + ontology
make smoke   # runs 6 Athena queries that confirm everything works
```

## Tear it down

```bash
make down    # full cleanup; idempotent
```

Stack outputs (bucket names, db name, etc.) are written to
`data/stack-outputs.json`. Chapter demos read this file.

## Cost

Bringing core up: ~$0.05 (Athena queries + S3 storage).
Persisting core: free (no compute resources, just S3 + Glue Catalog metadata).
A reasonable workflow is `make up` once, run several chapter demos against it,
then `make down` when done with all chapters.
