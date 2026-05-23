---
title: "part-7/chapter-16.md"
nav_exclude: true
search_exclude: false
---

# Chapter 16: Handoff + Pattern Extraction — Abstracting the Solution into Reusable Assets

## Opening

```
An FDE wraps up a 12-week Agent project. Technically, it's a success.

3 months later, the customer's ops team asks:
  "We want to change that prompt — how do we change it?"
She flies in. 2 hours and it's done.

6 months later, customer:
  "The Agent's error rate is creeping up — can you take a look?"
She flies in. A full day of debugging.

9 months later, customer:
  "We want to add another use case."
She flies in, opens her own old code, and realizes
  she's a little fuzzy on it too.

A teammate at the FDE's company picks up a similar project
for a new customer and comes by to ask her:
  "How did you do this again?"
Her answer: "Look at my old code...
            but every customer is different. Just redo it."

Her CEO sees the proposal for the third customer and asks:
  "Why are we quoting 12 weeks for three similar projects?
   It should be 4 weeks."

She has no answer.

This chapter covers two things:
  1. Handoff — getting the customer to truly take over
     (so you stop getting the call to fly back in)
  2. Pattern extraction — making the next similar project a 4-week job
```

---

## 16.1 The Engineering Definition of Handoff

```
        Handoff = "the customer can run this system without you"

        The bar (4 capabilities):
        ──────────────────────────────────────

  1. The customer can deploy a hot fix on their own
     (change a prompt / KB / model id)

  2. The customer can read the dashboard and find root cause on their own
     (you don't read the trace for them)

  3. The customer can run an Eval on their own
     (no longer dependent on you before a model upgrade)

  4. The customer can handle the top 5 incident types on their own
     (instead of calling you on every P1)
```

**All 4 must be met → real handoff. Miss one = the project isn't fully delivered.**

---

## 16.2 The 3-Week Handoff Countdown

Handoff doesn't start at launch — it starts three weeks before launch:

```
        T-3 weeks ── T-2 weeks ── T-1 week ── T launch ── T+4 weeks
        ─────────    ─────────    ─────────    ────────    ─────────

        Plan         Train        Shadow       Independent  FDE exits
        kickoff      + docs       ops          ops

  T-3   ✓ Identify the customer ops owner (person + email + rotation)
        ✓ Outline the Runbook
        ✓ Give the customer dashboard access

  T-2   ✓ 4-hour training (Runbook + dashboard + Eval)
        ✓ Have the customer owner perform every action hands-on once
        ✓ Q&A

  T-1   ✓ Customer owner shadows the FDE through everything
        ✓ FDE doesn't drive — only reviews the customer's actions
        ✓ End of week: customer owner writes "what I learned"

  T     Launch + canary
        ✓ Customer owner leads, FDE in the back row

  T+4   FDE fully steps away
        ✓ Still on-call, but not actively watching
        ✓ Customer reports their own ops status weekly
```

---

## 16.3 The Runbook — the Customer's Operations Manual

A Runbook is not documentation — it's an **executable instruction list**.

```
        The 7 sections every Runbook needs
        ─────────────────────────────────────

  1. System architecture diagram (one A4 page)
  2. Deploy / rollback steps (commands / screenshots)
  3. Top 10 incident types + handling SOPs
  4. How to run Eval + what the thresholds mean
  5. Where the key configs live + how to change them
  6. Data / KB update SOP
  7. Escalation path (when to call whom)
```

### A sample Runbook SOP

```
═══════════════════════════════════════════════════════════════════
  SOP-001: Sudden spike in Agent error rate
═══════════════════════════════════════════════════════════════════

  Symptom: dashboard shows error rate > 1% (baseline 0.3%)

  Step 1: Check Bedrock service status
    - Open https://health.aws.amazon.com
    - Check us-east-1 Bedrock service health
    - If AWS incident → wait + notify users

  Step 2: Check recent commits
    - GitLab → main branch, last 5 commits
    - Any prompt / KB / model changes?
    - If yes → go to Step 3 (rollback)

  Step 3: Rollback
    - Command: ./scripts/rollback.sh prod --target-version=$LAST_GOOD
    - Wait 5 minutes and watch the dashboard
    - Error rate back to baseline → done
    - Not back → go to Step 4

  Step 4: Page the FDE on-call
    - Slack: @fde-oncall
    - Phone: +XX-XXX-XXXX (24h)

  Step 5: Write the incident report
    - Template: docs/incident-template.md
    - Submit within 24 hours
═══════════════════════════════════════════════════════════════════
```

