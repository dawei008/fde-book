---
title: "part-3/chapter-07.md"
nav_exclude: true
search_exclude: false
---

# Chapter 7: Decision Tree — RAG / Fine-tune / Prompting / Agent

## Opening

```
The customer CTO says: "I want to build an AI customer-support agent."

The new FDE's reaction:
  A) "Great, let's build a RAG and index the FAQs."
  B) "Great, let's fine-tune a model on customer dialogue."
  C) "Great, let's wire up GPT-4 with a multi-Agent setup."

The veteran FDE's reaction:
  "Wait — what's the biggest pain point in your support today?

   Are answers wrong (→ maybe RAG)?
   Or correct but robotic (→ maybe prompting + few-shot)?
   Or do you need to take action across systems (→ maybe Agent)?
   Or is some industry-specific phrasing impossible to nail
     (→ maybe fine-tune)?

   Different pain points map to completely different solutions.
   Pick the wrong one here, and six weeks are wasted."

The goal of this chapter: decide which one in 30 seconds,
and explain why in 10 minutes.
```

---

## 7.1 The Essential Difference Between the Four Approaches

```
              Input handling     Knowledge source     Output generation
              ─────────          ──────────           ──────────

  Prompting   raw query          model weights         model generates directly
                                 (learned at training)

  RAG         query → retrieve   external KB           retrieval + model generation
                                 (updatable)

  Fine-tune   raw query          new weights           new model generates
                                 (trained by you)

  Agent       query → plan       tool-call results     multi-step reasoning + synthesis
                                 + model weights
                                 + KB
```

Plain language:

- **Prompting** = "tweak the prompt; the model already knows"
- **RAG** = "put the answer in a corpus; the model looks it up"
- **Fine-tune** = "teach the answer into the model's brain"
- **Agent** = "let the model use tools to get things done"

---

## 7.2 The Main Decision Tree

```
              Customer's core pain point
                    │
        ┌───────────┴───────────┐
        ↓                       ↓
    "doesn't know the answer"   "knows but it's wrong"
        │                       │
        ↓                       ↓
    Need external knowledge?    Style / format / industry-phrasing issue?
        │                       │
        ├─Yes→ RAG               ├─Yes→ Prompting + Few-shot
        └─No→ Prompting         │       (90% of the time, enough)
                                ↓
                            Tried and failed?
                                │
                                ├─Yes→ Fine-tune
                                └─No→ keep iterating Prompting

   "Need to actively act / cross systems"
        │
        ↓
    Agent (tool use)
```

### Reading the Main Path

```
Default order:
  1. Start with Prompting (cheapest, fastest)
  2. Not enough → RAG (add external knowledge)
  3. Still not enough → Agent (let the model take action)
  4. Last resort → Fine-tune (most expensive, hardest to maintain)
```

**For 90% of LLM applications, Prompting + RAG is enough.** Fine-tune is the last-of-the-last option to consider.

---

## 7.3 RAG vs Fine-tune — The Eternal Confusion

The boundary between RAG and Fine-tune is what new FDEs get wrong most often.

```
                    RAG                       Fine-tune
                    ─────────                 ─────────

  What it solves    Knowledge missing         Wrong answer style
                    from the model            Non-standard terminology / format
                    Frequently updated data   High-frequency, low-complexity tasks
                    Need traceable citations

  Data requirements Documents (no labels)     High-quality Q&A pairs
                    Hundreds — millions       Hundreds — tens of thousands

  Dev cycle         1-2 weeks                 4-8 weeks

  Maintenance cost  Just update the docs      Data drift = retrain

  Explainability    High (with citations)     Low (black box)

  Good fit          Knowledge bases / FAQ     Vertical-industry phrasing
                    Dynamic business rules    Fixed output formats
                    Compliance with sourcing  Ultra-low latency (small models)

  Bad fit           Need "voice"              Frequently changing data
                    Ultra-low latency         Need source attribution
                    Fine-tune is cheaper      Tight budget
```

### A Quick-Decision Mantra

```
"Fact / knowledge" correctness        → RAG
"Tone / style / format"               → Prompting → Fine-tune
"Action / cross-system"               → Agent
"Latency / cost"                      → model selection + caching (not necessarily method change)
```

### Counter-Example: Misusing Fine-tune

> *A customer needed "customer-support answers to policy questions". A new FDE went straight to fine-tuning a 7B model and shipped after three weeks. A month later, policy updated; the model gave wrong answers and complaints rolled in. Re-fine-tuning took another three weeks.*
>
> *Postmortem: policy questions = factual knowledge = should use RAG. With RAG, you update the KB — no retraining.*

**FDE failure mode**: treating a RAG problem as a fine-tune problem.

