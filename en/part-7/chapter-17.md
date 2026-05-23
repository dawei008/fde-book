---
title: "part-7/chapter-17.md"
nav_exclude: true
search_exclude: false
---

# Chapter 17: The FDE's T-Shape Growth — Engineering Depth + Industry Depth

## Opening

```
Two FDEs at the same company, same title.

A — 3 years in, 8 customers. Each one was a new industry, new stack, new team.
  - Self-intro: "I've done every kind of LLM project."
  - Takes 4-5 weeks to ramp on a new customer.
  - Has not become anyone's "designated FDE."

B — 3 years in, 6 customers. 5 of them in financial services.
  - Self-intro: "Financial-services LLM, from underwriting to anti-fraud, 3 years deep."
  - In the first meeting, can directly discuss "how MLPS Level 3 actually lands on an LLM application."
  - 3 of his old customers renew every year + refer new customers.
  - Internally known as "the financial-services FDE elder."

When A job-hops, HR doesn't know what he's good at.
When B job-hops, three insurance companies send him offers immediately.

The two have similar engineering depth.
The difference is — B picked an industry to go deep on. A didn't.

This chapter covers: how an FDE walks the "T-shape growth" path,
so that 5 years from now you aren't merely "someone who's done a lot of projects"
but "someone irreplaceable in some domain."
```

---

## 17.1 T-Shape = Engineering Depth × Industry Depth

```
        T-shape growth structure
        ─────────────────────────────────

           Engineering breadth (LLM / data / integration / deployment)
       ┌─────────────────────────────────────┐
       │                                     │
       └────────────────┬────────────────────┘
                        │
                        │ Industry depth
                        │ (insurance / finance / manufacturing ...)
                        │
                        │
                        │
                        ▼
                   Deep domain expertise
```

```
                                T-shape vs I-shape vs dash-shape
                        ────────────────────────────────────

  Pure breadth (dash):  Knows many things, all shallow
                         → 5 years in, still a "project worker"

  Pure depth (I):       Deep in one industry, weak engineering
                         → easily replaced by AI tools

  T-shape:              Engineering breadth + industry depth
                         → 5 years in, becomes "irreplaceable"
```

---

## 17.2 Engineering Breadth — the 5 Required Foundations

Whether you sit on the LLM side or the data-driven side, an FDE needs all 5:

```
  1. Data engineering
     SQL + dbt + Spark + warehousing + schema design
     → Ch 9

  2. LLM application engineering
     Prompt + RAG + Agent + Eval + MCP
     → Ch 6/7/8/14/15

  3. Cloud engineering
     Strong proficiency in at least one of AWS / Azure / Aliyun
     IaC (Terraform / CDK / Bicep)
     → Ch 10

  4. Platform engineering
     CI/CD + monitoring + canary + rollback
     → Ch 13

  5. Soft skills
     Discovery + customer conversations + writing + presenting
     → Ch 4/5/16
```

**Missing any of the 5 → you're not an FDE; you're a "frontline PM" or a "frontline implementation engineer."**

---

## 17.3 Industry Depth — How to Pick One and How to Go Deep

### 3 criteria for picking an industry

```
  1. Customer base
     - How many customers in this industry, in your company / your country?
     - 100 → worth going deep on
     - < 20 → may not feed you

  2. Your interest + temperament
     - Finance demands rigor + compliance
     - Manufacturing demands on-site + physical
     - Retail demands speed + creativity
     - Pick one you "won't get sick of in 5 years"

  3. The industry's LLM adoption stage
     - Early (2023-2024): customers are "just trying things"
     - Now (2025-2026): customers are "serious about landing it"
     - You want one that's "now + will stay relevant for the next 5 years"
```

### The 3 levels of industry depth

