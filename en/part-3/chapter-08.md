---
title: "Chapter 8  Eval Before Code"
parent: "Part III — Tech Stack Selection"
nav_order: 3
---

# Chapter 8  Eval Before Code

Chapter 6 picked the model, Chapter 7 picked the connector. The last D5 dimension — evaluation and observability — is this chapter.

A real-but-genericized scene first. An FDE in PoC week five does a customer demo. The business owner says: "Last week's demo was good — why is today's answer different?" The FDE flips through prompt commits: Tuesday's edit changed the system prompt. Looks at the trace: the case that worked last week is failing today. Customer: "Don't you usually test?" FDE: silence.

Next day he did the right thing: hooked the 200-sample Eval set into CI, every PR runs scoring, scores below last week block merge. From then on, never panicked again the night before a demo — score ran the night before, whatever the customer asks today, he knows the answer.

This chapter is about turning "Eval-driven" — the iron rule — into daily engineering discipline rather than a slogan in meetings.

---

## 8.1  The truth behind that 40% accuracy in Chapter 6

Back to Chapter 6 §6.3's bench — the four candidates all hit 40% on "fault type accuracy" on Hesheng's Eval set. I said it was an eval design problem, not a model problem, and saved the explanation for this chapter.

What I meant. Look at one of the 10 samples again:

```json
{"id": "T-2025-Q4-0142",
 "ticket": "X-axis servo motor overheat alarm 1042",
 "expected_team": "Electrical",
 "expected_fault_type": "Servo system"}
```

Model output: "Electrical / Servo motor." My scoring logic was exact-string match: `predicted == expected`. "Servo motor" ≠ "Servo system" — judged wrong.

But **business-wise the two are the same** — the customer's dispatch flow treats "servo system" and "servo motor" as the same category. My Eval set mistook string difference for business difference, and so all four models stayed at 40%.

This error exposes **two general problems with Eval-set design**:

First, **the evaluation metric isn't aligned with real business judgment.** I used exact string match; business-equivalent variants get judged wrong. This kind of problem will never surface in "model A vs. model B" comparisons — because all models get the same false negative. To catch it at baseline, **have a business expert look at a few eval results**, not just the score.

Second, **the Eval set leaves no room for "equivalent expressions."** If this sample had `expected_fault_type: ["Servo system", "Servo motor", "Servo"]` — any match counts — all four models jump to 100% immediately.

That's what 8.2 is about: an Eval set isn't just samples — it's **samples + scoring logic.** Both have to be designed.

---

## 8.2  Eval set = samples + scoring logic

Chapter 5 already covered the minimal Eval set structure (200 samples, three scoring functions). This chapter expands on the **design of scoring logic.**

The scoring function has to answer three questions:

**One: how is each sample considered "right"?**

What I described above. "Servo system" equals "servo motor" — the scoring function has to know. How do you define equivalence classes? Three sources:

- **Synonym dictionary**: the customer's domain synonyms (jargon, abbreviations, varied usage across departments). Each domain is different — insurance synonyms and manufacturing synonyms have nothing in common. **Business experts beat engineers** at this.
- **Rules**: certain compliance-related fields must be exact (policy number, amount), no relaxation.
- **LLM judge**: complex judgments ("does the answer capture the core of the customer's question") that can't be ruled. Use an LLM to judge what rules can't.

For Hesheng: "Servo system / Servo motor / Servo" form one class — synonym dictionary. Alarm codes must be exact — rule. "Is the customer priority reasonable" — LLM judge.

**Two: how do you compose multiple metrics into a single score?**

Chapter 5 gave an example: 0.3 × keyword + 0.3 × similarity + 0.4 × LLM judge. How are weights set?

The way to decide: **let the customer's business side vote on a few boundary cases.** Pull 5 each of "high keyword, low LLM judge" and "low keyword, high LLM judge," ask the business expert which class is closer to "business-acceptable." The customer's votes set the weights.

Don't have the FDE set weights alone — your weights will reflect engineering aesthetics, not business aesthetics. The customer's final acceptance is on business aesthetics.

