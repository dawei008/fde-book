# Chapter 3: Two FDE Modes — Data-Driven vs LLM-Driven

## Opening

```
Two FDEs in the same coffee shop.

A is at Palantir, 10 years in. Today he's editing some PySpark to
incrementally sync a customer ERP table into Foundry's Ontology and
build a "customer-order-shipment" graph. He reads Avro schemas faster
than he reads novels.

B is at OpenAI, 1 year in. Today he's tuning a prompt template so an
Agent can auto-create subtasks in the customer's Jira. He knows the
system-prompt style differences across 5 LLMs by heart.

Both have the title Forward Deployed Engineer.
The work they do looks completely different.

But spend an hour with them and you'll find — their ways of thinking
are 80% the same, and their tool stacks are 80% different.

This chapter covers: where the boundary between the two FDE modes is,
when to switch, and — when you take on a project — how to decide
which mode you should be in.
```

---

## 3.1 The Essential Difference Between the Two Modes

```
                  Data-Driven FDE             LLM-Driven FDE
                  ─────────────────           ─────────────────
Representative    Palantir, AWS GenAIIC      OpenAI, Anthropic
companies         Snowflake PS, Databricks   Cohere, Cresta
                  Traditional B2B            Downstream AI
                  consulting                 startups

Core question     "How do we put the         "How do we automate
                  customer's data to use?"   the customer's
                                             workflow?"

Main deliverables Ontology + Pipeline        Agent + Prompt + Toolset
                  + Dashboard + Report       + Eval Set

Hard skills       SQL, Spark, ETL, dbt       LLM API, Prompt
                  Warehouse modeling,        RAG, Agent frameworks
                  schema evolution           MCP, Function Calling
                  Avro/Parquet/Iceberg

Soft skills       Working with the data      Working with business
                  team / DBAs                PMs / frontline staff
                  Data governance /          Business processes /
                  privacy compliance         user personas

Time split        50% data exploration       40% Discovery / business
                  30% Pipeline engineering   30% Prompt + Eval
                  20% business alignment     30% integration + deploy

What success      Customer can answer        A specific action in the
looks like        questions directly with    customer's workflow has
                  data when making           a meaningfully shorter
                  decisions                  median time

Most fatal        Data is correct but no     Demo is brilliant but
failure           one uses it                no one can use it
```

---

## 3.2 What Decides the Mode Is the Project, Not the Company

A lot of people assume "I'm at company X, so I'm in mode X." Wrong.

**What actually decides the mode is the phase of the project and the customer's bottleneck**:

```
            Which mode are you currently in?
            ─────────────────────────────────

  Q1: Is the customer's bottleneck "data we can't use" or
      "workflow not automated"?
        ↓                              ↓
        Data we can't use              Workflow not automated
        → Data-driven mode             → See Q2
                                      ↓
  Q2: Is the existing workflow based on structured data or on
      natural language?
        ↓
        Structured data                Natural language /
        → Lean data-driven             documents / dialogue
        (e.g., automated reports)      → LLM-driven mode
                                       (e.g., support / contracts /
                                        knowledge Q&A)
```

### A Few Real Examples

**Example 1**: A finance customer wants "claims automation"

- Weeks 1-4: read their claims process; the key bottleneck is converting "doctor's chart → claim amount" from unstructured to structured → **LLM-driven** (OCR + LLM extraction)
- Weeks 5-8: the extracted fields need to join against policy clauses, build a rules engine → **Data-driven**
- Weeks 9-12: re-package the rule-based judgments into an explainable Agent → **LLM-driven**

**Same project, three phases, three modes.**

**Example 2**: A manufacturing customer wants "predictive maintenance"

- Core of the project is time-series data + models → **Data-driven main line**
- But report generation / work-order language / operator Q&A use LLM → **LLM-driven side line**

70% data-driven main line, 30% LLM-driven side line. **Not either-or.**

---

## 3.3 How the "Three Iron Rules" Land Differently in Each Mode

The rules don't change — the way they land does:

### Sell the outcome

| | Data-Driven | LLM-Driven |
|---|---|---|
| Outcome example | Monthly report on-time rate 60%→95% | Customer-service first-response median 4h→30min |
| Where the number comes from | Computable from the data system itself | Requires new instrumentation / trace |
| Who you talk to | Data team + BI + business | Business team + frontline staff |

### Eval-driven

| | Data-Driven | LLM-Driven |
|---|---|---|
| Eval target | Data correctness, semantics, SLA | Answer quality, relevance, safety |
| Eval tooling | dbt tests, Great Expectations, hand-rolled SQL | DeepEval, Promptfoo, Bedrock Evaluations |
| Run frequency | Every ETL run | Every PR + daily regression |

### Fix Forward

| | Data-Driven | LLM-Driven |
|---|---|---|
| What to fix on site | A SQL snippet / a dbt model / a schedule | A prompt / a retriever config / a tool definition |
| Hot-fix channel | Airflow / dbt cloud direct deploy | Config service / Lambda / sidecar prompt repo |
| Deploy permission | DB write permission (limited) | App config write permission (often available) |

---

## 3.4 Two Sets of Muscles in the Tool Stack

Use the two checklists below to spot which side you're missing:

### Required for Data-Driven FDE

```
Entry              Intermediate          Advanced
─────              ────────────          ────────
SQL (must-have)    dbt                   Data modeling (Kimball / Inmon)
Python pandas      Airflow / Prefect     Apache Iceberg / Delta
JSON / Avro        Spark / PySpark       Ontology design (Palantir style)
PostgreSQL         Snowflake / BigQuery  Schema evolution
                   Redshift              Real-time pipelines (Kafka, Kinesis)
                   Kerberos / IAM        Data lineage (OpenLineage)
                   ETL debugging         Privacy compliance (GDPR, PII)
```

