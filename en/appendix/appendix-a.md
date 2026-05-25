---
title: "Appendix A: Tool Stack Cheat Sheet"
parent: "Appendix"
nav_order: 1
---

# Appendix A: FDE Tool Stack Cheat Sheet (2026 Edition)

3-5 candidates per category, plus the dimensions to choose by. Built for 30-minute decisions during PoC scoping.

> Editorial stance: this book uses AWS as the demo platform. The non-AWS open-source / third-party tools listed below are included for reference when integrating with a customer's existing stack — not as horizontal head-to-head comparisons.

---

## A.1 Model APIs (Available on Bedrock as of 2026-05)

| Model | Strength | Best For | Price Tier |
|---|---|---|---|
| Claude Opus 4.5 | Top-tier reasoning + tool-search + effort parameter | Complex Agent / Judge / critical path | High |
| Claude Sonnet 4.5 / 4.6 | Balanced + long context + tool calling | General RAG / Agent default | Mid |
| Claude Haiku 4.5 | Fast + cheap | High QPS / simple classification | Low |
| Claude 4.7 family | Latest generation | Use the version available in your primary region | Mid-High |
| Nova 2 Lite | 1M token + code interpreter + web grounding | Long documents / cost-sensitive | Low |
| Nova 2 Pro | AWS first-party flagship | AWS one-stop heavyweight scenarios | Mid |
| Qwen3-Next / Qwen3 Coder Next | Chinese + code | Chinese scenarios / coding tasks | Mid-Low |
| DeepSeek V3.2 | Reasoning + Chinese | Chinese + reasoning | Low |
| Mistral Large 3 / Magistral | Multilingual / reasoning | Europe / multilingual | Mid |
| GLM 4.7 / Kimi K2.5 / MiniMax M2.1 | Chinese open-source | Backup option for Chinese scenarios | Low |
| gpt-oss / gpt-oss-safeguard | OpenAI API-compatible | Migrating existing OpenAI SDK code | Low |

**Note**: The two expansion waves in 2025-12 and 2026-02 (24 open-weight models combined) mean Bedrock is no longer just Claude; among them, Project Mantle provides OpenAI-compatible endpoints + PrivateLink and runs in 14 regions.

**Selection dimensions**: deployment shape (cloud / VPC / private) / context length / Chinese vs. English / reasoning needs / monthly budget / OpenAI SDK compatibility required or not.

**Inference Service Tiers** (since 2025-11): Standard / Priority (real-time priority) / Flex (discounted, latency-tolerant) / Reserved (1- or 3-month commitment, overflow falls back to Standard). The full Claude 4.5 family (Sonnet/Opus/Haiku) supports Reserved.

---

## A.2 Self-Hosted / Private-Deployment Models

| Model | Form | Best For |
|---|---|---|
| Llama 3.2 / 3.3 | Open-source flagship | General private deployment |
| Qwen3 family (incl. 32B) | Chinese / multilingual | Chinese private deployment / RFT base model |
| DeepSeek V3.2 | Reasoning + Chinese | Chinese + strong reasoning |
| gpt-oss-20B | OpenAI-compatible | RFT distillation target |
| Gemma 4 (E4B / 26B-A4B / 31B) | Multimodal + function calling | Multilingual / non-Anthropic alternative |
| Mistral Large 3 / Ministral 3 | Multilingual | European compliance |

**Deployment platforms**: SageMaker JumpStart (since 2026-04, 30+ models have official cost/throughput/latency-optimized deployments) / SageMaker HyperPod (including G7e RTX PRO 6000 instances) / EKS + vLLM.

---

## A.3 Orchestration / Frameworks

| Framework | Strength | Best Stage | Risk |
|---|---|---|---|
| Strands Agents (Python / TS 1.0) | Lightweight + AWS first-party SDK | Production Agent | Younger ecosystem |
| Bedrock AgentCore (GA 2025-10) | Runtime / Gateway / Memory / Browser / Code Interpreter / Identity / Observability / Evaluations / Policy / Registry (preview) / Payments (preview) — 11 capabilities, adoptable independently | Production Agent + VPC + 8h long tasks + multi-BU governance | AWS lock-in |
| LangGraph | State graph + Agent | Production Agent | Learning curve |
| LangChain | Largest ecosystem | Quick PoC demos | Leaky abstractions |
| LlamaIndex | RAG specialist | RAG projects | Weak Agent support |
| AutoGen / CrewAI | Multi-agent / role-play | Research / content | Not very stable |
| Native SDK + state machine | Most stable | Production critical path | Slower to develop |

**Field experience**: PoCs use LangChain / LlamaIndex; production agents default to Strands + AgentCore, or native SDK + Step Functions. AgentCore Runtime supports direct code deployment (no Dockerfile required) since 2025-11, stateful MCP servers since 2026-03, and adds a managed harness (preview) and CLI in 2026-04.

---

## A.4 Vector Stores / Knowledge Bases