**Three: how many samples per run?**

LLMs are probabilistic. Same input twice can yield different output. With one sampling, the score has ±5–10 points of noise — you see 0.85 today, 0.78 tomorrow, very possibly without any change, just different sampling.

Practical: **run 3 times per sample, average.** A simple cost trick on Bedrock: use batch inference (Flex tier, half price), run offline. If real-time feedback isn't required, this is the default.

---

## 8.3  The pyramid structure of an Eval set

200 samples aren't uniformly distributed. Layered:

```
                ┌──── Production ────┐
                │  Sampled from prod  │  Continuously growing
                └─────────┬───────────┘
                          ↑
                ┌─── Adversarial ────┐
                │  Edge / attack      │  ~30-50 samples
                └─────────┬───────────┘
                          ↑
                ┌──── Golden Set ────┐
                │  Human-labeled      │  100-300 samples
                └─────────┬───────────┘
                          ↑
                ┌────── Seed ────────┐
                │  From Discovery     │  50 samples
                └────────────────────┘
```

Each layer has a job:

**Seed** — 50, from Discovery. **Use:** rapid baseline; doesn't run the full set every time. During development, run seed every prompt change, 30 seconds for a score. If seed doesn't pass, no point running golden set.

**Golden Set** — 100–300, co-labeled by business experts. **Use:** the customer sign-off "passing score" computed at this layer. Objective contractual basis.

**Adversarial** — 30–50 edge cases. **Use:** find the model's failure modes. Includes:

- Vague phrasing ("that thing's not working")
- Long-tail fault types (very rare ones)
- Cross-intent (one ticket bundling multiple unrelated needs)
- Adversarial inputs (prompt injection, privilege escalation)
- "Should refuse" samples (PII, out-of-scope)

New FDEs most often skip this layer. But **production incidents almost all come from adversarial-class inputs.** Chapter 13 expands.

**Production (sampled from prod)** — real inputs from launch flowing back continuously. **Use:** the Eval set's "live water." Every week sample 10–20 new real cases, label, and add to golden set. Six months post-launch, this layer becomes the bulk of the Eval set.

---

## 8.4  Wire it into CI: every PR runs scoring

A built Eval set can't only run by hand. It has to be part of the dev flow.

Minimum viable CI integration:

```yaml
# .github/workflows/eval.yml
on: pull_request
jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: python scripts/bench.py --eval data/seed.jsonl --runs 3
      - run: python scripts/check_threshold.py --min 0.85
```

Which samples to run? Two-tier strategy:

- **PR triggered**: run only seed (50 samples). 30 seconds for a score. **Use:** prevent obvious regressions.
- **Daily scheduled (e.g., 2 a.m.)**: run full set (golden + adversarial). 20 minutes. **Use:** catch the detail issues PR runs can't.

How are thresholds set? Two principles:

- **Can't be worse than last week.** PRs that drop the score by 2+ points vs. last week auto-block merge. Force the developer to explain.
- **Can't drop below the sign-off threshold.** The 0.85 in the customer contract — no PR can let the score fall below this line.

The two together are the **regression gate.** It turns "evaluation" from "weekend project" into "an engineering question every PR has to answer head-on."

---

## 8.5  Running Evals on Bedrock

Bedrock provides three evaluation job types: Model Evaluation (single model), Knowledge Base Evaluation (RAG), Agent Evaluation (multi-step reasoning).

The console version is best for PoC — running a baseline in 10 minutes without code. Flow:

1. Upload jsonl Eval set to S3
2. Bedrock console → Inference and Assessment → Evaluations → Create job
3. Pick evaluation type (model / KB / agent)
4. Pick evaluator: built-in (keyword, similarity) / LLM-as-judge / human
5. Review the report — overall, dimensional scores, failed-sample CSV, trace links

The console version's limitation is that it doesn't wire into CI. After Scaffolding moves into formal development, switch to the code version — frameworks like deepeval, promptfoo, running in GitHub Actions or the customer's CI.

Specific APIs and console entries change with product iteration; check docs.aws.amazon.com.

