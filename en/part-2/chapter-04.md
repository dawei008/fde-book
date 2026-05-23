---
title: "Chapter 4  Week One on the Customer's Site"
parent: "Part II — Customer Discovery"
nav_order: 1
---

# Chapter 4  Week One on the Customer's Site

Here's a real story about an FDE's first time on a customer's site, simplified.

He prepared thoroughly. 30 questions written down. Read the customer's website and annual report. Brought a "customer scenario evaluation questionnaire." The meeting ran from 9 a.m. to 4 p.m., the customer rotated five people through it to answer everything. He went back to the hotel that night to write up notes — and the more he wrote, the emptier they felt. Thirty questions had been "answered," but he didn't have a single concrete requirement he could write code against. Worse, he couldn't tell which answers were real and which were just polite "standard" replies.

The next day he did something different. He went and sat in the customer's call center for half a day, watched 30 calls land on agents — what systems they opened, what they searched, what they jotted down.

The notes he came back with that night were ten times more valuable than the previous day's seven hours of meetings.

That's the observation this chapter is built on: **in Discovery, looking matters more than asking.**

Coming back to this book's core formula *Outcome = Harness × Customer*: Chapters 1–3 mostly unpacked Harness (the FDE role and its working style). This chapter and the next unpack Customer (figuring out the customer's real problems, constraints, and decision chain). The two sides come back together for welding in Chapter 6.

---

## 4.1  Why "look" beats "ask"

When customers answer your questions, they tend to answer **the workflow they think they have**, not **the workflow they actually run.**

Behavioral economics has a term for this: *stated preference vs. revealed preference* — what people say they prefer often diverges from what their actions reveal. In FDE Discovery work, the gap is even wider:

- The customer's leadership tells you "we use the CRM to track deals." You sit next to a sales rep for a day and see them spend 70% of their time in Excel.
- Customer Compliance tells you "all data is in SAP." You query around and find 30% of critical data lives in some shared drive Excel file.
- The customer's PM tells you "customer service is standardized." You listen to three real calls and find every agent runs their own variant.

Why does this happen? Not because customers lie. Because what they say is the **ought** — how the system is supposed to be used in theory. What you see with your eyes is the **is** — how the system actually gets used. An FDE project must be built on the **is**. Build on the **ought** and three weeks later the customer will say "this doesn't match our workflow" — you got it wrong.

Two methods to expose the **is**: have them do the work while you watch, and have them show you the real artifacts. That's what 4.2 and 4.3 are about.

---

## 4.2  Three ways to "look"

### Shadowing: tail one person at work for half a day

Beginner FDEs most often get stuck at this step — "how do I even ask the customer to let me sit with a front-line operator?" A one-line opener:

> "I'd like to understand how Mr. Zhang handles tickets day to day. Could I shadow him for half a day? I'll stay quiet, won't interrupt, and I'll write up an observation note for you afterward."

This usually doesn't get rejected. Three reasons: the customer doesn't feel you're there to "evaluate" the operator, you're there to "learn" the workflow; half a day is a low time cost for the customer; you're promising a return (the observation note, which the customer's leadership often wants to see anyway).

If the customer refuses — usually because "too busy" or "data sensitivity." For the former, schedule it 1–2 weeks out. For the latter, that data range has compliance constraints, and you need to flag it under Data Access in 4.5.

You shadow one front-line operator for 4 hours. Be the silent observer — don't interrupt, don't comment, don't coach. Just watch.

Bring a notebook with two columns: what they do, and where they get stuck. A real shadowing-note fragment looks like this:

```
Time   What they do                        Where they're stuck
────   ────────                            ────────────────────
0:00   Open 5 tabs:                        CRM takes 8s to load
       Outlook + CRM + Excel
       + shared drive + internal wiki

0:08   Search customer "ABC Corp"          CRM returns 3 dupes,
                                           don't know which is right

0:12   Switch to Outlook to find           Manually digging,
       most recent emails                  4 minutes lost

0:18   Back to CRM to type a note          Plain text only,
                                           date format inconsistent
```

The four hours of "looking" and eight hours of "meeting" produce different things. Neither replaces the other. **In meetings you're listening to consensus; in shadowing you're seeing the is.** The detail you see in shadowing can't surface in a meeting — the tab-switching frequency, the duplicated typing, the small mental notes — even the customer themselves doesn't notice these in a meeting setting. But the reverse holds too: shadowing won't show you decision-makers' intent, won't show you inter-departmental politics, won't reveal "the lines that can't be crossed." Only meetings (and meals) give you those. **Both have to happen in week one of Discovery.** Not either-or.

