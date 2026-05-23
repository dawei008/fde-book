# Chapter 14: Deploying Agents in Customer Environments — Toolsets / Sandboxing / Failure Recovery

## Opening

```
An FDE built a "sales assistant Agent" for a customer with 47 tools:
  - Read CRM
  - Update CRM
  - Read ERP
  - Update ERP
  - Send email
  - Update calendar
  - Create ticket
  - Close ticket
  - Adjust price
  - Send coupon
  - ... all the way to tool #47

Week 1 demo: flawless.
Week 3, the customer's business owner pulls the FDE aside:
  "This week the Agent sent 100%-off coupons to three customers
   in a row. Loss: roughly ¥200K."

Post-mortem: under certain prompts the model "took initiative" and called
send_coupon(100). No sandbox. No amount cap. No dry-run.

The FDE rewrote it overnight:
  - 47 tools cut to 18 (merged + deleted dangerous ones)
  - Write/update tools got "second confirmation + amount cap + dry-run"
  - Added audit trail and alerts

Week 5 relaunch: zero incidents.

This chapter covers the four things that matter when deploying an Agent in
a customer environment — toolset design / sandboxing / failure recovery / eval.
```

---

## 14.1 Toolset Design — Less Is More

### The "magic numbers" of tool count

```
        Agent tool count vs. accuracy (empirical)
        ──────────────────────────────────────

  ≤ 5     95%+ accuracy, simple
  6-10    90% accuracy, engineering-friendly
  11-20   80% accuracy, requires careful prompt design
  21-30   70% accuracy, recommend splitting
  31-50   60% accuracy, uncontrollable
  > 50    "tool hell," accuracy is folklore
```

**First principles**: the probability of the model picking the wrong tool grows exponentially with tool count.

### Four principles for toolset design

```
  1. One verb + one object
     ✓ create_ticket(title, body)
     ✗ smart_helper(action, params)  (too broad)

  2. Descriptions must be "model-friendly"
     ✓ "Returns customer order history. Use when user asks about
        past purchases."
     ✗ "Get orders" (model has no idea when to call it)

  3. Strict parameters
     ✓ JSON Schema with hard validation
     ✓ Required vs Optional clearly marked
     ✓ Enums constrain values

  4. Tier dangerous operations
     - read tools: execute directly
     - write tools: second confirmation / dry-run
     - large amount / irreversible: multi-party approval
```

### Tool description template

```python
# A well-formed tool definition
{
    "name": "send_email",
    "description": (
        "Send an email to specified recipients. "
        "Use this tool when user explicitly asks to send/notify someone. "
        "Do NOT use for internal logging or status updates. "
        "Maximum 5 recipients per call."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "to": {
                "type": "array",
                "items": {"type": "string", "format": "email"},
                "maxItems": 5,
                "description": "Recipient email addresses"
            },
            "subject": {"type": "string", "maxLength": 200},
            "body": {"type": "string", "maxLength": 5000},
            "dry_run": {
                "type": "boolean",
                "description": "If true, validate but do not actually send",
                "default": false
            }
        },
        "required": ["to", "subject", "body"]
    }
}
```

---

## 14.2 Sandbox — The Agent's "Permission Boundary"

### Three lines of defense

```
        The Agent execution sandbox — three layers
        ───────────────────────────────────

  Layer 1: model layer
    - System prompt strictly constrains behavior
    - Guardrails block dangerous output
    - Few-shot examples steer it

  Layer 2: tool layer
    - Dangerous tools require second confirmation
    - dry-run mode on by default
    - Caps on amount / quantity / frequency

  Layer 3: execution layer
    - IAM / database permission isolation
    - VPC network isolation
    - Rate limiting + circuit breakers
```

### Key technique: dry-run mode

```python
# A design pattern with dry_run=True as the default
def send_coupon(customer_id, amount, dry_run=True):
    if dry_run:
        return {
            "status": "dry_run",
            "would_send_to": customer_id,
            "amount": amount,
            "note": "Set dry_run=false to actually send"
        }
    # actual send logic...
```

**Any time the Agent calls a write tool, the first call must be dry_run**. The model decides on its own whether to set dry_run=false the second time (with a second-confirmation mechanism in place).

### Key technique: amount / frequency limits

```python
# Hard limits inside the tool
MAX_COUPON_AMOUNT = 50  # CNY
MAX_COUPON_PER_HOUR = 10  # calls

def send_coupon(customer_id, amount):
    if amount > MAX_COUPON_AMOUNT:
        return {"error": f"Amount exceeds limit ({MAX_COUPON_AMOUNT})"}
    if rate_limit_exceeded("coupon", "1h", MAX_COUPON_PER_HOUR):
        return {"error": "Rate limit exceeded"}
    # actual send
```

**These limits cannot live in the prompt** (prompt injection bypasses them); they have to be hard-coded in the tool implementation.

### Permission isolation — tools use the user context, not a service account

