---
title: "Appendix B: Comparison Matrix"
parent: "Appendix"
nav_order: 2
---

# Appendix B: Model / Framework / Platform Comparison Matrix

> Appendix A is a "breadth cheat sheet"; this appendix is the "depth comparison". Look here when you need a serious decision inside one tool category.
>
> Editorial stance: this book uses AWS as the demo platform. Non-AWS tools below are referenced for "integrating with the customer's existing stack" only — not as horizontal vendor-vs-vendor commercial comparisons.

---

## B.1 Mainstream Foundation Models — 9 Dimensions (2026-05)

| Dimension | Claude Opus 4.5 | Claude Sonnet 4.5 | Claude Haiku 4.5 | Nova 2 Lite | Nova 2 Pro | Qwen3-Next | DeepSeek V3.2 | gpt-oss-20B |
|---|---|---|---|---|---|---|---|---|
| Context | 200K | 200K+ | 200K | 1M | Long | Long | Long | Mid |
| Chinese | Excellent | Strong | Strong | Mid | Mid | Excellent | Excellent | Average |
| Reasoning | Top-tier | Excellent | Good | Good | Strong | Strong | Excellent | Good |
| Tool calling | Excellent (incl. tool-search, effort param) | Excellent | Good | Built-in code interpreter / web grounding | Strong | Good | Good | Good |
| Multimodal | Vision | Vision | Vision | Text+Vision | Text+Vision | Vision (VL variant) | Text | Text |
| Available on Bedrock | ✅ | ✅ | ✅ | ✅ (GA) | Preview | ✅ (Project Mantle) | ✅ (Mantle, OpenAI-compat) | ✅ (Mantle) |
| Reserved tier | ✅ | ✅ | ✅ | — | — | — | — | — |
| Prompt cache TTL | 5 min / 1 hour | 5 min / 1 hour | 5 min / 1 hour | — | — | — | — | — |
| Price tier | High | Mid | Low | Low | Mid | Mid-Low | Low | Low |

**FDE decision pattern**:

```
  Enterprise default (AWS):    Bedrock Claude Sonnet 4.5 — balanced + AWS-native
  High QPS / classification:   Claude Haiku 4.5
  Highest quality / Judge:     Claude Opus 4.5 (use the effort parameter to control cost)
  Long doc / 1M context:       Nova 2 Lite
  Chinese + private:           Qwen3-Next / DeepSeek V3.2 (Mantle endpoint + PrivateLink)
  Existing OpenAI SDK code:    gpt-oss / DeepSeek on Mantle (drop-in compatible)
  European multilingual:       Mistral Large 3 / Magistral
```

**Inference Service Tiers** (since 2025-11):

| Tier | Best For | Notes |
|---|---|---|
| Standard | Regular production | Default |
| Priority | Real-time critical path | Higher price, more stable quota |
| Flex | Batch / offline eval / summarization | Discounted, latency-tolerant |
| Reserved | Predictable capacity | 1- or 3-month commitment, overflow falls back to Standard |

---

## B.2 RAG Framework Comparison

| Dimension | LangChain RAG | LlamaIndex | Haystack | Bedrock KB | Build-Your-Own |
|---|---|---|---|---|---|
| Time to first demo | Mid | Fast | Mid | Very fast | Slow |
| Document parsing | Mid | Strong (LlamaParse) | Strong | Mid + Bedrock Data Automation | Custom |
| Chunking strategies | Many | Many | Many | Default + custom | Custom |
| Retrieval strategies | Many | Very many | Many | Hybrid (OS) | Custom |
| Multimodal | DIY | DIY | DIY | ✅ (GA 2025-11: text/image/audio/video) | Custom |
| Rerank | Plug Cohere/external | Built-in + external | Built-in | Plug Cohere | Custom |
| Incremental updates | Roll your own | Roll your own | Roll your own | Auto (S3) | Custom |
| Multi-source fusion | Strong | Excellent | Mid | Mid | Custom |
| Production maturity | Mid | Mid | High | High | Depends on team |
| Lock-in risk | Low | Low | Low | High (AWS) | None |

**Field experience**:
- PoC: LlamaIndex ships demos fastest
- Production + AWS: Bedrock KB (saves about half the engineering over 4 weeks; multimodal goes native)
- Long-term complex RAG: build-your-own (Bedrock as the retrieval layer, with your own orchestration)

