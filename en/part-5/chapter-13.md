# Chapter 13: Observability / Cost / Canary / Rollback

## Opening

```
A retail customer's Agent, day 3 of production, 2 AM:

  P1 alert: Agent error rate 18% (baseline < 0.5%)

  The customer's on-call ops engineer calls the FDE:
    "Your Agent is broken. What do we do?"

  What the FDE should be thinking:
    1. Look at trace → find root cause (within 5 minutes)
    2. Shift 1% of traffic back to the old version → stop the bleeding (within 2 minutes)
    3. If that doesn't work, shift 100% back (within 1 minute)
    4. After fixing, canary back up → controlled

  What actually happens (bad case):
    1. No trace wired up → can't tell which step failed
    2. No canary lane → either tough it out or take everything offline
    3. No baseline → can't tell whether it really is "worse than usual"
    4. 1 hour of fumbling → the customer is watching

The "four-piece set" this chapter covers — observability / cost / canary / rollback —
exists so that at 2 AM you can stop the bleeding in 5 minutes.
```

---

## 13.1 Observability — Not Just "Reading Logs"

```
        Three observability dimensions
        ───────────────────────────────

  Metrics (aggregated numbers)
    QPS, P50/P95 latency, error rate, token throughput
    → trends, alarms

  Logs (single text records)
    Concrete error stacks, full prompt + response
    → root-cause investigation

  Traces (cross-service call chains)
    User request → API → retrieval → model → tool → response
    → finding bottlenecks / linking issues end to end
```

LLM applications have 4 **special observability dimensions**:

```
  1. Token economics:
     - input/output tokens per request
     - cost per request (priced by model)

  2. Eval drift:
     - sample from production → run Eval → watch the score trend

  3. Hallucination monitoring:
     - rate of answers not supported by grounding documents
     - sampled real-time scoring with LLM-as-judge

  4. Agent path:
     - distribution of steps per completion
     - tool-call success rate
     - retry counts
```

### AWS Practice: The Observability Three-Piece Set

```
        Minimum observability stack (on AWS)
        ──────────────────────────────────────

  Metrics:
    - CloudWatch Metrics (auto: Bedrock invocations, latency, tokens)
    - CloudWatch Custom Metrics (yours: eval score, hallu rate)

  Logs:
    - CloudWatch Logs (application logs, must include trace_id)
    - Bedrock Model Invocation Logging (prompt + response)
    - Long-term archive → S3

  Traces:
    - X-Ray (across Lambda / API Gateway / ECS)
    - Optional: LangFuse / Phoenix (LLM-specific tracing)

  Dashboard:
    - CloudWatch Dashboard (ops)
    - Custom BI (business KPIs)
```

### The 6 Must-Have Dashboard Cards

```
  ┌─────────────────────────────────────────────┐
  │  1. QPS + Error rate (overall health)       │
  │  2. P50 / P95 / P99 latency (experience)    │
  │  3. Token usage + Cost trend (money)        │
  │  4. Eval score (real-time sampled) (quality)│
  │  5. Top failure types (debug entry)         │
  │  6. Agent step distribution (Agent health)  │
  └─────────────────────────────────────────────┘
```

> **AWS knowledge references**: search "CloudWatch metrics for Bedrock", "X-Ray for Bedrock Agents", "Bedrock model invocation logging".

---

## 13.2 Cost Control — Tokens Are the New "Utility Bill"

The biggest "non-engineering" risk for an LLM application is **money**.

```
        Typical cost structure (monthly)
        ────────────────────────────────────

  Bedrock model calls (60–80%)
    - input tokens × unit price
    - output tokens × unit price (typically 4–5x more expensive)

  Embeddings (5–10%)
    - one-time at indexing + every query

  Knowledge Base / Vector DB (5–15%)
    - OpenSearch Serverless OCU or pgvector instance

  Other (5–15%)
    - Lambda / ECS / network / monitoring
```

### The 4 Engineering Moves on Cost

