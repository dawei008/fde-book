---
title: "Chapter 9 — Data Engineering"
parent: "Part IV — Engineering for the Real Customer Environment"
nav_order: 1
---

# Chapter 9: The Customer Data Stack — Ontology, ETL, and Trade-offs in Real-Time Pipelines

That ticket Agent at Suzhou Hesheng Precision Heavy Industries — in Chapter 6 we signed the architecture sheet in the conference room, in Chapter 7 we settled on RAG + tool use, in Chapter 8 we wired the eval set into CI. Now Scaffolding is in week three, and the job is turning "the model can run" into "the data can flow."

There was one line on the board's wishlist I didn't dare answer lightly back then: "Should the Agent pull real-time spare-parts inventory from the customer's local distributors?" — behind that single line sat the data-integration workload of 5 sites in Southeast Asia + 1 ERP at HQ + 8 external systems at distributors in each region. I told Gu Jianguo that day, "I need to draw a data map before I can answer this." That map is what this chapter is.

This chapter doesn't teach you "what is a data warehouse" — you've done five years of backend work, you know all that. What this chapter is about is **looking at the data stack from the customer's perspective, deciding what to integrate first and what to defer, what to gather under Ontology and what to leave to raw SQL** — these judgments are the FDE's core actions on customer site, and they're not the same thing as the "data architecture" in textbooks.

---

## 9.1 The "5-Layer Data Map" You Must Draw in Week 1

Across the projects I've personally been in, data integration accidents are never because somebody didn't know how to use a tool — they happen because the FDE didn't spend a morning in the first two weeks drawing the customer's data stack clearly. Week 3 starts and you're trying to integrate, and you discover that "customer" means four different IDs in four systems, and "yesterday's orders" can't even be aligned on which timezone's "yesterday."

I make a habit of drawing a map like this in week 1 — five layers, bottom up:

```
  L5  Application / Agent / API           ← Most FDE work lives here
        Bedrock Agent / Lambda / internal apps

  L4  BI / Dashboard                      ← What the business looks at daily
        QuickSight / Tableau / Power BI / in-house

  L3  Metric layer / Data Mart            ← "Customer" is defined here
        dbt models / business views / canonical definitions

  L2  Warehouse / Data Lake               ← Where analytics runs
        Redshift / Snowflake / S3 + Iceberg / Databricks

  L1  OLTP databases                      ← Primary store for business systems
        PostgreSQL / Oracle / SQL Server / MongoDB
```

Hesheng's map ended up like this: L1 has 5 — HQ PostgreSQL (CRM tickets), Oracle (contracts/finance), Singapore RDS (MES), local MongoDB at each site (field operations logs), and 30% of critical data sitting in Excel files on a shared drive (spare-parts inventory is one of those). L2 is a Redshift in the Singapore region that's been running for two years. L3 is a pile of views maintained by two people on the data team, no dbt. L4 is QuickSight plus a few static weekly reports for the board. L5 is empty right now — they've never built an Agent before.

The point of drawing this map isn't aesthetics, it's to answer three questions:

- **Which layer is the data in now, and which layer is it going to?** Our Agent is at L5. The data it queries is either at L1 (real-time ticket status) or at L2/L3 (historical dispatch records). Which layer is the Excel spare-parts inventory in? Strictly, it's in the "unstructured corner" of L1 — and that's a textbook integration headache.
- **How many layers does it cross?** The more layers it crosses, the more engineering work. The Agent reading directly from L1 PostgreSQL is the fastest but most coupled approach; routing through L2 → L3 is a day slower but stable. That choice is what 9.3 unpacks.
- **Does L3 have "unified definitions"?** Most B2B customers are messy at this layer — the same "customer" is `customer_id` in CRM, `cust_no` in ERP, `client_code` in the finance system. No mapping table, the business side patches it together by experience. That's the Ontology problem 9.2 covers.

> Lawrence in *Forward Deployed Engineer Rule Book* wrote a line that stuck with me: *Most LLM hallucinations are actually data quality problems wearing a costume.* After a few projects I increasingly agree — the smarter the Agent, the more easily it confidently composes inconsistent data into a wrong answer. Drawing this map clearly in week 1 is how you save time on every "why did the Agent get this wrong" incident later on.