---

## 7.4 Sub-Decisions Inside RAG

Once you've picked RAG, four sub-decisions remain.

### Sub-Decision 1: Chunk Granularity

```
        Granularity choices
        ─────────────────────────────────

  By sentence (50-100 tokens)
    → recall sharp, but little context
    → fits: FAQ, short answers

  By paragraph (200-500 tokens)
    → balanced (most common)
    → fits: knowledge bases, document Q&A

  By section (1000-3000 tokens)
    → full context, fuzzier recall
    → fits: legal, contract analysis

  By document (whole doc)
    → use a long-context model (Claude 200K)
    → fits: small number of large docs, contract review
```

### Sub-Decision 2: Retrieval Strategy

```
  Pure vector retrieval (semantic)
    → strength: strong semantic understanding
    → weakness: weak keyword hits

  Pure keyword retrieval (BM25)
    → strength: exact match
    → weakness: weak semantics

  Hybrid retrieval (Hybrid: semantic + BM25 + rerank)
    → strength: strongest overall
    → weakness: higher complexity
    → recommended: this is the production default
```

### Sub-Decision 3: Whether to Add a Reranker

```
            Signals to add a reranker
            ─────────────────

  ✓ Top-10 recall contains the right answer, top-3 doesn't
  ✓ Business is sensitive to recall precision (legal / medical)
  ✓ Document corpus > 10K
  ✓ Budget allows it (one extra model call per query)

  → hit any 2 → add a reranker
```

### Sub-Decision 4: Index Update Frequency

```
  T+1 (daily index)
    → docs visible the next day
    → simple (daily batch)

  T+1h (near real-time)
    → one-hour latency
    → needs an incremental indexing pipeline

  Real-time
    → write-then-query immediately
    → high complexity, use sparingly
```

### AWS Hands-On: Bedrock Knowledge Bases as One-Stop RAG

```
        Bedrock Knowledge Bases architecture
        ─────────────────────────────────────

  Sources: S3 / Confluence / Salesforce / Web
            ↓
  Bedrock automatically:
    - Chunks (configurable chunking strategy)
    - Embeds (Titan Embed v2 / Cohere Embed)
    - Writes to vector store (OpenSearch Serverless by default)
            ↓
  Retrieve API:
    - retrieve(query, top_k)
    - retrieveAndGenerate(query, model)
            ↓
  Generation + citations
```

Minimal runnable config:

```
1. Create the KB:
   - Bedrock console → Knowledge bases → Create
   - Data source: S3 bucket
   - Chunking: default (300 tokens, 20% overlap)
   - Embedding: Titan Embed v2

2. Sync data:
   - One-click sync, minutes to hours (depending on size)

3. Test query:
   - retrieveAndGenerate(query="...", modelArn="claude-3-5-sonnet")
   - Output comes with citations
```

> **AWS reference**: search "Amazon Bedrock Knowledge Bases setup" for the latest supported source types.

---

## 7.5 Agent — When to Reach for One

Agent ≠ "complicated RAG". An Agent's value is **actively calling external tools to complete tasks**.

```
        Signals you need an Agent
        ─────────────────

  ✓ The task requires 2+ "decide + act" steps
  ✓ Need to call external APIs / databases / systems
  ✓ The input doesn't map to a fixed answer
  ✓ Single prompt + RAG has been tried and failed

  → 3+ of these → consider an Agent
```

### Three Typical Agent Shapes

```
1. Reactive Agent (single-step tool)
   query → LLM picks a tool → execute → return

   Fits: simple lookups ("where's my order?")
   Tool count: 5-20

2. ReAct Agent (multi-step loop)
   query → LLM thinks → call tool → see result → think again → ...

   Fits: multi-step tasks (order + shipping + refund)
   Tool count: 10-50

3. Multi-agent (multiple agents)
   master agent splits the task → sub-agents execute → aggregate

   Fits: cross-team complex flows
   Tool count: 50+
```

### Agent Failure Modes

```
❌ Tool count > 30 → probability of picking the wrong tool spikes
❌ Tool descriptions sloppy → Agent calls the wrong one or skips
❌ No fallback → one wrong step, everything fails
❌ No trace → can't locate failures
❌ Multi-agent nesting → debugging hell
```

**The FDE rule of thumb on Agents**: start with a single Agent + tool augmentation; only escalate to Multi-agent when a single Agent can't cope.

### AWS Hands-On: Getting Started with Bedrock Agents

```
Bedrock Agents core components
─────────────────────────────────

1. Agent: the entry point (bound to a foundation model)
2. Action Groups: the toolset
   - Lambda function (your code)
   - OpenAPI schema (describes the tool)
3. Knowledge Bases: linked RAG
4. Guardrails: input/output filtering
5. Memory: cross-session state (new feature)
```