```
  1. Caching
     - Cache identical queries for 1 hour
     - Prompt-prefix caching (Anthropic / Bedrock now support it)
     - Saves 30–70%

  2. Routing
     - Simple query → mini / haiku
     - Complex query → sonnet / opus
     - Saves 50–80%

  3. Compression (context compression)
     - Too many top_k results retrieved by RAG → cap them
     - Optimize the system prompt (dedupe + tighten)
     - Saves 10–30%

  4. Batching
     - Async tasks via Bedrock Batch (50% discount)
     - Good for eval / offline analysis
```

### AWS Practice: Bedrock Cost Monitoring

```
        Three layers of Bedrock cost monitoring
        ──────────────────────────────────

  Layer 1: AWS Cost Explorer
    - Aggregate by service / region / tag
    - Monthly trend + anomaly alarms

  Layer 2: Cost Allocation Tags
    - Tag every Agent / KB (project / team / customer)
    - Allocate cost by tag

  Layer 3: Application-layer instrumentation
    - Per invoke, record input/output tokens + model
    - Aggregate by business scenario / user / department
    - Report to CloudWatch Metrics
```

### Budget Alarm Is Mandatory

```
  AWS Budgets:
    - Monthly budget of $X
    - 80% / 100% / 120% three-tier alerts
    - Above 100%: email + Slack to owner
    - (Use auto-stop carefully in production)
```

> **AWS knowledge references**: search "AWS Cost Explorer for Bedrock", "Bedrock prompt caching", "Bedrock batch inference".

---

## 13.3 Canary Releases — Not "All or Nothing"

### Why Canary Is Mandatory

```
  A no-canary deploy:
    Launch → discover problem → full rollback → all users affected
    Damage = all users × outage time

  A canary deploy:
    1% → monitor 30 min → 10% → ... → 100%
    Damage = 1% of users × short time
    100x more headroom to stop the bleeding
```

### Canary Strategies

```
        Three canary methods
        ──────────────────────────────

  By percentage (traffic share)
    - 1% → 5% → 25% → 50% → 100%
    - Best for: general features / high traffic

  By user / segment
    - Internal staff first → beta users → premium → all
    - Best for: high-risk / business-critical features

  By feature flag
    - Same binary, config center toggles the switch
    - Best for: A/B tests / hot-switchable features
```

### Canary "Gates"

Each canary stage needs a "gate" condition:

```
  From 1% to 5%:
    ✓ Error rate ≤ baseline + 0.5%
    ✓ P95 latency ≤ baseline + 200ms
    ✓ Real-time-sampled Eval ≥ baseline − 0.02
    ✓ No P1 alarms

  From 5% to 25%:
    ✓ All of the above + at least 30 minutes stable
    ✓ Written sign-off from customer business side
```

### AWS Practice: 3 Canary Approaches

```
Approach A: API Gateway Stage + Lambda Alias
  - One-click traffic-percent shift (Lambda traffic shifting)
  - Simple / most common for Bedrock applications

Approach B: ECS / EKS blue-green / canary
  - CodeDeploy + ECS service
  - Supports the full canary toolkit

Approach C: Application-layer feature flag
  - LaunchDarkly / AWS AppConfig
  - Shift traffic without redeploying
  - Recommended: pair with Lambda
```

---

## 13.4 Rollback — Must Be Switchable Within 5 Minutes

```
        3 things rollback must achieve
        ─────────────────────────────────

  1. Easy trigger
     One command / one button / one PR revert
     Not "5 config steps + redeploy"

  2. Bounded time
     From decision to in effect: < 5 minutes
     Ideally < 1 minute

  3. Data compatibility
     Data written by the new version is readable by the old version
     (forward-compatible design)
```

### Rollback Checklist

```
  ✓ Config rollback (config / prompt / model / KB version)
  ✓ Code rollback (Lambda alias / ECS service)
  ✓ Data rollback (DB schema / embedded data)
  ✓ Frontend rollback (CDN cache invalidation)
```

### Special Handling for Prompt / Model / KB Rollback

In LLM applications, "rollback" isn't only about code:

```
  Prompt rollback:
    - Store prompts in a config center (AppConfig / SSM Parameter Store)
    - Don't hard-code them
    - Switch = change one parameter

  Model rollback:
    - Application reads model_id from config
    - Switch = change modelArn in config

  Knowledge Base rollback:
    - Version your KB (snapshot before each data-source change)
    - Application reads KB id from config
    - Switch = change KB id in config
```