---

## 9.2 Ontology: Bringing the Five Lakes and Four Seas Under One ID Card

Ontology was the term Palantir popularized — they built it into the core abstraction of their product. Strip the marketing layer and it's three things:

```
  Object       The "gold standard" definition of a business object
               Customer / Order / Product / Contract / Asset

  Property     Attributes of each object + source-of-truth
               Customer.id = ?, Customer.tier = ?

  Relationship Relationships between objects
               Customer 1:N Order, Order 1:N Item
```

This sounds like Data Modeling 101, but Ontology has one critical distinction from traditional data modeling — **it isn't defined behind closed doors by the data team; it's a contract co-signed by business, data, and application teams**. Who is "the customer"? That decision can't be made by a data engineer alone — the business side has to speak.

At Hesheng, in week 2 I sat down with Chen Xue and Gu Jianguo and walked through it. The questions I asked weren't technical, they were four business questions:

**One, who is "the customer"?** In Hesheng's CRM "customer" is the buyer; in ERP "customer" is the paying party; in the after-sales system "customer" is the equipment user. For one five-axis machining center, the buyer might be an agent in Singapore, the paying party a factory in Malaysia, the user the workshop in Ho Chi Minh City. Three different "customer" IDs. Our Agent ingests tickets from the user — so **the after-sales system's `customer_id` is the gold ID**.

**Two, what's the primary key?** The after-sales system's `customer_id` looks like `SVC-VN-HCM-001423`. Region prefix, sequence number — looks tidy, but more than 200 historical records were hand-keyed and the prefix isn't consistent (`VN-HCM` vs `VHCM` vs `HCM-VN`). We can't use it directly — we have to build a "gold ID → actual system ID" mapping table that anchors the dirty data. Chen Xue and two customer-service reps spent two days in week 3 hand-fixing it. **There's no silver bullet here, just hand work**.

**Three, who has the right to change it?** Once the Ontology is set, every downstream dbt model and every Agent prompt is built on top. Renaming a single field is a major event. We agreed Chen Xue (the business side) is the Ontology owner; any change needs her email confirmation. That clause went into the SOW appendix.

**Four, how many objects does v1 cover?** Hesheng's first phase is just ticket triage — only Customer, Asset (equipment), Ticket, Engineer — 4 objects. Order/Contract aren't in Ontology v1. **Don't model objects the business scope doesn't reach** — Ontology isn't "build it ahead just in case," it's "build the ones you use."

That's the Ontology design done. What tool do we land it on? Hesheng is an AWS customer with the primary region in ap-southeast-1; there's no reason to bring in Palantir Foundry — overkill, and it wouldn't get past Gu Jianguo ("don't open up a second vendor relationship"). On AWS in this customer scenario, we built a lightweight version with Glue Data Catalog + Lake Formation:

```
  Glue Data Catalog as the Ontology registry

    database: hesheng_ontology_v1

    table: customer
      customer_id        string  PK    -- gold ID
      legal_name         string
      country            string
      tier               string
      crm_id             string        -- maps to CRM
      erp_no             string        -- maps to ERP
      finance_code       string        -- maps to finance
      lf_tags:           PII=yes, region=APAC
      owner:             chen.xue@hesheng.com

    table: asset
      asset_id           string  PK
      customer_id        string  FK -> customer
      model              string
      install_date       date
      ...
```

Permissions go through Lake Formation LF-Tags: PII fields are masked unconditionally in dev, and in prod they're partitioned by IAM role. This isn't a "complete Ontology framework" — it doesn't have Foundry's GUI object browser, it doesn't have automatic lineage — but it's enough, and it doesn't introduce a new vendor. This is the most common trade-off the FDE makes on customer site: **using the customer's existing platform capabilities to deliver 70% of what Palantir's abstraction does, and patching the remaining 30% with SOPs and dbt models**.

If your customer is on Snowflake or Databricks, the equivalents are Snowflake Tags + Polaris and Databricks Unity Catalog. Different cloud, same thinking.