```
        Level 1: You know the vocabulary
        ─────────────────────────
  Can follow customer-internal conversations.
  e.g. Insurance — knows the difference between
       underwriting / claims / sales / policy issuance.
  Time: 3-6 months

        Level 2: You understand the business flow
        ─────────────────────────
  Can sketch the customer's main business flows.
  Can anticipate their pain points and compliance constraints.
  e.g. Insurance — knows "the standard underwriting flow
       + the 5% case-by-case underwriting flow."
  Time: 1-2 years

        Level 3: You have judgment
        ─────────────────────────
  Can tell the customer "don't do this" + "why."
  Can offer "an angle they hadn't considered."
  e.g. Insurance — "Don't fully automate claims on day one;
       run human first-pass review + AI decision suggestion
       until it's stable, then expand."
  Time: 3-5 years
```

---

## 17.4 How to Deepen Industry Depth — 6 Moves

It's not "read more articles." It's deliberately doing 6 things:

```
  1. Read 2-3 industry classics every year
     - Insurance: "Principles of Insurance" / "Intro to Solvency II"
     - Finance: "Bank 4.0" / "Risk Management" textbooks

  2. Read 1 piece of "customer-internal material" every month
     - The customer's annual report / interim report
     - Reports from industry associations
     - New regulatory rulings

  3. Attend 1 industry conference every quarter
     - Not an AI conference — a conference of the industry itself
     - e.g. an insurance product innovation forum / annual meeting

  4. At the end of each project, write "industry template v X+1"
     - The pattern extraction from Ch 16
     - In a year, your "insurance RAG template" gets very mature

  5. Make friends with the customer's "business veterans"
     - Not IT — the business side
     - One sentence from a business veteran is worth 100 articles

  6. Give "non-technical" talks to customer execs
     - Speak to "the trends I'm seeing in your industry"
     - Don't talk AI — talk industry
     → Customers start treating you as "one of their own"
```

---

## 17.5 Engineering Depth vs Engineering Breadth — Go Deep on 1-2

The "vertical" in T-shape has another distinction:

```
  Engineering breadth: all 5 (Section 17.2)
  Engineering depth:   pick 1-2 of the 5 to go deep on

  Recommended directions to deepen (FDE long-term value):

  A. LLM applications + Eval + Agent (the frontier)
     → Suits: people who chase new + understand distributed systems

  B. Data governance + Ontology + data stack (the Palantir line)
     → Suits: people who like stability + understand business

  C. Cloud-native + IaC + platform engineering
     → Suits: people who like engineering aesthetics + DevOps temperament

  D. Security + compliance + audit
     → Suits: rigorous types + lots of large-enterprise customers
```

**Don't try to "go deep on all 5."** Not impossible, but unnecessary + no time. **Going deep on 1-2** is enough to form competitive advantage.

---

## 17.6 The 5-Year Growth Path

A typical 5-year path for "T-shape growth":

```
        Year 1: Onboarding
        ─────────────────────────
  - Shadow a senior FDE on 1-2 projects
  - Engineering breadth at 60% (entry-level on all 5)
  - Pick an industry (try 1-2; commit by year-end)
  - Year-1 project retros become 30 pages of docs

        Year 2: Standing on your own
        ─────────────────────────
  - Lead 2-3 projects independently (1-2 in your chosen industry)
  - Engineering breadth at 80% (mid-level on all 5)
  - Industry: Level 1 → Level 2
  - Engineering: start going deep on 1 area

        Year 3: Forming expertise
        ─────────────────────────
  - 3-4 projects independently; 70% in your chosen industry
  - Engineering breadth at 90% + 1-2 areas at depth (senior)
  - Industry: Level 2 → on the edge of Level 3
  - Internal "industry-X elder" reputation starts forming

        Year 4: Irreplaceable
        ─────────────────────────
  - Customers come to you directly (no longer assigned by the company)
  - Industry: Level 3
  - Engineering depth: 1 area at top tier + 1 at senior
  - Start mentoring new hires / writing internal best practices

        Year 5: Pick the next move
        ─────────────────────────
  Path A: Senior FDE / Principal
         → Same model, higher-end customers
  Path B: FDE team lead
         → Lead 5-10 FDEs
  Path C: Move to product / internal product lead
         → Use FDE experience to build product
  Path D: Founder
         → In your industry depth + engineering direction
```

