---
title: "part-1/chapter-02.md"
nav_exclude: true
search_exclude: false
---

# Chapter 2: The Three Iron Rules — Sell Outcomes / Fix Forward / Eval-Driven

## Opening

```
You're in the customer's conference room. The customer's CTO is
pointing at an architecture diagram you drew on the projector.
He points at the box in the middle and asks: "Once we buy this
Agent, who's responsible for tuning it?"

Your gut reactions are:
A) "Your Ops team can tune the prompts on a regular cadence"
B) "I'll own it; monthly regression on me"
C) "Your Sales Director can take it on"

Wrong. All three are degraded versions of FDE thinking.

There's only one right answer —
"What you originally wanted wasn't an Agent. You wanted the
month-end sales report on-time rate to go from 60% to 95%.
This month we hit 92%. Next month, when we hit 95%, whoever
has that 95% directly tied to their KPI is the owner."

Pulling the conversation away from the product and back to the
outcome — that's the most important of the FDE's three iron rules.
```

---

## 2.1 Iron Rule 1: Sell the Outcome, Not the Product

### Why This One Matters Most

Bob McGrew said this in a 2025 YC interview, and it's been quoted endlessly:

> "*Stop selling the product — sell the outcome.*"

Why does this rule matter most?

Because **software / AI systems are means; the customer's business result is the end**. A customer doesn't pay because they want "an Agent" — they pay because they want to:

- Take month-end report on-time rate from 60% to 95%
- Take customer-ticket first-response time from 4 hours to 30 minutes
- Move sales conversion up by 5 points

If you're selling a "tool," the customer evaluates you with "is this tool good?" — that judgment isn't quantifiable, and it never reaches a finish line.

If you're selling a "result," the customer evaluates you with "did the number land?" — that judgment is quantifiable, has a finish line, and reaches a mutual win.

### How an Engineer Operationalizes This

Every conversation with the customer, ask yourself:

```
Q1: At the end of this conversation, did the customer change their
    "product understanding" or their "business-result expectation"?
Q2: Can I describe the outcome of this conversation with a single
    number?
Q3: Once that number lands, what's the number for the next
    conversation?
```

**The FDE's job is to keep dragging customer conversations from "feature discussion" back to "result discussion."**

### In Practice: Three Conversation Translation Templates

```
Customer: "Can the Agent also handle email?"

❌ Direct answer:  "Yes, we'll schedule it for next week"
✅ Translation:    "You're adding email so sales can reply faster on
                   open opportunities, right? Let's check the current
                   median reply time, estimate what email integration
                   would bring it down to, then put it in the backlog."

────────────────────────────────────────────────────

Customer: "What's the actual accuracy of your RAG?"

❌ Direct answer:  "0.83 on the test set, 0.78 in production"
✅ Translation:    "0.78 recall by itself doesn't mean much. The number
                   that matters: account managers used to take 4 minutes
                   to find a policy clause via search. They now take an
                   average of 28 seconds with RAG. That 28 seconds maps
                   to the '<30 seconds' KPI you originally set."

────────────────────────────────────────────────────

Customer: "We want an 'AI-powered company-wide knowledge base'"

❌ Direct answer:  "Got it, we'll draft the architecture"
✅ Translation:    "'Company-wide knowledge base' is too big a target.
                   Pick one outcome first: new-hire ramp time from 30
                   days to 15? Or customer-service resolution rate
                   from 65% to 80%? Once we pick one, we can ship a
                   first version in 6 weeks."
```

---

## 2.2 Iron Rule 2: Fix Forward

### The Principle — Fix It On Site

Lawrence hammers *Fix Forward* repeatedly in the *Rule Book*:

> "*Don't carry the problem back to HQ. Fix it at the customer site.*"

It sounds simple, but the engineering philosophy underneath is:

**FDE is not a two-stage role of "front-line pre-sales + back-office R&D." On the front line, the FDE is pre-sales, R&D, and Ops, all at once.**

If your first instinct when you hit a problem is "go back, file a Jira, get HQ to schedule it" — you've already retreated into the "implementation engineer" position.

### What Counts as Fix Forward in Practice