| Tool | Form | Best Scale | Notes |
|---|---|---|---|
| Bedrock Knowledge Bases | AWS managed | Mid | Multimodal GA in 2025-11 (text/image/audio/video) |
| OpenSearch (Serverless / self-hosted) | AWS / OSS | Mid-Large | Strong hybrid search |
| Aurora pgvector / RDS PG | AWS Aurora / RDS | Small-Mid | First choice inside a VPC; default when the customer already runs PG |
| Pinecone | SaaS | Mid-Large | Lowest-effort |
| Weaviate | OSS + SaaS | Mid | Multi-modal |
| Milvus | OSS | Large | K8s deployment |
| Chroma | OSS | Small / PoC | In-memory |

**Selection dimensions**: scale / deployment / metadata filtering / what the customer already runs.

---

## A.5 Eval / Trace

| Tool | Type | Strength |
|---|---|---|
| Bedrock Evaluations | AWS managed | Model / KB / RAG / Agent |
| AgentCore Evaluations | AWS managed | OpenTelemetry-trace-based evaluation of agent behavior; 3 evaluator forms (built-in / LLM-judge / code via Lambda); 5 modes (online / on-demand / batch / dataset / simulation); 3 granularities (SESSION / TRACE / TOOL_CALL) |
| CloudWatch GenAI Observability | AWS managed | Unified dashboard for model invocations + AgentCore, with evaluations integration |
| AgentCore Optimization (preview) | AWS managed | Auto-generate prompt / tool-description improvements from production traces; batch eval + Gateway A/B validation; statistical-significance reports |
| AWS Agent Registry (preview) | AWS managed | Enterprise-grade discovery + approval + governance catalog for agents / tools / MCP servers; hybrid search; MCP-native endpoint |
| Bedrock Advanced Prompt Optimization | AWS managed | Cross-model migration + multimodal + built-in eval (2026-05) |
| LangFuse | OSS + Cloud | One-stop LLM trace + eval |
| LangSmith | LangChain official | LangChain projects |
| Phoenix (Arize) | OSS | Friendly to private deployment |
| DeepEval | Python library | Drop-in inside pytest |
| Promptfoo | YAML-driven | CI-friendly |
| Ragas | OSS | RAG-specific |

**Field experience**: when the customer is on AWS → AgentCore Evaluations + CloudWatch GenAI Observability covers everything; multi-cloud or CI-bound → Promptfoo + LangFuse.

---

## A.6 Data Engineering

| Tool | Type | Best For |
|---|---|---|
| Bedrock Data Automation | AWS managed | Document/image/audio/video extraction (blueprint optimization since 2025-12; custom speech vocabularies since 2026-04) |
| dbt | SQL transforms | In-warehouse ETL |
| Airflow | Orchestration | Complex workflows |
| AWS Glue | Serverless ETL | AWS one-stop |
| Spark / EMR | Big data | TB+ scale |
| Iceberg / Delta | Table formats | Data lake |
| Snowflake / BigQuery / Redshift | Warehouses | Analytics |
| Lake Formation | AWS | Permission governance |

---

## A.7 Deployment / Runtime

| Tool | Type | Best For |
|---|---|---|
| AWS Lambda | Serverless | Single-step LLM / simple Agent |
| ECS Fargate | Containers | MCP server / mid-size services |
| EKS | K8s | Complex / large scale |
| AgentCore Runtime | AWS managed Agent runtime | 8h long tasks / VPC / MCP |
| SageMaker Endpoint / JumpStart | Training + deploy | Self-hosted models |
| SageMaker HyperPod | Training cluster | Self-training / large-scale fine-tune |
| Step Functions | Orchestration | Long flows / HITL |
| API Gateway | API gateway | Auth + rate limiting |
| AppConfig | Config service | Hot-swap prompt / model |

---

## A.8 Security / Compliance

| Tool | Purpose |
|---|---|
| IAM Identity Center | SSO + SCIM |
| KMS | Key management |
| Secrets Manager | API keys / OAuth |
| CloudTrail | API audit |
| Config | Configuration compliance |
| Security Hub | Unified security |
| Macie | Auto-discovery of PII |
| Bedrock Guardrails | LLM content filtering; supports code use cases (comments / identifiers / literals) since 2025-11; cross-account safeguards GA in 2026-04 |
| AgentCore Policy (Cedar) | Policy gating at the Agent tool-call level (2025-12 preview) |
| WAF | Web application firewall |

---

## A.9 IaC

| Tool | Type | Best For |
|---|---|---|
| Terraform | Multi-cloud | General-purpose |
| AWS CDK | Programmatic IaC | AWS projects + complex logic |
| AWS SAM | Serverless-specific | Lambda / API GW |
| Pulumi | Programmatic multi-cloud | Same idea as CDK, multi-cloud |
| CloudFormation | AWS native | Simple stacks |

---

## A.10 Monitoring / Alerting

| Tool | Purpose |
|---|---|
| CloudWatch + GenAI Observability | AWS-native metrics + logs + LLM/Agent dashboards |
| X-Ray | AWS distributed tracing |
| OpenTelemetry | Protocol + SDK (compatible with Strands / LangChain / LangGraph) |
| Datadog | Unified observability |
| Grafana / Prometheus | OSS + private deployment |
| Sentry | Error tracking |
| PagerDuty | On-call |
| Slack / Teams alerts | Collaborative notifications |

---

## A.11 Customer Collaboration

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
