# Chapter 15: MCP and Enterprise Integration — Wiring Agents into Customer Tools

## Opening

```
In November 2024, Anthropic released MCP (Model Context Protocol).

Through 2025–2026, almost every enterprise B2B project demands MCP support.

An FDE's first MCP engagement:
  - The customer already has: Confluence + Jira + Salesforce + internal Wiki
  - The customer wants: "Claude / Bedrock Agent should be able to use all of them"
  - Old approach: hand-write a LangChain Tool for each → 6 weeks
  - With MCP:
      → Confluence MCP server (community already has one)
      → Jira MCP server (community already has one)
      → Salesforce MCP server (FDE writes one)
      → Internal Wiki MCP server (FDE writes one)
      → Wire it into Claude Desktop / Bedrock Agent
      → 1 week

  10x development efficiency.

But MCP's "power" is also a "risk":
  - One MCP server exposes the customer's internal API
  - The Agent can hit 50+ tools at once
  - Security / audit / permission boundaries are 100% the FDE's design

This chapter covers the engineering practice of deploying MCP inside a
customer's enterprise.
```

---

## 15.1 What MCP Is

```
        World without MCP                World with MCP
        ────────────────────             ────────────────────

  Agent 1 integrates Tool A        Every Agent shares the MCP protocol
  Agent 1 integrates Tool B
  Agent 2 integrates Tool A        Tool A implements one MCP server
  Agent 2 integrates Tool B        Tool B implements one MCP server

  An N × M integration nightmare    A standard interface — N + M
```

MCP is essentially **a USB-C interface between LLMs and tools**:

```
        The three layers of MCP
        ──────────────────────────────────

  Client (LLM application)
    Claude Desktop / Cursor / Bedrock Agent / homegrown Agent
       ↕ JSON-RPC over stdio / SSE / HTTP
  Server (tool implementation)
    File / Slack / Jira / Salesforce / internal API ...
       ↕
  Resource (capabilities exposed by the tool)
    - tools (function calls)
    - resources (files / data)
    - prompts (predefined prompt templates)
```

### An MCP server exposes three kinds of capability

```
  Tools — functions the LLM can invoke
    e.g., list_jira_issues(status, project)

  Resources — things the LLM can read
    e.g., file:///docs/policy.md
          confluence://wiki/space/PROD/pages/123

  Prompts — predefined prompt templates
    e.g., "summarize_pr" template
          "review_security" template
```

---

## 15.2 Three Forms of Enterprise MCP Deployment

```
  Form 1: Local MCP server (developer machine)
    Scenario: Cursor / Claude Desktop
    Deployment: process launch, stdio transport
    Fit: individual / small team

  Form 2: Remote MCP server (HTTP/SSE)
    Scenario: shared across the enterprise / multiple users
    Deployment: K8s / ECS / Lambda + API Gateway
    Fit: enterprise-grade

  Form 3: Centralized MCP gateway
    Scenario: 50+ MCP servers to manage
    Deployment: one gateway aggregates every server
    Fit: large enterprise + multi-tenant
```

**90% of enterprise B2B projects are Form 2; some large customers are Form 3**.

---

## 15.3 Writing an Enterprise MCP Server — Hands-On

Take a "Salesforce CRM MCP server" as an example:

### Step 1: Design the tools

```python
# Enumerate the customer's business-critical operations
tools = [
    "list_accounts",
    "get_account_details",
    "search_opportunities",
    "create_task",  # write
    "log_activity",  # write
    "update_stage",  # write, requires confirmation
]
```

### Step 2: Implement the MCP server (Python SDK)

```python
from mcp import Server, Tool
from mcp.types import TextContent
import simple_salesforce as sf

server = Server("salesforce-mcp")

@server.tool()
async def list_accounts(name_contains: str = None, limit: int = 10):
    """List Salesforce accounts. Use when user asks about customers/accounts."""
    sf_client = get_sf_client()  # uses user-scoped OAuth token
    query = "SELECT Id, Name, Industry FROM Account"
    if name_contains:
        query += f" WHERE Name LIKE '%{name_contains}%'"
    query += f" LIMIT {limit}"
    results = sf_client.query(query)
    return TextContent(text=json.dumps(results['records']))

@server.tool()
async def update_stage(opp_id: str, stage: str, dry_run: bool = True):
    """Update opportunity stage. Use only when user explicitly asks to change stage."""
    if dry_run:
        return {"status": "dry_run", "would_set": stage}
    sf_client = get_sf_client()
    sf_client.Opportunity.update(opp_id, {'StageName': stage})
    return {"status": "updated"}

if __name__ == "__main__":
    server.run()
```

