# Chapter 1: The FDE Workflow — A Real Week, A Real Quarter

## Opening

```
Tuesday, Shanghai, conference room at a fintech customer.

09:00  Customer Ops @-mentions you in Slack — "RAG recall dropped from
       0.82 to 0.61 overnight"
09:15  Open LangFuse traces, scroll through the last 200 failed requests
       from yesterday. 78 of them are about "policies issued in the last
       3 days" — the customer added a batch of new insurance products
       last week and didn't sync them into the KB
09:40  Drop a two-line re-ingest SOP into the channel
10:00  Standup with the customer's business PM: 4 new intents to add,
       boss wants a demo next week
10:30  Pair with customer engineering on an OAuth error (you didn't
       write it, but you know the system best)
11:00  30-minute call with a remote staff engineer at your company —
       should we split retrieval into a separate retriever-ensemble
       service? Park it for now
12:00  Lunch in the customer cafeteria. Someone in Operations across
       the table grumbles "that dashboard from last time is slow" —
       you note it down. May not matter for this project, but it's
       a signal
13:30  Write the 4 prompt variants you'll demo this afternoon, run them
       against the Eval set first — you do not freestyle in front of
       the customer
15:00  Demo. The customer's business owner throws out 2 new scenarios
       on the spot. You don't engage head-on —
       "Let me run them through Eval and come back tomorrow with a
       pass/fail call"
17:00  Author Eval cases: 4 new scenarios × 5 edge samples = 20 entries
17:30  Ship last night's ingest fix to a 10% canary
18:00  Daily report: today's progress / 3 things for tomorrow / 1 risk
```

That's a day of FDE.

Less than 25% of it is writing code, but every single thing you did was an engineering action.

---

## 1.1 The Weekly Rhythm — The FDE's "Clocks"

Abstract an FDE week into three "clocks":

```
            ┌─────────────────────────────────────────────┐
            │ Customer Cadence                            │
            │ - Monday standup / Friday demo / monthly    │
            │   review                                    │
            │ - Driven by the customer's calendar; FDE    │
            │   cannot miss it                            │
            ├─────────────────────────────────────────────┤
            │ Engineering Cadence                         │
            │ - PR cadence, Eval cadence, release cadence │
            │ - Driven by you and your team               │
            ├─────────────────────────────────────────────┤
            │ Learning Cadence                            │
            │ - Read customer business docs, browse their │
            │   wiki, eat lunch with Ops                  │
            │ - Only you can protect this one             │
            └─────────────────────────────────────────────┘
```

**The classic rookie FDE mistake is letting the entire week be eaten by the Customer Cadence** — every day spent chasing customer requests, no fixed Engineering Cadence, and certainly no Learning Cadence.

Three weeks in, you'll notice: delivery quality slowly degrades because you put zero time into Eval, and the customer starts going around you to your manager because you're no longer offering anything insightful.

---

### Recommended Weekly Template (5-day version)

```
        Mon         Tue         Wed         Thu         Fri
        ─────       ─────       ─────       ─────       ─────
07:00                                                     ← Reserve learning time
09:00   Customer    Deep work   Customer    Deep work   Weekly demo
        standup     (no-mtg)    standup     (no-mtg)    + weekly
        + plan                  + Eval                   report
                                review

Lunch   With        Remote sync With        Read         With customer
        customer    with your   customer    customer     decision-makers
        Ops         own team    business    wiki
                                PM

PM      Discovery   Engineering Customer    Engineering  Customer demo
        interview   deep work   eng         deep work    + feedback
                                handoff                  digest

17:00   Daily       Daily       Daily       Daily        Weekly report
        report      report      report      report       + next week's
                                                         plan
```

The non-negotiable piece is the **Tuesday / Thursday "Deep Work Days (no-meeting days)"**. Lose them and all you have left is "senior PM + pre-sales" — you're no longer a Forward Deployed *Engineer*.

---

## 1.2 The Quarterly Rhythm — The FDE's "Four Quadrants"