---

## B.3 Agent Framework Comparison

| Dimension | Strands Agents | AgentCore | LangGraph | AutoGen | CrewAI | Native SDK + state machine |
|---|---|---|---|---|---|---|
| Programming model | Lightweight SDK (Py / TS 1.0) | Managed Runtime + Gateway | State graph (DAG) | Multi-agent dialogue | Role-play | Fully custom |
| Tool integration | Free + MCP | MCP / Action / Gateway | Free | Free | Free | Free |
| Long tasks | Self-managed | Built-in 8h execution window | LangGraph Cloud | Weak | Weak | Custom |
| HITL | DIY | Stateful MCP (2026-03) + Cedar policy | Built-in interrupt | Mid | Weak | Custom |
| Observability | OTEL → CloudWatch | CloudWatch GenAI Observability + Evaluations | LangSmith | Custom | Custom | Custom |
| Evaluation | Plug Bedrock Eval | Built-in 13 evaluators + Performance Loop (2026-05) | LangSmith | Custom | Custom | Custom |
| Lock-in risk | Low (open source) | High (AWS) | Mid | Low | Low | None |
| Best scale | Small to large | Mid-Large + AWS customers | Small to large | Research / experimentation | Content generation | High complexity |

**Field experience**:
- Customer on AWS + wants "out-of-the-box" production line → AgentCore (Runtime + Gateway + Identity + Observability + Evaluations)
- Customer wants a lightweight SDK while keeping AWS integration → Strands (incl. TS 1.0, frontend teams can adopt)
- Multi-cloud + complex business flow → LangGraph
- Critical path + maximum rigor → native SDK + state machine

---

## B.4 Vector Stores Compared — 6 Production Dimensions

| Dimension | OpenSearch (AWS) | Aurora pgvector | Pinecone | Weaviate | Milvus | Chroma |
|---|---|---|---|---|---|---|
| Deployment | AWS managed / Serverless | AWS Aurora / RDS | SaaS | SaaS + OSS | OSS (K8s) | OSS / local |
| Single-store scale | 1B+ | 100M | 1B+ | 1B+ | 10B+ | Tens of millions |
| Hybrid retrieval | Excellent | Weak (extension required) | Supported | Supported | Supported | Weak |
| Metadata filtering | Excellent | Excellent (SQL) | Strong | Strong | Strong | Mid |
| Multi-modal | Mid | Weak | Mid | Strong | Mid | Weak |
| Incremental / updates | Easy | Trivial (UPDATE) | Easy | Easy | Easy | Easy |
| Deploy inside VPC | Serverless / self-hosted | RDS / Aurora | Private edition | Self-hosted | Self-hosted | Self-hosted |
| Customer already has it | Some AWS customers | **Many customers already run PG** | Usually not | Usually not | Usually not | Usually not |

**FDE field decision**:

```
  Customer already runs PG / Aurora  → pgvector (zero extra tooling)
  Customer on AWS + mid scale        → OpenSearch Serverless
  Scale > 500M                        → Milvus or Pinecone
  PoC / small project                 → Chroma
```

---

## B.5 Eval Tools Compared

| Dimension | Bedrock Evaluations | AgentCore Evaluations | LangFuse | Phoenix | DeepEval | Promptfoo | Ragas |
|---|---|---|---|---|---|---|---|
| Form | AWS managed | AWS managed | OSS + Cloud | OSS | Python lib | YAML CLI | OSS |
| Eval scope | Model / KB / RAG / Agent | Agent + 13 built-in evaluators | Full LLM stack | Full LLM stack | Embedded in unit tests | Prompt comparison | RAG-specific |
| LLM-as-judge | Built-in | Custom model-based | Supported | Supported | Supported | Supported | Supported |
| Online trace | Mostly static | Connected to CloudWatch | Strong | Strong | No | No | No |
| CI-friendly | Mid | Mid | Mid | Mid | Strong | Excellent | Mid |
| Cost | Per token + judge | Per invocation | OSS / Cloud | OSS | OSS | OSS | OSS |

**Typical combo (AWS customer)**:

