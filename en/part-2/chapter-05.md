# Chapter 5: From Requirements to Acceptance — Eval Set / Acceptance Criteria / SOW

## Opening

```
Two weeks into Discovery, the FDE has three things in hand:

  1. A 3-page Discovery report (template from Ch 4)
  2. A one-line real problem + a single outcome number
  3. 50 seed samples drawn from customer tickets

Her manager asks: "Great — can we start writing code next week?"

She replies: "Three more artifacts first —
        Eval set v0.1 (the outcome translated into an exam
                       you can run automatically)
        Acceptance criteria (a shared definition of 'passing'
                             that we and the customer both sign)
        SOW (the 12-week boundary nailed down in writing,
             so scope can't creep)

        Without those three, writing code next week is a leap of faith."

Her manager pauses three seconds and says:
"Then put in some overtime this week and finish the three of them."

She says: "These three aren't a week of overtime —
          they're the entirety of my next 5 working days."

This chapter shows how to translate Discovery into
       Eval set + acceptance criteria + SOW —
       the three contractual artifacts of an engineering project.
```

---

## 5.1 How the Three Artifacts Relate

```
            Discovery Report
                  ↓
        ┌─────────┼─────────┐
        ↓         ↓         ↓
      Eval Set  Acceptance   SOW
      (eng.)    Criteria     (commercial)
                (business)
        │         │         │
        └────────▼─────────┘
            All three aligned
                  ↓
              Start coding
```

The three are **the same thing in three languages**:

- **Eval set**: the language engineers can run (input / expected output / pass criteria).
- **Acceptance criteria**: the language the customer can sign (numbers + dates + boundaries).
- **SOW**: the language legal can stamp (scope / responsibilities / payment / exit).

**If the three disagree, the project's internal definition of "success" disagrees — and someone is going to get torn apart at the end.**

---

## 5.2 Eval Set v0.1 — The Engineer's Exam

### Why You Need an Eval Set

Back to Iron Law 3: an LLM project without Evals is a faith-based project.

What the eval set does for you:

1. **During development**: every PR runs the eval automatically — your regression net.
2. **Pre-launch**: the "passing score" the customer signs off on.
3. **Post-launch**: an early-warning signal for model upgrades and data drift.
4. **After handoff**: the customer can run it themselves without depending on you.

### The Minimum Structure of Eval Set v0.1

```
evals/
├── README.md                  # how to run, how to read results
├── seed_samples.jsonl         # 50 seed samples (from Discovery)
├── golden_set.jsonl           # 100 samples with reference answers
├── adversarial.jsonl          # 30 edge / attack / anomaly inputs
├── metrics.py                 # scoring functions (keywords, similarity, LLM-as-judge)
├── runner.py                  # batch entry point
└── reports/                   # historical run snapshots
```

### What a Single Eval Sample Looks Like

Take a **policy-clause Q&A** project as an example:

```json
{
  "id": "eval-007",
  "category": "critical-illness / waiting-period",
  "input": {
    "user_question": "I just bought a critical illness policy. Two weeks later a physical found a thyroid nodule — am I covered?",
    "context_hint": "Policyholder ID: P-2024-XXX-001"
  },
  "expected": {
    "must_contain_keywords": ["waiting period", "90 days", "180 days", "diagnosis date"],
    "must_not_contain": ["not covered", "definitely covered"],
    "min_relevance_score": 0.8,
    "reference_answer": "Critical-illness policies generally have a 90–180 day waiting period; conditions diagnosed during that window can be excluded by the insurer. Refer to your specific policy for the exact term —"
  },
  "metadata": {
    "source": "support ticket #2024-1042",
    "annotator": "Li (domain expert)",
    "difficulty": "medium",
    "weight": 1.0
  }
}
```

**Key design points**:

- Not just input/output — every sample carries category, source, difficulty, and weight.
- Not just a "reference answer" — three layers: required keywords + forbidden phrases + reference text.
- Not a single number — multiple metrics composed together (keyword recall / semantic relevance / safety).

### Three Ways to Score

