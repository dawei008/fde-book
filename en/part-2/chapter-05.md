---
title: "Chapter 5  From Requirements to SOW and Eval Set"
parent: "Part II — Customer Discovery"
nav_order: 2
---

# Chapter 5  From Requirements to SOW and Eval Set

Two weeks of Discovery in the books. You have three things in hand: a 3-page Discovery report, a one-sentence real problem plus an outcome number, 50 customer-ticket seed samples.

Your boss asks: "Great. Can we start writing code next week?"

No. There are three more things to lock down — otherwise next week's coding is faith-based:

- **Eval set v0** — translates the outcome into an auto-runnable exam paper.
- **Acceptance criteria** — a unified definition of "passing" between you and the customer.
- **SOW** — locks the 12-week scope to prevent scope creep.

This chapter is about turning Discovery's three things into these three "engineering contract artifacts." It's the last mile of Discovery, and the entry ticket to Scaffolding.

---

## 5.1  How the three artifacts relate

They're three languages for the same thing:

- **Eval set:** the language an engineer can run (input, expected output, pass condition)
- **Acceptance criteria:** the language a customer can sign (numbers, time, boundaries)
- **SOW:** the language Legal can stamp (scope, responsibilities, payment, exit)

```
            Discovery report
                  ↓
        ┌─────────┼─────────┐
        ↓         ↓         ↓
       Eval     Accept     SOW
      (tech)   criteria  (commercial)
                (business)
        │         │         │
        └────────┬─────────┘
            three aligned
                  ↓
            start writing code
```

Why three? Because they each have different readers. Engineers don't read SOWs, Legal doesn't understand Eval sets, the customer's business side neither understands nor signs technical documents. Three documents for three audiences — but **the three must agree.** What the Eval set tests has to be what acceptance criteria put a number on; the boundary in acceptance criteria has to be what's listed in SOW scope.

**Disagreement among the three = misaligned definition of "success" = late-project tug-of-war is guaranteed.** Section 5.5 gives a 3-way cross-check list to ensure agreement.

---

## 5.2  Eval set v0: the engineer's exam paper

### Why build an Eval set

Chapter 2's iron rule 2 already covered why. Here's the expansion: the Eval set has **four roles across the project lifecycle**:

- **During development:** every PR runs scoring automatically — prevents the regression of "fixed A, broke B."
- **Before launch:** the "passing score" for customer sign-off, written into the contract.
- **After launch:** early warning for model upgrades and upstream data drift. If the score drops 5 points one day, an alert fires.
- **After Handoff:** the customer can run the Eval set themselves and monitor the system without depending on you.

Chapter 2 covered the cold start from 0 to 30. This chapter covers the expansion from 30 to 200, the structure, and how to score.

### A minimal Eval set's shape

Directory layout:

```
evals/
├── README.md                  # how to run, how to read results
├── seed_samples.jsonl         # 50 seeds (from Discovery)
├── golden_set.jsonl           # 100 with standard answers (human labeled)
├── adversarial.jsonl          # 30 edge / attack / anomalous inputs
├── metrics.py                 # scoring functions
├── runner.py                  # batch entry point
└── reports/                   # historical score snapshots
```

The fields a sample should carry, using insurance-clause Q&A as the example:

```json
{
  "id": "eval-007",
  "category": "critical-illness-waiting-period",
  "input": {
    "user_question": "I just bought critical illness insurance. Two weeks later, my checkup found a thyroid nodule. Can I claim?",
    "context_hint": "Insured policy number: P-2024-XXX-001"
  },
  "expected": {
    "must_contain_keywords": ["waiting period", "90 days", "180 days", "diagnosis date"],
    "must_not_contain": ["definitely won't pay", "definitely will pay"],
    "min_relevance_score": 0.8,
    "reference_answer": "Critical illness insurance typically has a 90-180 day waiting period. The insurer may decline claims for diagnoses within the waiting period. Specifics depend on your policy."
  },
  "metadata": {
    "source": "customer service ticket #2024-1042",
    "annotator": "Li (business expert)",
    "difficulty": "medium",
    "weight": 1.0
  }
}
```

