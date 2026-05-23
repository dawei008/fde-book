---
title: "en/preface.md"
nav_exclude: true
search_exclude: false
---

# Preface

## What This Book Is

```
Monday, 9:00 AM. You boot up.
The customer's security officer has emailed you a 27-item compliance questionnaire.
Slack has 4 unread channels from the previous FDE; the latest message is
"Why is the RAG recall dropping again?"
Your calendar shows: 11 AM customer VP sync, 13:00 model vendor cost review,
15:00 PoC review deck due to your manager.

You have one hour before you open the IDE.
What do you spend it on?
```

This is the kind of question this book answers.

---

## Who It's For

**Engineers already doing FDE work, or assigned FDE work without the title.**

Concretely:

- 5+ years of engineering experience; can own an entire backend service
- Have run at least one customer PoC; have been stuck in production hand-off at least once
- Have called LLM APIs and shipped demos; haven't yet run an agent in a customer environment
- Comfortable reading OpenAPI specs, running SQL, reading distributed traces — no intermediaries needed

If you've never been customer-facing or never used an LLM API, do a few small projects first. This book doesn't teach the basics.

---

## Who It's Not For

| Not the audience | Why |
|---|---|
| Job-seekers deciding "should I become an FDE" | This book skips the career-judgment layer |
| Investors / policymakers | Too low-level; you want conclusions |
| Students / new grads | Missing prerequisites — won't be useful yet |
| Readers wanting LLM internals | No transformer / attention coverage |

---

## Three Promises

**1. Every judgment call comes with a concrete scenario.**

No "FDEs should value customer interviews." Instead: "In your first week on a project, what to do, what *not* to do, and the 5 questions to ask in the first 3 customer meetings."

**2. Every technical choice gives you decision dimensions.**

No "RAG beats fine-tuning" or vice versa. A matrix instead: data volume / update frequency / answer determinism / inference budget / compliance — judge for yourself.

**3. Every chapter ends with an action checklist + an anti-pattern checklist.**

The action checklist is what you can copy-do this week; the anti-pattern checklist is what real FDEs keep getting wrong.

---

## Core Sources

The book leans heavily on:

- **A. Lawrence**, *Forward Deployed Engineer Rule Book* (Oct 2025)
- **Bob McGrew @ Y Combinator** (2025) — "Sell the outcome, not the product"
- **AWS GenAI Innovation Center** — public 45-day / 73% figures
- **Conikeec @ Substack**, *The FDE Playbook*
- **Nabeel Qureshi**, *Reflections on Palantir*

Full list in [bibliography.md](bibliography.md).

---

## How to Read It

The most useful way: **read it alongside a real FDE project**.

After each chapter, ask yourself:

1. Does my current project have this problem?
2. If yes, how did I handle it before?
3. How does the chapter's approach differ from mine? Which is better?

End-to-end takes 6-7 hours; with a real project alongside, 2-3 weeks is probably more useful.

---

## Feedback

GitHub Issues is the fastest channel. What I want most:

- **Counter-examples**: where the book's recipe failed in your context
- **Real numbers**: your PoC conversion rate, customer NPS, week-one deliverables
- **Missing chapters**: critical engineering topics you think this book missed

The next edition will probably absorb the strongest signals.

---

> *Written May 2026.*