**A good Runbook lets the customer stop the bleeding on a P1 in 5 minutes.**

---

## 16.4 Training — a 4-Hour Course

```
        Handoff training: 4-hour agenda
        ─────────────────────────────────────

  Hour 1: Architecture + business flow
    ├── Where data comes from and where it goes (15 min)
    ├── The Agent's toolset and capability boundaries (15 min)
    ├── What Eval is for (15 min)
    └── Walkthrough of every monitoring panel (15 min)

  Hour 2: Daily operations
    ├── How to read the dashboard (hands-on) (20 min)
    ├── How to run an Eval (hands-on) (20 min)
    └── How to change a prompt + canary it (hands-on) (20 min)

  Hour 3: Incident handling
    ├── Top 10 incident drills (hands-on) (40 min)
    └── Rollback drill (hands-on) (20 min)

  Hour 4: Data / KB maintenance + Q&A
    ├── KB update SOP (hands-on) (30 min)
    └── Q&A (30 min)
```

**Key**: every segment must be **hands-on by the customer**, not the FDE demoing.

---

## 16.5 Pattern Extraction — Making the Next Project 5x Faster

### What "pattern extraction" means

At the end of every project, ask 4 questions:

```
  Q1: Which work in this project would be "basically the same" for another customer?
       → That's a reusable asset.

  Q2: Which work "ate huge time but could be avoided next time"?
       → That's the source of an engineering template.

  Q3: Which "customer-specific" things are actually shared by many customers?
       → That's the source of an industry template.

  Q4: Which things "I thought were easy turned out hard"?
       → That's the source of a warning card.
```

### Pattern extraction outputs — 4 asset classes

```
        The FDE's "post-project asset library"
        ───────────────────────────────────

  1. Code templates
     - LLM RAG starter kit
     - Bedrock Agent starter kit
     - Eval CI starter kit
     - Lambda MCP server starter kit

  2. Document templates
     - Discovery report template (Ch 4)
     - SOW template (Ch 5)
     - Runbook template (this chapter)
     - Acceptance criteria template

  3. Decision cards
     - "Customer asks this → answer that" cheat sheet
     - "This signal appears → switch to this approach"
     - "For this kind of problem, do these 3 things first"

  4. Anti-pattern case files
     - Real incident postmortems
     - Cost of the mistake + lesson learned
```

### Template "granularity" — lessons learned

```
  ❌ Too coarse: "Bedrock starter template"
     → Still requires major rework on day one

  ✓ About right: "Bedrock + Knowledge Bases + Aurora pgvector,
                  VPC deployment + IAM Identity Center starter template"
     → 80% of customer use cases use it as-is

  ❌ Too fine: "China Merchants Bank private-cloud RAG starter template"
     → Granularity so narrow it's only ever used once
```

---

## 16.6 The Engineering Moves of Pattern Extraction

Within 1 week of every project ending, do 5 things:

```
  1. Write a 1-page "project retrospective"
     - What we did
     - What we got right / wrong
     - Numbers (outcome / Eval / cost / time)

  2. Code review your entire project
     - Which blocks are "obviously reusable"
     - Lift them into the company internal repo

  3. Pull out 3 "decision moments"
     - At that moment, what did you judge → write it as a card

  4. Pull out 1-2 "if I redid it, I would..."
     - Write it into "project template v X+1"

  5. Run a 1-hour brown-bag with teammates
     - Not bragging about wins — talking about the pitfalls they don't know
```

---

## 16.7 Industry Templates — One Example

