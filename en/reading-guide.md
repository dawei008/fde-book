---
title: "en/reading-guide.md"
nav_exclude: true
search_exclude: false
---

# Reading Guide

> 17 chapters, ~6-7 hours end to end. Two tracks running in parallel — pick the route that matches your FDE flavor.

---

## Pick a Track

### Track A: LLM-Application FDE (default)

**Best for**: FDEs at OpenAI / Anthropic / Cohere / Chinese model labs and downstream startups, shipping LLM applications in customer environments.

**Path**: Part I → Part II → **Part III** → Part V → **Part VI** → Part VII.

**Highlights**: Ch 6 stack matrix, Ch 7 RAG/FT/Agent decision tree, Ch 8 eval-driven development, Ch 14 agent deployment, Ch 15 MCP.

**Time**: ~5 hours.

---

### Track B: Field-Delivery FDE (Palantir style)

**Best for**: FDEs at Palantir, AWS GenAI Innovation Center, AI consultancies — delivering data + software in customer environments.

**Path**: Part I → Part II → **Part IV** → Part V → Part VII.

**Highlights**: Ch 9 ontology / ETL, Ch 10 VPC deployment, Ch 11 SSO/SCIM/audit, Ch 12 PoC cut-over, Ch 16 handoff.

**Time**: ~4 hours.

---

### Track C: Full Read (FDE leads, staff/principal cross-track)

**Best for**: FDE team leads, anyone doing internal training, FDEs who span both tracks.

**Path**: Part I straight through to Part VII.

**Time**: 6-7 hours.

---

### Track D: Reference

**Best for**: A specific question — "how do I size hardware for private deployment?", "how do I write PoC acceptance criteria?"

**Use**: Jump to appendices A–D and the relevant chapter.

| Your question | Where to look |
|---|---|
| Choose a model / framework / vector DB | Appendix A, Appendix B |
| Write an eval set | Ch 8, Appendix C |
| Write an SOW / security questionnaire / risk register | Appendix D |
| Design an agent sandbox | Ch 14 |
| Customer VPC deployment checklist | Ch 10 |

---

## Difficulty Markers

```
🟢 Direct — copy and apply
🟡 Reflection — judge against your project
🔴 Decision — org / commercial / compliance call
```

| Part | Difficulty |
|---|---|
| I Foundations | 🟢 |
| II Discovery | 🟡 |
| III Scaffolding | 🟢 |
| IV Data & Integration | 🟡 |
| V PoC→Production | 🟡 |
| VI Agent Era | 🟢 |
| VII Handoff & Mastery | 🔴 |

---

## Chapter Format

```
Opening — concrete scene or concrete counter-example
Body — 3-5 sections, each one engineering call
Key citations — a quote or two from Lawrence / McGrew / Conikeec / AWS
Action checklist — copy-do items for this week
Anti-pattern checklist — recurring failures real FDEs hit
```

If you're short on time, **read the action and anti-pattern checklists first**.

---

## Recurring Concepts

Full glossary in [glossary.md](glossary.md). The load-bearing few:

| Concept | One-liner |
|---|---|
| **Sell the outcome** | Sell results, not tools — McGrew's first law |
| **Fix Forward** | Fix it on-site, don't drag it back to HQ — Lawrence's principle |
| **Eval-driven** | Eval set first, code second — Ch 8's spine |
| **Ontology** | Palantir's core abstraction; Ch 9 gives an engineering view |
| **Agent Toolset** | The set of tools an agent can call — Ch 14's topic |
| **MCP** | Model Context Protocol — standard for connecting agents to enterprise tools — Ch 15 |
| **PoC Cut-over** | The chasm from PoC to production — Ch 12 |
| **Handoff** | The departure-day delivery move — Ch 16 |

---

## Companion Resources

- **research/** — All research notes (7 docs, public)
- **Appendix D** — 12 ready-to-use templates for week one
- **GitHub Issues** — Counter-examples, real numbers, missing-chapter requests

---

Next: [Preface](preface.md) → [Part I Intro](part-1/intro.md)
