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

## Region note: 为什么 demo 跑 us-east-1，正文写 ap-southeast-1

合昇案例的叙事 region 是 **ap-southeast-1（新加坡）**——海外服务部
就在那里，章节里反复强调"客户数据不出 ap-southeast-1"。但所有 demo
实际跑在 **us-east-1**，因为 Claude 4.5 系列 + Bedrock Knowledge
Bases + AgentCore 在 us-east-1 可用性最完整、跨区 inference profile
免配置。Ch6 §6.3 节脚注里有详细解释。

落地客户项目时把所有 region 配置改成 `apac.*` 前缀的 inference
profile + ap-southeast-1 endpoint，工程逻辑完全相同，只换 SDK
参数。这就是 FDE 的"先选模型可用性再选 region 合规"判断顺序。

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