```
  AgentCore Evaluations + CloudWatch GenAI Observability  → online + dashboard
  Bedrock Evaluations                                     → compliance acceptance
  Promptfoo                                               → CI prompt comparisons
  AgentCore Performance Loop                              → eval → optimize closed loop
```

---

## B.6 Deployment Platforms — LLM Application Dimensions

| Dimension | Lambda | ECS Fargate | EKS | AgentCore Runtime | SageMaker Endpoint | Step Functions |
|---|---|---|---|---|---|---|
| Startup latency | Cold start 100ms-3s | Container start in seconds | Pod in seconds | microVM in seconds | Endpoint in seconds | Orchestration overhead |
| Max single run | 15 min | None | None | 8 h | None | 1 year |
| Concurrency model | Auto | Self-managed | Self-managed | Managed | Self-managed | N/A |
| Best for | Single LLM call / simple Agent | Long-running server / MCP | Complex clusters | Agent + MCP + VPC | Self-hosted models | Long flows / HITL |
| State | Stateless | Stateless / EFS | StatefulSet | Session microVM (incl. stateful MCP) | Stateless | State held in SF |
| Private network | VPC | VPC | VPC | VPC + PrivateLink | VPC | — |

**Field experience**:
- Simple RAG / API → Lambda
- MCP server / Agent service → ECS Fargate or AgentCore Runtime (the latter is the recommendation: zero maintenance, built-in 8h long task)
- Long flow + HITL → AgentCore + stateful MCP, or Step Functions + Lambda
- Self-hosted 70B+ models → SageMaker JumpStart optimized deployment / HyperPod / EKS + GPU

---

## B.7 Programming Languages / Runtimes

| Dimension | Python | TypeScript | Go | Rust |
|---|---|---|---|---|
| LLM SDK maturity | Top-tier | Good (Strands TS 1.0 covers AWS Agents too) | Good | Early stage |
| Data processing | Excellent | Mid | Strong | Strong |
| Async concurrency | asyncio (mid) | Native strong | goroutine strong | tokio strong |
| Deployment size | Large | Mid | Tiny (single binary) | Tiny |
| Hiring | Easiest | Easy | Mid | Hard |
| FDE recommended scenarios | Data / Eval / PoC | Frontend / Lambda / Agent | API / high concurrency | Critical path / embedded |

**FDE default**: Python + TypeScript dual stack covers the vast majority of scenarios. With Strands TS 1.0, frontend teams can own Agent code independently.

---

## B.8 Combined Decision Table

```
        Customer scenario → recommended stack
        ─────────────────────────────────────────────────

  Mid-size US insurer on AWS + document RAG
    Model:    Bedrock Claude Sonnet 4.5 (Reserved tier)
    Framework: Bedrock Knowledge Bases + Lambda
    Vector:   OpenSearch Serverless
    Eval:     Bedrock Evaluations + Promptfoo CI
    Deploy:   Lambda + API Gateway
    IaC:      AWS CDK
    Monitor:  CloudWatch GenAI Observability + X-Ray
    Security: IAM Identity Center + Bedrock Guardrails (incl. cross-account)

  ─────────────────────────────────────────────────

  On-prem PG database + Chinese finance + intranet
    Model:    DeepSeek V3.2 / Qwen3-Next (Bedrock Mantle + PrivateLink),
              or self-hosted (vLLM)
    Framework: Native SDK + state machine, or Strands
    Vector:   pgvector
    Eval:     Phoenix (self-hosted) + custom judge
    Deploy:   K8s / EKS
    IaC:      Terraform
    Monitor:  Prometheus + Grafana
    Security: Internal LDAP + custom audit

  ─────────────────────────────────────────────────

  Cross-border retailer + multi-SaaS integration + Agent
    Model:    Claude Sonnet 4.5 (primary) + Haiku 4.5 (routing / classification)
    Framework: Strands + AgentCore (Gateway + Identity)
    Vector:   OpenSearch Serverless
    Eval:     AgentCore Evaluations + Performance Loop
    Deploy:   AgentCore Runtime
    IaC:      CDK
    Monitor:  CloudWatch GenAI Observability
    Security: IAM Identity Center + AgentCore Policy (Cedar) + Guardrails
```

---

[← Back to Contents](../README.md) · [Next: Eval Set Design Templates →](appendix-c.md)
