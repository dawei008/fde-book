---
title: "part-3/chapter-06.md"
nav_exclude: true
search_exclude: false
---

# Chapter 6: Tech Stack Quick-Decision Matrix — Model / Framework / Database / Orchestration

## Opening

```
A new FDE is doing her first PoC.

She drew a selection table in Notion:
  - LLM: GPT-4o vs Claude 3.5 vs Llama 3.1 vs Bedrock Titan vs ...
  - Vector store: Pinecone vs Weaviate vs OpenSearch vs pgvector vs ...
  - Orchestration: LangChain vs LlamaIndex vs LangGraph vs native ...
  - Agent framework: AutoGen vs Bedrock Agents vs CrewAI vs ...

Each candidate was scored on 8 dimensions
(performance / cost / community / security / deployment / ...).

Ten days later, she's still selecting. Not a single line of business code.

Her boss grabs the table, draws four X's, and says:
"Cut these four candidates outright. Take the remaining one or two,
 spend a week building v0.1, and look at the Eval score.
 Don't spend more than a week on selection."

She does it. By Week 4 the customer is looking at a demo.

This chapter doesn't give you a "perfect" stack. It gives you a
working set you can decide on in 30 minutes — and revert within
six weeks if you're wrong.
```

---

## 6.1 Two Principles for Stack Selection

### Principle 1: Pick "good enough", not "the best"

The nature of LLM engineering:
- The stack changes substantially every six months
- However "perfect" your selection, you'll re-select within six months
- **Selection cost = cost of getting it wrong + cost of replacement**

→ A stack you can "onboard in 30 minutes and swap out in a week" beats the "optimal" stack.

### Principle 2: Constraints first, candidates second

```
                    Constraint priority
                    ─────────────

  1. Customer compliance / deployment shape (VPC / offline / cloud)
     → cuts 60% of candidates

  2. Data sensitivity / PII
     → cuts half of what's left

  3. Budget / monthly token cap
     → determines model tier

  4. Team familiarity
     → determines framework choice

  5. Performance / experience targets
     → fine-tunes the specifics
```

**The new-FDE mistake** is to start at #5; the veteran starts cutting at #1.

---

## 6.2 Model Selection Matrix

```
                    Scenario → Recommended default model
                    ─────────────────────────

  General chat / RAG / customer support  → Claude Sonnet (top pick on Bedrock)
                                            or GPT-4o-mini (low cost)

  Code generation / complex reasoning    → Claude Opus / GPT-4o

  Very long documents (>50K tokens)      → Claude (200K context)

  Low latency / high QPS                 → Haiku / GPT-4o-mini / Llama 3 8B

  Fully offline / on-prem                → Llama 3 / Mistral self-hosted

  Chinese-first / domestic compliance    → Qwen / ERNIE / DeepSeek

  Embedding                              → Bedrock Titan Embed v2 (English + multilingual)
                                            or BGE-M3 (Chinese-first)
```

### Five Questions to Pick a Model

```
1. Deployment shape?
   Managed cloud is fine → Bedrock / OpenAI / Claude API
   Must run in customer VPC → Bedrock VPC endpoint / SageMaker JumpStart
   Offline → self-hosted Llama / Qwen

2. Average input length per request?
   <8K  → any model
   8-32K → prefer Claude / Bedrock
   >32K  → Claude 200K / Gemini 1M

3. Monthly budget?
   <$1k → must use mini / haiku tier
   $1-10k → mini as the workhorse, escalate for complex cases
   >$10k → can default to sonnet / 4o

4. Strong need for JSON / structured output?
   Strong → prefer OpenAI / Claude (strict mode / tool use)

5. Business language?
   English-only → GPT-4o / Claude
   Chinese-only → domestic models
   Mixed → Claude / Gemini / Qwen
```

### AWS Hands-On: Baseline Model Selection on Bedrock

```
Step 1: Run 5 seed samples in Bedrock playground
        - Claude 3.5 Sonnet
        - Claude 3 Haiku
        - Llama 3.1 70B
        - Mistral Large
        - Titan Text Premier
        Eyeball output quality once.

Step 2: In Bedrock Evaluations, create a Model Evaluation Job
        - Dataset: 50 seed samples
        - Evaluator: built-in (accuracy + robustness)
        - Compare multiple models

Step 3: Read the report
        - Sort by total score
        - Sort by unit price
        - Pick the one with "best price/perf + covers 90% of cases"

Step 4: Make that model the default
        Use the others as the upgrade path ("complex queries go to Opus")
```

> **AWS reference**: search docs.aws.amazon.com for "Bedrock supported foundation models" and "Bedrock model invocation pricing".

---

## 6.3 Framework Selection Matrix