| Scenario | "Fix Forward in practice" bar |
|---|---|
| Eval set surfaces a new failure mode | Patch the prompt / retriever the same day; verify with Eval that afternoon |
| A customer API returns intermittently | Don't wait for customer IT scheduling; write a fallback / retry layer yourself |
| RAG recall drops | Don't wait for the "next major release"; hot-fix that night, canary at 10% |
| Customer compliance asks about a detail | Open the architecture diagram on the spot, revise it, and send the corrected version in the same email |
| Customer says "this demo doesn't sound like us" | Tune the prompt style that week and label 5 reference samples for the customer |

### A Counter-Example — From Lawrence's Book

> *An FDE was deployed at a defense customer in Europe. He found that 5% of the data samples were unusual (unicode + legacy encoding). He filed a ticket back to HQ and waited 3 weeks. R&D came back with "the general solution requires a refactor." By week 4 the customer lost patience and the project stalled.*
>
> *The next FDE who took over wrote a 30-line transformer that handled the 5% on the first day. The data flowed clean by day two. Three months later the customer renewed for $2M.*

**Fix Forward is not "skip the ticket"; it's "ticket and hot-fix in parallel."**

### The Engineer's Fix Forward Setup

To Fix Forward at all, the FDE needs some **on-site fix capabilities** in place:

- Deploy permission in the customer environment (at minimum, staging)
- Direct push to your repo's main branch (gated by CI)
- At least one release channel that can hot-fix to production (Lambda / sidecar container / config service)
- A simple "patch script directory" (python scripts / one-liner shells)

If any of the above is missing, **50% of your FDE work is already incapable of Fix Forward**.

---

## 2.3 Iron Rule 3: Eval-Driven

### The Principle — Without Eval, an LLM/Agent Project Is a "Faith Project"

The biggest difference between LLM systems and traditional software: **same input, output not guaranteed; a prompt that worked today may break after the model upgrades**.

No Eval set = both you and the customer judge by feel = one day the customer feels it's bad, and you have no idea why.

### The Engineering Definition of Eval-Driven

Not "run a quick eval after the code is done." It's:

```
1. Define the outcome number first (Iron Rule 1)
2. Translate the outcome into an automatable Eval set
   (input → expected output → pass condition)
3. Every PR while writing code runs Eval
4. Before launch, Eval must hit the customer-signed-off bar
5. In production, sample new cases continuously and add them to
   Eval (regression set)
```

**The Eval set is built in week 1 of FDE work, not patched in before launch.**

### A Minimal Eval Example

Suppose the customer is building "policy-clause Q&A RAG." The Eval set looks like this:

```python
# evals/insurance_qa_v0.1.jsonl
{"input":"How long is the typical waiting period for critical illness insurance?","expected_keywords":["90","180","waiting period"],"min_score":0.8}
{"input":"My physical last year found a thyroid nodule — can I still apply?","expected_keywords":["underwriting","disclosure","nodule"],"min_score":0.7}
{"input":"Within the cooling-off period, how much do I get back if I cancel?","expected_keywords":["full refund","cooling-off"],"min_score":0.9}
# ... 50-200 entries
```

Two layers of scoring:
- **Keyword recall** (machine, automatic) — does it run at all
- **Domain expert scoring** (sampled, manual) — is it actually any good

Updated weekly, run forever.

### Eval Engineering Practice on AWS

If you're building an LLM application on AWS Bedrock, Bedrock has built-in evaluation capabilities you can use directly:

- **Amazon Bedrock Evaluations** — run evaluations directly in the Bedrock console / API against models / RAG / Agents, supporting LLM-as-judge, human evaluation, and programmatic evaluators.
- **Knowledge Base Evaluations** — an evaluation flow purpose-built for "retrieval quality" and "generation quality" of RAG systems.
- **Agent Evaluations** — evaluation for agents' multi-step reasoning paths, with custom scoring dimensions.

Practical recommendations:
- **PoC phase**: use Bedrock's built-in LLM-as-judge to get a baseline running in 10 minutes
- **Pre-production**: write code-level Eval (pytest / DeepEval / Promptfoo) and run it in CI
- **In production**: collect real samples in CloudWatch → periodically sample them back into the Eval set