---

## 13.5 Failure Drills — Chaos Engineering for LLM

```
        5 failure types to drill
        ─────────────────────────────────

  1. Model fully unavailable
     → Switch to backup model (cross-region or cross-provider)

  2. KB / retrieval unavailable
     → App degrades to "model-only answer + risk warning"

  3. Tool call fails
     → Agent returns gracefully + creates ticket

  4. Single-region outage (AWS)
     → DR failover to backup region

  5. Upstream/downstream throttling / overload
     → Circuit breaker + queue + retry
```

### How to Drill

```
  Quarterly: one full DR drill (cross-region)
  Monthly:   one small drill (kill the KB / model / tool)
  Weekly:    sampled trace review + anomaly analysis
```

---

## 13.6 A Sample Production Dashboard

```
══════════════════════════════════════════════════════════════════
  Customer Insurance Assistant — Production Dashboard
══════════════════════════════════════════════════════════════════

[Health]                                  [Cost]
  QPS: 23.4 (avg)                          Today: $89.2
  Error rate: 0.3% (baseline 0.4%) ✅      MTD:   $1,847
  P95 latency: 1.8s (target <3s)  ✅      Forecast: $5,420 / mo
  Active users: 312                         Budget: $6,000     ✅

[Quality]                                 [Eval Drift]
  Sampled accuracy: 87.2% ✅                7-day:  0.872 ↘ (-0.005)
  User thumbs-up: 89%                       30-day: 0.876
  User thumbs-down: 4%                      Threshold: 0.85 ✅
  Unrated: 7%

[Top Failures (last 24h)]
  - Tool 'get_policy_pdf' timeout: 12 cases
  - Hallucination flag: 3 cases (sampled)
  - Guardrail block (PII): 18 cases (intended)

[Canary]
  Current rollout: 100%
  Last change: 2026-05-19 14:00 (prompt v2.3.1)
  Auto-rollback armed: ✅
══════════════════════════════════════════════════════════════════
```

**This dashboard sits on the customer's on-call screen, the FDE has it on theirs, and both sides are looking at the same source of truth**.

---

## Key Quotes

> "*A system without observability is a system you don't own.*"
> — A. Lawrence, *FDE Rule Book*, 2025

> "*Every dollar saved by caching is a dollar of production runway.*"
> — Anthropic enterprise best practices, 2025

> "*If you can't roll back in 5 minutes, you can't deploy on Friday.*"
> — AWS GenAI Innovation Center, 2025

---

## Hands-On Checklist

PoC weeks 4–6 + pre-launch — must do:

1. **Wire up CloudWatch + X-Ray + Bedrock Logging** (none optional).
2. **Build the 6-card dashboard** (section 13.1).
3. **Configure Cost Explorer Tag + AWS Budgets monthly alarm**.
4. **Route prompt / model / KB through a config center** (no hard-coding).
5. **Add canary deploy to CI/CD** (API Gateway / Lambda Alias).
6. **Write a "5-minute rollback SOP"**: from decision to in-effect flow.
7. **Run the first failure drill** (kill the KB and watch it degrade gracefully).

---

## Anti-Patterns

- ❌ **Hard-coding prompt / model in code** (every change requires a release).
- ❌ **Going live without cost monitoring** (the bill is a month-end surprise).
- ❌ **Canary only at 0% and 100%** (any incident takes down everyone).
- ❌ **Rollback that means "redeploy the previous version"** (5 minutes becomes 50).
- ❌ **Dashboard the customer can't see** (customer on-call doesn't know what's happening).
- ❌ **Trusting "in theory we can switch" without drilling** (when it actually breaks, it's too late).
- ❌ **Too many alerts → numbness** (only alarm on what's truly actionable).

---

## Relation to the Next Part

By here, the "PoC → production" gap has been crossed: your LLM/Agent is running stably in the customer's production environment.

The next Part enters the **Agent era** — not the "let's add RAG" kind of Agent, but truly "autonomous decision + tool use + cross-system action" Agents. The FDE's engineering work changes shape at this stage.

[← Previous: PoC Pass-Line Conditions](chapter-12.md) · [Next Part: The Agent Era →](../part-6/intro.md)
