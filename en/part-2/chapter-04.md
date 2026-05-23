# Chapter 4: Discovery — Observe Before You Ask

## Opening

```
An FDE walks into the customer site for the first time.

He's well prepared: 30 questions written down, customer website,
annual report, and product white paper read in advance,
and a "customer scenario assessment questionnaire" in hand.

The meeting runs from 9 AM to 4 PM. The customer fields five people
who take turns answering every question on his list.

Back at the hotel he writes up his notes — and the further he goes,
the emptier they feel. All 30 questions "answered," yet not one
specific enough to write code against.
Worse, he has no way to tell which answers were real
and which were the boilerplate the customer hands every vendor.

The next day he does something different: he sits in the customer's
call center for half a day and watches the agents take 30 calls —
which systems they open, what they look up, what they write down.

The notes from that half-day are worth ten times the notes
from the seven-hour meeting.

This chapter has one line: observe before you ask.
```

---

## 4.1 Why Observation Beats Asking

When customers answer your questions, they tend to describe **the workflow they think they have**, not **the workflow they actually have**.

The engineering term is **stated preference vs. revealed preference**:

- What people say they prefer (stated) and what their behavior reveals they prefer (revealed) are routinely inconsistent.
- The customer's exec tells you "we run the pipeline in CRM"; you sit next to a sales rep for a day and see them spend 70% of the time in Excel.
- Compliance tells you "all the data lives in SAP"; one query later you find that 30% of the critical data is sitting in an Excel file on a shared drive.

**FDE Discovery has to be built on revealed preference.** How do you reveal it? You observe.

---

## 4.2 Three Observation Techniques

### Technique 1: Shadowing

Follow a single front-line employee for half a day. Be a mute — don't interrupt, don't comment, just watch.

Carry a notebook with two columns:

```
        What they do                What they get stuck on
        ────────────                ───────────────────────
0:00    Opens 5 tabs                CRM takes 8s to load
        Outlook + CRM + Excel
        + shared drive + wiki

0:08    Searches "ABC Corp"         3 duplicate hits in CRM
                                    no idea which is the real one

0:12    Opens Outlook to find       4 minutes manually paging
        the latest email            and searching

...
```

**Four hours of sitting next to someone** beats eight hours of meetings.

### Technique 2: System Walkthrough

Ask the customer to log into the systems they use most often and **narrate as they click**: "Why do you check this one first, then that one?"

You're not auditing system features; you're observing the **actual interaction pattern between the human and the systems**.

What to record:

- How many systems does an average task touch?
- Which paths are hot (used every day) and which are cold (used occasionally)?
- Where on the hot paths are the pain points: pasting, tab-switching, waiting, manual arithmetic?

### Technique 3: Artifact Mining

Ask the customer to show you five **real artifacts**:

1. Last week's sales report from a sales manager to their boss (real structure).
2. A resolved customer ticket from last month (real flow).
3. The minutes from a recent internal stand-up (real vocabulary).
4. A contract addendum the customer rejected (real reasons for rejection).
5. Last quarter's KPI report (real metrics).

**Real artifacts > any PowerPoint pitch.** The vocabulary used internally, the precise way KPIs are defined, the actual nodes of the workflow — they're all in the artifacts.

---

## 4.3 The 12 Questions You Must Always Ask

Observation plus these 12 questions is enough for one solid first round of Discovery:

### Business Reality (4 questions)

1. **If you do nothing today, what does this problem look like in three months?**
   - "About the same" → no real pain; be cautious about taking the project.
   - "Worse" → quantify how much worse.
2. **How many times a month does this workflow run, and how long does each instance take?**
   - No numbers → your week-1 task is to instrument it.
3. **Has anyone tried to solve this before? Why didn't it work?**
   - Nobody tried → be cautious (the problem may not actually matter).
   - Someone tried and failed → listen carefully to why; avoid the same trap.
4. **If this were solved today, how would you know?**
   - This question fixes the outcome number.

### Technical Reality (4 questions)

5. **Where does the data come from? Does it have an owner?**
   - Data without an owner is data you can't use.
6. **When was the last time you renovated this system, and who approved it?**
   - Reveals the decision chain.
7. **How long does an average production deployment take, and what approvals does it need?**
   - Determines whether your Fix Forward setup is even viable.
8. **If the model gets it wrong and gives a bad answer, what's the worst case?**
   - Drives the fault-tolerance design / safety constraints / Guardrails strength.

### Organizational Reality (4 questions)

9. **Whose KPI is directly tied to this project succeeding?**
   - Nobody's → the project will most likely go cold.
10. **Who's the opponent? Why do they oppose it?**
    - No opponent → probably nobody actually understands what's being built.
11. **Who will operate it after we leave, and when do they get involved?**
    - Nobody → handoff risk has already arrived.
12. **If the PoC succeeds, what does it look like three months later?**
    - No answer → the customer has no real plan for production.

---

## 4.4 Discovery Report Template

After the first Discovery round (1–2 weeks recommended), you should produce a Discovery report no longer than three pages, written **for both your own leadership and the customer's decision-makers to read together**:

