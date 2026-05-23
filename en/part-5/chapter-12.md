# Chapter 12: PoC Pass-Line Conditions — What Makes It, What Stalls Out

## Opening

```
A SaaS company. The FDE delivers a PoC in week 6, and the results are stunning:
  - Customer CEO applauds at the demo
  - Eval composite score 0.91
  - The press even covers it

Week 7, the customer's IT director asks: "How do we get to production?"
The FDE answers: "Just deploy this demo."

Week 14, still not live.
What's blocking it?

  - No staging environment (the demo was a modified dev)
  - No deploy scripts (the demo was started by hand)
  - No load tests (1 request per second is the ceiling)
  - Not wired into customer monitoring (ops doesn't know how to on-call)
  - Cost budget not approved ($20K/month, leadership hadn't planned for it)
  - No canary plan (only "all or nothing")

Postmortem: during the PoC stage, the "6 things for productionizing"
were not done in parallel.
The flashier the PoC, the harder the path to production.

This chapter gives: the 6 things to do during the PoC stage,
plus the 4 signals that "guarantee a stall."
```

---

## 12.1 PoC vs Production — Engineering Bars Differ by 100x

```
                    PoC bar                Production bar
                    ─────────              ──────────────

  Concurrency       single user / a few    100–10K QPS

  Availability      "good enough to demo"  99.5% / 99.9%

  Latency           P50 of 5s acceptable   P95 < 3s

  Fault tolerance   "restart on error"     auto-retry + isolation

  Observability     console.print          full-trace tracing

  Permissions       FDE's admin in hand    RBAC + audit

  Data              "give me 50 rows"      full + real-time

  Cost              boss didn't say        monthly budget control

  Releases          "I edit the prompt"    CI/CD + canary

  Customer          FDE always there       customer ops runs it solo
```

**90% of PoC failures aren't technical — they're about how far the "engineering bar" is from production**.

---

## 12.2 The 6 Things to Do During the PoC Stage

### Thing 1: Environment Tiers (dev / staging / prod)

```
        Split from day 1:
        ──────────────────────────────────────

  dev:        FDE's workbench, change anything
  staging:    same config as prod, runs regression
  prod:       customer ops manages, strictest

  Even at PoC stage, staging is a must
  Otherwise: "no one remembers the prompt change from the demo"
              → can't find it at launch
```

### Thing 2: Wire Up CI/CD in Week 1

```
        Minimum CI/CD pipeline:
        ──────────────────────────────────────

  on push to feature branch:
    - lint
    - unit test
    - eval (50 seed cases)

  on PR to main:
    - eval (200 golden cases)
    - integration test
    - cost estimate

  on merge to main:
    - auto-deploy dev
    - trigger staging deploy

  on tag release:
    - deploy staging
    - wait for human sign-off
    - canary deploy prod (10% → 50% → 100%)
```

**A PoC without CI/CD shouldn't enter PoC**.

### Thing 3: Wire Up Monitoring / Trace in Week 1

```
  4 must-have trace dimensions:
    1. Latency (per step)
    2. Cost (input/output tokens, model)
    3. Quality (eval / user feedback)
    4. Error (stack trace + correlation_id)

  Tooling (review Ch 6):
    - Cloud: LangFuse Cloud / LangSmith / Bedrock built-in
    - Private: LangFuse self-host / Phoenix
```

### Thing 4: Cost Transparency (Start Reporting at PoC Stage)

```
        Weekly report must include:
        ──────────────────────────────

  - This week's token spend (input + output)
  - Distribution by model
  - Distribution by scenario (RAG / Agent / Eval)
  - Average cost per request
  - Monthly extrapolation

  Start at PoC stage → no "we burned $50K in the first week
  and the boss is shocked"
```

### Thing 5: Customer Ops "On the Bus"

```
        Starting in week 4:
        ────────────────────────────────────

  - At least 1 customer ops engineer joins the project Slack
  - On-call together (even if not real on-call during PoC)
  - Watch the dashboards together
  - Handle alerts together

  Not on the bus: at launch, customer ops "takes over" =
                  starts from zero, 3 months to be self-sufficient
  On the bus:     at launch, customer ops is already familiar,
                  handoff in 1 week
```

### Thing 6: Degradation Plan (Fallback)

```
        Critical paths must have a fallback:
        ────────────────────────────────────

  Bedrock model down → switch to backup model (cross-region)
  Knowledge Base down → switch to cached embeddings
  Agent tool down → reject request + friendly error
  All down → static reply + ticket created

  At PoC stage at minimum:
    ✓ Write one "everything down" backstop
    ✓ Run one "everything down" drill
```

---

## 12.3 The 4 Signals of "Guaranteed Stall"

### Signal 1: No One on the Customer Side Wants to Be Owner

```
        Projects where "who owns this" has no answer:

  ✗ Business says "this is IT's problem"
  ✗ IT says "this is the business's problem"
  ✗ Leadership says "both sides own it together"

  → After launch: no one to on-call, no one to review prompt changes,
                  no one to update the KB
  → "Natural death" within 6 months
```

**FDE's move**: Hard-write "customer-side owner" into the SOW. No owner, no kickoff.

### Signal 2: Eval Set Is Written Solo by the FDE

```
  FDE writes 200 Eval cases alone →
  After launch, customer business experts say
  "these aren't the questions we care about"
  → Eval set fully redone
  → Launch slips 2–4 weeks

  Move: Starting in week 3, pull in customer business experts
        to label together.
        FDE writes v1 → business experts review → re-label
```