Minimal runnable flow:

```
Step 1: Write a Lambda function (one tool)
        e.g., get_order_status(order_id) → returns order status

Step 2: Write an OpenAPI schema describing the Lambda
        - paths: /get_order_status
        - parameters: order_id
        - responses: { status: string, eta: string }

Step 3: Bedrock console → Agents → Create
        - Foundation model: Claude 3.5 Sonnet
        - Instructions: "You are an order-support assistant ..."
        - Action group: link the Lambda above

Step 4: Test in Agent playground
        "Where is my order #1234?"
        Agent: auto-calls Lambda → returns a structured answer
```

> **AWS reference**: search "Bedrock Agents quick start".

---

## 7.6 The Master Decision Table

```
┌──────────────────────────────────────────────────────────────────┐
│  Typical scenario           Recommended approach                  │
├──────────────────────────────────────────────────────────────────┤
│  Internal KB Q&A            RAG (Bedrock KB + Sonnet)            │
│  FAQ support                RAG + light prompting                │
│  Contract / doc review      Long-context prompting (Claude 200K) │
│  Code generation / review   Prompting + Few-shot (Opus / GPT-4)  │
│  Cross-system order lookup  Reactive Agent (Bedrock Agents)      │
│  Cross-team ticket routing  ReAct Agent + 5-10 tools             │
│  Email auto-reply           RAG + Prompting + Style few-shot     │
│  Industry-term translation  Fine-tune (LoRA on Llama 3 8B)       │
│  Regulatory report gen      RAG + multi-step prompting + rules   │
│  Research / info gathering  Multi-agent (CrewAI / LangGraph)     │
└──────────────────────────────────────────────────────────────────┘
```

**80% of real projects fall in the first 5 rows.**

---

## 7.7 Switching Signals

In practice you rarely pick right the first time. Learn to read the "switching signals".

```
Currently using Prompting, you observe:
  ✓ Eval score is stuck at 70%, not climbing
  ✓ Need repeated lookups against external knowledge
  → switch to RAG

Currently using RAG, you observe:
  ✓ Recall is fine, but answer style / format is hard to tune
  ✓ Few-shot keeps growing the prompt
  → add Fine-tune (lightweight LoRA)

Currently using RAG, you observe:
  ✓ Users start asking "do X for me" instead of "what is X"
  ✓ Need to write to / modify external systems
  → upgrade to Agent

Currently using an Agent, you observe:
  ✓ Tool count < 10 yet accuracy < 80%
  ✓ Trace shows the wrong tool gets called repeatedly
  → fall back to Prompting + templates (don't force the Agent)
```

**An FDE's craft is in "knowing when to switch".**

---

## Key Quotes

> "*Most LLM problems are not LLM problems — they're product problems.*"
> — A. Lawrence, *FDE Rule Book*, 2025

> "*Try prompting first. Always.*"
> — OpenAI internal best practices, 2025

> "*Fine-tuning is the last 10% you do for the last 10% of cases.*"
> — AWS GenAI Innovation Center, 2025

---

## Action Checklist

Must-dos in the first week of a new project:

1. **Write the customer's pain points in 5 sentences** and locate the main path against §7.2's decision tree
2. **Run 10 seed samples to set a Prompting baseline** (don't jump straight to RAG)
3. **If the baseline is < 70%, add RAG and run a comparison**
4. **Write a "why we're not fine-tuning" memo** (default: no fine-tune; need a strong reason to do it)
5. **If the customer brings up "Agent", run them through §7.5's 4 signals first**
6. **Review switching signals every two weeks**; don't push through.

---

## Anti-Pattern Checklist

- ❌ **Customer says "AI customer support" → straight to multi-Agent** (RAG covers 80%)
- ❌ **Any inaccuracy → add Fine-tune** (Fine-tune doesn't solve knowledge-update problems)
- ❌ **Layering RAG + Fine-tune + Agent in the same project** (impossible to localize the cause)
- ❌ **Skipping the baseline and going straight to a complex approach** (you don't know if the complexity pays off)
- ❌ **Tool list > 10 → force Multi-agent** (try a single Agent first)
- ❌ **Putting trendy frameworks (CrewAI / AutoGen) into production** (fine for PoC, careful in production)

---

## Relation to the Next Chapter

This chapter answered "which approach". The next chapter says: **whatever the approach, you must turn the Eval set into a CI gatekeeper before you start writing code** — the concrete way to live the Eval-driven rule.

[← Previous: Tech Stack Quick-Decision Matrix](chapter-06.md) · [Next: Eval First, Code Second →](chapter-08.md)