Things to notice in this schema:

- **It's not just input/output.** Each item carries category, source, difficulty, weight. These fields matter when you want to see "where the system is dropping the ball."
- **It's not just a "standard answer."** Three layers of constraints: required keywords (correctness), forbidden phrases (avoiding wrong claims), reference answer (for semantic similarity).
- **It's not a single score.** Multiple metrics composed — a single score hides problems.

### Three scoring approaches

Each sample eventually produces a score. Three approaches, each with use cases:

**Rule-based scoring** — cheapest and most stable. Keyword hits, blacklist misses, JSON Schema validation. Suitable for "must / must not" hard constraints (policy number must appear, "definitely will pay" is absolutely forbidden). Not suitable for natural language fluency or style judgments.

**Semantic similarity** — medium cost. Embed the answer and the reference answer, compute cosine. Suitable for relevance checks on open-ended Q&A. Not suitable for precise numbers ("30 days" and "31 days" have high semantic similarity but aren't business-equivalent) or list completeness.

**LLM-as-judge** — most expensive, most flexible. Use a strong model (GPT-4 / Claude) to judge whether the answer is correct. Suitable for style, complex judgments, multi-dimensional scoring. **Warning**: the judge can't be in the same family as the model under test — that's "same-source bias," and a model systematically rates outputs in its own style higher (some public studies show 5–15 percentage points of bias). If you're testing Claude, judge with GPT-4 or Llama; if testing GPT-4, judge with Claude.

Practical advice: **use all three layers, composite by weight.** A common ratio is 30% rule + 30% similarity + 40% LLM-judge. Tune weights for your project, and **ideally have the customer's business side watch you tune them** — they have a say in "which form of correctness matters more." That's the form of business judgment Eval ultimately has to reflect.

### Running Evals on AWS

If the project runs on Bedrock, the platform offers Evaluations natively, saving some of the wheel-rebuilding. Three job types:

- **Model Evaluation:** evaluate a single foundation model's output (no RAG / Agent). Use for model selection — e.g., comparing Claude vs. Llama vs. Titan.
- **Knowledge Base Evaluation:** evaluate RAG retrieval and generation quality. Auto-computes Context Relevance and Answer Faithfulness — the two core RAG metrics.
- **Agent Evaluation:** evaluate an agent's multi-step reasoning trajectory. Key metrics include step count, tool-call accuracy, final-output correctness.

Minimal viable flow: upload your jsonl dataset to S3 → in the console, create an Evaluation Job (pick type, evaluator, metrics) → review the report (overall score, dimension scores, failed-sample CSV, trace links) → integrate with CI (Bedrock Eval API runs on PR trigger; below-threshold blocks merge).

Specific APIs and console entries change with product iteration; check docs.aws.amazon.com.

### Common Eval-set mistakes

The pitfalls beginners most often step on:

- **Using training data as Eval data** — model has memorized the answers, score is inflated. Scaffolding shows 0.95 weekly; production drops to 0.6 immediately on launch.
- **All high-frequency, typical questions** — no edge cases, production gets blown up by edge inputs. Reserve 20–30% of slots for adversarial samples.
- **Only "should-succeed" samples, no "should-refuse" samples** — model freely answers PII, out-of-scope, sensitive questions. This category has to be explicitly included.
- **One sample, one score** — when something fails, you can't tell whether retrieval or generation went wrong.
- **Eval set only runs once before customer demo** — loses the meaning of "development constraint." It has to run in CI, locally, daily regression.

---

## 5.3  Acceptance criteria: the customer's signature line

Acceptance criteria is a document the customer's business side and your commercial side sign jointly. The core requirement is **verifiability** — any potential dispute should be resolvable by some sentence in this document.

### A counterexample and a positive example

**Counterexample** — what most contracts look like:

> The system should accurately answer customer policy inquiries with industry-leading accuracy.

This sentence isn't verifiable. What does "accurate" mean? What does "leading" mean? Who judges? The end of the project becomes a fight.

**Positive example** — verifiable version:

```
Acceptance criteria v1.0
─────────────────────────────────────────────────

Environment: customer staging (production-equivalent data, anonymized)
Eval set: v0.1, 200 samples (co-labeled with customer business expert)

Pass conditions (all must hold):
  1. Overall accuracy ≥ 85%
     (composite of keyword recall + semantic relevance + LLM-judge)
  2. Top 20 high-frequency questions accuracy ≥ 95%
  3. Safety: refuse PII / out-of-scope questions 100%
  4. Performance: P95 response time ≤ 3s
     (P95 = 95% of requests faster than this)
  5. 7 consecutive days with no human intervention,
     auto-scoring stable

Below-threshold handling:
  - Single criterion below → fix and re-run
  - Overall below → bilateral negotiation: extend OR cut scope

Verification milestones:
  - Day 60: mid-checkpoint (70% achievement)
  - Day 84: formal acceptance

Acceptance owners:
  - Customer side: [Business Director] + [IT Director]
  - Our side:      [FDE] + [Tech Lead]
```

Reading this acceptance criteria: **all 5 elements present** — numbers (a set of thresholds), time (eval window plus acceptance date), set (which Eval set to compute on), environment (which environment to run in), below-threshold handling (who has authority to extend, who has authority to cut scope). Missing any of these turns into a dispute at project end.

### Checklist of the 5 required elements

| Element | Meaning | Consequence of omission |
|---|---|---|
| **Number** | One or more concrete thresholds | Customer can later say "I don't think it passed" |
| **Time** | Eval window, stability duration, acceptance date | Customer can extend acceptance indefinitely |
| **Set** | Which dataset to compute on (Eval set v0.X, version-stamped) | Both sides argue over "which samples count" |
| **Environment** | Which environment to run in (dev / staging / prod shadow traffic — shadow traffic = production requests duplicated to the system but results not returned to users, only used for evaluation) | Customer scores it lower in production, fight |
| **Below-threshold handling** | Who has authority to extend, who has authority to cut scope | When threshold isn't hit, no one can decide; project stalls |

### Who decides the numbers

The customer's business side proposes expectations, the FDE proposes the evaluation method, the commercial side mediates. **No one party can decide alone:**

- Customer alone → numbers will be too high ("industry leading"), project undeliverable
- FDE alone → numbers will be conservative ("what we can do"), customer won't accept
- Commercial alone → numbers come from a contract template, no business meaning

The most common fight is over the number itself — customer wants 95%, you say 80% is realistic. Two ways to handle this:

1. **Run baseline on the Eval set in front of the customer.** Run the simplest baseline once on Eval set v0 (an unoptimized LLM answering directly), produce a number, then say "this is the floor; our engineering target is to push from this number up by X." The customer recalibrates expectations after seeing the floor.
2. **Tiered acceptance.** Day 60 mid-checkpoint at 70%, Day 84 formal acceptance at 85%. Customers accept tiers far more easily than a single high target.

---

## 5.4  SOW: the commercial artifact

The SOW (Statement of Work) is where outcome, acceptance criteria, time, and money become a legal document.

**The FDE must personally draft 4 sections:** Scope, Deliverables, Acceptance Criteria, Change Management — these 4 are all about "how the project content is defined, how it's accepted, who has authority to change it." The FDE writes them because only the FDE knows what's engineeringly possible.

**Sections the FDE should review but doesn't need to draft:** payment milestones (commercial), IP ownership (legal), confidentiality / NDA (legal), liability (legal), termination (legal and commercial). The customer will use their template, so you don't have to write from scratch — but review carefully, especially "payment milestones aligned with deliverable dates." Don't let payment land a week before or two weeks after a deliverable.

The 4 sections you must draft:

### The 4 sections an FDE must draft

**Section 1: Scope (what we do / what we don't)**

```
Scope (in):
  - Insurance clause RAG Q&A (within v0.1 Eval set's 200-sample coverage)
  - Account manager web client (OpenAPI v1)
  - CloudWatch monitoring integration
  - One Handoff training session (4 hours)

Scope (out):
  - Mobile integration (customer does it themselves)
  - Multi-language support (Chinese only)
  - Pre-sales scripts (out of scope)
  - Historical data migration (customer prepares data)
```

**Scope (out) matters more than Scope (in).** It's the most valuable thing you give the customer in the SOW — a boundary. The customer might instinctively ask "why list so many things you won't do?" — you can explain: "Listing what we won't do is so we focus all our energy on doing what we will."

**Section 2: Deliverables**

```
D1: Discovery report             (Week 2)
D2: Eval set v0.1                (Week 3)
D3: Demo + evaluation report     (Week 6)
D4: Production deploy + monitoring dashboard (Week 10)
D5: Runbook + Eval v1.0 + training (Week 12)
```

Each deliverable must carry **recipient + delivery method + acceptance standard.** D3, for example, isn't just a demo link — it's "demonstrated to the customer's business director on customer staging, passing score ≥ 70%, accompanied by an evaluation report PDF."

**Section 3: Acceptance Criteria** — directly reuses 5.3's content.

**Section 4: Change Management**

```
Change triggers:
  - Customer proposes new requirement → goes through change process
  - Customer business direction shifts → goes through change process

Change process:
  Step 1: Customer submits written change request
  Step 2: FDE assesses impact on scope / time / budget within 5 business days
  Step 3: Both sides decide:
        Option A: Accept change → revise SOW + adjust timeline + adjust budget
        Option B: Defer to Phase 2
        Option C: Decline

Verbal requirements outside this process → not added to backlog
```

**No change process = customer adds new requirements weekly = project never ends.**

### A real counterexample

12-week project, the SOW said "AI assistant to help sales improve efficiency." Week 4 the customer added "and help purchasing too." FDE didn't push back. Week 8, purchasing said "this isn't what we wanted," requiring a redo. Week 12, undeliverable; project delayed.

Postmortem: the original SOW had no Scope (out), no change process. "Sales" and "purchasing" are two workflows that shouldn't have been mixed.

**This is FDE projects' #1 failure mode: scope wasn't locked down.** Spend two extra hours in week one writing Scope (out) and a change process. Don't let the project fail.

---

## 5.5  Cross-checking the three artifacts

After Eval set + acceptance criteria + SOW are written, do a **3-way cross-check:**

| # | Cross-check question | If it fails | What real failure looks like |
|---|---|---|---|
| 1 | Does every metric in the Eval set have a corresponding numeric threshold in acceptance criteria? | Add it to acceptance criteria | At project end customer finds your LLM-judge hit 0.92, but they wanted keyword recall 0.95 |
| 2 | Can the "passing score" in acceptance criteria actually be computed from the Eval set? | Refine the metric definition | Acceptance says "high naturalness," but the Eval set has no metric measuring it |
| 3 | Does every Deliverable in the SOW have a corresponding acceptance condition? | Add it | D3 demo delivered, customer says "this isn't what we wanted," but the SOW didn't specify how to verify the demo |
| 4 | Do items in Scope (out) actually not appear in the Eval set? | Remove them from the Eval set | SOW says "no multi-language," but the Eval set has 5 English samples included in scoring |
| 5 | Does the change clause in the SOW cover Eval set updates? | Add "Eval set updates monthly" | Week 8 added 50 new samples, score dropped, customer disputes — argues "the standard changed" |

These 5 cross-checks look tedious, but each maps to a real failure mode. Spending one day on this in week three prevents week eleven's collapse.

---

## 5.6  An end-to-end example

Stitching Chapter 4's Discovery report and this chapter's three artifacts together — what the project foundation looks like:

```
─── Discovery output ─────────────────────────────────────

Real problem:
  Account managers' median time to find an insurance clause
  is 4:30, occurring 12,000 times/month.

Expected outcome:
  Cut median time to within 30s in 3 months.

Seed samples:
  Customer service ticket export of 1,000 → business expert
  filters 50 representative ones.

─── Eval set v0.1 ────────────────────────────────────────

Dataset:    seed_samples (50) + golden_set (150) = 200 samples
metrics:    keyword_recall (rule)
            semantic_similarity (cosine, 0.7+)
            llm_judge_accuracy (Bedrock Claude)
Scoring:    0.3 × keyword + 0.3 × similarity + 0.4 × judge
Pass score: 0.85

─── Acceptance criteria ───────────────────────────────────

Environment: customer staging (anonymized data)
Pass conditions:
  1. Eval set total score ≥ 0.85
  2. Top 20 high-frequency questions ≥ 0.95
  3. P95 latency ≤ 3s
  4. Median time from 4:30 to ≤ 30s (real sample stats)
  5. 7 days stable without human intervention
Acceptance date: Day 84

─── Key SOW sections ─────────────────────────────────────

Scope (in):     Insurance-clause RAG (Chinese)
                Web OpenAPI
                CloudWatch monitoring
                4-hour Handoff training

Scope (out):    Mobile / multi-language / sales scripts / data migration

Deliverables:   D1 Discovery report (W2)
                D2 Eval set v0.1 (W3)
                D3 Demo (W6)
                D4 Production deploy (W10)
                D5 Runbook + Eval v1.0 + training (W12)

Change process: Written → FDE 5-day assessment → revise SOW

Total budget:   ¥XX
Down/mid/final: 30% / 40% / 30%
```

**This contract bundle plus the Discovery report is your blueprint for the next 12 weeks.** Every "should I do this, did this pass, should we change scope" judgment that comes up during Scaffolding has its answer somewhere in this bundle.

---

## 5.7  Pitfalls in weeks two and three

Putting this chapter together with the last, the most common pitfalls across the entire Discovery phase (typically 1–3 weeks):

**Saving the Eval set for pre-launch.** Violates iron rule 2. The entire Scaffolding phase has no ground truth.

**Acceptance criteria that say "industry-leading."** Unverifiable means unpassable. Late-project fight guaranteed.

**SOW without Scope (out).** Top source of scope creep.

**SOW without change process.** Customer adds requirements weekly, never finished.

**Eval set = training set.** Data leakage, inflated scores, production collapse.

**Three artifacts not aligned, kicked off anyway.** Internal misalignment on "success." Week 10, fight guaranteed.

**Eval set labeled by FDE only.** No business expert calibration. Model right, customer doesn't accept.

---

## Closing

By the end of this section, Discovery has fully closed: you have **a real problem + outcome number + 50 seeds + 200-sample Eval set + acceptance criteria + SOW.** With this bundle signed, the project moves from "thinking through what to do" to "doing it" — Scaffolding.

Part III begins Scaffolding. The first question: what tech stack? Facing a real customer project, how do you decide which model, which orchestration framework, whether to bring in an agent platform? Chapter 6 walks through a complete industrial-manufacturing case — the selection meeting, cross-model benchmarking, decision flow, all using real data.

---

## Public references for this chapter

- A. Lawrence, *Forward Deployed Engineer Rule Book* (2025) — argument for locked scope and change processes
- Conikeec, *The Forward Deployed Engineer Playbook: A Practitioner's Field Manual (Early Draft)* (Substack) — source of "if you can't write the Eval set, you don't really understand the problem yet"

---

[← Previous: Week One on the Customer's Site](../chapter-04/) · [Next Part: Tech Stack Selection →](../../part-3/intro/)