---

## 8.6  Post-launch evaluation

In PoC, evaluation focuses on "did this code change drop the score." Post-launch, evaluation focuses on a different thing — **what's happening on the real distribution.**

Three things must happen:

**One: emit CloudWatch metrics.** Every model call records: input, output, token usage, latency, fallback flag, model ID. These are the foundation data for everything downstream.

**Two: weekly LLM-judge sampling.** Randomly sample 100 production traffic items per week, have a strong model judge response quality. Generate a "weekly production quality score." If this drops — meaning the real input distribution is shifting (customer business changed, upstream data has issues, users are asking new questions) — go do shadowing as in Chapter 4 to understand what's happening.

**Three: the alert truth isn't the production score itself, it's the trend.** If this week's 0.83 is below last week's 0.85 — noise or signal? The answer is in the standard deviation. If your historical standard deviation is 0.02, then 0.85 → 0.83 is 1 sigma — normal. If it's 0.85 → 0.78, 3.5 sigma — alert. Chapter 13 covers monitoring dashboards.

---

## 8.7  Eval-set operating cadence

The Eval set isn't "build once, done." It has its own operating cadence:

| Phase | Eval-set size | Primary action |
|---|---|---|
| Discovery end | 50 (seed) | Business expert co-labels |
| Scaffolding mid (weeks 4–5) | 150–200 (seed + golden) | Business experts batch label |
| Scaffolding end (weeks 6–7) | 200–250 (+ adversarial) | FDE leads finding edge cases |
| Production (week 8+) | Continuously growing | Weekly sampling back |
| Handoff end | Typically 300–500 | Customer can run independently |

Hesheng phase one ends with roughly 250–300 samples. That's **enough**. Bigger isn't better; coverage and the rationality of scoring logic are what matters.

The most common operating mistake is **freezing the Eval set** — never updated post-launch. Six months later, customer business has shifted, model vendor upgraded, Eval set is still on the original version. Score still looks fine (because nothing has changed in the set), but real production quality is degrading — and neither you nor the customer knows. Weekly sampling-back is the only way to prevent this.

---

## 8.8  Evaluation and acceptance

Chapter 5's acceptance criteria + this chapter's evaluation flow stitch together like this:

```
Discovery report (Ch 4)
    ↓ one-line problem + outcome number
SOW + acceptance criteria (Ch 5)
    ↓ "0.85 passing" written into contract
Eval set v0 → v1 (this Ch 8)
    ↓ scoring outputs "0.87"
Production monitoring (this Ch 8)
    ↓ weekly tracking
Handoff (Ch 16)
    ↓ customer takes over Eval
```

Every step's output is the next step's input. Break any link and the project hits trouble: Discovery without an outcome number → acceptance criteria can't be made verifiable; acceptance criteria without numbers → Eval set has no target; Eval set not in CI → pre-launch discovers regression too late; launch without monitoring → six months in customer says "this isn't working" and you don't know why.

**The evaluation system is the project's lifeline.** It turns "are we doing it right" — an abstract question — into "today 0.87, two points up from yesterday's 0.85" — a number both sides can actually discuss. Customer, business, commercial, your boss — all talking via the same set of numbers. That's why Eval-driven ranks #2 of the iron rules (only behind Sell the Outcome).

---

## Closing

Part III's three chapters are done: Chapter 6 model selection, Chapter 7 connector, Chapter 8 evaluation. With these three, the FDE project has a complete "technical skeleton" — Discovery decides what to do, the technical skeleton decides how to do it and what counts as done.

Part IV enters the rest of Scaffolding (about 70%): data engineering (how do you wire the customer's scattered data into the system), scaffolding and the dev loop (how do you build the smallest system the customer can use for over a week), VPC / SSO / compliance (the three things FDEs can't dodge in enterprise environments).

---

## Public references for this chapter

- Anthropic engineering blog — *Evaluating LLM-based Applications* series
- Bedrock docs — product specs for Model / Knowledge Base / Agent Evaluation
- DeepEval, Promptfoo and other open-source eval-framework design docs