```
┌──────────────────────────────────────────────────────────┐
│ 1. Rule-based scoring (cheapest, most stable)            │
│    - Keyword hits / blocklist misses / JSON Schema check │
│    - Good for: hard "must / must-not" constraints        │
│    - Bad for: natural-language fluency, style            │
├──────────────────────────────────────────────────────────┤
│ 2. Semantic similarity (medium cost)                     │
│    - cosine(embedding(answer), embedding(reference))     │
│    - Good for: open-ended Q&A relevance                  │
│    - Bad for: precise numbers, list completeness         │
├──────────────────────────────────────────────────────────┤
│ 3. LLM-as-judge (most expensive, most flexible)          │
│    - GPT-4 / Claude / Bedrock judges the answer          │
│    - Good for: style, complex judgment, multi-axis score │
│    - Bad for: judging the same model that produced       │
│      the answer (same-source bias)                       │
└──────────────────────────────────────────────────────────┘
```

**Practical rule**: use all three with different weights. Rules 30% + similarity 30% + LLM-as-judge 40%.

### AWS in Practice: Running Evals with Bedrock Evaluations

If your application runs on AWS (Bedrock + Knowledge Bases + Agents), you can build eval jobs directly in **Amazon Bedrock Evaluations** — through the console or the API:

```
        Bedrock Evaluations — three job types
        ─────────────────────────────────────────────

  1. Model Evaluation
     Evaluate a single foundation model's output
     (no RAG / Agent attached)
     → For model selection (Claude vs Llama vs Titan)

  2. Knowledge Base Evaluation
     Evaluate a RAG system's "retrieval + generation quality"
     → Computes Context Relevance / Answer Faithfulness automatically

  3. Agent Evaluation
     Evaluate the correctness of an Agent's multi-step trajectory
     → Key metrics: step count, tool-call accuracy, final output
```

Minimum runnable Bedrock eval flow:

```
Step 1: Upload the JSONL dataset to S3
        s3://my-bucket/evals/insurance-qa-v01.jsonl

Step 2: Create an Evaluation Job in the Bedrock console
        - Pick the evaluation type (Model / KB / Agent)
        - Pick the evaluator (Built-in / LLM-as-judge / Human)
        - Pick metrics (Accuracy / Robustness / Toxicity / custom)

Step 3: Read the report when the job finishes
        - Overall score + per-dimension scores
        - List of failed samples (CSV download)
        - Trace links (useful for Agent / KB)

Step 4: Wire the report into CI
        - Trigger the Bedrock Eval API on every PR
        - Below threshold → block merge
```

> **AWS reference**: search "Amazon Bedrock evaluation jobs" and "Knowledge Base evaluation" on docs.aws.amazon.com. Console path: Bedrock console → Inference and Assessment → Evaluations.

### Anti-Examples: Common Eval-Set Mistakes

```
❌ Using training data as the eval set
   → the model has memorized the answers; scores are inflated

❌ Only "the questions customers love to ask"
   → no edge cases; production gets blown up by edge cases

❌ Only "success cases" — no "should-refuse" samples
   → the model casually answers PII / out-of-scope questions

❌ One score per sample
   → can't tell whether retrieval or generation is broken

❌ Running the eval set once, the day before customer demo
   → loses its meaning as a "development constraint"
```

---

## 5.3 Acceptance Criteria — The Customer's Signature Line

### Acceptance Criteria = "Numbers + Dates + Boundaries"

No vagueness allowed. Written so legal can use it, the customer can sign it, and engineering can verify it.

### A Bad Example and a Good One

❌ **Vague version** (90% of contracts read this way):

```
"The system shall accurately answer customer policy questions,
 with accuracy at industry-leading levels."
```

→ Unverifiable: what's "accurate"? What's "leading"? Who decides?

✅ **Verifiable version**:

```
Acceptance Criteria v1.0
────────────────────────────────────────────────────────

Environment: customer staging (production-equivalent data, anonymized)
Eval set: v0.1, 200 samples (jointly annotated with customer SMEs)

Pass conditions (all must hold):
  1. Overall accuracy ≥ 85% (composite of keyword recall +
     semantic relevance + LLM-as-judge)
  2. High-frequency questions (top 20) accuracy ≥ 95%
  3. Safety: refuses 100% of PII / out-of-scope queries
  4. Performance: P95 latency ≤ 3 seconds
  5. 7 consecutive days with no human intervention,
     stable automated scoring

Handling of misses:
  - Single-metric miss → fix and rerun
  - Overall miss → both sides negotiate: extend OR cut scope

Acceptance milestones:
  - Day 60: midpoint check (70% is enough)
  - Day 84: formal acceptance

Acceptance owners:
  - Customer side: [VP of Business] + [VP of IT]
  - Our side: [FDE name] + [Tech Lead name]
```

