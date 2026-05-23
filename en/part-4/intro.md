---
title: "Part IV — Engineering for the Real Customer Environment"
nav_order: 14
has_children: true
---

# Part IV: Engineering for the Real Customer Environment

Once an LLM demo runs on your laptop, the next step is to move it into the customer's environment. This single move is where most projects start hemorrhaging time.

The data won't connect — the customer's core data is scattered across SAP / Oracle / a private cloud / an offline data center / a cross-border hybrid setup, and every one of those has its own DBA, its own allow-list, its own approval workflow. Then it connects but compliance won't sign off — PII can't leave the region, cross-border transfers need filings, China MLPS (等保) needs evidence, audits need trails. None of these are solved by writing a few lines of code; they consume blocks of time end-to-end.

Part IV is about that distance — the gap between "it runs on my laptop" and "it runs in the customer's environment." A Palantir-style FDE spends roughly half their time on the topics in this Part. An LLM-style FDE will hit them the moment they walk toward production.

---

Chapter 9 is data engineering. The shape of the customer's data is almost guaranteed to differ from what you assumed during the demo phase: missing fields, naming chaos, mismatched definitions across systems, incremental sync ten times harder than full reload. This chapter walks through how to use Ontology as the abstraction layer that aligns semantics first, then decide how to build ETL or real-time pipelines.

Chapter 10 is the Scaffolding-phase development loop. "Running in the customer's environment" and "running on your own machine" differ on more than the network — the dependency chain is longer, error signals are weaker, rollback is more expensive. This chapter is about moving the minimum loop from Part III into the customer's VPC, private deployment, or offline data center, so that code can stay observable and iterable inside a constrained environment.

Chapter 11 is cross-system integration and compliance — SSO / SCIM / audit / VPC networking. The FDE often plays "bridge between customer IT and the solution side" here, and needs to understand what words like China MLPS 2.0, SOC 2, and GDPR actually mean as concrete actions in the customer's context, instead of being scared off by the jargon.

---

Part IV's prerequisite is that Part II's Discovery has surveyed the customer's data reality (otherwise you'll only discover during Scaffolding that the critical data simply can't be exposed). Part IV usually runs in parallel with Part III — tech-stack selection and data integration advance on two parallel tracks. Part V's productionization and Part VI's Agent tool calling both depend on the foundations laid here.