> **AWS reference**: search "Amazon Bedrock evaluation" or "Knowledge Bases evaluation" in AWS docs. Bedrock Evaluations live in console → "Evaluations"; the latest specifics evolve with the product, so use docs.aws.amazon.com as the source of truth.

### Why FDEs Must Insist on Eval-Driven

```
Project without Eval:           Project with Eval:
─────────────────               ─────────────────
"feels okay today"              0.83 today, +0.02 vs yesterday
Customer judges subjectively,   Customer reads scores weekly,
drifts week to week              fully explainable
You can't dare to upgrade       Model upgrade? Run Eval overnight,
the model when the vendor        decide in the morning
ships a new version
PoC pass = "demo luck"          PoC pass = numbers
Post-Handoff, no one knows      Post-Handoff, the customer runs Eval
if it's any good                themselves to monitor
```

---

## 2.4 How the Three Rules Relate

The three rules aren't parallel. They're **a single judgment loop**:

```
       ┌──────────────────┐
       │ Sell the outcome │  ← decides "what to do"
       └────────┬─────────┘
                ↓
       ┌──────────────────┐
       │   Eval-driven    │  ← decides "did it land"
       └────────┬─────────┘
                ↓
       ┌──────────────────┐
       │   Fix Forward    │  ← decides "fix on site"
       └──────────────────┘
                ↓
            outcome lands
                ↓
            (next outcome)
```

If you can only remember one, remember **Sell the outcome**.
If two, add **Eval-driven**.
If three, add **Fix Forward**.

---

## 2.5 How to Sell These Three Rules to the Team / Your Manager

In real work, you'll need to "sell" these three to:

- Your own company's product / sales (they'll try to push "sell the product" onto you)
- The customer's project manager (they'll try to push "ship features" onto you)
- The customer's CTO (they'll try to push "AI strategy" onto you)

Sample script:

> *"The first thing I'll do on this project is pin down a number — for example, the median time for an account manager to find a clause goes from 4:30 to 30 seconds. Then I'll build an 80-entry Eval set and score it weekly. No PR gets into main without passing Eval. Three months from now, what you'll see at delivery isn't an 'AI system' — it's the number 'median time went from 4:30 to 27 seconds.'"*

Most customers will agree after that pitch. If they don't, the problem is bigger — the customer doesn't know what outcome they want, and you should be doing Discovery first (Ch 4).

---

## Key Citations

> "*Stop selling the product — sell the outcome.*"
> — Bob McGrew @ YC, 2025

> "*Don't carry the problem back to HQ. Fix it at the customer site.*"
> — A. Lawrence, *FDE Rule Book*, 2025

> "*If you don't have an eval set, you don't have a system — you have a hope.*"
> — Anonymous FDE, *The FDE Playbook*, 2025

---

## Action Checklist

Apply the three rules to your current project:

1. **Write down the outcome number for your current project**: one sentence + one number + one time window
2. **Judge whether your current PR directly serves that number**; if not, kill it next week
3. **Build Eval set v0.1**: even just 20 entries (one morning's work — don't wait for "perfect samples")
4. **Turn on CI** so Eval runs on every PR
5. **Audit your Fix Forward setup**: do you have staging deploy permission? a hot-fix channel?
6. **In Monday's meeting**, use the §2.5 script to align the customer and your team

---

## Anti-Pattern Checklist

- ❌ **Believing "good demo" equals "good project"** (a demo is a proxy for the outcome, not the outcome itself)
- ❌ **Patching Eval in only before launch** (Eval is a development constraint, not an acceptance document)
- ❌ **First reaction to a problem is "I'll go file with R&D"** (you ARE R&D)
- ❌ **Accepting "let's see how it works first, then talk numbers"** (that "see how it works" day never arrives)
- ❌ **Treating Eval as QA's job** (Eval is one of the FDE's core deliverables)
- ❌ **Selling three outcomes at once** (one at a time, finish, then the next)

---

## Relation to the Next Chapter

The iron rules are the ruler for "did I get it right." The next chapter covers two FDE modes — when "data-driven" and "LLM-driven" switch inside the same project, and how each rule is applied differently.

[← Previous](chapter-01.md) · [Next: Two FDE Modes →](chapter-03.md)
