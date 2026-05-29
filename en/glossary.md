---
title: "Glossary"
nav_order: 90
---

# Glossary

> Alphabetical order. Source pages in [bibliography](../bibliography/).

---

## A

**A. Lawrence** — Author of *Forward Deployed Engineer Rule Book* (2025-10), the only standalone English-language book on FDE to date.

**Agent (AI Agent)** — An LLM application that plans, calls tools, and iterates autonomously. Subject of Part VI.

**Agent Toolset** — The set of tools (read/write/exec/network/...) an agent can call. Topic of Ch 14.

**Anthropic** — Maker of Claude.

**AWS GenAI Innovation Center** — Amazon's FDE-equivalent organization. Officially uses the term "Forward deployment engineering"; published the 45-day / 73% figures.

## B

**Bob McGrew** — Former Chief Research Officer at OpenAI. Origin of "Sell the outcome, not the product."

## C

**Conikeec** — Substack author of *The FDE Playbook: A Practitioner's Field Manual*.

**Confluence** — Atlassian's enterprise wiki. A common form of the customer's documentation library; unavoidable in the Discovery phase.

## D

**Discovery** — The first FDE phase: observe the customer's workflow, read existing systems, find the real problem. Topic of Part II.

**Dual-Credential Training** — Lawrence's concept: an FDE must hold both engineering credibility and domain credibility.

## E

**ETL (Extract-Transform-Load)** — Classic data-pipeline operations. Topic of Ch 9.

**Eval / Eval Set / Eval-driven** — The evaluation set; the practice of writing the eval set before feature code. Spine of Ch 8.

**Embedded Problem Solver** — Lawrence's framing: an FDE is embedded *inside* the customer's problem.

## F

**FDE (Forward Deployed Engineer)** — An engineer who lives at the customer site and ships AI/software into production. Subject of this book.

**Fine-tuning** — Continuing LLM training on customer-private data. A choice point in Ch 7.

**Fix Forward** — Lawrence's principle: solve on-site; do not drag the problem back to HQ.

**Foundry** — Palantir's flagship platform — ontology + data integration + application layer. Reference frame for Ch 9.

**Forward Deployment Engineering** — AWS's official term; equivalent to FDE elsewhere.

## G

**GTM (Go-To-Market)** — How a product reaches customers.

## H

**Handoff** — The move at FDE departure: returning the project to the customer's internal team. Topic of Ch 17.

## I

**Immersion Before Judgment** — Lawrence's principle: live in the customer workflow before making judgments.

## J

**JD (Job Description)** — A job posting.

## L

**LLM (Large Language Model)** — The book assumes you can already call APIs.

## M

**MCP (Model Context Protocol)** ⭐ — Anthropic-led open protocol standardizing how agents connect to external tools. Topic of Ch 15.

**Morgan Stanley (MS)** — OpenAI's public case study; source of the 6-8+4 cycle reference.

## N

**Nabeel Qureshi** — Early Palantir; the most influential English-language interpreter of the FDE model.

## O

**Ontology** ⭐ — Formal modeling of customer business concepts (entities, properties, relationships, actions). Palantir's core abstraction; primary battlefield of the FDE data track. Topic of Ch 9.

**Outcome (in "Sell the outcome")** — The customer's business result (revenue, cost, risk), as opposed to a feature, tool, or demo.

## P

**Palantir** — Inventor of the FDE model.

**PoC (Proof of Concept)** — Concept verification. Ch 12 focuses on the PoC → production cut-over criteria.

**Private Deployment / VPC Deployment** — Customer-private / VPC deployment. Topic of Ch 10.

## R

**RAG (Retrieval-Augmented Generation)** — A choice point in Ch 7.

**Rule Book** — Shorthand for Lawrence's *Forward Deployed Engineer Rule Book*.

## S

**SCIM (System for Cross-domain Identity Management)** — Enterprise identity-sync standard. Topic of Ch 11.

**Sell the outcome, not the product** — Bob McGrew's first law. Topic of Ch 2.

**SOW (Statement of Work)** — Project scope document. Topic of Ch 5.

**SSO (Single Sign-On)** — Almost always required in customer compliance. Topic of Ch 11.

## T

**Skill** ⭐ — Anthropic's agent extension shape: a directory containing `SKILL.md` (with `name` / `description` frontmatter) + body + co-located scripts/templates. Loaded on demand by description match across Claude Code / Agent SDK / Claude API; body costs no tokens unless triggered. Sits beside Tool (capability) and MCP (interop) as one of three agent extension shapes. Topic of Ch 16.

**T-shaped Growth** — Engineering depth + domain depth. Topic of Ch 18.

**Trace / Tracing** — Distributed tracing. Topic of Ch 13.

## V

**VPC (Virtual Private Cloud)** — A common substrate for customer-private deployment.

## Other

**Anti-pattern** — A common but harmful practice. End-of-chapter checklist throughout this book.

**Action Checklist** — Engineering moves you can copy-do this week. Standing end-of-chapter section throughout this book.

---

[← Back to Contents](../)