### Signal 3: Cost Calculated Only at Month-End

```
  Demo stage: $500/month
  Week 1 of launch: $5K
  Customer leadership sees the bill: "We can't run this. Cut it."

  Move: In PoC week 2, give leadership the first cost projection.
        Before launch, give a "cost curve at 3 different scales."
        After launch, weekly cost dashboard.
```

### Signal 4: Customer IT Did Not Attend Any PoC Review

```
  6-week PoC entirely with the business side, zero IT involvement.
  At launch, IT vetoes:
    "VPC Endpoint not wired up"
    "Audit logging doesn't meet our bar"
    "Won't pass our compliance review"
  → Tear down, start over.

  Move: Bring IT in as early as week 1 Discovery.
        IT-FDE sync every two weeks.
        Starting in week 4, IT attends demos.
```

---

## 12.4 The 5 Hard Metrics for PoC Pass-Line

Write these 5 into the SOW. Miss any of them, no production:

```
┌─────────────────────────────────────────────────────────────────┐
│  Metric                      Pass-Line Condition                 │
├─────────────────────────────────────────────────────────────────┤
│  Eval composite score        ≥ SOW-agreed value (typically 0.85)│
│  Production-scenario load    P95 < 3s, 100 QPS stable for 30 min│
│  Cost                        Cost per request ≤ budgeted X      │
│  Audit                       100% of calls logged to CloudTrail │
│  Canary plan                 Can shift 1% / 10% / 50% / 100%    │
└─────────────────────────────────────────────────────────────────┘
```

**5 of 5 pass → enter canary production**. Miss 1 → defer.

---

## 12.5 A Real PoC → Production Timeline

```
        Typical 12-week project timeline
        ──────────────────────────────────────

  W1-2  Discovery (Part II)
        - 5 deliverables: report / Eval seed / SOW
        - Customer owner / IT onboarded / security review

  W3-6  Scaffolding (Part III)
        - 6.7 quick-decision-table baseline
        - Eval CI wired up (Ch 8)
        - First demo

  W6    Mid-PoC checkpoint
        - First run of the 12.4 hard metrics
        - Which ones miss?

  W7-9  Productionize Phase 1
        - Data integration + VPC + SSO + audit (Part IV)
        - Monitoring + cost + canary prep (Ch 13)

  W10   Final PoC checkpoint
        - All 5 hard metrics from 12.4 pass
        - Three-way sign-off: customer IT + business + leadership

  W11   Canary rollout (10% → 50%)

  W12   100% live
        + Handoff (Ch 16) kicks off
```

**Pacing matters more than feature completeness**.

---

## 12.6 A Real Counter-Example

> *An internet company's FDE team built an 8-week LLM customer-service PoC.
> In week 8 the customer CEO saw the demo, was satisfied, and was ready to sign a 12-month contract.*
>
> *During the PoC, the following were not done:*
> *- Customer SSO not integrated (used a service account)*
> *- CloudTrail not wired up (said "we'll add it after launch")*
> *- No load testing (demo was at 1 QPS)*
> *- No architecture sync with customer IT (IT first saw the diagram right before signing)*
>
> *After signing, the IT department spent 3 weeks reviewing the architecture and filed 47 change requests.
> Rework took 5 weeks.*
>
> *Customer business side: "You promised an 8-week launch — why are you still iterating at week 16?"*
>
> *The FDE team lost the next-phase renewal.*

**Postmortem**: During a PoC, **business-side approval ≠ project ready to ship**. **If IT / security / compliance / finance — any one of them — is not satisfied, the project can be torn down and restarted**.

---

## Key Quotes

> "*The PoC is not the project — it's the trailer for the project.*"
> — A. Lawrence, *FDE Rule Book*, 2025

> "*A 73% PoC-to-production conversion rate doesn't come from better models. It comes from running PoC like it's already production.*"
> — AWS GenAI Innovation Center, 2025

> "*Every PoC has a critic — find them in week 1, not week 8.*"
> — Bob McGrew @ YC, 2025

---

## Hands-On Checklist

In week 1 of a PoC, do these:

1. **Write the "5 hard pass-line metrics" into the SOW** (section 12.4).
2. **On day 1, split dev / staging / prod into three environments**.
3. **Wire up CI/CD in week 1** (Eval + lint + deploy).
4. **Wire up trace + cost dashboard** (CloudWatch or LangFuse).
5. **Pull IT / security / finance / business owners into the project channel**.
6. **Starting in week 4, customer ops watches dashboards alongside the FDE**.
7. **In week 6, run a "pretend launch" drill** (cost projection + load test + failure drill).

---

## Anti-Patterns

- ❌ **Treating the PoC as a "demo build"** (everything has to be redone for prod).
- ❌ **Demoing straight from dev** (no staging).
- ❌ **No monitoring / audit / SSO during the PoC** (saying "we'll add it after launch").
- ❌ **Customer IT not in the project channel** (vetoed at the last minute).
- ❌ **Cost calculated only after launch** (leadership doesn't approve, project dies suddenly).
- ❌ **No canary plan, only 0% / 100%** (no graceful rollback when things go wrong).

---

## Relation to the Next Chapter

This chapter gave the "5 hard metrics for PoC pass-line." The next chapter goes into the engineering practice of the production "four-piece set": observability / cost / canary / rollback.

[← Part V Intro](intro.md) · [Next: Observability / Cost / Canary / Rollback →](chapter-13.md)