**The 5 required elements of acceptance criteria**:

| Element | Meaning |
|---|---|
| Numbers | One or more concrete thresholds (accuracy ≥ X%, P95 latency ≤ Y ms) |
| Time | Evaluation window, stability duration, acceptance date |
| Set | Which dataset the score is computed on (eval set v0.X) |
| Environment | Where it runs (dev / staging / prod shadow traffic) |
| Miss handling | Who can extend, who can cut scope |

---

## 5.4 SOW — The Commercial Artifact

A SOW (Statement of Work) is the legal document that turns outcome / acceptance criteria / time / money into a contract.

**The FDE doesn't need to write the whole thing**, but **must own these four sections** — without them, scope creep will drag the project to its grave:

### The 4 Sections the FDE Must Draft

#### 1. Scope (in / out)

```
Scope (in):
  - Policy-clause RAG Q&A (within the v0.1 eval-set scope, 200 samples)
  - Account manager Web client (OpenAPI v1)
  - CloudWatch monitoring integration
  - One handoff training session (4 hours)

Scope (out):
  - Mobile integration (customer's responsibility)
  - Multilingual support (Chinese only)
  - Pre-sale sales scripts (out of scope)
  - Historical data migration (customer prepares the data)
```

**Scope (out) matters more than Scope (in).**

#### 2. Deliverables

```
D1: Discovery report (Week 2)
D2: Eval set v0.1 (Week 3)
D3: Demo + evaluation report (Week 6)
D4: Production deployment + monitoring dashboard (Week 10)
D5: Runbook + Eval v1.0 + 4-hour training (Week 12)
```

Every deliverable needs a **recipient + delivery method + acceptance criteria**.

#### 3. Acceptance Criteria — reuse 5.3 directly.

#### 4. Change Management

```
Triggers:
  - Customer raises a new requirement → change-control flow
  - Customer's business direction shifts → change-control flow

Flow:
  Step 1: Customer files a written change request
  Step 2: FDE assesses impact on scope / time / budget
  Step 3: Both sides decide within 5 working days
        Option A: Accept → revise SOW + adjust schedule + adjust budget
        Option B: Defer to Phase 2
        Option C: Don't do it

Verbal requests outside this flow → not in the backlog.
```

**No change-control flow = the customer brings new requirements every week = the project never ends.**

### A Real Counter-Example

> *An FDE took on a 12-week project. The SOW said "AI assistant to help sales improve efficiency." Week 4, the customer added "and let procurement use it too" — the FDE didn't push back. Week 8, procurement said "this isn't what we wanted" and demanded a rework. Week 12 arrived; nothing was deliverable.*
>
> *Postmortem: the original SOW had no Scope (out) and no change-control flow. "Sales" and "procurement" are two different workflows that should never have been mixed in the first place.*

**This is FDE failure mode #1**: scope wasn't nailed down.

---

## 5.5 How the Three Cross-Check Each Other

After the eval set + acceptance criteria + SOW are drafted, run **three-way cross-checks**:

```
        ┌────────────────────────────────────────┐
        │  Question                              │
        ├────────────────────────────────────────┤
        │  1. Is every metric in the eval set    │
        │     reflected in the acceptance        │
        │     criteria?                          │
        │     —— if not, add it                  │
        │                                        │
        │  2. Can the "passing score" in the     │
        │     acceptance criteria actually be    │
        │     computed from the eval set?        │
        │     —— if not, fix the metric          │
        │                                        │
        │  3. Does every Deliverable in the SOW  │
        │     have acceptance criteria attached? │
        │     —— if not, add them                │
        │                                        │
        │  4. Does the SOW's Scope (out) really  │
        │     not appear in the eval set?        │
        │     —— if it does, remove it           │
        │                                        │
        │  5. Does the SOW's change clause cover │
        │     eval-set updates?                  │
        │     —— if not, add it                  │
        └────────────────────────────────────────┘
```

Run these five checks and the foundation of the project is finally stable.

