---
title: "Chapter 3  Two FDE Modes"
parent: "Part I — Role and Mindset"
nav_order: 3
---

# Chapter 3  Two FDE Modes

Chapter 1 gave you the FDE's time shape. Chapter 2 gave you the judgment shape. This chapter gives you the **capability shape** — the same FDE role, on different projects, exercises different muscles.

Why this matters: when your next project asks you to do something you've never done before, you don't need to panic with "am I cut out for FDE?" You're just switching modes. A few weeks and you'll come up to speed. Mindset doesn't change. Iron rules don't change. The muscles do.

---

## 3.1  Two modes

The "FDE" role across the industry actually covers two main modes. What separates them isn't the company — it's **what problem the project is currently trying to solve.**

**Data-driven.** The customer has piles of data they can't use. The FDE's job is to plumb the data, model it, and surface it to decision-makers. Palantir is the origin of this mode, and their FDEs spend most of the week writing ETL, designing the ontology, integrating customer databases, running data validation. Deliverables: a data pipeline plus dashboards or APIs that let the business answer questions with numbers directly.

**LLM-driven.** Some workflow inside the customer has heavy repetitive labor that can be automated. The FDE's job is to embed an LLM application into the customer's workflow. Customer engineering teams at OpenAI, Anthropic, and similar firms are the canonical example. Most AI-application startups walk the same path. Most of the week goes to prompt tuning, Evals, retrieval, agent tool-calling debugging. Deliverables: one or a few LLM applications that visibly drop the median time of some action in the customer's workflow.

The two modes share **the same mindset, different muscles** in the FDE craft. Mindset: "embedded with the customer, accountable for the outcome rather than the code, helping the customer make technical decisions through engineering judgment." Muscles: different tech stacks and tooling.

The table below grounds the difference:

| | Data-driven | LLM-driven |
|---|---|---|
| **Core problem** | How does the customer's data get used | How does the customer's workflow get automated |
| **Primary deliverables** | Ontology + data pipeline + dashboards | LLM application + prompts + Eval set + Toolset |
| **Typical week distribution** | 50% data exploration / 30% pipeline engineering / 20% business alignment | 40% Discovery and business understanding / 30% prompts and Eval / 30% integration and deploy |
| **Hard skills you need** | SQL, Spark, ETL, dbt, warehouse modeling | LLM API, prompt engineering, RAG, agent frameworks |
| **Soft skills you need** | Collaboration with data team / DBAs, data governance | Collaboration with business PM / front-line operators, business processes |
| **What success looks like** | Customer can answer decisions directly with data | Customer's workflow median time drops measurably for a target action |
| **Most fatal failure** | Data modeling done right but no one uses it | Demo dazzles, but it can't actually be used |

Note when reading this table: **the gap in tooling between the two modes is bigger than it looks.** A data-driven FDE typically takes 1–2 years to come up from beginner to fully delivering on their own — warehouse modeling and schema evolution potholes alone consume a year. An LLM-driven FDE takes 6–12 months — the stack itself is young, and the industry hasn't accumulated as much.

But **the way you make judgments is highly similar across the two.** The four-phase model from Chapter 1, the three iron rules from Chapter 2 — both apply across both modes. The difference is only in what specific work happens inside each phase.

---

## 3.2  Mode is decided by the project, not the company

Many people miscalibrate as "I'm at company X, so I'm in mode X." That judgment is wrong.

**What actually decides is where the project is currently stuck.** The same FDE, at the same company, with the same customer, on the same project, may switch modes between phases.

Two real-but-genericized examples:

**Example 1: Financial customer building claims automation.**

- Weeks 1–4: read their claims flow, locate the key bottleneck at "doctor's medical record → claim amount" — turning unstructured handwritten doctor's notes into structured fields. This is **LLM-driven**: OCR + LLM for information extraction.
- Week 5, a concrete switch moment: in the standup you demo LLM extraction at 85% accuracy. The customer's claims-system engineer says on the spot: "Those fields can't enter our rules engine because our specialty codes use ICD-10, and what you extracted is text." That moment, you realize — extraction engineering is enough; downstream integration isn't a prompt problem, it's a schema problem. That week you switch modes: build mapping tables, write a dbt model that normalizes LLM output to ICD-10. This is **data-driven.**
- Weeks 9–12: rule-based judgments need to be re-wrapped as a "business-explainable" agent with traceable decision paths. Switch back to **LLM-driven.**

Same project, three phases, three mode switches. The skill of recognizing "time to switch" matters more than "expert in both."

**Example 2: Manufacturing customer building predictive maintenance.**

