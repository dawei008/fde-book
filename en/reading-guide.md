---
title: "Reading Guide"
nav_order: 2
---

# Reading Guide

> 17 chapters, ~6-7 hours end to end. Two tracks running in parallel — pick the route that matches your FDE flavor.

---

## Pick a Track

### Track A: LLM-Application FDE (default)

**Best for**: FDEs at OpenAI / Anthropic / Cohere / Chinese model labs and downstream startups, shipping LLM applications in customer environments.

**Path**: Part I → Part II → **Part III** → Part V → **Part VI** → Part VII.

**Highlights**: Ch 6 stack quick-decision matrix, Ch 7 RAG/FT/Agent decision tree, Ch 8 eval-driven, Ch 14 agent deployment, Ch 15 MCP.

**Time**: ~5 hours.

---

### Track B: Field-Delivery FDE (Palantir style)

**Best for**: FDEs at Palantir, enterprise AI consultancies, or cloud-vendor solutions teams — delivering customer-site data + software in customer environments.

**Path**: Part I → Part II → **Part IV** → Part V → Part VII.

**Highlights**: Ch 9 ontology / ETL, Ch 10 VPC deployment, Ch 11 SSO/SCIM/audit, Ch 12 PoC cut-over, Ch 16 handoff.

**Time**: ~4 hours.

---

### Track C: Full Read (FDE leads, cross-track)

**Best for**: FDE team leads, staff/principal engineers running internal training, FDEs spanning both kinds of projects.

**Path**: Part I straight through to Part VII.

**Time**: 6-7 hours.

---

### Track D: As Reference

**Best for**: A specific question — "the customer wants private deployment, how do I size hardware?", "how do I write PoC acceptance criteria?"

**Use**: Jump directly to appendices A–D and the relevant chapter.

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
🟢 Direct — engineers can copy and apply
🟡 Reflection — judge against your own project
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

Each chapter opens on a concrete scene — a meeting, an incident, an eval set — then unfolds a few engineering judgments, with reflective passages woven in. Anti-patterns aren't piled at the end as a checklist; they appear alongside the main narrative scenes, so "why this is wrong" stays glued to "the situation in which it gets done."

If you're short on time, scan the section headings of each chapter and read the few that match your current project.

---

## Recurring Concepts

Full glossary in [glossary](../glossary/). The load-bearing few:

| Concept | One-liner |
|---|---|
| **Sell the outcome** | Sell results, not tools — McGrew's first law |
| **Fix Forward** | Fix it on-site, don't drag it back to HQ — Lawrence's principle |
| **Eval-driven** | Eval set first, code second — Ch 8's spine |
| **Ontology** | Palantir's core abstraction; Ch 9 gives an engineering view |
| **Agent Toolset** | The set of tools an agent can call — Ch 14's topic |
| **MCP** | Model Context Protocol — standard for connecting agents to enterprise tools |
| **PoC Cut-over** | The chasm from PoC to production — Ch 12 |
| **Handoff** | The departure-day delivery move — Ch 16 |

---

## Companion Resources

- **research/** — All research material, openly available (11 docs)
- **Appendix D** — 12 ready-to-use templates for week one
- **GitHub Issues** — Counter-examples, real numbers, missing-chapter suggestions

---

Next: [Preface](../preface/) → [Part I Intro](../part-1/intro/)
