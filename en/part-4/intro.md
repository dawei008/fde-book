# Part IV: Data & Integration — Inside Real Customer Environments

> Applies to: **field-delivery track** (data / integration / VPC / compliance). The LLM-application track must also read all of this whenever real customer data is involved.

---

## What This Part Solves

After an LLM application makes it past demo, two things kill it most often:

1. **The data won't connect** — customer data lives in SAP / Oracle / a private cloud / offline / hybrid cloud
2. **It connected, but compliance won't sign off** — PII / cross-border / China MLPS (等保) / audit

A Palantir-style FDE spends 50% of their time on the topics in this Part. An LLM-style FDE will hit them as soon as they walk toward production.

This Part gives three practical chapters:

- **Chapter 9**: the data stack itself (Ontology / ETL / real-time pipelines)
- **Chapter 10**: how to actually engineer inside the customer's VPC / private deployment / offline data center
- **Chapter 11**: integrating with legacy systems (SSO / SCIM / API / audit)

## Chapters

See [SUMMARY.md](../SUMMARY.md).

## Relation to Other Parts

- **Prerequisite**: Part II's Discovery must have surfaced the data reality (Ch 4.5, data admission)
- **Parallel**: during Part III's Scaffolding phase, data integration runs in parallel
- **Follow-on**: Part V's productionization and Part VI's Agent tool calling both depend on the foundations laid here

---

[← Back to Contents](../README.md)