A quarter is roughly 12 weeks. A typical FDE project unfolds across "four quadrants":

```
        Week 1-3          Week 4-7          Week 8-10        Week 11-12
        ─────────         ─────────         ─────────        ─────────
        DISCOVERY         SCAFFOLDING       PROD-IZATION     HANDOFF

        ─────────         ─────────         ─────────        ─────────

Goal    Pin down the      Get a minimal    Stable launch +   Customer
        "real problem"    closed loop      rollback plan     takes over
        and "real         + Eval baseline                    + pattern
        budget"                                              extraction

Output  Discovery        Demoable build +  Production        Runbook +
        report +         Eval set v0.1     deploy +          Eval v1.0 +
        SOW draft                          monitoring        Handoff doc
                                           dashboards

Iron    Sell outcome     Eval-driven       Fix Forward       All three
rule
focus

Risk    Drifting         Missing Eval      Production        No one
        requirements                       incident          maintains
        + drifting                                           after Handoff
        expectations
```

Remember one thing: **the boundaries between these four phases are blurry**. Discovery never "ends," Eval is never "enough." But each phase has a single **primary task**, and 70% of your time should be on it.

---

### Reading the Phase You're In

When you take over a project, first figure out which phase it's in:

```
  Q1: Has the customer's "definition of success" been pinned to a number?
        ↓
  No  ──→ You're in DISCOVERY. Do Discovery first; do not write code.
  Yes ↓
  Q2: Do you have an Eval set, and can you score the current version?
        ↓
  No  ──→ You're in SCAFFOLDING. Build Eval first, then build the demo.
  Yes ↓
  Q3: Has someone in the customer's "real production environment" used
       it for at least a week?
        ↓
  No  ──→ You're in PROD-IZATION. Focus on stability + monitoring.
  Yes ↓
  Q4: Is there someone inside the customer who can run it independently
       of you?
        ↓
  No  ──→ You're in HANDOFF. Write Runbook + train.
  Yes ──→ Project done. Do pattern extraction (Ch 16).
```

90% of FDE failure stories trace back to **misreading which phase you're in**. The most common mistake: thinking you're in Scaffolding when you're still in Discovery, then shipping a pile of features no one asked for.

---

## 1.3 Workflow Differences Across the Two Tracks

The same week looks very different for an **LLM application FDE** versus a **field-delivery FDE**:

| Time slot | LLM Application FDE | Field-Delivery FDE (Palantir / AWS GenAIIC style) |
|---|---|---|
| Mon AM | Pull LangFuse / LangSmith traces, analyze failure samples | Check customer pipeline alerts, confirm ETL is healthy |
| Mon PM | Discovery: align with business PM on intents and data shape | Discovery: align with data team on schema and data ownership |
| Tue full day | Tune prompts / upgrade RAG / swap models | Write ETL jobs / model Ontology entities / tune SQL |
| Wed AM | Run Eval, ship a new build | Run data-validation batches, deploy pipelines |
| Wed PM | Customer eng integration: API, rate limits, caching | Customer eng integration: DB connections, Kerberos, network allowlists |
| Thu full day | Deep work: refine eval set, ablate prompt variables | Deep work: optimize jobs / refactor data model |
| Fri | Demo: scenario dialogues + metrics | Demo: dashboards + data correctness |

**On the FDE job, both tracks are the same mindset and different muscles**. Inside the same company on the same project, you'll switch tracks across phases — that's exactly what Ch 3 unpacks.

---

## 1.4 Where Should the Time Go — Three Diagnostics

### Diagnostic 1: ≥ 8 hours per week on "non-coding engineering"

That includes: Discovery interviews, labeling Eval, reading customer business docs, writing Runbooks, reading traces.

**Below 8 hours and the FDE tends to turn the project into "remote outsourcing."**

### Diagnostic 2: ≥ 1 unsolicited customer face-time every two weeks

Not a meeting you organized — one you walked into yourself. For example:
- Lunch in the customer cafeteria
- Friday afternoon, sit at their workstation and watch them use the product
- A 30-minute 1:1 with a customer Ops or frontline employee

