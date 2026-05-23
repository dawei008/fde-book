# Appendix B: Model / Framework / Platform Comparison Matrix

> Appendix A is a "breadth cheat sheet"; this appendix is a "depth comparison." When you need to make a serious decision inside one tool category, look here.

---

## B.1 Mainstream LLMs — 9-Dimension Comparison

| Dimension | Claude 3.5 Sonnet | Claude 3 Opus | Claude 3 Haiku | GPT-4o | GPT-4o-mini | Llama 3.1 70B | Qwen 2.5 72B | DeepSeek V3 |
|---|---|---|---|---|---|---|---|---|
| Context | 200K | 200K | 200K | 128K | 128K | 128K | 128K | 128K |
| Output tokens | 8K | 4K | 4K | 16K | 16K | 8K | 8K | 8K |
| Chinese | Strong | Excellent | Average | Strong | Good | Average | Excellent | Excellent |
| Reasoning | Excellent | Top-tier | Average | Excellent | Good | Good | Good | Excellent |
| Tool use | Excellent | Excellent | Good | Excellent | Excellent | Good | Good | Good |
| Multimodal | Vision | Vision | Vision | Vision + audio | Vision | Text | Vision | Text |
| Price (input / M tok) | $3 | $15 | $0.25 | $5 | $0.15 | Self-hosted | Self-hosted | $0.27 |
| Price (output / M tok) | $15 | $75 | $1.25 | $15 | $0.6 | Self-hosted | Self-hosted | $1.1 |
| Bedrock available | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ (available on AWS China) | ❌ |

**FDE decision pattern**:

```
  Enterprise default: Claude 3.5 Sonnet (Bedrock) — balanced + AWS-native
  High QPS:           Claude 3 Haiku or GPT-4o-mini
  Highest quality:    Claude 3 Opus (judge / critical path)
  Chinese + private:  Qwen 2.5 72B or DeepSeek V3 self-hosted
  European compliance: Mistral Large
```

---

## B.2 RAG Framework Comparison

| Dimension | LangChain RAG | LlamaIndex | Haystack | Bedrock KB | Build your own |
|---|---|---|---|---|---|
| Onboarding speed | Mid | Fast | Mid | Very fast | Slow |
| Document parsing | Mid | Strong (LlamaParse) | Strong | Mid | Custom |
| Chunking strategies | Many | Many | Many | Default + custom | Custom |
| Retrieval strategies | Many | Very many | Many | Hybrid (OS) | Custom |
| Rerank | External (Cohere/etc.) | Built-in + external | Built-in | External (Cohere) | Custom |
| Incremental updates | DIY | DIY | DIY | Automatic (S3) | Custom |
| Multi-source fusion | Strong | Very strong | Mid | Mid | Custom |
| Production maturity | Mid | Mid | High | High | Depends on team |
| Lock-in risk | Low | Low | Low | High (AWS) | None |

**Rules of thumb**:
- PoC: LlamaIndex ships demos fastest
- Production + AWS: Bedrock KB (saves half the engineering across 4 weeks)
- Long-term complex RAG: build your own (use Bedrock for the retrieval layer, control orchestration yourself)

---

## B.3 Agent Framework Comparison

| Dimension | LangGraph | Bedrock Agents | AutoGen | CrewAI | OpenAI Assistants | Native SDK + state machine |
|---|---|---|---|---|---|---|
| Programming model | State graph (DAG) | Configuration-based | Multi-agent dialogue | Role-play | API + state service | Fully custom |
| Tool integration | Free-form | Action Group | Free-form | Free-form | Built-in + Function | Free-form |
| Long tasks | LangGraph Cloud | Pair with Step Functions | Weak | Weak | Built-in threads | Custom |
| HITL | Built-in interrupt | Weak engineering | Mid | Weak | Weak | Custom |
| Observability | LangSmith | CloudWatch + Trace | Custom | Custom | OpenAI dashboard | Custom |
| Lock-in risk | Mid | High (AWS) | Low | Low | High (OpenAI) | None |
| Best scale | Small to large | Mid + AWS customers | Research / experiments | Content generation | Personal assistants | High complexity |

**Rules of thumb**:
- Customer on AWS + simple business flow → Bedrock Agents
- Customer multi-cloud + complex business flow → LangGraph
- Critical path + rigorous → native SDK + state machine

---

## B.4 Vector Store Comparison — 6 Production Dimensions

| Dimension | Pinecone | Weaviate | Milvus | OpenSearch | pgvector | Chroma |
|---|---|---|---|---|---|---|
| Deployment | SaaS | SaaS + OSS | OSS (K8s) | AWS / OSS | PG extension | OSS / local |
| Single-DB scale | 1B+ | 1B+ | 10B+ | 1B+ | 100M | 10M |
| Hybrid search | Supported | Supported | Supported | Excellent | Weak (needs extension) | Weak |
| Metadata filtering | Strong | Strong | Strong | Excellent | Excellent (SQL) | Mid |
| Multimodal | Mid | Strong | Mid | Mid | Weak | Weak |
| Incremental / updates | Easy | Easy | Easy | Easy | Trivial (UPDATE) | Easy |
| In-VPC deployment | Private edition | Self-hosted | Self-hosted | Self-hosted / Serverless | RDS / Aurora | Self-hosted |
| Cost | High | Mid | Mid (ops cost) | Mid | Very low (PG already there) | Very low |
| Customer already has it | Usually no | Usually no | Usually no | Some AWS customers | **Many customers already have PG** | Usually no |