```
Discovery Report — [Customer] / [Project]
Date: YYYY-MM-DD
Author: FDE [name]

==================================================
1. The real problem (one sentence)
   "The median time for an account manager to find a specific
    policy clause is 4m 30s; this happens ~12,000 times a month;
    the pain is ___."

2. Target outcome (one number + one time window)
   "Within [time], cut the median to [number]; measured by ___."

3. Five pieces of observed evidence for the current pain
   - [shadowing observation 1]
   - [system walkthrough observation 2]
   - ...

4. Key constraints
   - Data: [available / unavailable]
   - Deployment: [VPC / private / cloud / offline]
   - Compliance: [MLPS / SOC2 / GDPR / PII]
   - Cost: [budget cap / monthly token budget]

5. Risks and unknowns (top 3)
   - [Risk 1: impact + mitigation]
   - [Risk 2]
   - [Risk 3]

6. Recommended approach (3-week scaffolding)
   - Shape: [data-driven / LLM-driven / hybrid]
   - Key tech: [model / framework / deployment mode]
   - Eval set v0.1: [N samples covering K scenarios]
   - First milestone: [in X weeks, hit Y number]

7. What we will NOT do (Out of Scope)
   - [Excluded ask 1 + reason]
   - [Excluded ask 2]

8. Next steps
   - Customer: [3 things the customer needs to do]
   - Us: [what the FDE team does in the next 2 weeks]
==================================================
```

**Section 7 (what we will not do) and Section 5 (risks) are the two most valuable sections of the Discovery report**, and the two beginners are most likely to skip.

---

## 4.5 Common AWS Data-Access Flow During Discovery

If you're delivering on AWS (especially in the GenAIIC field-delivery style), Discovery has to nail down the **legal path to the data** explicitly. Skip this and no pipeline downstream will stand up.

A typical AWS data-access flow:

```
        Customer raw data                  FDE working environment
        ─────────────────                  ────────────────────────
                                            (FDE works in the customer
        1. S3 (production bucket)            AWS account or a shared
              ↓                              sandbox account)
        2. AWS Lake Formation                       ↓
           (register data, define perms)    4. Request fine-grained
              ↓                                permissions
        3. AWS Glue Data Catalog               (LF tags, column-level)
           (unified metadata)                       ↓
                                            5. Athena exploratory queries
                                                    ↓
                                            6. Assess data shape
                                              (fields, null rates,
                                               distributions)
                                                    ↓
                                            7. Add a "data access
                                               manifest" to the
                                               Discovery report
```

Key practices:

- **Don't query data with ROOT credentials.** Have the customer issue specific LF-tag permissions through IAM Identity Center / Lake Formation.
- **Run all exploration through Athena.** Don't download full datasets to a laptop (compliance risk).
- **Record ownership for every data source** — who owns the data, who can approve schema evolution.

> **AWS reference**: see "AWS Lake Formation getting started" and "Granting data permissions" on docs.aws.amazon.com.

---

## 4.6 Discovery Specifics for LLM Projects

LLM projects add two moves to Discovery:

### 1. Inventory the existing "natural-language assets"

The raw material for an LLM application is unstructured: documents, conversations, emails. During Discovery, inventory them:

| Asset type | Volume | Update frequency | Maintainer | Who can search it today |
|---|---|---|---|---|
| Internal wiki | XX million chars | Weekly | Department PMs | Everyone (search is bad) |
| Support chat logs | XX million entries | Real-time | Support system (auto) | Data team |
| Sales contract PDFs | XX files | Monthly | Legal | Legal |
| ... | | | | |

If data ownership is unclear / formats are inconsistent / nobody maintains it → **the LLM project is not yet ready to start**.

### 2. A 50-sample seed set

End Discovery by collecting 50 **real customer questions / tickets / task examples**. This is the seed of Eval set v0.1.

Where to source them:

- Export the last 1,000 tickets from the support system; have a domain expert pick 50 representative ones.
- Sales reps' work logs.
- The internal issue tracker.
- Real email exchanges (after redaction).

**With 50 seeds in hand, Discovery is 80% done.**

---

## Key Citations

> "*Stated preference and revealed preference are different — and engineers must trust the latter.*"
> — A. Lawrence (paraphrased), *FDE Rule Book*, 2025

> "*The best Discovery week is one where you don't write any code.*"
> — Conikeec, *The FDE Playbook*, 2025

---

## Action Checklist

The 8 things to do in weeks 1–2 of a new project:

1. **Schedule at least 2 shadowing sessions** (4 hours each), watching front-line employees on site.
2. **Run 3 system walkthroughs**, covering the most-used systems.
3. **Pull 5 real artifacts** (Section 4.2 — artifact mining).
4. **Work through the 12 must-ask questions** (Section 4.3).
5. **Inventory the customer's AWS account / data access / network allowlists** (Section 4.5).
6. **Inventory the customer's existing "natural-language assets"** (Section 4.6, LLM projects).
7. **Collect 50 seed samples.**
8. **Deliver a 3-page Discovery report at the end of week 2** (template in 4.4).

---

## Anti-Pattern Checklist

- ❌ **Meetings only, no field time** (you'll only get stated preference).
- ❌ **Writing code in week 1 of Discovery** (guaranteed to be the wrong direction).
- ❌ **No "what we will not do" in the Discovery report** (scope will get out of control).
- ❌ **Moving into Scaffolding without 50 seed samples** (no Eval is possible).
- ❌ **Not validating the customer's "numbers"** ("we do 10,000 tickets a day" might actually be 1,000).
- ❌ **Not recording data owners** (nobody can approve schema evolution later; the project locks up).

---

## Connection to the Next Chapter

Discovery has produced the problem + outcome + 50 seeds. The next chapter translates those into engineerable contractual artifacts — **eval set + acceptance criteria + SOW**.

[← Part II Intro](intro.md) · [Next: From Requirements to Acceptance →](chapter-05.md)