### Step 3: Authentication — the critical part

```
        Three auth modes for an enterprise MCP server
        ─────────────────────────────────

  Mode A: User OAuth (recommended)
    User signs in → obtains token → starts MCP server
    → MCP server calls downstream with that token
    → Downstream system enforces permissions

  Mode B: Service account
    MCP server calls downstream with a service account
    Problem: anyone can use MCP to escalate privileges
    Only acceptable for internal admin tools

  Mode C: Per-call token forwarding
    Every MCP call carries the user's token
    MCP server forwards the token to downstream
    Most rigorous, but more complex to implement
```

**Enterprise production**: Mode A or Mode C. Mode B is reserved for tightly controlled internal tools.

### Step 4: Deploy into the customer's VPC

```
        Enterprise deployment architecture
        ─────────────────────────────────────

  Customer VPC
    ├── ECS Service: salesforce-mcp-server
    │     ├── ALB (HTTPS, customer cert)
    │     ├── Container (Python, MCP SDK)
    │     └── Secrets Manager: SF OAuth config
    │
    ├── ECS Service: jira-mcp-server
    │     └── ...
    │
    ├── ECS Service: confluence-mcp-server
    │     └── ...
    │
    └── Bedrock Agent
          └── Action Group: hits the HTTP endpoint of the three MCP servers above
```

---

## 15.4 Four Engineering Pitfalls of MCP

### Pitfall 1: the MCP server exposes too much

Newcomers writing an MCP server tend to "expose every API." The result:

```
  ✗ Salesforce MCP exposes 80 tools
    → Agent picks the wrong one 60% of the time
    → Maintenance cost explodes

  ✓ Salesforce MCP exposes 8 high-frequency tools
    → Covers 90% of business scenarios
    → 90%+ accuracy
```

**Rule of thumb**: keep each MCP server to 5–15 tools. More than that, split the server.

### Pitfall 2: loose parameter schemas

```python
# Bad
@server.tool()
async def query(text: str):  # what is text?
    ...

# Good
@server.tool()
async def search_opportunities(
    name_contains: str = None,
    stage: Literal["Prospecting", "Qualification", "Negotiation"] = None,
    amount_min: int = None,
    limit: int = 10
):
    """Search Salesforce opportunities..."""
```

**Strict schemas = the model picks wrong far less often**.

### Pitfall 3: sloppy error handling

```python
# Bad
try:
    result = sf_client.query(...)
    return result
except Exception:
    return None  # the model has no idea what happened

# Good
try:
    result = sf_client.query(...)
    return {"status": "ok", "data": result}
except sf.SalesforceMalformedRequest as e:
    return {"status": "error", "type": "bad_query", "message": str(e), "hint": "check field names"}
except sf.SalesforceAuthenticationFailed:
    return {"status": "error", "type": "auth_failed", "message": "OAuth token expired", "hint": "re-authenticate"}
except Exception as e:
    return {"status": "error", "type": "unknown", "message": str(e)}
```

**Make errors readable so the model can recover on its own**.

### Pitfall 4: missing audit

```python
# Every MCP call must write audit
@server.tool()
async def update_stage(opp_id, stage):
    audit_log({
        "user_id": current_user_id(),
        "tool": "update_stage",
        "params": {"opp_id": opp_id, "stage": stage},
        "timestamp": now(),
        "trace_id": get_trace_id()
    })
    # actual execution
```

**An MCP server without audit is not production-shippable**.

---

## 15.5 AWS in Practice: Bedrock Agent + MCP Integration

```
        MCP deployment architecture on AWS
        ───────────────────────────────────────

  Customer Bedrock Agent
       ↓ (Action Group)
  Lambda: mcp-bridge
       ↓ (HTTP/SSE)
  ALB / API Gateway
       ↓
  ECS Fargate: MCP servers
    ├── salesforce-mcp
    ├── jira-mcp
    ├── confluence-mcp
    └── internal-wiki-mcp
       ↓
  Downstream systems (each SaaS / internal API)
```

A minimal Lambda bridge:

```python
# Lambda: mcp-bridge
import boto3
import requests

def lambda_handler(event, context):
    # Called by the Bedrock Agent
    action_group = event['actionGroup']
    api_path = event['apiPath']
    parameters = event['parameters']

    # Forward to the matching MCP server
    mcp_url = MCP_SERVER_MAP[action_group]
    user_token = event['sessionAttributes'].get('user_token')

    response = requests.post(
        f"{mcp_url}/tools/call",
        json={"name": api_path, "arguments": parameters},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    return {
        'response': {
            'actionGroup': action_group,
            'apiPath': api_path,
            'httpStatusCode': response.status_code,
            'responseBody': {
                'application/json': {'body': response.json()}
            }
        }
    }
```

> **AWS reference**: search "Bedrock Agent action group OpenAPI." The official MCP-to-Bedrock bridge story is still evolving through 2025–2026; track AWS announcements.

---

## 15.6 Multi-Server Choreography — A Customer Scenario

```
  Scenario: a sales assistant Agent

  MCP servers wired into the Agent:
    1. crm-mcp (Salesforce, 8 tools)
    2. email-mcp (Outlook / Gmail, 5 tools)
    3. calendar-mcp (Google Calendar, 4 tools)
    4. wiki-mcp (internal Confluence, 3 tools)
    5. order-mcp (internal ERP, 6 tools)

  Total tools: 26 → within the 14.1 "magic number ≤ 30"

  A representative dialogue:
    User: "What did ABC Corp give us as feedback last time?
           I'm visiting them next week."

    Agent path:
      Step 1: crm-mcp.search_accounts("ABC Corp")
      Step 2: crm-mcp.get_account_details(account_id="...")
      Step 3: crm-mcp.list_recent_activities(account_id="...")
      Step 4: email-mcp.search_emails(from="abc.com", days=30)
      Step 5: wiki-mcp.search("ABC Corp")
      Step 6: synthesize the answer
      Step 7 (after user confirmation): calendar-mcp.create_event(...)
```

**26 tools spread across 5 servers — each server cohesive and single-purpose**.

---

## 15.7 Security Checklist

```
        Enterprise MCP deployment security checklist
        ─────────────────────────────────────

  □ User OAuth, not service account
  □ MCP server inside the VPC, HTTPS enforced
  □ Every tool has a detailed description + JSON schema
  □ Write tools default to dry_run
  □ Dangerous operations go through HITL
  □ End-to-end trace_id
  □ Audit log (who / what / when / result)
  □ Bedrock Guardrails as a second line of defense
  □ Rate limit per user (not just per IP)
  □ Tool enable/disable through a config service (not code edits)
  □ Minimal toolset (each server ≤ 15)
  □ MCP server gets its own vuln scan + pen test
```

---

## Key Citations

> "*MCP turned tool integration from O(N×M) to O(N+M).*"
> — Anthropic MCP launch, 2024-11

> "*A poorly designed MCP server is a backdoor with documentation.*"
> — A. Lawrence, *FDE Rule Book*, 2025

> "*The future enterprise agent will use 50+ MCP servers — the FDE's job is to make all 50 boring.*"
> — AWS GenAI Innovation Center, 2025

---

## Action Checklist

In the first week of an MCP integration project, you must:

1. **Inventory the customer's tools** — which SaaS, which internal APIs
2. **Check whether the community already has an MCP server** (Awesome MCP / Anthropic's official repo)
3. **For the rest, write your own MCP server** — one or two days with the Python SDK
4. **Wire up user OAuth** (no service accounts)
5. **Write a complete description + schema for every tool**
6. **Add tracing + audit logging**
7. **Build an Eval set** (including counter-examples for "wrong calls")
8. **Deploy inside the VPC + HTTPS + auth**

---

## Anti-Pattern Checklist

- ❌ **Exposing all 60 tools in v1** (accuracy is folklore)
- ❌ **Running an MCP server under a service account** (auth incident #1)
- ❌ **No schema, letting the LLM "guess" parameters** (error rate skyrockets)
- ❌ **Returning None on error** (the model has no idea what happened)
- ❌ **Deploying an MCP server on the public internet** (anyone who finds it can call it)
- ❌ **Tools too coarse-grained** (omnibus functions like "smart_helper")
- ❌ **Shipping with no audit** (compliance fails immediately)

---

## Relation to the Next Part

By this point, the FDE has walked the entire arc inside the customer's environment — "PoC → production → Agent → enterprise integration."

One Part remains: **Delivery and Craft Progression** — Handoff so the customer can take it forward, pattern extraction that turns engagements into reusable assets, and the FDE's own T-shaped growth.

[← Previous: Deploying Agents in Customer Environments](chapter-14.md) · [Next Part: Delivery and Craft Progression →](../part-7/intro.md)