---

## 9.3 ETL: Deciding "Fresh Enough" and "Accurate Enough"

Ontology defines what an object looks like; ETL solves how that object gets assembled out of 5 systems.

I never debate "which ETL tool is best" on customer site. The order of judgment is reversed — **answer the SLA first, then the tool**.

I work in three SLA tiers:

```
  T+1 (next day)        ──→ 90% of projects, this tier is enough
                            Fits: weekly / monthly reports, history,
                                  customer-service RAG
                            Engineering baseline: 1x

  T+1h (hourly)         ──→ Roughly 8% of projects need this
                            Fits: business adjusts in the morning,
                                  wants to see results in the afternoon
                            Engineering baseline: 2-3x (incremental sync)

  Real-time (seconds)   ──→ Less than 2% of projects truly need this
                            Fits: risk control / recommendations /
                                  online status / inventory contention
                            Engineering baseline: 5-10x (CDC + streaming)
```

That spare-parts inventory at Hesheng — I asked Chen Xue once: "If the system recommends a part to an engineer, but inventory has actually been booked by another site, how long can you tolerate before discovering that?" She thought for a second: "A few hours. If a dispatch goes out in the morning, being able to fix it in the afternoon is fine."

That's T+1h. Not real-time. We saved ourselves a whole CDC pipeline.

In engineering reality, **jumping straight to a real-time pipeline is one of the most common holes the FDE falls into**. I personally fell into it on my second FDE project — the customer offhandedly said "ideally real-time," I didn't circle back to verify, I built out Kinesis + Flink end to end, and three weeks later realized what the business actually needed was "fixable in the morning, fixable in the evening." Three weeks wasted. Since then I've made it a habit: **for any "real-time" requirement, I ask back "could you accept a half-hour delay?", and if yes, I drop it one tier**.

Once the SLA is set, you pick the tool by scenario. I've drawn a quick-decision table; Hesheng went with row 1:

| Customer scenario | Recommended stack | Notes |
|---|---|---|
| AWS + transforms in warehouse | dbt + Redshift / Athena | First choice for 80% of projects, SQL-only |
| AWS + Spark-friendly | Glue / EMR + Iceberg | Glue suits customers who prefer serverless |
| AWS + simple scheduling | Step Functions + Lambda | Cheapest when data volumes are small and logic is simple |
| AWS + real-time | MSK / Kinesis + Flink/Firehose | Only if it has to be real-time |
| Customer on Snowflake | dbt + Snowflake | Same as above, different warehouse |
| Customer on Databricks | dbt + Databricks or pure PySpark | Depends on team style |

We ended up with dbt + Redshift. Hesheng's Redshift had been running two years; dbt was introduced by the data team last quarter (before that it was a pile of views), and the Agent project was a good occasion to systematize the customer_360 migration. The dbt project structure on Hesheng's side ended up like this:

```
  models/
    staging/
      stg_crm__customers.sql      -- clean CRM raw tables
      stg_erp__customers.sql      -- clean ERP
      stg_svc__tickets.sql        -- clean after-sales tickets
      stg_finance__clients.sql    -- clean finance
    intermediate/
      int_customer__id_mapping.sql   -- stitch customer_id across 4 systems
      int_ticket__enriched.sql       -- enrich tickets with asset + customer
    marts/
      dim_customer.sql            -- the customer object in Ontology
      dim_asset.sql
      fct_ticket.sql

  tests/
    not_null_customer_id.yml
    unique_customer_id.yml
    referential_asset_to_customer.yml
```