**FDE empirical decision**:

```
  Customer already has PG / Aurora → pgvector (zero extra tools)
  Customer on AWS + mid-scale     → OpenSearch Serverless
  Scale > 500M                     → Milvus or Pinecone
  PoC / small project              → Chroma
  Lowest ops effort / budget OK    → Pinecone
```

---

## B.5 Eval Tool Comparison

| Dimension | Bedrock Evaluations | LangFuse | Phoenix | DeepEval | Promptfoo | Ragas |
|---|---|---|---|---|---|---|
| Form | AWS managed | OSS + Cloud | OSS | Python lib | YAML CLI | OSS |
| Eval scope | Model / KB / Agent | Full LLM stack | Full LLM stack | Embedded unit test | Prompt comparison | RAG-specific |
| LLM-as-judge | Built-in | Supported | Supported | Supported | Supported | Supported |
| Auto metrics | BLEU / ROUGE / accuracy | Custom | Custom | Many built-in | Custom | 6 RAG metrics |
| Dataset management | S3 jsonl | UI + API | UI | Code | YAML | Code |
| Online trace | No (static) | Strong | Strong | No | No | No |
| CI-friendly | Mid | Mid | Mid | Strong | Excellent | Mid |
| Cost | Per token + judge | OSS free / Cloud paid | OSS free | OSS free | OSS free | OSS free |

**Typical combination**:

```
  LangFuse (trace + online) + Promptfoo (CI) + Bedrock Evaluations (compliance acceptance)
```

---

## B.6 Deployment Platform Comparison — From an LLM-app Lens

| Dimension | Lambda | ECS Fargate | EKS | SageMaker Endpoint | Step Functions |
|---|---|---|---|---|---|
| Startup latency | Cold start 100ms-3s | Container startup in seconds | Pod startup in seconds | Startup in seconds | Orchestration overhead |
| Max single run | 15 min | None | None | None | 1 year |
| Concurrency model | Automatic | Self-managed | Self-managed | Self-managed | N/A |
| Best for | Single LLM call / simple Agent | Long-running server / MCP | Complex clusters | Self-hosted models | Long flows / HITL |
| Cost shape | Pay-per-use | Per container | Per node | Per endpoint | Per state transition |
| State | Stateless | Stateless / EFS | StatefulSet | Stateless | State held in SF |
| Image size | 250MB / 10G (image) | Large | Large | Large | N/A |

**Rules of thumb**:
- Simple RAG / API → Lambda
- MCP server / Agent service → ECS Fargate
- Long flow + HITL → Step Functions + Lambda
- Self-hosting 70B+ models → SageMaker / EKS + GPU

---

## B.7 Programming Languages / Runtimes

| Dimension | Python | TypeScript | Go | Rust |
|---|---|---|---|---|
| LLM SDK maturity | Top-tier | Good | Good | Early |
| Data processing | Excellent | Mid | Strong | Strong |
| Async concurrency | asyncio (mid) | Native, strong | goroutines, strong | tokio, strong |
| Deployment size | Large | Mid | Tiny (single binary) | Tiny |
| Hiring | Very easy | Easy | Mid | Hard |
| FDE recommended use | Data / Eval / PoC | Frontend / Lambda | API / high-concurrency | Critical path / embedded |

**FDE default**: Python + TypeScript dual stack covers the vast majority of scenarios.

---

## B.8 Decision Synthesis Table

```
        Customer scenario → recommended stack
        ─────────────────────────────────────────────────

  AWS mid-size insurer + document RAG
    Model:    Bedrock Claude 3.5 Sonnet
    Framework: Bedrock Knowledge Bases + custom Lambda
    Vector:   OpenSearch Serverless
    Eval:     LangFuse Cloud + Promptfoo CI
    Deploy:   Lambda + API Gateway
    IaC:      AWS CDK
    Monitor:  CloudWatch + X-Ray
    Security: IAM Identity Center + Bedrock Guardrails

  ─────────────────────────────────────────────────

  Existing PG database + Chinese finance + intranet
    Model:    DeepSeek V3 / Qwen 2.5 72B self-hosted (vLLM)
    Framework: Native SDK + state machine
    Vector:   pgvector
    Eval:     Phoenix (self-hosted) + custom judge
    Deploy:   K8s
    IaC:      Terraform
    Monitor:  Prometheus + Grafana
    Security: Internal LDAP + custom audit

  ─────────────────────────────────────────────────

  Multinational retail + multi-SaaS integration + Agent
    Model:    Claude 3.5 Sonnet
    Framework: LangGraph + MCP servers
    Vector:   Pinecone
    Eval:     LangFuse + DeepEval
    Deploy:   ECS Fargate
    IaC:      Pulumi (multi-cloud)
    Monitor:  Datadog
    Security: Okta + per-call OAuth
```

---

[← Back to Contents](../README.md) · [Next: Eval Set Design Templates →](appendix-c.md)