**Less than once every two weeks and the FDE drifts into "increasingly abstract information,"** building things further and further from the customer's real work.

### Diagnostic 3: At least once a month, "push back" against the customer

Not arguing for sport — **rejecting a request or a proposal with evidence and numbers**.

Examples:
- The customer wants "company-wide multi-Agent collaboration"; you push back and propose starting with a single Agent + tool augmentation
- The customer wants to self-host Llama 70B; you cost out the inference and recommend starting on a hosted API

**Less than once a month and the FDE has usually already degraded into a "senior implementation engineer"** — judgment is no longer in play.

---

## 1.5 A Real Counter-Example

An anonymous FDE shared a failure story on Substack (2025):

> *Week 3 of the project, the customer said "we want an agent that can write emails, query CRM, edit calendars — all wired up." I didn't ask follow-ups. I went back and built a 6-week project with 3 tool integrations and orchestration logic. Demoed in week 8. Customer said "looks good" and ghosted us.*
>
> *Later I found out their CRM was 80% empty fields, and the CEO said that line because he'd just sat through someone else's demo. What was actually urgent was their sales team migrating data into ERP at month-end — a one-morning automation. I built a 6-week demo, and they couldn't buy it.*

**Diagnosis**:
- Jumped into Scaffolding while still in Discovery (wrong phase)
- No Eval, so "agent writes emails" had no quantifiable bar (broke Eval-driven)
- Didn't sell the outcome (data into ERP); sold the product (multi-tool agent)

Every later chapter in this book is, in some sense, helping you avoid this counter-example.

---

## Key Citations

> "*The most expensive line of code is the one nobody asked you to write.*"
> — Conikeec, *The FDE Playbook*, 2025

> "*Forward deployment is not a job; it's a posture toward the customer's workflow.*"
> — A. Lawrence, *FDE Rule Book* (paraphrased), 2025

> "*The best FDEs don't sell the agent; they sell the after-state of the workflow.*"
> — Bob McGrew @ YC, 2025

---

## Action Checklist

When you take on a new FDE project, do the following 7 things in week 1:

1. **Get access to the customer's existing wiki / Confluence** — not a "to-do," it must be in place by the end of week 1
2. **Start a personal "project journal" file** (Obsidian / Notion private space recommended); spend 5 minutes a day capturing 3 observations
3. **Draw your "Customer Cadence"**: which days of the week the customer has which standing meetings, and align your calendar to them
4. **Force two "Deep Work Days"** (Tuesday and Thursday recommended) — refuse all non-urgent meetings
5. **Before your first Discovery meeting**, prepare a 12-question checklist (see Ch 4)
6. **Find 1-2 frontline employees on the customer's "non-decision tier,"** and book a 30-minute coffee (this is Lawrence's *Immersion Before Judgment*)
7. **By the end of the first weekend, write a memo titled "I assumed the customer wants X, but it might actually be Y"** (a guard against the §1.5 counter-example)

---

## Anti-Pattern Checklist

- ❌ **Letting the entire week go to the Customer Cadence** (you become a "senior PM")
- ❌ **No "Deep Work Days"** (interrupted constantly, never get any engineering depth)
- ❌ **Skipping Discovery and writing demos directly** (the most expensive code is code no one asked for)
- ❌ **Not writing daily / weekly reports** (six months later you can't remember what you did, and pattern extraction is impossible)
- ❌ **Never "pushing back" on the customer** (the customer asks, you build — a few weeks from FDE degrading into implementation engineer)
- ❌ **Not knowing which phase you're in** (use the §1.2 decision tree to self-check)

---

## Relation to the Next Chapter

This chapter mapped out the FDE's "shape of time." The next chapter maps the "shape of judgment" — the three iron rules that decide whether you're doing the job right. After both chapters, you'll have a complete coordinate system for FDE engineering.

[← Back to Contents](../README.md) · [Next: Three Iron Rules →](chapter-02.md)