The core of this project is time-series data + prediction models — pure **data-driven main line**. But the customer wants the alerts and tickets the system generates to be natural-language readable, and field engineers to be able to query historical faults via Q&A — that part is the **LLM-driven side line**, about 30% of the work.

It isn't either-or. **A lot of FDE projects are data-driven main + LLM side, or the inverse.**

### How to tell which mode the current phase is in

Two questions, in order:

1. **Is the customer's current core bottleneck "data not usable" or "workflow not automated"?**
   - Data not usable (data scattered across systems, can't be queried, definitions disagree across teams) → data-driven.
   - Workflow not automated (heavy repetition, slow info retrieval, decisions depend on individuals) → see next question.

2. **Is the workflow being automated mostly operating on structured data or natural language?**
   - Structured (reports, orders, field filling) → leans data-driven.
   - Natural language or documents (customer service Q&A, contract review, knowledge retrieval) → LLM-driven.

The answers shift across phases. Re-ask every two weeks.

---

## 3.3  When to switch modes inside one project

Switch-timing is harder than mode-typing. Three signals that most often appear; if you see one, it's time to switch:

**Signal 1: discovering "the data is already there, just nobody can query it."**

Don't rush to write ETL or build a data platform. The customer says "we can't search our contract clauses." Maybe it's a format problem (PDFs aren't parsed). Maybe it's a search problem (no index on the search engine). Look first — RAG might solve it, no data-driven heavy lift needed.

**This is the easiest mistake for a data-driven mindset to make.** When you hear "data problem" from a customer, the reflex is to build pipelines and governance. But sometimes the real problem is just "existing data isn't connected to a natural-language entry point" — a 2-week LLM-driven solution where data-driven would take 3 months to ship the first version.

**Signal 2: discovering "LLM output is mostly right, but it can't connect to downstream systems."**

Switch back to data-driven. The fields the agent extracted can't enter ERP because the customer's coding isn't unified, semantics are ambiguous, required fields are missing. Now you need a data-governance mindset — mapping tables, validation rules, exception handling.

**This is where LLM-driven FDEs most commonly get stuck.** LLM does 80% of the work right, but the remaining 20% of "connect downstream" needs data-engineering capability, not prompt-tuning capability. If you don't switch in time, the project gets stuck at "demo is beautiful, can't be used in production."

**Signal 3: customer decisions need numbers, but existing data doesn't suffice.**

Switch back to a data-driven main line. The customer asks "how much time has the agent actually saved?" — and you find there's no instrumentation. You have to build instrumentation and ETL first, otherwise you can't even articulate the outcome (a violation of Chapter 2's first iron rule, Sell the Outcome).

The most common gap on LLM-driven projects is exactly this: **after the LLM application ships, there are no business metrics.** The system runs, but no one can articulate its business value. This is the most common slip in Handoff.

---

## 3.4  The three iron rules under each mode

Iron rules don't change. The way they land does. The table below translates each rule into the concrete actions for both modes:

| Iron rule (named in Ch. 2) | Data-driven | LLM-driven |
|---|---|---|
| **Sell the outcome** | Outcome example: monthly report on-time rate 60%→95%. The number comes from the data system itself. Communication targets: data team + BI + business | Outcome example: customer service first-response median 4h→30min. The number often requires new instrumentation / traces. Communication targets: business team + front-line operators |
| **Eval-driven** | Evaluation targets: data correctness, definition consistency, SLA. Tools: dbt tests, Great Expectations, hand-written SQL checks. Frequency: every ETL run | Evaluation targets: answer quality, relevance, safety. Tools: DeepEval, Promptfoo, platform-native evaluators (e.g., Bedrock Evaluations). Frequency: every PR + daily regression |
| **Fix forward** (fix at the customer's site) | Fix on site: a SQL snippet / a dbt model / a scheduled job. Hot-fix channel: Airflow / dbt Cloud direct ship. Permissions: limited DB write | Fix on site: a prompt / a retriever config / a tool definition. Hot-fix channel: config service / Lambda / sidecar prompt repo. Permissions: app-level config write (more common) |

One thing to notice when reading this table: **the configuration of "fix-on-site capability" differs significantly across modes.** Write permissions for data-driven work are usually heavily restricted — customer DBAs don't hand out DDL permissions casually. Application-level configuration on the LLM-driven side is usually more open — config services, prompt repos, those tend to be easier to negotiate.

That means **theoretically Fix Forward is easier to achieve for LLM-driven FDEs, and harder to negotiate for data-driven FDEs.** In practice it depends on the customer's compliance level. For finance, healthcare, government customers, even app-level configuration is tightly controlled, and the asymmetry levels out. If you're doing data-driven work for that kind of customer, the priority of getting staging write permission in week one is even higher — otherwise Fix Forward is essentially impossible to land.

---

## 3.5  Tool-stack comparison

A checklist on each side. You can use this to spot which muscle you're missing:

**Data-driven FDE muscle**

- Beginner: SQL, Python pandas, JSON / Avro, PostgreSQL
- Mid: dbt, Airflow / Prefect, Spark / PySpark, Snowflake / BigQuery / Redshift, Kerberos / IAM
- Advanced: data modeling (Kimball / Inmon), Apache Iceberg / Delta Lake, Ontology design, schema evolution, real-time pipelines (Kafka, Kinesis), data lineage, privacy compliance

**LLM-driven FDE muscle**

- Beginner: LLM API calls, prompt engineering, function calling, JSON Schema
- Mid: LangChain / LlamaIndex, RAG, vector stores (Pinecone, Weaviate, OpenSearch, pgvector), Eval frameworks, trace tooling, MCP protocol
- Advanced: agent frameworks, agent tool sandboxing and permissions, streaming and structured outputs, lightweight fine-tuning (LoRA), inference optimization (vLLM, TGI), managed-platform deployment (Bedrock, SageMaker, Vertex AI)

**An FDE doesn't need both stacks at full mastery.** But **both sides need "enough to ask the right questions."** If you're an LLM-driven FDE running into "we can't connect to ERP," you don't need to write the dbt model — you need to know that this kind of problem belongs to the data team and how to talk to them in shared vocabulary ("field mapping," "primary key constraint," "idempotency," "lineage").

The reverse holds — a data-driven FDE doesn't need to tune prompts, but should know when to say "this part is cheaper with an LLM than piling on rules engines."

### AWS tool-stack comparison across the two modes

If your project runs on AWS, the table below maps services commonly used in each mode:

| | Data-driven uses | LLM-driven uses |
|---|---|---|
| Storage | S3, Lake Formation | S3 (KB documents) |
| Data | Glue ETL, Glue Catalog | OpenSearch / Bedrock Knowledge Bases |
| Compute | EMR, Athena, Redshift | Bedrock model invocation |
| Orchestration | Step Functions, MWAA | Bedrock Agents, Step Functions |
| Governance | Lake Formation permission model | IAM + KMS |
| Monitoring | CloudWatch + data lineage | CloudWatch + Bedrock Guardrails + Bedrock Evaluations |

A project touching both Glue ETL and Bedrock Agent in the same week is normal. The data-driven track expansion in this book is mainly Chapter 9. The LLM-driven track expansion covers Chapters 6–15. Foundations needed by both (VPC, SSO, compliance) are in Chapter 11.

---

## 3.6  How to judge which side your current project should lean toward

Self-check biweekly with the table below. For each row, whichever side describes your project better is the lean. Most projects are mixed; the question is which side weighs more.

| Project trait | Lean |
|---|---|
| Customer's biggest pain is "data scattered, can't find, definitions inconsistent" | Data-driven heavier |
| Customer's biggest pain is "lots of repetition, slow retrieval, depends on individuals" | LLM-driven heavier |
| Customer has strict compliance, governance before usage | Data-driven heavier |
| Customer's business is growing fast, docs can't keep up | LLM-driven heavier |
| Customer already has a data team | You take the LLM-driven main line (data team owns the data-driven part) |
| Customer has no data team | You take the data-driven main line |
| Customer wants "results in 3 months" | LLM-driven heavier (faster v1) |
| Customer wants "infrastructure for the next 3 years" | Data-driven heavier (more solid foundation) |

When reading: **single rows don't decide; the aggregate does.** If a project is "wants 3-month results" + "strict compliance" — the first pushes LLM-driven, the second pushes data-driven — you need to find a sub-problem that satisfies both, ship that first, then expand.

---

## Closing

Part I, three chapters, gives the complete FDE engineering coordinate system:

- Chapter 1: time shape — what a day and a project look like
- Chapter 2: judgment shape — three iron rules deciding every concrete tradeoff
- Chapter 3: capability shape — when to switch between two modes

After reading these three chapters, you should be able to answer: which of the four phases is my current project in, which iron rule am I most at risk of breaking, which mode am I in. As the answers to these three change, your work focus should change with them.

Part II enters the first concrete action — Discovery. From the moment you take on a new project, what do you ask, what do you watch, what do you write in the first week? It's the most undervalued and highest-ROI phase of FDE work.

---

[← Previous: The Three Iron Rules](../chapter-02/) · [Next Part: Customer Discovery →](../../part-2/intro/)