```
                    Scenario → Recommended framework
                    ─────────────────────────

  Pure RAG, one-shot Q&A                → Bedrock Knowledge Bases directly
                                            or LlamaIndex

  RAG + multi-step pipeline             → LangChain (Python) / LangGraph

  Agent (tool use + multi-turn)         → LangGraph or Bedrock Agents

  Multi-agent collaboration             → AutoGen / CrewAI / LangGraph

  Production-grade control flow         → skip LangChain; native SDK + state machine
  (must be stable)

  Enterprise integration / MCP          → Bedrock Agents + MCP / Anthropic SDK
```

### Three Trade-offs in Framework Choice

```
                  Dev speed     ←─────→     Production stability
                  ←────────────→
                  LangChain                  Native SDK
                  fast, gotchas              slow, solid

                  Community     ←─────→     Consistency
                  ←────────────→
                  LangChain                  Bedrock Agents
                  many plugins               consistent + constrained

                  Debug visibility ←─────→  Framework abstraction
                  ←────────────→
                  LangFuse / Phoenix         LangChain internal chains
```

### Practical Advice (by Stage)

```
PoC stage (W1-W6):
  - Pick whatever ships a demo fastest: LangChain / LlamaIndex / Bedrock KB
  - Prefer SaaS: full Bedrock suite + LangFuse Cloud

Mid-stage (W7-W12, before production):
  - Replace the "3 most critical steps" in the pipeline with native SDK + state management
  - Wire up monitoring (Trace, Eval, Cost)
  - Rip out the unreliable LangChain components

Production stage (M3+):
  - 90% of the code is yours; the framework only sits at key nodes
  - Framework upgrades = no longer allowed to block the business
```

---

## 6.4 Vector Store Selection Matrix

```
        ┌──────────────────────────────────────────────────┐
        │              Scale vs Deployment Matrix          │
        ├──────────────────────────────────────────────────┤
        │  Scale         Managed         Self-hosted       │
        │  <1M           pgvector*       pgvector          │
        │  1-10M         OpenSearch      Weaviate / Milvus │
        │  10-100M       Pinecone /      Milvus / Vespa    │
        │                OpenSearch                        │
        │  >100M         dedicated       dedicated         │
        │                evaluation      evaluation        │
        └──────────────────────────────────────────────────┘
        * If the customer already has Postgres → pgvector first;
          don't introduce a new service.
```

### Four Questions to Pick a Vector Store

```
1. What is the customer already running?
   → already has PG → pgvector (saves ops)
   → already has ES/OpenSearch → use OpenSearch vector directly
   → already has Bedrock KB → backend defaults to OpenSearch Serverless

2. How often does the data update?
   → static (monthly) → anything works
   → high frequency (sub-second) → Pinecone / Weaviate / OpenSearch

3. Metadata filter requirements?
   → complex multi-dimensional → OpenSearch / Weaviate
   → simple → anything works

4. Deployment shape?
   → cloud SaaS allowed → Pinecone (least ops)
   → customer VPC → OpenSearch / pgvector / self-hosted Weaviate
   → offline → Milvus / FAISS
```

### AWS Hands-On: Picking the Backend for Bedrock Knowledge Bases

```
                    Bedrock Knowledge Bases backend choices
                    ─────────────────────────────────

  OpenSearch Serverless (default)
    - Zero ops, usage-based pricing
    - Fits PoCs and medium scale
    - Floor cost ~$345/month (minimum OCU)

  Aurora PostgreSQL with pgvector
    - Customer already on Aurora PG → plug in directly
    - Fits scale <10M chunks

  Pinecone
    - Easy cross-account / multi-region
    - High-QPS scenarios

  Redis Enterprise Cloud
    - Low latency (<10ms)
    - But expensive
```

> **AWS reference**: search "Bedrock Knowledge Bases supported vector stores" for the latest support matrix.

---

## 6.5 Orchestration / Workflow Selection

Once an LLM application is live, the hardest problem isn't "is the model right" — it's "is the flow stable."

```
                    Scenario → Recommended orchestration
                    ─────────────────────────

  Single LLM call                    → no orchestration needed (SDK direct)

  Sequential multi-step              → LangGraph / native async

  Parallel + fan-in                  → LangGraph / Step Functions

  Cross-service long flows (>5 min)  → AWS Step Functions
                                          or Temporal

  Agent autonomous multi-step        → LangGraph / Bedrock Agents

  Human-in-the-loop (HITL)           → Step Functions + SQS
                                          or Temporal signals
```

### One Judgment Call: When to Graduate from LangGraph to Step Functions

```
Signals to upgrade:
  ✓ Single execution > 5 minutes
  ✓ Need to persist intermediate state
  ✓ Need retry / resume from checkpoint
  ✓ Need audit / visualizable execution history
  ✓ Flow involves multiple services (not just LLM)

Hit any 2 → use Step Functions
None of them → LangGraph is fine
```

---

## 6.6 Monitoring / Trace Selection

LLM application without traces = no debugging = no iteration.