```
  Wrong:
    Agent → tool (with admin role) → DB
    → any user can read / modify any data

  Right:
    User logs in → obtains user_token
    Agent (carrying user_token) → tool → calls DB with user_token
    → user can only read / modify their own data
```

### AWS in practice: the Bedrock Agents permission model

```
        Bedrock Agent permissions — three layers
        ──────────────────────────────────

  1. Agent execution role
     - The Agent's own IAM role
     - Usually only allowed to call Bedrock + its own KB

  2. Action group Lambda
     - Each action group can have its own Lambda
     - Lambda uses its own role to call downstream services

  3. User context (passed via session attributes)
     - User login info (cognito / IAM identity)
     - Lambda uses this context to make ABAC decisions

  → Don't give the Agent one almighty role
  → Give the Agent permission to invoke Lambda,
    and let Lambda enforce per-user authorization
```

> **AWS reference**: search "Bedrock Agent session attributes," "Bedrock Agent execution role."

---

## 14.3 Failure Recovery — What to Do When a Multi-Step Task Breaks

### The "break points" of an Agent task

```
        A typical Agent task path
        ──────────────────────────────────────

  User: "Reassign all P1 tickets from last week to Zhang and notify him"

  Agent:
    Step 1: list_tickets(status="P1", week="last") → 5 items
    Step 2: assign_ticket(id=#101, to="zhang") ✓
    Step 3: assign_ticket(id=#102, to="zhang") ✓
    Step 4: assign_ticket(id=#103, to="zhang") ✗ (network blip)
    Step 5: ...

  Problem:
    - #101 and #102 are now assigned, #103 failed
    - Will a re-run reassign #101 and #102?
    - The model may simply give up on the task
```

### The fix: idempotency + state persistence

```python
# Tool calls must be idempotent
def assign_ticket(ticket_id, assignee, idempotency_key=None):
    if not idempotency_key:
        idempotency_key = f"assign-{ticket_id}-{assignee}"

    # Repeated calls with the same key return the previous result
    if cache.exists(idempotency_key):
        return cache.get(idempotency_key)

    result = actually_assign(ticket_id, assignee)
    cache.set(idempotency_key, result, ttl=86400)
    return result
```

```python
# Persist Agent execution state
class AgentSession:
    def __init__(self, session_id):
        self.session_id = session_id
        self.state = load_from_dynamodb(session_id) or {
            "task": None,
            "completed_steps": [],
            "pending_steps": []
        }

    def execute(self, task):
        for step in self.state["pending_steps"]:
            try:
                result = run_step(step)
                self.state["completed_steps"].append(step)
                save_to_dynamodb(self.session_id, self.state)
            except RetryableError:
                # leave it in pending — next run will resume
                save_to_dynamodb(self.session_id, self.state)
                raise
```

### AWS in practice: Step Functions as the Agent's safety net

```
        Wrap the Agent in Step Functions
        ────────────────────────────────────

  Good fit:
    - A single Agent task runs > 5 minutes
    - Multiple Agents collaborating
    - Need to persist intermediate state
    - Need human-in-the-loop

  Strengths:
    - Visualized execution history
    - Automatic retry + exponential backoff
    - Resume from break point on failure
    - Pause + wait for approval + resume

  Anti-pattern:
    - Simple single-step Agent → Step Functions is overkill
    - High-frequency low-latency → not a fit
```

> **AWS reference**: search "Step Functions express workflows for AI," "Step Functions human approval."

---

## 14.4 Agent Eval — A Different Kind of Eval

A regular LLM application's Eval looks at "is the answer right?" Agent Eval also has to look at:

```
        Five dimensions of Agent evaluation
        ────────────────────────────────────

  1. Task completion rate
     Did the user's goal ultimately get achieved?
     binary: yes / no

  2. Path correctness
     Were the execution steps reasonable? Any redundancy?
     metric: actual steps / "canonical path" steps

  3. Tool-use accuracy
     Right tool? Right parameters?
     metric: tool_call_accuracy

  4. Side-effect control
     Did it "do anything it shouldn't have"?
     metric: side_effect_count

  5. Experience cost
     Total latency / token cost / retry count
     metric: latency, cost, retries
```

### Designing Agent Eval samples

```jsonl
{
  "id": "agent-eval-007",
  "task": "Reassign all P1 tickets from last week to Zhang",
  "context": {"current_user": "manager-001"},
  "expected_outcome": {
    "tickets_assigned": ["#101", "#102", "#103", "#104", "#105"],
    "all_to": "zhang",
    "side_effects_allowed": ["notify_zhang"],
    "side_effects_forbidden": ["close_ticket", "notify_customer"]
  },
  "expected_path": {
    "min_steps": 6,
    "max_steps": 12,
    "must_use_tools": ["list_tickets", "assign_ticket"],
    "must_not_use_tools": ["delete_ticket", "send_coupon"]
  }
}
```

### AWS in practice: Bedrock Agent Evaluations

```
  Bedrock built-in Agent Evaluation:
    - Auto-evaluates trajectory (path)
    - Evaluates tool selection accuracy
    - Evaluates task success rate
    - Supports custom metrics
```

