---
title: "part-4/chapter-09.md"
nav_exclude: true
search_exclude: false
---

# Chapter 9: The Customer Data Stack — Ontology / ETL / Real-Time Pipelines

## Opening

```
A financial-services customer. The FDE's LLM Agent demo runs beautifully,
but it has to ship to production.

The first week of data integration is brutal:
  - Five customer databases: PostgreSQL (primary) + Oracle (contracts) +
    SQL Server (finance) + MongoDB (logs) + a shared drive of Excel (30%)
  - Primary keys disagree: CRM uses customer_id, ERP uses cust_no,
    finance uses client_code, no mapping table exists
  - Time zones disagree: UTC + Asia/Shanghai + customer's local TZ, mixed
  - One critical report pulls from 4 systems,
    each with a different definition of "customer"

The FDE walks away with one line:
  "80% of the engineering before an Agent goes live is data governance.
   Skip data governance and ship the Agent anyway,
   and the smarter the Agent the more confidently
   it will splice inconsistent data into a wrong answer."

This chapter is about taking a customer's data stack
from "scattered everywhere" to "an Agent can call it safely."
```

---

## 9.1 The Typical Shape of a Customer Data Stack

```
        The "5 layers" of a customer's data
        ─────────────────────────────────────

  L1 Operational databases (OLTP)
     - PostgreSQL / MySQL / Oracle / SQL Server
     - Primary store for business systems

  L2 Data warehouse / data lake (OLAP)
     - Snowflake / Redshift / BigQuery / Databricks / Iceberg
     - Where analytics runs

  L3 Middle layer (Data Mart / Cube)
     - dbt models / homegrown views
     - The "canonical definition" of business metrics

  L4 BI / dashboards
     - Tableau / Power BI / Quicksight / Looker

  L5 Business apps / Agents / APIs
     - Where data is consumed (most FDE work lives here)
```

**In Week 1, the FDE should draw a "5-layer data diagram"** and pin down what the customer actually has.

---

## 9.2 Ontology — Unifying What's Scattered

Ontology is the concept Palantir introduced and popularized. At its core it is a unified definition of **business objects + relationships + properties**.

```
              The 3 components of an Ontology
              ───────────────────────────────

  Object:
    Customer / Order / Product / Contract / Employee
    Each object has a "gold-standard definition"

  Property:
    Customer.id, Customer.name, Customer.tier
    Each property has a source-of-truth

  Relationship:
    Customer 1:N Order
    Order 1:N OrderItem
    Order N:1 Salesperson
```

### The 4 questions an Ontology has to answer

```
1. Who counts as a "customer"?
   - The CRM record? The paying entity? The contract counterparty?
   - Different departments answer differently → must be unified

2. Which ID is the canonical one?
   - The CRM's customer_id?
   - The contract counterparty's unified_party_id?
   - One ID has to be the gold ID

3. How is the mapping built?
   - Most of the time it's a hand-curated table
   - There is no silver bullet

4. Who has authority to change the Ontology?
   - Without an owner you'll see "A renames a field today,
     B renames it back tomorrow"
```

### AWS in practice: a lightweight Ontology with Lake Formation + Glue Data Catalog

AWS doesn't ship a full "Ontology framework" the way Palantir does, but Glue + Lake Formation give you a workable lightweight version:

```
        Glue Data Catalog as the Ontology registry
        ───────────────────────────────────────────

  Database: customer_360_ontology

  Table: customer  (← business object definition)
    Columns:
      - customer_id    (string, gold ID)
      - source_systems (struct: crm_id, erp_no, finance_code)
      - tier           (string)
      - tags           (LF tags: PII, region=APAC)

  Table: order
    ...

  ↓
  Lake Formation Tags (LF-Tags):
    - PII: yes / no
    - sensitivity: public / internal / restricted
    - region: APAC / EMEA / NA

  ↓
  IAM roles + LF-Tags decide who can query which fields
  on which object
```

**Why this works**:

- Ontology metadata is maintained in Glue
- Permissions are maintained via LF-Tags + IAM
- Athena / Redshift / EMR can all query it
- Bedrock Knowledge Bases reads Glue metadata directly

> **AWS reference**: search "AWS Lake Formation tags" and "Glue Data Catalog cross-account."