The hardest thing on a first shadowing isn't the watching, it's **resisting the urge to interrupt.** An LLM engineer watching a front-line operator dig through email for four minutes immediately wants to say "this can be automated." Don't. Let them finish — how they dig, what they look at, what fields they fill in. Interrupting puts the customer in "demo mode" — performing for you, not actually working.

### System Walkthrough: have the customer give you a tour of their systems

Have the customer log into the few systems they use most, and narrate as they click: "why are you searching here first, then there?"

You're not looking at system features. You're looking at **the actual interaction patterns between people and systems.** What to record:

- How many systems they have to open on average per task
- Which paths are hot (used daily), which are cold (rarely)
- Which hot paths have pain points: paste, switch, wait, manual computation
- What's the "glue" between systems — usually humans copying data manually

System walkthroughs are better than shadowing for understanding **why** the workflow looks the way it does. You can ask "why this first, then that?" and the customer will tell you the historical reason — maybe a legacy system can't surface a particular field, maybe a department's KPI dictated the order. Those historical reasons will determine whether your proposed solution can land.

### Artifact Mining: have the customer show you the real outputs

Ask the customer for 5 categories of real outputs:

1. Last week's sales weekly report a manager submitted to their boss (real structure, real metric definitions)
2. A real customer ticket resolution log from last month (real flow, real handoff points)
3. A meeting note from the last internal weekly sync (the customer's real internal vocabulary)
4. A contract attachment where the customer rejected a competitor (real reasons for rejection)
5. The KPI report from the last quarter (real metrics, what the business actually cares about)

**Real artifacts beat any PowerPoint introduction.** The customer's actual internal vocabulary, real metric definitions, real workflow nodes — they're all in the artifacts. When you use the words from those artifacts in conversation with the business side, they think "this FDE gets us." If you only use words from the customer's website or whitepaper, they think "this is sales."

Artifact mining has a hidden value: **it lets you see the actual shape of the problems that aren't yet solved.** For example, in customer ticket resolution logs, there's often a column called "engineer notes" that frequently says things like "Old Li helped take a look." That tells you there's an "Old Li step" in the ticket flow that doesn't exist in any system. If your solution doesn't account for that step, it'll hit the wall after launch.

---

## 4.3  12 questions you have to ask in week one

Observation is the main course, but you'll still have meetings. Don't ask 30 vague questions. Ask the 12 below. Each one is designed — not to "learn about the customer," but to **expose what the customer hasn't thought through.**

**Four questions about business state:**

1. **If we do nothing, what will this problem look like in 3 months?** "About the same" — no real pain, be cautious about taking the project. "Worse" — have them quantify how much worse.
2. **How often does this flow happen per month? How long per occurrence?** Can't answer with numbers — there's no instrumentation, and your week one task is to add it.
3. **Has anyone tried to solve this before? Why didn't it work?** Nobody's tried — maybe the problem isn't important, be cautious. Tried and failed — listen to the failure mode and avoid it.
4. **If this got solved today, how would you know?** This question forces the outcome number. Vague answer — they're still in Discovery, don't write code yet.

**Four questions about technical state:**

5. **Where does the data come from? Who owns it?** Data without an owner is essentially unusable — once schema changes, no one can approve.
6. **When was the last system change? Who approved it?** Reveals the customer's real decision chain. If they say "our IT lead approves," you know to pull that lead in early.
7. **How long does a production deploy take on average? What approvals are needed?** This determines whether your Fix Forward configuration is feasible. If production deploys take a two-week process, then your demo and test environments must be "FDE has authority" environments.
8. **If the model gives a wrong answer, what's the worst that happens?** Determines the strength of error tolerance, safety constraints, and guardrails. "Customer loses millions" and "customer sees one extra typo" are completely different solutions.

**Four questions about organizational state:**

9. **Whose KPI is directly tied to this project's success?** Nobody — the project is likely to go cold because no one has a stake in pushing it.
10. **Who's the opposition? Why?** No opposition — likely no one really understands this, decision-makers are guessing.
11. **Who'll take over operations? When do they get involved?** Nobody — Handoff risk has already surfaced. Flag it red in the Discovery report.
12. **If PoC succeeds, what does it look like in 3 months?** Can't answer — no real plan for productionization, even a successful PoC won't get bought into.

You don't need to ask these 12 in one session. Spread them over Discovery's 1–2 weeks. The point isn't "answered fast" — it's that **if the customer can't answer, the blank itself is the signal.**

---

## 4.4  The Discovery report

The first round of Discovery (typically 1–2 weeks) should output a Discovery report no longer than 3 pages. The report is **written for your own management and the customer's decision-makers to read together** — it's the project's first alignment artifact.

Template:

```
Discovery report — [customer name] / [project name]
Date: YYYY-MM-DD     Author: FDE [name]

1. Real problem (one sentence)
   "Account managers' median time to find a specific
    insurance clause is 4:30, happening ~12,000 times/month,
    with the biggest pain being inaccurate results."

2. Expected outcome (one number + one time window)
   "Reduce median time to within 30 seconds in 3 months,
    measured by: customer service system instrumentation."

3. Five observation pieces of evidence on current pain
   - shadowing: account managers switch 4 systems per clause lookup
   - artifact mining: 280 cases last month bounced for wrong clause
   - ...

4. Key constraints
   - Data: what's accessible / what isn't
   - Deployment: VPC / private / public cloud
   - Compliance: MLPS / SOC2 / GDPR / PII
   - Cost: budget cap / monthly token budget

5. Risks and uncertainties (top 3)
   - Risk 1: description + mitigation
   - Risk 2:
   - Risk 3:

6. Recommended approach (3-week scaffold)
   - Mode: data-driven / LLM-driven / hybrid
   - Key tech stack: model / framework / deployment mode
   - Eval set v0: N samples covering K scenarios
   - First milestone: hit Y number in X weeks

7. What we won't do (Out of Scope)
   - Excluded ask 1 + reason
   - Excluded ask 2

8. Next steps
   - Customer: 3 things the customer needs to do
   - Us: what the FDE team will do over the next 2 weeks
```

In this template, **section 5 (Risks) and section 7 (What we won't do) are the two most valuable sections.** Beginners most often skip them because they're "negative" — risks make the project look unprepared, "what we won't do" makes the FDE team look unenthusiastic.

But negative information is exactly where the report's value lives. Customer decision-makers usually hear "we can do it, we will do it, we definitely will do it" all day — when you hand them a report with concrete risks and clear boundaries, their trust in you climbs sharply. **This is the inflection point that separates FDE from a vendor implementation team.**

---

## 4.5  Data access: what week one must unblock

Discovery has to clarify the **legitimate path for data access.** If you skip this, downstream pipelines can't be built. If you do it wrong, Compliance shows up in week three.

For a beginner FDE, the most common reality in week one is not the clean "customer IT provisions an account, configures permissions" path. It's a degraded version:

- Customer DBA runs a SQL and pings you the 1,000-row result over chat
- Customer PM hands you an Excel and says "have a look first"
- Customer Ops gives you SSH to a bastion to read logs, but doesn't define scope

These degraded versions get you **emergency-started**, but none of them is a long-term plan. They share the same problem: no audit log, data scope uncontrolled, the "permissions" given to the FDE aren't traceable in the customer's system. Three weeks later, when Compliance asks "what data has the FDE seen," neither side can answer.

The ideal path is to push for a proper channel from week one. If the project runs on AWS, the typical flow:

```
Customer raw data                   FDE working environment
─────────────────                   ────────────────────────
                                    (FDE in customer's AWS account
1. S3 (production bucket)            or a shared sandbox account)
       ↓                                   ↓
2. Lake Formation                  4. Request fine-grained perms
   (register data + define perms)   (LF tags, column-level)
       ↓                                   ↓
3. Glue Data Catalog              5. Athena exploratory queries
   (unified metadata)                       ↓
                                  6. Assess data shape
                                    (fields, null rates, distribution)
                                          ↓
                                  7. Add "data access manifest"
                                    to the Discovery report
```

Operational keys for this flow:

**Don't use root credentials to query data.** Have the customer use IAM Identity Center / Lake Formation to give you specific LF-tag permissions. If you query as root, week one looks fine, but in week three when Compliance asks, you can't articulate "which fields you've seen and which you haven't" — that's the worst state to be in for a compliance audit.

**Run all data exploration through Athena. Don't download bulk data locally.** Athena queries leave audit logs — who queried what, how many rows, when — all in CloudTrail. Local downloads turn your laptop into a temporary host for PII data. Compliance risk is high.

**Record ownership for every data source.** Who is the data owner, who approves schema evolution, who has the authority to decide "this field can be exposed to the LLM." This list is an appendix to the Discovery report, but in practice it's the prerequisite for every downstream piece of data engineering.

Specific IAM Identity Center / Lake Formation configuration changes with product iteration; check docs.aws.amazon.com before usage.

**Transition strategy for the degraded path.** If proper permissions on the customer side require a 1–2 week process, you can accept the degraded path in week one (chat-shared screenshots, Excel samples), but do two things: (1) explicitly note "data range accessed via degraded path" in an appendix to the Discovery report; (2) switch to an audit-able channel by end of week two. If the customer drags into week four without proper permissions, that's a project-level red flag — it means internal support for the project isn't strong enough, and the situation should be escalated.

---

## 4.6  A reference "week one timetable"

What exactly should you do each day of week one? A reference cadence below. Specific timing depends on the customer's calendar, but **the signal points and artifacts must be hit in order.**

| Day | Key actions | Expected outputs |
|---|---|---|
| Day 1 | Customer kickoff + introductions to all relevant people; ask for the 5 artifacts (4.2 third type) | A list of key people (with KPI relationships), artifacts in hand |
| Day 2 | First system walkthrough + read artifacts; 1:1 with IT lead on data access | System overview diagram (hand-drawn is fine), data-access requirements list |
| Day 3 | First shadowing (4 hours); afternoon to write up observation notes | A shadowing note + 5 real pain points |
| Day 4 | Of the 12 questions, the 4 business-state and 4 technical-state ones, in two sessions | 8 of 12 answered; remaining 4 listed for follow-up |
| Day 5 | Second shadowing (different role); 1:1 with the opposition | The opposition's real concerns surfaced |
| Days 6–7 | Write Discovery report v0; line up the contact for ~50 seed samples | Draft report + confirmed seed-sample contact |
| Days 8–10 | Report review meeting + sample filtering + outcome number sign-off | Report v1 + 50 seed samples + outcome number |

When reading this table: **some actions are paced by the customer** — like the kickoff and data-access approvals; you can't speed those up. **Others are paced by you** — like shadowing and artifact reading; if you don't push, no one will. The most common beginner mistake is treating every action as "wait for the customer" — and ending week one with nothing.

---

## 4.7  LLM projects: two extra Discovery actions

LLM application projects need two extra Discovery actions on top of data-driven Discovery.

**First: inventory the natural-language assets.**

The "raw material" of an LLM application is documents, conversations, emails, tickets — unstructured assets. Discovery is when you inventory them:

| Asset type | Volume (count / words) | Update frequency | Maintainer | Who can access today |
|---|---|---|---|---|
| Internal wiki | 100K words | Weekly | Department PMs | Everyone (search is bad) |
| Customer service conversation history | 500K records | Real-time | CS system auto-records | Data team |
| Sales contract PDFs | 8,000 docs | Monthly | Legal | Legal |

Read this table by asking: for each type, **what's the current volume? Who maintains it? Is the format clean? Who can use it today?**

If a category has unclear ownership, messy format, no maintainer — that part can't be fed into the LLM application immediately. Either build a governance flow first (delaying the project) or exclude that category (shrinking scope).

**Second: collect 50 seed samples.**

At the end of Discovery, find 50 **real customer questions, tickets, or task samples.** These are the seed of Eval set v0.

Channels: export the last 1,000 customer service tickets and have a business expert filter 50 representative ones; sales-rep work logs; internal issue tracker; real email threads (after redaction).

The 50 don't need standard answers — this step is just collecting "what do real requests in the customer's world look like." Standard answers come at SOW time in Chapter 5.

**With 50 seed samples in hand, Discovery is 80% done.** The remaining 20% is having a business expert review the 50 to confirm coverage.

---

## 4.8  Pitfalls that show up in week one

Based on experience, the most common pitfalls in Discovery week one:

**Only meetings, never the floor.** Meetings give you stated preference. If the customer won't let you on the floor or near front-line operators, that's a red flag — the customer's openness is too low and the project won't last.

**Starting code in week one.** Coding inside the first Discovery week necessarily codes the wrong direction, because your understanding of the requirement isn't complete yet. Resist the urge to open the IDE; focus on 4.2 and 4.3.

**Discovery report without "what we won't do."** "What we won't do" defines the project's boundary. Without it, the customer can add things at any time three weeks in, and your SOW won't hold.

**Entering Scaffolding without 50 seed samples.** No seeds means no Eval set, which means rule 2 of Chapter 2 is directly violated. Scaffolding will get progressively vaguer.

**Not validating the customer's "numbers."** The customer says "we have 10K tickets a day" — you query their ticket system and find it's only 1K. Numbers from the customer should be validated by default.

**Not recording data ownership.** Per 4.5, this is the linchpin of schema evolution.

---

## Closing

Discovery has produced three things: a one-sentence real problem, a one-number outcome, 50 seed samples. Those three are the inputs for the next chapter.

The next chapter translates those three into engineerable contract artifacts — Eval set v0, acceptance criteria, SOW. These three documents are what you'll use to hold scope in Scaffolding, decide "should this go live" in Production, and say "the project is done per contract" in Handoff.

Discovery is the most undervalued, highest-ROI phase of FDE work. The next chapter solidifies its outputs into contract artifacts you can hand to the customer for sign-off.

---

## Public references for this chapter

- A. Lawrence, *Forward Deployed Engineer Rule Book* (2025) — the FDE-context articulation of *stated preference vs. revealed preference*
- Conikeec, *The FDE Playbook: A Practitioner's Field Manual* (2025, Substack) — practical observations on not coding during Discovery