---

## 17.7 Anti-Patterns — 5 Years and No T

```
  ❌ A new industry on every project
     → 5 years in, no industry is deep

  ❌ Engineering "tries everything new" with nothing deep
     → 5 years in, every area is shallow

  ❌ No retros, no template extraction
     → 5 years in, still a "project worker"

  ❌ No friends among business experts
     → 5 years in, still a "tools person" — never enters
       the customer's decision-making circle

  ❌ "FDE is a stepping-stone"
     → One year in and you're already eyeing PM / big tech
     → You never extract the FDE role's real value
```

---

## 17.8 Four Sentences to You, Right Now

```
  1. With every customer, ask yourself:
     "What can I take away from this project as a deposit?"
     Not the outcome (that belongs to the customer and the company),
     but the patterns / decisions / industry knowledge.

  2. Pick one industry. Stay 3 years.
     Even if you don't enjoy year 1, by year 3 you'll find
     you've become "one of the few who can speak engineering
     in that industry's language."

  3. Reserve a "study hour" every week.
     Read industry material / read papers / write retros.
     That hour is the source of your long-term FDE value.

  4. Write it down.
     Knowledge in your head isn't knowledge — only on paper is it.
     5 years from now, looking back at your 200 notes
     will tell you "who you've become" better than any résumé.
```

---

## Key Citations

> "*The best FDEs become so industry-fluent that customers think they used to work for the customer.*"
> — A. Lawrence, *FDE Rule Book*, 2025

> "*Optionality is overrated. Depth is underrated.*"
> — Bob McGrew @ YC, 2025

> "*A T-shaped engineer is the only kind that survives the next decade of AI.*"
> — Anthropic engineering culture, 2025

---

## Action Checklist

In the next 4 weeks:

1. **Draw your own T**: score yourself on each of the 5 breadth areas; have you picked an industry?
2. **Whichever breadth area you're missing → fix it this quarter** (one per quarter)
3. **No industry yet → pick one this month** (use the 3 criteria from 17.3)
4. **Build a private retro library**: write a retro within 1 week of every project ending
5. **Reserve a "study hour" every week**: industry + engineering depth
6. **Brown-bag with teammates after the next project**: share the pitfalls, not the wins
7. **3 years from now, re-read this book**: see which anti-patterns you avoided

---

## Anti-Pattern Checklist

- ❌ **A new industry on every project** (5 years, all shallow)
- ❌ **Always chasing new in engineering, never going deep on one** (high risk of being replaced by AI tools)
- ❌ **Jumping ship the moment "AI Engineer" becomes a hot role** (FDE scarcity is precisely *because* it's hard)
- ❌ **No retros** (knowledge in your head isn't knowledge)
- ❌ **No friendships with business veterans** (you'll never enter the customer's decision-making circle)
- ❌ **Treating FDE as a "stepping-stone"** (you don't extract the real value)

---

## Closing the Book

Here ends the practical handbook of FDE engineering.

```
        17 chapters in one line each
        ─────────────────────────────────────

  Part I:   The FDE is the most "PM" of engineers, and the most "engineer" of PMs.
  Part II:  Without thorough Discovery + an Eval set, writing code is faith-based.
  Part III: Selection in 30 minutes, Eval in week one, prompting first.
  Part IV:  Data + network + identity + audit = the foundations of enterprise FDE.
  Part V:   Build PoCs like production; canary + rollback + cost from week one.
  Part VI:  Less is more for Agent toolsets; MCP is the enterprise default for the next 2 years.
  Part VII: 4-week Handoff countdown; pattern extraction every project; T-shape growth ask yourself yearly.
```

The last line is for every FDE:

> **"Sell the outcome. Fix forward. Eval first. Hand it off. Extract the pattern."**

5 years from now, when you re-read this book, I hope you've already become **the irreplaceable** FDE in some industry.

[← Previous: Handoff + Pattern Extraction](chapter-16.md) · [Back to Contents](../README.md)