---

## 5.6 An End-to-End Mini Example

Stitching the Chapter 4 Discovery report together with this chapter's three contractual artifacts:

```
─── Discovery output ─────────────────────────────────────

Real problem:
  Median time for an account manager to find a policy clause
  is 4m 30s; this happens 12,000 times a month.

Target outcome:
  Cut median time to under 30s within 3 months.

Seed samples:
  Export 1,000 support tickets → SME picks 50 representative ones.

─── Eval set v0.1 ────────────────────────────────────────

Dataset: seed_samples (50) + golden_set (150) = 200
Metrics:
  - keyword_recall (rule)
  - semantic_similarity (cosine, 0.7+)
  - llm_judge_accuracy (Bedrock Claude)
Score formula: 0.3 * keyword + 0.3 * sim + 0.4 * judge
Pass: 0.85

─── Acceptance criteria ──────────────────────────────────

Environment: customer staging (anonymized data)
Pass conditions:
  1. Eval overall ≥ 0.85
  2. Top 20 frequent questions ≥ 0.95
  3. P95 latency ≤ 3s
  4. Median time drops from 4:30 to ≤ 30s (real-sample stat)
  5. 7 days stable, no human intervention
Acceptance day: day 84

─── SOW key sections ─────────────────────────────────────

Scope (in):
  - Policy-clause RAG (Chinese)
  - Web OpenAPI
  - CloudWatch monitoring
  - 4-hour handoff training

Scope (out):
  - Mobile / multilingual / sales scripts / data migration

Deliverables:
  D1 Discovery report (W2)
  D2 Eval v0.1 (W3)
  D3 Demo (W6)
  D4 Production deployment (W10)
  D5 Runbook + Eval v1.0 + training (W12)

Change control:
  Written request → FDE 5-working-day assessment → revise SOW

Total budget: ¥XX
Down / mid / final payment: 30 / 40 / 30
```

**This package of contractual artifacts + Discovery report = your blueprint for the next 12 weeks.**

---

## Key Citations

> "*If you can't write the eval set, you don't understand the problem yet.*"
> — Conikeec, *The FDE Playbook*, 2025

> "*Scope creep is not a customer problem; it's a contract problem.*"
> — A. Lawrence, *FDE Rule Book*, 2025

> "*Acceptance criteria is the only piece of the contract the engineer must own.*"
> — AWS GenAI Innovation Center, internal training, 2025

---

## Action Checklist

After Discovery, the 7 things to do in week 3:

1. **Grow the seed from 50 to 200 samples** (jointly annotated with SMEs).
2. **Write `metrics.py`** (at least three scorers: keyword / similarity / LLM-as-judge).
3. **Write `runner.py` and run a baseline** (an unoptimized version sets the floor).
4. **Draft acceptance criteria v1.0** (the 5 required elements).
5. **Draft the 4 SOW sections** (Scope / Deliverables / Acceptance / Change).
6. **Run the 5 cross-checks** (Section 5.5).
7. **Three-way sign-off**: customer business + customer IT + your commercial side, in one room.

---

## Anti-Pattern Checklist

- ❌ **Eval set deferred until launch** (violates Eval-driven Iron Law).
- ❌ **Acceptance criteria written in unmeasurable phrases like "industry-leading"** (unverifiable = unpassable).
- ❌ **No Scope (out) in the SOW** (top source of scope creep).
- ❌ **No change-control flow** (new requirements every week, project never ends).
- ❌ **Eval set = training set** (data leakage; inflated scores).
- ❌ **Starting work before the three artifacts agree** (mismatched definitions of "success" → tearing later).
- ❌ **Eval set annotated only by the FDE** (no SME calibration → model right but customer disagrees).

---

## Connection to the Next Part

Discovery is now fully closed: you have the **real problem + outcome number + 50 seeds + 200-sample eval set + acceptance criteria + SOW**.

The next Part enters the **Scaffolding stage**. From week 3, the FDE spends 6 weeks building a minimum closed loop **the customer can demo, score, and feel the shape of**. Chapter 6 starts with the overall LLM application stack — **what model, what framework, what deployment shape, and why**.

[← Previous: Discovery](chapter-04.md) · [Next Part: Scaffolding →](../part-3/intro.md)
