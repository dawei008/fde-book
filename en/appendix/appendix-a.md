---
title: "appendix/appendix-a.md"
nav_exclude: true
search_exclude: false
---

# Appendix A: FDE Tool Stack Cheat Sheet (2026 Edition)

3-5 candidates per category, plus the dimensions to choose by. Built for 30-minute decisions during PoC scoping.

---

## A.1 Model APIs

| Model | Strength | Best For | Price Tier |
|---|---|---|---|
| Claude 3.5 Sonnet | Balanced + long context | General RAG / Agent | Mid |
| Claude 3 Opus | Strong reasoning | Complex tasks / Judge | High |
| Claude 3 Haiku | Fast + cheap | High QPS / simple tasks | Low |
| GPT-4o | Strong + multimodal | General + vision | Mid-high |
| GPT-4o-mini | Cost-performance | High QPS general | Low |
| Llama 3.1 70B | Open-source flagship | Private deployment | Self-hosted |
| Qwen2.5 72B | Strong Chinese | Chinese-language scenarios | Self-hosted |
| DeepSeek V3 | Reasoning + Chinese | Chinese + reasoning | Self-hosted |
| Bedrock Titan | AWS-native | AWS one-stop | Mid-low |
| Mistral Large | European | Multilingual | Mid |

**Selection dimensions**: Deployment shape (cloud / private) / context length / Chinese vs. English / reasoning needs / monthly budget.

---

## A.2 Orchestration / Frameworks

| Framework | Strength | Best Stage | Risk |
|---|---|---|---|
| LangChain | Largest ecosystem | PoC fast demos | Leaky abstractions |
| LlamaIndex | RAG specialist | RAG projects | Weak Agent support |
| LangGraph | State graph + Agent | Production Agents | Learning curve |
| Bedrock Agents | AWS one-stop | AWS projects | AWS lock-in |
| AutoGen | Multi-agent | Research / complex multi-agent | Not very stable |
| CrewAI | Role-play | Content / research | Not very stable |
| Native SDK | Most stable | Production critical path | Slow to develop |

**Rule of thumb**: LangChain for PoCs; switch to native SDK + state machine in production.

---

## A.3 Vector Stores / Knowledge Bases

| Tool | Form | Best Scale | Notes |
|---|---|---|---|
| Bedrock Knowledge Bases | AWS managed | Mid | OpenSearch backend by default |
| OpenSearch (Serverless / self-hosted) | AWS / OSS | Mid-large | Strong hybrid search |
| Pinecone | SaaS | Mid-large | Easiest, but expensive |
| Weaviate | OSS + SaaS | Mid | Multi-modal |
| pgvector | PostgreSQL extension | Small-mid | First choice when the customer already has PG |
| Milvus | OSS | Large | K8s deployment |
| Chroma | OSS | Small / PoC | In-memory |
| Aurora pgvector | AWS Aurora | Small-mid | First choice inside a VPC |

**Selection dimensions**: scale / deployment / metadata filtering / what the customer already runs.

---

## A.4 Eval / Trace

| Tool | Type | Strength |
|---|---|---|
| Bedrock Evaluations | AWS managed | Three eval types: Model / KB / Agent |
| LangFuse | OSS + Cloud | One-stop LLM trace + eval |
| LangSmith | LangChain official | LangChain projects |
| Phoenix (Arize) | OSS | Friendly to private deployment |
| DeepEval | Python library | Drop-in inside pytest |
| Promptfoo | YAML-driven | CI-friendly |
| Ragas | OSS | RAG-specific |
| Helicone | Proxy trace | OpenAI-compatible proxy |

**Rule of thumb**: LangFuse Cloud for PoCs; self-hosted LangFuse / Phoenix for enterprise.

---

## A.5 Data Engineering

| Tool | Type | Best For |
|---|---|---|
| dbt | SQL transforms | In-warehouse ETL |
| Airflow | Orchestration | Complex workflows |
| AWS Glue | Serverless ETL | AWS one-stop |
| Spark / EMR | Big data | TB+ scale |
| Iceberg / Delta | Table formats | Data lake |
| Snowflake / BigQuery / Redshift | Warehouses | Analytics |
| Lake Formation | AWS | Permission governance |
| OpenLineage | Lineage | Data lineage |

---

## A.6 Deployment / Runtime

| Tool | Type | Best For |
|---|---|---|
| AWS Lambda | Serverless | Single-step LLM / simple Agent |
| ECS Fargate | Containers | MCP server / mid-size services |
| EKS | K8s | Complex / large scale |
| SageMaker | Training + deploy | Self-trained models |
| SageMaker JumpStart | One-click deploy | Self-hosted LLMs |
| Step Functions | Orchestration | Long flows / HITL |
| API Gateway | API gateway | Auth + rate limiting |
| AppConfig | Config service | Hot-swap prompt / model |

---

## A.7 Security / Compliance

| Tool | Purpose |
|---|---|
| IAM Identity Center | SSO + SCIM |
| KMS | Key management |
| Secrets Manager | API keys / OAuth |
| CloudTrail | API audit |
| Config | Configuration compliance |
| Security Hub | Unified security |
| Macie | Auto-discovery of PII |
| Bedrock Guardrails | LLM content filtering |
| WAF | Web application firewall |

---

## A.8 IaC

| Tool | Type | Best For |
|---|---|---|
| Terraform | Multi-cloud | General-purpose |
| AWS CDK | Programmatic IaC | AWS projects + complex logic |
| AWS SAM | Serverless-specific | Lambda / API GW |
| Pulumi | Programmatic multi-cloud | Same idea as CDK, multi-cloud |
| CloudFormation | AWS native | Simple stacks |
| Bicep | Azure | Azure projects |

---

## A.9 Monitoring / Alerting

| Tool | Purpose |
|---|---|
| CloudWatch | AWS-native metrics + logs |
| X-Ray | AWS distributed tracing |
| Datadog | Unified observability |
| Grafana / Prometheus | OSS + private deployment |
| OpenTelemetry | Protocol + SDK |
| Sentry | Error tracking |
| PagerDuty | On-call |
| Slack alerts | Collaborative notifications |

---

## A.10 Customer Collaboration

| Tool | Purpose |
|---|---|
| Confluence | Customer wiki |
| Jira | Customer tickets |
| Notion | FDE internal notes |
| Slack / Teams | Real-time chat |
| Linear | High-efficiency ticket management |
| Loom | Screen recording (explaining issues) |
| Excalidraw | Architecture diagrams |
| Miro | Collaborative whiteboard |

---

[← Back to Contents](../README.md)