### Required for LLM-Driven FDE

```
Entry               Intermediate          Advanced
─────               ────────────          ────────
LLM API calls       LangChain /            Agent frameworks (LangGraph,
                    LlamaIndex             AutoGen, Bedrock Agents)
Prompt engineering  RAG (vector DBs)       MCP protocol
Function Calling    Eval frameworks        Agent tool sandboxing /
JSON Schema         Trace tools            permissions
                    (LangFuse, Phoenix,    Composite Function Calling
                     LangSmith, Bedrock)   Streaming / structured output
                    Vector DB              Fine-tuning (LoRA)
                    (Pinecone, Weaviate,   Inference optimization
                     OpenSearch, pgvector) (vLLM, TGI)
                                           Deployment (SageMaker, Bedrock)
```

**An FDE doesn't need to master both sets**, but **needs to know each well enough to ask the right questions**.

---

## 3.5 Switching Modes Inside a Single Project

In practice, the hardest part is "when to switch." Three signals:

### Signal 1: You discover "the data is already there, just no one can query it"

→ This is an LLM-driven opportunity (natural-language query, RAG)

Example: customer says "we can't find anything in our contract clauses." Don't rush to write ETL — check whether the issue is data format or retrieval. RAG might solve it on day one.

### Signal 2: You discover "LLM output is mostly correct, but downstream systems can't ingest it"

→ Switch back to data-driven (structured output, schema validation)

Example: the Agent's extracted fields can't enter ERP because encodings are inconsistent. You now need data-governance thinking — mapping tables / validation rules / exception handling.

### Signal 3: You discover "the customer's decisions need numbers, but the existing data isn't enough"

→ Data-driven main line (instrumentation, ETL, dashboards)

Example: customer asks "how much time has this Agent actually saved?" — and you find there's no instrumentation. Build instrumentation → ETL → dashboards first, then resume the LLM work.

---

## 3.6 Mapping the Two Modes from an AWS Lens

The AWS GenAI Innovation Center FDEs are the canonical example of "doing both modes." Their projects typically use this stack:

```
        Data-Driven side               LLM-Driven side
        ────────────────              ────────────────
Storage  S3, Lake Formation            S3 (KB documents)
Data     Glue ETL, Glue Catalog        OpenSearch / Knowledge Bases
Compute  EMR, Athena, Redshift         Bedrock (model invoke)
Orches.  Step Functions, MWAA          Bedrock Agents / Step Functions
Govern.  Lake Formation perms          IAM + KMS
Monitor  CloudWatch + OpenLineage      CloudWatch + Bedrock guardrails
                                       + Bedrock Evaluations
```

In a single week on a single customer project, you may touch Glue ETL and Bedrock Agents both. **The FDE has to be able to switch up/down/left/right.**

> **AWS reference**: see Appendix A (FDE Toolstack Quick Reference) and Appendix B (Comparison Matrix) for the full two-track tool list.

---

## 3.7 Self-Check: Which Mode Should You Lean Into Right Now

```
─────────────────────────────────────────────────────
 Project trait                            → Lean toward
─────────────────────────────────────────────────────
 Customer's biggest pain is "can't find   → Data-driven 60%
 data"
 Customer's biggest pain is "too much     → LLM-driven 70%
 repetitive work"
 Customer compliance is very strict       → Data-driven 50% (govern first)
 Customer business growing fast,          → LLM-driven 60%
 docs can't keep up
 Customer already has a data team         → You take the LLM-driven main
 Customer has no data team                → You take the data-driven main
 Customer wants "results in 3 months"     → LLM-driven (faster wins)
 Customer wants "infrastructure for       → Data-driven (more solid base)
 the next 3 years"
─────────────────────────────────────────────────────
```

---

## Key Citations

> "*The forward deployed engineer is data-driven by training and LLM-driven by opportunity.*"
> — A. Lawrence (paraphrased), *FDE Rule Book*, 2025

> "*The boundary between data work and AI work disappeared the moment LLMs became infrastructure.*"
> — AWS GenAI Innovation Center positioning, 2025-2026

---

## Action Checklist

1. **Identify the mode of your current project** (use the §3.2 / §3.7 decision trees)
2. **Write a one-liner for your manager**: this quarter, 70% time in mode X, 30% in mode Y
3. **Audit your tool-stack gaps** (the two §3.4 lists); pick the most critical gap and close it this week
4. **Buy coffee for a senior FDE in the other mode at your company**, ask about their common failure modes
5. **Draw a "two-mode breakdown diagram" for your current project**, labeling each module by which side it leans toward
6. **In your next customer conversation**, deliberately ask yourself: "Is this a data-type request or an LLM-type request?"

---

## Anti-Pattern Checklist

- ❌ **Forcing one mode onto everything** ("I'm strong on LLM, so I'll solve everything with LLM")
- ❌ **Stacking Agents before data governance is done** (the foundation is shaky; more Agents make it worse)
- ❌ **Forcing yourself to write ETL when the data is already ready** (you miss the LLM fast-win window)
- ❌ **Switching modes without telling the customer or your team** (downstream gets confused)
- ❌ **Believing "switch mode = throw out and redo"** (most of the time it's just adding an adapter layer)

---

## Relation to the Next Part

Part I's three chapters set up the full coordinate system for FDE engineering: the shape of time (Ch 1), the shape of judgment (Ch 2), the shape of capability (Ch 3).

Part II steps into the first concrete action — Discovery. From the moment you take on a new project, **what do you actually ask, observe, and write in week 1?** This is the most overlooked phase in FDE work, and the one with the highest ROI.

[← Previous: Three Iron Rules](chapter-02.md) · [Next Part: Discovery →](../part-2/intro.md)