---

## 14.5 Human-in-the-Loop — High-Risk Actions Always Need a Reviewer

```
        Three HITL modes
        ──────────────────────────────────

  1. Always-approve (high risk)
     - Delete data / large transfer / external email
     - Agent prepares → push for approval → human clicks → execute

  2. Sample-approve (medium risk)
     - Update CRM / create ticket
     - Agent acts directly
     - But 5% / 10% sampled into approval queue (post-hoc + calibration)

  3. No-approve (low risk)
     - Queries / reports / internal memos
     - Agent fully autonomous
```

### Implementation architecture

```
  Agent → detect high-risk action → write to SQS / DynamoDB
                            ↓
                       (notify human via Slack / email)
                            ↓
                       Human approves in a Web UI
                            ↓
                       Step Functions resumes
                            ↓
                       Agent executes
```

---

## 14.6 Deployment Checklist

```
        Pre-production Agent checklist
        ─────────────────────────────────────

  □ Tool count ≤ 20 (split by force if more)
  □ Every tool has a complete description + JSON schema
  □ Write / update / delete tools default to dry_run
  □ Amount / frequency / quantity caps hard-coded
  □ User context plumbed through to tools (no service account)
  □ Idempotency key enforced
  □ State persisted (DynamoDB / Step Functions)
  □ Bedrock Guardrails: PII + Topic + Content
  □ High-risk actions go through HITL
  □ Trace + cost dashboard
  □ Eval set covers task / path / tool / side-effect (all four)
  □ Canary + rollback path
  □ Failure drills (model down / tool down)
```

---

## 14.7 An End-to-End Agent Deployment

```
  Customer scenario: an insurance company's "claims assistant Agent"

  Toolset (12 tools):
    [read]
      - get_policy(policy_id)
      - get_claim_history(customer_id)
      - get_doctor_records(claim_id)
      - search_clauses(keyword)
    [write — simple]
      - create_followup_ticket(claim_id, note)
      - send_internal_msg(team, msg)
    [write — important]
      - request_more_info(claim_id, items[]) → dry_run + agent approval
      - flag_for_review(claim_id, reason) → supervisor approval
      - approve_claim(claim_id, amount) → human approval, always
      - reject_claim(claim_id, reason) → human approval, always
    [escalate]
      - escalate_to_human(claim_id, reason)
      - request_legal_review(claim_id)

  Sandbox:
    - approve_claim must have amount <= ¥5000
    - approve_claim must go through HITL
    - All write tools called with the agent's user_id

  Failure recovery:
    - Tasks orchestrated via Step Functions
    - Each step's state written to DynamoDB
    - Retry 3 times, still failing → escalate

  Eval:
    - 100 historical claims as the golden set
    - Measure:
      - Approval/rejection alignment with the human decision
      - Average tool count (canonical 5–8 steps)
      - Wrong-tool call rate

  Rollout:
    - W11: 1% canary (internal claims agents)
    - W12: 10% canary (low-risk cases)
    - W14: 50%
    - W16: 100%
```

---

## Key Citations

> "*An agent without a sandbox is a liability.*"
> — A. Lawrence, *FDE Rule Book*, 2025

> "*The best agents have boring tools.*"
> — Anthropic Claude tool use guide, 2025

> "*Don't ship an agent until you've watched it fail safely 100 times.*"
> — AWS GenAI Innovation Center, 2025

---

## Action Checklist

When you take on an Agent project, before deployment you must:

1. **Draw the tool list and tag each as read/write/delete**
2. **Add dry_run + caps to every "write" tool**
3. **Plumb user context through; no service accounts**
4. **Wire up an idempotency cache** (DynamoDB / Redis)
5. **Configure Bedrock Guardrails for PII / business red lines**
6. **Wrap high-risk tasks in Step Functions** (resumable from break points)
7. **Build a 4-dimensional Eval set** (task / path / tool / side-effect)
8. **Configure HITL** (amount / irreversibility / external impact)

---

## Anti-Pattern Checklist

- ❌ **Shipping with > 30 tools** (accuracy is folklore)
- ❌ **Writing without dry_run** (incident source #1)
- ❌ **Agent calling downstream with admin / service account** (every user gets escalated privileges)
- ❌ **Letting the model "retry by itself" on failure** (no idempotency means duplicated operations)
- ❌ **No HITL on high-risk actions** (you find out about the loss in front of the customer)
- ❌ **Evaluating an Agent with regular Eval** (misses trajectory / side-effect)
- ❌ **Going to 100% without a failure drill** (you'll meet the truth at 2 AM)

---

## Relation to the Next Chapter

This chapter handled the engineering problems of an Agent in "its own environment." The next chapter handles how the Agent gets "wired into the customer's tools" — enterprise integration in the era of **MCP (Model Context Protocol)**.

[← Part VI Intro](intro.md) · [Next: MCP and Enterprise Integration →](chapter-15.md)