---

## 9.3 ETL — Making the Data Flow

ETL (Extract / Transform / Load) is the engineering of L1 → L2 → L3.

### The 3 engineering signals for ETL

```
  Is the data "fresh enough"? → look at the SLA
    - T+1: next-day (covers 90% of projects)
    - T+1h: hourly (when latency matters)
    - Real-time: seconds (only CDC can deliver this)

  Is the data "accurate enough"? → look at quality tests
    - Primary key uniqueness
    - No nulls where there shouldn't be
    - Numeric values within sane ranges
    - Business rules (order amount > 0)

  Is the data "stable enough"? → look at the dependency graph + monitoring
    - When upstream fails, downstream should fail gracefully
    - Failures must alert
    - Reruns must be idempotent
```

### ETL tooling cheat-sheet

```
                    Scenario → recommended tooling
                    ──────────────────────────────

  Cloud + Spark family   Databricks / EMR + Delta
                         AWS Glue (serverless-friendly)

  Cloud + warehouse-     dbt + Snowflake / BigQuery / Redshift
  native

  Cloud + streaming      Kafka + Kinesis Data Streams + Flink

  Self-hosted / offline  Airflow + Spark + Iceberg

  Small / simple         AWS Step Functions + Lambda + S3
```

### dbt is the FDE's "Swiss Army knife"

If the customer runs a cloud warehouse, **80% of your ETL will be written in dbt**:

```
        Standard dbt project structure
        ──────────────────────────────────

  models/
    staging/
      stg_crm_customers.sql        (clean raw)
      stg_erp_customers.sql
    intermediate/
      int_customer_unified.sql     (joins / mappings)
    marts/
      dim_customer.sql             (business-object layer)
      fct_orders.sql

  tests/
    not_null_customer_id.yml       (data quality)
    unique_customer_id.yml

  macros/
    pii_mask.sql                   (reusable logic)
```

Why dbt:

- SQL-only (the FDE doesn't have to learn a new language)
- Built-in lineage (data lineage visualized for free)
- Built-in testing (uniqueness / not-null / accepted-values)
- Git-managed + code review (data engineering becomes engineering)

---

## 9.4 Data Lineage — The Lifeline of Failure Diagnosis

```
        Without lineage:
        "downstream report is wrong" → one person hunts through 5 systems
                                       for 3 days

        With lineage:
        "downstream report is wrong" → 5 minutes to see which upstream ETL
                                       changed schema
```

### Tools

```
  Open source:
    - OpenLineage (supported by dbt / Airflow / Spark)
    - Marquez (the OpenLineage backend)

  Commercial / cloud:
    - DataHub
    - Atlan
    - AWS Glue (has a lineage view)
    - Unity Catalog (Databricks)
    - Foundry (Palantir)
```

### The FDE's minimum bar

Don't try to instrument "the whole company's lineage," but **every dbt model / Glue Job you write must emit lineage**:

```
1. dbt: lineage is generated automatically (dbt docs serve)
2. Airflow / Glue: install the OpenLineage hook
3. When something breaks, the first move is to read the lineage
   and find the root cause
```

---

## 9.5 Real-Time Data Pipelines — Use Sparingly

### When you genuinely need real time

```
  ✓ Business flow demands sub-second feedback (risk / recommendation / ad bidding)
  ✓ Decision windows are short (inventory / pricing)
  ✓ User-perceptible (presence / real-time notifications)

  → If 1 of these holds, consider real time
  → If none hold → use T+1 and save 70% of the engineering
```

### The engineering traps in a real-time pipeline

```
  ❌ Going real-time on day one → debugging hell
  ❌ No idempotency → replays produce wrong data
  ❌ No schema-evolution plan → any upgrade breaks it
  ❌ No dead-letter queue → one bad record blocks everything
  ❌ No lag monitoring → you find out from a user complaint
```

### AWS in practice: the MSK + Kinesis + Firehose trio

```
        Typical AWS real-time pipeline
        ─────────────────────────────────

  Producer
    ↓
  MSK (Managed Kafka) or Kinesis Data Streams
    ↓
  Consumer choice:
    A. Lambda processes directly (low traffic)
    B. Flink on EMR / KDA (high traffic + complex logic)
    C. Kinesis Firehose lands directly to S3 / Redshift
    ↓
  Downstream: S3 (Iceberg) / Redshift / OpenSearch
```

For simple cases use Firehose (auto buffering + compression + S3 partitioning); for complex logic use Flink.

> **AWS reference**: search "Amazon MSK best practices," "Kinesis Data Firehose."

---

## 9.6 The "Minimum 5 Things" of Data Governance

This is not a "complete data governance system" — it's the bare minimum the FDE has to put in place on customer site:

```
1. Data ownership table
   Every table / dbt model has one owner (person + email)

2. PII tagging
   Which fields are PII; they must be tagged and masked in dev

3. Schema-change process
   Adding a field: notify + document
   Changing a type / dropping a field: review + notify downstream

4. Test coverage
   Every primary table has at least 3 dbt tests
   (uniqueness / not-null / referential)

5. Lineage visualization
   You can answer "where did this number come from?" in 5 minutes
```

**Miss any of the five and the Agent is walking onto a minefield.**

---

## 9.7 A Real End-to-End Example

```
  Customer: an insurance company
  Agent's job: automated underwriting (applicant risk assessment)

  Data needs (surfaced by the FDE in Discovery):
    - Applicant basic info (CRM)
    - Historical claims (claims system, Oracle)
    - Health declaration PDFs (scans + OCR)
    - Blacklist (compliance system, SQL Server)
    - Credit score (external API)

  → 5 systems: 4 internal + 1 external

  The FDE's engineering plan:
    Week 1: Register the 4 internal systems in Glue Data Catalog
            Build a customer Ontology (unified customer_id mapping)
    Week 2: Write dbt models to merge the 4 systems' customer data
            into customer_360
            Apply LF-Tags (mask PII fields)
    Week 3: Lambda + EventBridge to pull external API credit scores
    Week 4: Bedrock Agent calls Athena to query customer_360
            + calls Lambda for credit + calls OCR
    Weeks 5-6: Eval + canary

  Key engineering moves:
    - No real-time pipeline (Discovery confirmed T+4h was acceptable)
    - Glue Data Catalog as the Ontology (lightweight)
    - All PII fields masked in dev
    - Every dbt model has an owner + tests
```

---

## Key Quotes

> "*The Ontology is the contract between data engineering and the rest of the company.*"
> — Palantir Blog, *On Ontology*, 2024

> "*Most LLM hallucinations are actually data quality problems wearing a costume.*"
> — A. Lawrence, *FDE Rule Book*, 2025

> "*If you can't explain where the number came from, the customer can't trust the answer.*"
> — AWS GenAI Innovation Center, 2025

---

## Action Checklist

When you walk into a data-heavy FDE project, weeks 1-2 must include:

1. **Draw the customer's "5-layer data diagram"** (§9.1)
2. **Identify the source-of-truth for 3 core business objects** (customer / order / product)
3. **Stand up a Glue Data Catalog database** (even for a PoC)
4. **Tag every table with owner + LF-Tags (PII / region / sensitivity)**
5. **Write a unified view like customer_360 in dbt**
6. **Wire up OpenLineage** (dbt has it built in)
7. **Decide the SLA**: T+1 / T+1h / real-time (default to T+1; if T+1 works, ship T+1)

---

## Anti-Pattern Checklist

- ❌ **Skipping Ontology and plugging an Agent straight in** (the Agent will confidently splice inconsistent data into wrong answers)
- ❌ **Connecting 5 systems directly without unification** (any small upstream change breaks everything)
- ❌ **Tables without owners** (a schema change ships and nobody downstream is told)
- ❌ **Real-time pipeline in v1** (10x debugging cost, often not worth it)
- ❌ **Real PII in dev** (the most common compliance incident)
- ❌ **dbt project with no tests** (you only learn about bad data when downstream complains)
- ❌ **No lineage** (data-issue triage goes from 5 minutes to 5 days)

---

## Bridge to the Next Chapter

You have the data stack — but most customers won't let you use cloud "out-of-the-box" services. The data has to live inside the customer's VPC / private deployment / offline data center. The next chapter covers the FDE's engineering moves inside network-isolated environments.

[← Part IV intro](intro.md) · [Next: Working in the Customer's VPC →](chapter-10.md)
