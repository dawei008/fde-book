---
title: "en/README.md"
nav_exclude: true
search_exclude: false
---

<p align="center">
  <img src="../cover.png" alt="FDE Book Cover" width="520" />
</p>

<h1 align="center">FDE Book</h1>
<h3 align="center">A Practical Field Manual for Forward Deployed Engineers</h3>

<p align="center">
  <code>Sell the outcome. Fix forward. Eval first.</code>
</p>

<p align="center">
  <a href="../README.md">中文</a> ·
  <a href="../FDEBook-en.pdf">English PDF</a> ·
  <a href="../FDEBook-zh.pdf">中文 PDF</a> ·
  <a href="bibliography.md">Bibliography</a>
</p>

<p align="center">
  <em>17 Chapters · 7 Parts · 4 Appendices · Bilingual (CN/EN)</em>
</p>

---

> *This book is an independent synthesis of FDE engineering practice. All sources are cited; no copyrighted code or long-form text is reproduced.*

---

## What This Book Is

**A practical handbook for engineers already doing — or about to do — FDE work.**

It does not tell career stories, retrace Palantir's history, or argue whether FDE is the right next move for you. It assumes you've already taken the role, or are about to.

What it does cover: when you walk into a customer's conference room facing a pile of Confluence docs and a vague objective — **what you do in week 1, week 6, and month 6** — the concrete engineering moves and judgment calls at each step.

The book runs two parallel tracks:

- **LLM Applications track** (Parts III, VI): models / RAG / agents / evals / toolsets — what most FDEs do in 2026
- **Field-delivery track** (Part IV): ontology / VPC deployment / integration / data pipelines — Palantir-style traditional FDE work

Both tracks merge in Part II (Discovery), Part V (PoC→Production), and Part VII (Handoff).

---

## Why You'd Pick This Up

If any of the following sounds like your week:

- Your manager said "go work with the customer and push the PoC over the line" — and you're not sure what's in scope
- You're inside a customer VPC for the first time and getting blocked by approval flows, SSO, and security questionnaires
- The customer loved the demo but said "let's revisit at production time" — and you haven't heard from them since
- You inherited a project from a previous FDE — docs incomplete, no eval set, customer expectations have drifted
- The agent runs locally but the customer won't let it ship — you don't yet know how to design the sandbox / rollback / observability story

Every chapter answers questions in this shape.

---

## Table of Contents

[Preface](preface/) · [Reading Guide](reading-guide/)

**Part I — Role and Mindset**
- [Chapter 1 — The Real FDE Workflow](part-1/chapter-01/)
- [Chapter 2 — The Three Iron Rules](part-1/chapter-02/)
- [Chapter 3 — Two FDE Modes](part-1/chapter-03/)

**Part II — Customer Discovery**
- [Chapter 4 — Week One on the Customer's Site](part-2/chapter-04/)
- [Chapter 5 — From Requirements to SOW and Eval Set](part-2/chapter-05/)

**Part III — Tech Stack Selection**
- [Chapter 6 — Week-One Tech Stack Selection](part-3/chapter-06/)
- [Chapter 7 — RAG / Fine-tune / Agent Decision Tree](part-3/chapter-07/)
- [Chapter 8 — Eval Before Code](part-3/chapter-08/)

**Part IV — Engineering for the Real Customer Environment**
- [Chapter 9 — Data Engineering](part-4/chapter-09/)
- [Chapter 10 — Scaffolding and the Development Loop](part-4/chapter-10/)
- [Chapter 11 — VPC, SSO, Compliance](part-4/chapter-11/)

**Part V — Going Live and Operating**
- [Chapter 12 — PoC to Production](part-5/chapter-12/)
- [Chapter 13 — Monitoring and Guardrails](part-5/chapter-13/)

**Part VI — Agents and MCP**
- [Chapter 14 — Agent Toolset Design](part-6/chapter-14/)
- [Chapter 15 — MCP Integration](part-6/chapter-15/)
- [Chapter 16 — Skill: Packaging Customer Expertise for Agents](part-6/chapter-16/)

**Part VII — Handoff and Continuity**
- [Chapter 17 — Project Handoff](part-7/chapter-17/)
- [Chapter 18 — The FDE's Next Step](part-7/chapter-18/)

**Appendices**
- [A — Toolstack Quick Reference](appendix/appendix-a/)
- [B — Comparison Matrix](appendix/appendix-b/)
- [C — Eval Set Templates](appendix/appendix-c/)
- [D — Customer Onboarding Pack](appendix/appendix-d/)

[Glossary](glossary/) · [Bibliography](bibliography/)

---

## How to Read

- **Cover to cover**: ~6-7 hours
- **LLM/Agent FDE only**: Parts I → III → V → VI → VII
- **Field-delivery FDE only**: Parts I → II → IV → V → VII
- **Reference**: Appendices A–D as needed

See [reading-guide](reading-guide/).

---

## What This Book Won't Do

- Not a Palantir history retelling
- Not a Python / SQL / Docker tutorial — assumes 5+ years of engineering
- Not yet another LLM tutorial — no "what is a transformer," yes "how to pick a model in a customer setting"
- No 100-page bibliography — only the few sources that matter, named in-line

---

## Status

- Writing in progress (started May 2026)
- Chinese is the source of truth; the English version mirrors structure under `en/`
- Research notes and source list are public under `../research/`

If you're doing FDE work, please open a GitHub Issue with concrete questions or counter-examples — they may end up in the next edition.