dbt at this layer has three benefits that map directly to FDE pain points: **SQL-only** (the team doesn't have to learn a new language), **lineage built in** (`dbt docs serve` visualizes it), **tests built in** (uniqueness / not-null / referential integrity / accepted values). The third matters most — what an Agent project fears most isn't "today the data is wrong," it's "today the data is wrong and nobody knows." Three dbt tests per main table is now my default on every project.

---

## 9.4 Data Lineage: 5 Minutes vs 5 Days When Failures Happen

Two weeks before Hesheng went live, we hit a small incident. A dbt model `dim_customer` suddenly had an extra row — a `customer_id` had been renamed in CRM, then renamed back, and that triggered an edge-case bug in a left join in the staging layer. The downstream Agent prompt picked up a record where "customer name = NULL" and pushed an absurd dispatch suggestion to an engineer.

Chen Xue @ed me in the Slack channel: "Why is this ticket assigned to the electrical group?" I traced from this ticket back to the Agent's prompt, then back to the customer info the prompt referenced, then back to that one row in `dim_customer` — the whole walk took 4 minutes thanks to dbt's built-in lineage.

If there had been no lineage — I'd have had to open CRM, ERP, the finance system, and Redshift's view definitions one by one and reconcile by hand. Conservative estimate: half a day.

This is why "wire up lineage" isn't a nice-to-have; it's one of the first-week actions for the FDE. The minimum bar:

- **dbt projects**: built in by default, just run `dbt docs generate` + `dbt docs serve` and share the link with the customer and your team
- **Glue / Airflow non-dbt jobs**: install the OpenLineage hook and ship lineage to Marquez or DataHub
- **Bedrock Agent calling Athena**: write the query and the returned `query_id` into CloudWatch Logs — that's the last mile of lineage

Commercial products (DataHub Cloud, Atlan, Foundry) are worth it for compliance-heavy customers — they bundle IAM, audit, and cross-cloud lineage. But for a customer at Hesheng's scale, dbt's built-in is enough. **Don't deploy heavy tooling where the customer doesn't need it** — that's a boring but valuable bit of FDE judgment.

---

## 9.5 PII and "the Minimum 5 Things Before Going Live"

Hesheng does B2B tickets, so PII looks light — but customer data still contains contact phone numbers, emails, signatory names. Several Southeast Asian countries have data localization requirements (Indonesia PP 71/2019, Vietnam Cybersecurity Law). On the compliance side we confirmed with Gu Jianguo: customer data does not leave ap-southeast-1.

For PII handling we did three things:

```
  1. PII fields tagged in Glue Data Catalog with LF-Tag: PII=yes
  2. dev environment: column-level hash mask via Lake Formation
  3. prod environment: only the IAM role used by the Agent gets access,
     traffic stays inside the VPC via VPC endpoint
```

Three sentences went into the SOW — very concrete: IAM role names, LF-Tag names, VPC endpoint IDs. **PII controls written in the SOW must be engineering-verifiable**; "strictly protect customer privacy" is useless. Writing "customer data access is controlled by IAM role `hesheng-agent-runtime-role` + LF-Tag `PII=yes`, dev environment uses hash masking" gives you something to put in front of an auditor.

Before the data engineering goes live, the FDE has to clear at least these 5 items — this isn't a "complete governance regime," it's the minimum bar for a typical B2B customer like Hesheng:

```
  1. Each main table has an owner (person + email)
  2. All PII fields have LF-Tags, dev environment masked
  3. Schema changes go through PR review, downstream notified
  4. At least 3 dbt tests per main table
  5. Lineage wired up (can answer "where did this number come from"
     in 5 minutes)
```

If any of the 5 are missing → the Agent walks into a minefield on day one. This isn't fearmongering — on a previous project I skipped item 4 (dbt tests). In week 3 of go-live, an upstream library schema change altered a column type; the downstream Agent silently picked up nulls; three days later the business side noticed during reporting. After that incident I wrote those 5 items into my own checklist, and I run it once per new project.

---

## 9.6 Stitching 9.1-9.5 Together: What Hesheng's Phase Actually Looked Like

Back to Hesheng's ticket Agent. From week 3 to week 5, the actual data-engineering timeline was:

**Week 3 (data profile + Ontology)**

- Monday morning: drew the 5-layer data map with Chen Xue and Gu Jianguo
- Monday afternoon to Wednesday: walked Chen Xue through the 4 Ontology business questions, settled on Customer/Asset/Ticket/Engineer as the 4 objects
- Thursday and Friday: Chen Xue and customer-service reps hand-fixed the customer_id mapping (200+ rows); I registered the 4 Ontology v1 tables in Glue Data Catalog with LF-Tags

**Week 4 (dbt models + tests)**

- Monday and Tuesday: wrote the staging layer (cleaning the 4 systems) and the intermediate layer (id mapping + ticket enrichment)
- Wednesday: wrote the marts layer's `dim_customer` / `dim_asset` / `fct_ticket`
- Thursday: added 5-7 dbt tests per main table (uniqueness / not-null / referential / accepted-values)
- Friday: ran `dbt docs generate`, sent the lineage link to the customer

**Week 5 (spare-parts inventory T+1h + Agent integration)**

- Monday and Tuesday: spare-parts inventory (Excel) goes through Glue crawler + Athena, with a Step Functions pipeline running every 4 hours (not real-time)
- Wednesday: Bedrock Agent connects to the Athena tool and can query `dim_customer` + `dim_asset` + `fct_ticket`
- Thursday: ran eval-v1 (200 rows), found the NULL issue from the `dim_customer` left join (the 9.4 incident)
- Friday: fixed it, added the corresponding dbt test, re-ran the eval set above the go-live threshold

The whole data-engineering effort consumed three weeks. If we had built the spare-parts inventory in real-time in phase one, that would have added at least two weeks by my experience — and the business didn't actually need it.

## 9.7 End-to-end demo: from dirty data to an agent

9.1-9.6 above were narrative. This section gives an end-to-end demo **you can reproduce in your own AWS account** — turning the chapter's judgment calls into runnable code. Full code lives in the repo under `demos/ch9-data/`, tear it down right after, single-run cost < $1.

The synthetic data is generated in Hesheng's style: 200 pieces of equipment, 500 tickets, 300 dispatch records, **deliberately dirty at both the surface and the semantic layer** — three timestamp formats mixed (67% iso8601 / 22% Chinese format / 11% Unix epoch), 9 different namings for the priority field (P1/high/1 / P2/medium/2 / P3/low/3), 6 different namings for the team field (机械组/Mech/M-team / 电气组/Elec/E-team), two prefixes for part_id (P-101 / PART-101), and 36 tickets referencing equipment IDs that don't exist (broken FKs).

Running the full pipeline:

```
01-generate-data.py    →  3 CSVs written locally
02-setup-aws.py        →  S3 + Glue Crawler + Glue DB
                          (the crawler fails on tickets/work_orders the
                           first time because Chinese fault_desc in the
                           CSV contains commas)
04-explicit-schema.py  →  fix by explicitly registering an OpenCSVSerde
                          schema (this is a real first-week FDE pothole)
05-explore-athena.py   →  6 Athena queries that expose every shape of
                          dirty data
06-build-ontology.py   →  4 SQL views that fold the dirty data into an
                          ontology (ticket_clean / equipment_clean /
                           work_order_clean / ticket_resolution)
07-create-kb.py        →  uploads 5 repair manuals (but this phase does
                          not put them in a KB; we use prompt-stuffing
                          instead — < 30 small manuals don't justify a KB)
08-agent-with-athena-tool.py
                       →  Claude Haiku 4.5 + a single SQL tool, answers
                          4 Hesheng-style business questions
09-teardown.py         →  tears everything down
```

Real numbers from the run (measured 2026-05-25 in us-east-1):

**Athena exploration phase** — 6 queries, scanned data volume < 0.1 MB each (the dataset is small), average engine time 600ms. Athena prices at $5/TB scanned, so the entire exploration phase costs < $0.01.

**Ontology view construction** — 4 views; the most complex one, `ticket_resolution`, contains a LEFT JOIN plus a subquery and takes 858ms to create. Each query re-executes on demand without pre-materialization (appropriate for Hesheng's data scale; consider materializing once you reach TB scale).

**Agent live conversation** (excerpt from the first question):

```
USER: 过去 90 天里 Singapore 站点 P1 工单的平均解决时间是多少?
      (What's the average resolution time for P1 tickets at the Singapore
       site over the past 90 days?)

  TOOL CALL: query_tickets(
    SELECT AVG(total_hours), COUNT(*) ... INTERVAL '90' day ...)
  TOOL RESULT: ERROR — Trino doesn't support INTERVAL syntax this way
  TOOL CALL: query_tickets(
    SELECT ... ts_utc >= date_add('day', -90, current_date) ...)
  TOOL RESULT: avg_resolution_time_hours=5.26, p1_ticket_count=9

AGENT: Over the past 90 days the Singapore site had 9 P1 tickets, with
       an average resolution time of 5.26 hours. On top of the SLA's
       4-hour on-site arrival window, only 1.26 extra hours were spent
       on field troubleshooting — meaning the field engineers' emergency
       response and diagnosis efficiency is high.
```

Note the first SQL fails and the agent self-corrects on retry. This is the **kind of fault tolerance you really do see** when an agent is wired to a SQL tool — Trino dialect quirks, field-type mismatches, stale views all surface as tool-call failures. In production you'll want to give the tool a more precise schema description so the model gets it right on the first try, but this very capability (the agent catching its own mistakes and fixing them) is one of the core values of LLM applications.

**Full agent answers across the 4 questions** (see the repo `demos/ch9-data/` for details):

| Question | Agent answer |
|---|---|
| Singapore P1 average resolution time | 5.26 hours (9 tickets), with SLA interpretation |
| ALM 4501 site distribution | Ho Chi Minh 19 / Bangkok 14 / Jakarta 13 / Singapore 11 / KL 10 / data missing 6, plus a business inference |
| How many tickets reference non-existent equipment | 36 tickets = 7.2%, plus a governance recommendation |
| Jakarta tickets exceeding SLA this month | Honestly says "no data for this month" and asks back to clarify the time window |

**The most valuable takeaway from this section**: going from 200 rows of dirty data to an agent that can answer business questions in business language, end-to-end on AWS data services, took 8 scripts, single-run cost < $1, and a team engineer can run it from scratch in 30 minutes. **This is what data engineering "ready for an LLM to use" looks like** — not putting up OpenSearch, not a major ETL overhaul, but Athena views plus a single SQL tool.

When do you upgrade to KB / AgentCore Runtime / Gateway? Three signals:

1. **More than 30 manuals or weekly updates** → move to Bedrock Knowledge Base (this phase, 5 prompt-stuffed manuals are enough)
2. **Agent needs cross-session state or long-running tasks** → move to AgentCore Runtime (this phase is 30-second Q&A turns, Lambda is enough)
3. **Multiple BU teams plug into the same agent** → move to AgentCore Gateway (this phase is a single team, plain Converse tool use is enough)

None of the three signals applies to Hesheng's phase one. Chapters 14 and 15 will lay out the judgment and path for upgrading to AgentCore in phase two.

---

## Wrapping Up

Data engineering isn't the showiest part of an FDE project — talk RAG, Agents, model comparisons in the conference room and the business side's eyes light up; talk Ontology, dbt tests, PII tagging, and they want to scroll their phones. But **80% of Agent go-live incidents have their root cause in the data layer** — if you can't fix Ontology inconsistencies, even the best model will just confidently misstate the chaos.

These days, the first week on every customer site I make sure to: draw the 5-layer data map, walk the Ontology with the business side once, look at the PII status. Each of the three takes 1-2 hours, all done within the same week. Once they're done, I have a rough sense of whether this project can ship and how long it'll take. If you take over a customer with a chaotic data stack and you're being pushed to demo an Agent in week 2 — that's a red light. The next chapter is on a related topic: how the FDE works inside the customer's network-isolated environment.

---

## Public references cited in this chapter

- A. Lawrence, *Forward Deployed Engineer Rule Book* (public GitHub document)
- Palantir engineering blog — *Ontology* series
- AWS docs — *Lake Formation Tag-Based Access Control*, *Glue Data Catalog cross-account*
- AWS docs — *Amazon MSK best practices*, *Kinesis Data Firehose*
- dbt official docs — *Tests*, *Documentation and Lineage*
- OpenLineage / Marquez project documentation
- Indonesia PP 71/2019, Vietnam Cybersecurity Law (public data localization compliance materials)

[← Part IV intro](../intro/) · [Next: Working in the customer's VPC →](../chapter-10/)