```
                    Scenario → Recommended trace
                    ─────────────────────────

  PoC + quick eyeballing             → LangFuse Cloud / LangSmith Cloud
                                          (5 min to wire up)

  Enterprise + data must stay in     → LangFuse self-hosted
  domain                                or Phoenix (Arize)

  Deep AWS integration               → CloudWatch + X-Ray + Bedrock built-ins

  Multi-step Agent visualization     → LangSmith / Phoenix
                                          (purpose-built for Agent path viz)
```

### Four Dimensions You Must Trace

```
  1. Latency (per-step time)
  2. Cost (input/output tokens + model)
  3. Quality (Eval score + user feedback)
  4. Error (failure stack + upstream/downstream correlation)
```

### AWS Hands-On: Bedrock + CloudWatch + X-Ray, One Stop

```
        ┌───────────────────────────────────────┐
        │ Application                            │
        │   ↓ (invoke Bedrock model)            │
        │ Bedrock                                │
        │   ↓ (auto emit metrics)               │
        │ CloudWatch Metrics:                    │
        │   - Invocations                        │
        │   - InvocationLatency                  │
        │   - InputTokenCount / OutputTokenCount │
        │   - InvocationClientErrors             │
        │   ↓                                    │
        │ CloudWatch Logs:                       │
        │   - Bedrock Model Invocation Logging   │
        │     (when on, logs every prompt/resp)  │
        │   ↓                                    │
        │ X-Ray Tracing:                         │
        │   - Cross-service trace                │
        │     (Lambda → Bedrock)                 │
        └───────────────────────────────────────┘
```

Turn on Bedrock Model Invocation Logging:

```
Bedrock console → Settings → Model invocation logging
  ✓ Enable
  ✓ Destination: CloudWatch Logs (or S3)
  ✓ Log: Text + Image data (as needed)
```

> **AWS reference**: search "Bedrock model invocation logging" and "CloudWatch metrics for Bedrock".

---

## 6.7 The One-Page Quick-Decision Table (30 Minutes)

```
┌─────────────────────────────────────────────────────────────────┐
│  Constraint / Scenario     Default stack                         │
├─────────────────────────────────────────────────────────────────┤
│  Cloud + medium-scale RAG│ Bedrock + Claude Sonnet              │
│                          │   + Knowledge Bases (OpenSearch)     │
│                          │   + LangFuse Cloud                   │
│                          │   + CloudWatch                       │
├─────────────────────────────────────────────────────────────────┤
│  Customer VPC + strict   │ Bedrock VPC endpoint                 │
│  compliance              │   + Aurora pgvector                  │
│                          │   + LangFuse self-hosted             │
│                          │   + KMS + CloudTrail                 │
├─────────────────────────────────────────────────────────────────┤
│  Fully offline /         │ Qwen / DeepSeek + vLLM self-hosted   │
│  domestic-only           │   + Milvus cluster                   │
│                          │   + self-hosted Phoenix trace        │
├─────────────────────────────────────────────────────────────────┤
│  Agent automation        │ Bedrock Agents OR LangGraph          │
│                          │   + Step Functions (long flows)      │
│                          │   + Lambda (tools)                   │
│                          │   + DynamoDB (state)                 │
└─────────────────────────────────────────────────────────────────┘
```

**60% of projects can lift one of the defaults above directly.** Spend the time you saved on Eval / Discovery / Handoff.

---

## Key Quotes

> "*The best stack is the one your team can debug at 2am.*"
> — A. Lawrence, *FDE Rule Book*, 2025

> "*Don't pick the most powerful model — pick the cheapest one that passes eval.*"
> — Bob McGrew @ YC, 2025

> "*If your stack diagram has more than 7 boxes, you're going to lose at handoff.*"
> — AWS GenAI Innovation Center, 2025

---

## Action Checklist

Six things you must do in Week 3 of any new LLM project:

1. **Write the constraints in 5 sentences**: deployment shape / data sensitivity / budget / team familiarity / performance target
2. **Pick one default stack from §6.7** (within 30 minutes)
3. **Run 50 seed samples on the default to establish a baseline** (no tuning, just running)
4. **A/B 2-3 candidate models in Bedrock Evaluations**
5. **Wire up trace (LangFuse or CloudWatch)** — without it, you can't debug later
6. **Write a "selection decision memo"**: what you picked today, what you cut, what signals will trigger reselection in a month

---

## Anti-Pattern Checklist

- ❌ **Selection takes more than a week** (the PoC dies in the selection phase)
- ❌ **Selecting on benchmarks alone, ignoring deployment shape** (one compliance check kills everything)
- ❌ **Riding LangChain straight into production** (chain abstraction bites back in production)
- ❌ **Shipping a demo with no trace wired up** (you can't locate problems when they hit)
- ❌ **Re-selecting from scratch for every project** (a single company should have a default template)
- ❌ **Chasing the "newest, strongest" model** (changing every two weeks burns the team out)

---

## Relation to the Next Chapter

This chapter answered "which tool". The next chapter answers "which approach" — for the same problem, do you use RAG / Fine-tune / Prompting / Agent? When do you switch?

[← Part III intro](intro.md) · [Next: Decision Tree →](chapter-07.md)