```
  Industry: Insurance
  Template: "Insurance RAG/Agent starter kit v3.2"

  Contents:
  ├── Industry knowledge
  │   ├── Common org structures of insurance companies
  │   ├── Three main flows: underwriting / claims / sales
  │   ├── Common regulatory requirements (CBIRC / MLPS)
  │   └── Common data stack (core + ECIF + channels + risk)
  │
  ├── General Discovery template
  │   ├── 12 insurance-specific questions
  │   └── Checklist of 5 critical deliverables
  │
  ├── Code templates
  │   ├── Policy clause chunking (PDF + tables)
  │   ├── Customer identity matching (ID card / customer no. / policy no. mapping)
  │   ├── Bedrock + Aurora pgvector + KMS deployment IaC
  │   └── MLPS-compliant audit logging spec
  │
  ├── Eval templates
  │   ├── 200 golden insurance Q&A
  │   ├── 50 safety items (PII / inappropriate promises)
  │   └── Business-expert calibration process
  │
  └── Handoff templates
      ├── Insurance ops handover SOP
      └── Regulatory inspection response template
```

**A new FDE picking up an insurance customer**: starts from v3.2, and by week 4 the customer is already seeing a demo.

---

## 16.8 Pattern Management at the Company Level

Pattern extraction is not an individual habit — the company should accumulate it in a structured way:

```
        Structure of an FDE team's "knowledge center"
        ─────────────────────────────────

  Company Wiki:
    /fde-knowledge/
      patterns/                (cross-industry)
        rag-starter/
        agent-starter/
        eval-ci-starter/
      industries/              (industry)
        insurance/
        finance/
        retail/
        manufacturing/
      anti-patterns/           (counter-examples)
        2025-Q3-incidents.md
        ...
      decision-cards/          (decision cards)
      tools/                   (internal tools)

  Code Repo:
    fde-platform/
      starter-kits/
      common-lambdas/
      shared-prompts/
      eval-suites/
```

**80% of the gap between a senior FDE and a junior one lives in the depth of this knowledge center.**

---

## Key Citations

> "*Handoff is not a milestone — it's a 4-week process you start 3 weeks before launch.*"
> — A. Lawrence, *FDE Rule Book*, 2025

> "*The second project on a customer should take 1/3 the time of the first.*"
> — Bob McGrew @ YC, 2025

> "*Pattern extraction is the difference between a consultant and an engineer.*"
> — AWS GenAI Innovation Center, 2025

---

## Action Checklist

Mandatory in the last 4 weeks of a project:

1. **Start the Handoff countdown at T-3 weeks** (Section 16.2)
2. **Write the 7 Runbook sections** (Section 16.3)
3. **Run the 4-hour customer ops training** (hands-on)
4. **Have the customer owner shadow-run ops for 1 week**
5. **Within 1 week of project end, write the retro + extract 3 decision cards**
6. **Pull out reusable code / docs / configs into the company internal repo**
7. **Run a 1-hour brown-bag with teammates** (talk pitfalls, not wins)

---

## Anti-Pattern Checklist

- ❌ **Only thinking about Handoff in launch week** (no time to train)
- ❌ **Writing the Runbook as a "feature doc"** (instead of an executable SOP)
- ❌ **Training that's all slides, no hands-on** (the customer won't remember)
- ❌ **Customer ops paging the FDE on every P1** (the 4 capabilities weren't trained in)
- ❌ **Project ends, straight to the next, no retro** (every project starts from zero)
- ❌ **Patterns live only in your own head** (teammates don't know, the company doesn't know)
- ❌ **Retros that only cover the wins** (the most valuable part is the pitfalls)

---

## Relation to the Next Chapter

By here, the full loop is closed: Discovery → Scaffolding → production → Handoff → pattern extraction.

The final chapter covers how the FDE's *own* capability grows over the long run — not chasing the latest tech, but **T-shape growth**: deepening engineering depth and industry depth in both directions.

[← Part VII Intro](intro.md) · [Next: T-Shape Growth →](chapter-17.md)
