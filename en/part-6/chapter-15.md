---
title: "Chapter 15 — MCP Integration"
parent: "Part VI — Agents and MCP"
nav_order: 2
---

# Chapter 15: MCP Integration — Wiring Agents Into the Customer's Existing Tool Stack

Hesheng Precision Heavy Industries, overseas business unit, month 2 after phase-two GA.

The 14 tools in phase two were ours — Lambdas wrapping ERP / CRM / tickets / email / calendar, five systems direct. After running for a month, Zhou Mingyuan came over: the sales director wanted the agent to also read their Salesforce; Gu Jianguo, IT lead, wanted it to query internal Confluence; Chen Xue from after-sales hoped the agent could read Jira tickets directly. Three new interfaces, three different SaaS tools.

If I wrote them in the phase-two style, I'd need six more Lambdas, six schemas, six dry_runs. I estimated three weeks.

Chen Xue asked: "These tools — other companies must've integrated them already, right? Why are we writing from scratch?"

She was right. MCP (Model Context Protocol) is the answer to that question.

---

## 15.1 What MCP Is Solving

Anthropic open-sourced the MCP protocol in November 2024, and it's now hosted by the independent working group at [modelcontextprotocol.io](https://modelcontextprotocol.io). Its engineering motivation is one sentence: have a standard interface between LLM applications and tools, like LSP for editors and languages, like USB-C for devices and peripherals.

Before MCP, every integration like phase two's meant writing one Lambda, one schema, one error-handling block per SaaS. N agents × M tools = N×M of work. MCP turns it into N+M: each tool implements an MCP server once, each agent implements an MCP client once, both speak standard JSON-RPC.

The protocol itself defines three resource categories:

```
tools       Functions the LLM can call
            The 14 tools from Chapter 14 are this category
resources   "Data" the LLM can read
            URIs like confluence://wiki/pages/123
prompts     Pre-defined prompt templates from the tool side
            "Summarize this PR" / "Review this SQL" type
```

All 14 of Hesheng's phase-two tools are tools. The three new ones — Confluence / Salesforce / Jira — have tool capabilities not specific to Hesheng's business; they're "general SaaS" tools used by many companies, with community-written MCP servers already available. That's where MCP saves the most work: reuse community for general capabilities, write your own for business-specific ones.

---

## 15.2 When to Use MCP, When to Write a Function Yourself

My judgment criterion is two signals; meet either and go MCP, otherwise stick to the phase-two style of writing your own Lambda:

```
Signal 1: Tool is "generic SaaS / generic infrastructure"
          Confluence, Jira, Salesforce, GitHub, Slack,
          Postgres, S3, file system ...
          Community probably has an MCP server already, take it

Signal 2: The same tool group is reused across multiple agents / multiple IDEs
          Used once by developers in Claude Desktop, once by developers
          in Cursor, once by a production agent — implement the tool
          once, used in three places
```

12 of Hesheng's 14 phase-two tools are Hesheng-specific — `create_part_order`'s schema hard-codes "amount ceiling ¥50,000, must pass `destination_site`"; no other company will reuse it. MCP has no benefit here, and adds a JSON-RPC serialization layer.

But Confluence / Jira / Salesforce — community MCP servers are listed at [modelcontextprotocol.io/servers](https://modelcontextprotocol.io/servers). I spent half a day reviewing implementation quality, update frequency, issue response on three servers — conclusion: the official/community Confluence and Jira servers are usable; Salesforce had too many issues, so we wrote our own. Three weeks of work became five days.

Conversely, what I didn't do: I didn't convert phase two's 14 tools into MCP servers. They were already running stable in Bedrock Agent action groups, business-specific, with no reuse, maintained internally — converting to MCP would just add a layer. **MCP isn't "the more the better"; it's "the cost of standardizing the interface should be lower than writing your own."**

---

## 15.3 MCP's Two Communication Forms

The MCP protocol itself defines two transports:

```
stdio       Local process, communicates over stdin/stdout
            Scenario: a developer's machine running Claude Desktop / Cursor
                      starts a local server, processes pipe between each other
            Pros: zero network configuration, fast startup
            Cons: one copy per machine, can't be shared across people, can't cross network

streamable HTTP   HTTP long connection, server-side streaming
            Scenario: enterprise deployment, one server serving many users
            Pros: deploy once, call from many; auth follows HTTP standards
            Cons: requires deployment + TLS + auth setup
```

For an enterprise scenario like Hesheng's, stdio is out — you can't have Chen Xue start a Confluence MCP process on her machine every day. **Enterprise deployment goes streamable HTTP only.** That's the prerequisite for the deployment architecture in 15.4.

---

## 15.4 Deploying MCP Servers on AgentCore

In phase two we didn't use AgentCore — the A4 in 6.4 is clear: single agent, single team, Level 0 direct-write. But making MCP servers callable by Bedrock Agent while preserving session state, with standard auth + observability, isn't worth standing up from scratch.

In March 2026 AWS made AgentCore's stateful MCP capability GA ([AWS What's New, 2026-03](https://aws.amazon.com/about-aws/whats-new/) post; public-materials list at end of chapter). Briefly, AgentCore Runtime can now host MCP servers directly, giving you three things for free:

One, **session persistence**. The MCP protocol has session as a first-class concept (the client maintains context once connected); stateful MCP stores session state in AgentCore-managed storage — server pods restart without losing state and scale horizontally without splitting. Phase two we wound around statelessness in Lambda; this layer is now handled.

Two, **auth wires straight into Identity Center / Cognito**. The HTTP layer goes through IAM SigV4 or OAuth bearer tokens; AgentCore validates before forwarding to the server's handler. I don't have to re-write token validation in server code.

Three, **observability lands in CloudWatch**. Each tool call records a trace, errors hit metrics — same source as phase two's 14.6 trace dimension; one CloudWatch Logs Insights query joins across agent and MCP server.

Hesheng's deployment landed on AgentCore like this:

```
        Hesheng Bedrock Agent (already in phase two)
              │
              ├─ action group: 14 in-house tools (Lambda)
              │
              └─ action group: MCP servers
                    │
                    │  HTTPS + SigV4
                    ▼
              AgentCore Runtime (stateful MCP)
                    │
                    ├─ confluence-mcp  (community server, wrapped)
                    ├─ jira-mcp        (community server, wrapped)
                    └─ salesforce-mcp  (FDE-written)
                          │
                          ▼
                    Each SaaS API
```

Hesheng's 14 in-house tools stay on Lambda action groups — they're unrelated to MCP. The three new SaaS go through MCP servers deployed on AgentCore. Two paths coexist.

---

## 15.5 Writing an Enterprise MCP Server — the Salesforce Example

Community Salesforce server unusable; written ourselves. The Python SDK runs in roughly two days; the interesting part is a few engineering decisions.

**One, control the tool set to 5-15.** Salesforce REST exposes 300+ objects and thousands of endpoints. I had Chen Xue and the sales director list the "sales scenarios this agent really needs at Hesheng" — six came out: query customers, view opportunities, find recent contact records, query products, log activities, change stage. Six tools, each a clear verb; no `salesforce_query(action, params)` catch-all. 14.1's lesson applies to MCP servers verbatim.

**Two, write-class tools still get dry_run + idempotency.** The MCP protocol doesn't mandate these — it only specifies how a tool's schema is serialized. But I write them into every write tool:

```python
from mcp.server.fastmcp import FastMCP
from typing import Literal

mcp = FastMCP("salesforce-mcp")

@mcp.tool()
async def update_opportunity_stage(
    opportunity_id: str,
    new_stage: Literal["Prospecting", "Qualification",
                       "Negotiation", "Closed Won", "Closed Lost"],
    idempotency_key: str,
    dry_run: bool = True,
) -> dict:
    """Update the Stage field of a Salesforce opportunity.

    Use ONLY when the user has explicitly asked to change an
    opportunity's stage. The first call MUST be dry_run=true so
    the agent can confirm with the user before committing.
    """
    cached = await idem_lookup(idempotency_key)
    if cached:
        return cached

    if dry_run:
        return {"status": "dry_run",
                "would_set_stage": new_stage,
                "opportunity_id": opportunity_id}

    # Downstream call uses the user-propagated OAuth token; see 15.6
    sf = get_salesforce_client_from_session()
    sf.Opportunity.update(opportunity_id, {"StageName": new_stage})
    result = {"status": "updated", "opportunity_id": opportunity_id}
    await idem_save(idempotency_key, result)
    return result
```

The schema design principles from 14.1 carry into here unchanged. An MCP server is just another packaging form for tool implementation; **the underlying engineering discipline is the same**.

**Three, structured error returns.** The MCP protocol allows tools to return errors, but the error fields are open. I make every error return `error_code` (enum) + `error_message` + `suggested_action` — same shape as in 14.5. The "shape of errors" the agent sees is the same across in-house tools and MCP tools; reasoning doesn't have to learn two schemas.

---

## 15.6 Auth: User Identity Must Propagate Downstream

The judgment in 14.3 — "tools calling downstream must use user context, not service account" — only gets stricter under MCP. An MCP server is usually deployed once and shared by many agents; if it uses one service account to call Salesforce, any client that can reach the MCP server can read the entire company's sales data.

Hesheng's approach is OAuth on-behalf-of:

```
Engineer signs into web ─── Cognito
                              │
                              ▼
              Get Salesforce OAuth token
              (Salesforce SSO connected to Cognito)
                              │
                              ▼
              session attribute carried to Bedrock Agent
                              │
                              ▼
              Agent calls MCP server, HTTP header carries token
                              │
                              ▼
              MCP server uses this token to call Salesforce
                              │
                              ▼
              Salesforce sees the engineer themselves; permission
              decided by Salesforce's profile / sharing rules
```

AWS calls this combination of [inbound auth + outbound auth](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-session-state.html) — inbound is how the client proves which user it is; outbound is how the server uses that user identity to call downstream. Neither side can be flattened to a service account.

The #1 incident I've seen: an MCP server cheaped out with a service account — fine in demo, then in prod a user asks the agent "show me Director Wang's recent opportunities," the service account is sales-director-level, and the agent reads the entire company's sales data. That customer was lucky there wasn't a PR incident. **Before MCP servers go to production in an enterprise, the auth chain must pass a full pen test.**

---

## 15.7 Tool Counts With Multiple Servers

Hesheng wired in three MCP servers — Confluence, Jira, Salesforce — each capped at 6 tools or fewer:

```
Hesheng MCP servers (3 servers, 18 tools total)
─────────────────────────────────────────────

[confluence-mcp · 4]
  search_pages(query, space_key=None, top_k=5)
  get_page(page_id)
  list_recent_pages_by_user(user_email, days=7)
  get_page_attachments(page_id)

[jira-mcp · 5]
  search_issues(jql, top_k=10)
  get_issue(issue_key)
  list_my_open_issues(user_email)
  add_comment(issue_key, body)              write
  transition_issue(issue_key, transition)   write

[salesforce-mcp · 6]
  search_accounts(name_contains, top_k=10)
  get_account(account_id)
  search_opportunities(filters, top_k=10)
  get_recent_activities(account_id, days=30)
  log_activity(account_id, type, body)      write
  update_opportunity_stage(...)             write
```

Plus the 14 in-house tools, Hesheng's agent now has 32 tools total. But 14.4's action group routing still applies — on any one invocation the model still sees 3-6 tools. **MCP widens the source of tools; the discipline from 14.4 ("the model sees only one group at a step") must be upheld.** Anthropic's argument in [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) about tool count affecting selection accuracy only matters more once MCP is wired in.

---

## 15.7b The Next Step in Tool Scaling — AWS Agent Registry (preview)

I can manage Hesheng's 32 tools in phase two. In phase three, if the rest of the Hesheng group's BUs (sales, finance, IT ops) also start building agents, the tool count climbs to a few hundred fast. Each BU's FDE reinventing the wheel — sales BU writes its own Salesforce MCP, IT BU writes its own Jira MCP — wastes effort, and there's no group-level governance (which servers are safe and trustworthy, which version is the current recommended one, who maintains it).

In 2026 AWS pushed **AWS Agent Registry** to preview, exactly for this scenario. It's a central catalog for publishing, approving, and discovering agents / tools / skills / MCP servers / custom resources. A two-resource model:

- **Registry** — the container; you can have multiple by BU, by environment (prod/QA/dev), or by resource type
- **Record** — a single resource entry, validated against a protocol schema (MCP servers against the MCP schema, agents against the A2A schema)

Four roles / workflow:

- **Admin** creates the Registry in the group AWS account, configures IAM or JWT authorization (integrating Cognito / Okta / Entra ID)
- **Publisher** submits a record — e.g., the IT team submits jira-mcp v1.2 to the registry
- **Curator** approves or rejects — typically a corporate security or platform team role
- **Consumer** searches and discovers — FDE or agent both can search (the Registry itself exposes an MCP endpoint, so an agent can query it directly to discover tools)

Hesheng phase two doesn't need the Registry yet — a single FDE team can manage 32 tools just fine. I'm covering it here because in phase three or in any group-level multi-BU project the FDE will run into the "how do we govern agents / tools" question — at that point Registry shifts from "good to know about" to "have to use."

**Distinguish it from Gateway**: Gateway is "turn an existing API/Lambda into an MCP tool"; Registry is "discover existing agent/tool resources." The two complement each other — a tool you build with Gateway can be published to the Registry so other teams can find it.

Same preview caveat as Optimization: by default it doesn't enter the production critical path on FDE projects, but it's fine for PoC exploration; wait for GA before formal production.

Docs: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/registry.html
Announcement: https://aws.amazon.com/blogs/machine-learning/the-future-of-managing-agents-at-scale-aws-agent-registry-now-in-preview/

---

## 15.8 Pre-Launch Security Check for MCP

Before MCP went to production at Hesheng, Gu Jianguo and I walked the following list together. It's not a textbook list; it's what I assembled after the service-account near-miss in phase two:

```
□ Each MCP server deployed inside the VPC, not reachable from public
□ Streamable HTTP + TLS, not bare HTTP
□ Inbound auth: SigV4 or OAuth bearer; reject anonymous
□ Outbound auth: tools call downstream with user OAuth tokens, not
   service accounts; if service account is genuinely needed, write
   it explicitly in the server README and route through approval
□ Every write tool defaults dry_run=true; idempotency_key required
□ Tool descriptions explicitly say "use only when..." / "do not use for..."
□ Tool input schema uses enum / pattern / min / max to constrain values
□ Errors structured (error_code + alternatives + suggested_action)
□ Each tool call writes audit log: who / what / when / result / trace_id
□ Rate limit per user, not just per IP
□ Tool toggles managed via config center (feature flag), not code redeploy
□ MCP servers run a vulnerability scan once before launch, quarterly thereafter
```

This list is printed and pinned on the wall in Hesheng IT. Run through it for every new MCP server.

---

## Wrapping Up

This chapter pairs with Chapter 14: Chapter 14 is on cutting an agent's own tool stack from 47 to 14, writing schemas, adding dry_run; this chapter is on when not to write your own, when to reuse community MCP servers, deploying to AgentCore stateful MCP runtime, propagating user identity. Both chapters share the same engineering discipline — strict schemas, dry_run for write-class, structured errors, never lose user context, tool-count partitioning — the only thing that changes is the packaging from Lambda action groups to MCP servers. Hesheng's 32 tools are this coexistence: business-specific stays on Lambda, generic SaaS goes through MCP. The next Part walks into delivery and craft progression — handing this off so the customer's engineers can maintain it independently, abstracting reusable patterns from the project, and the FDE's own T-shape growth path.

---

## Public references cited in this chapter

- Anthropic, [Model Context Protocol website](https://modelcontextprotocol.io) — protocol spec, SDKs, community server list
- Anthropic, [MCP launch blog (2024-11)](https://www.anthropic.com/news/model-context-protocol) — MCP design motivation and the N×M → N+M argument
- Anthropic, [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) — tool description quality, tool partitioning
- AWS, [Bedrock AgentCore — Stateful MCP Runtime GA announcement (2026-03)](https://aws.amazon.com/about-aws/whats-new/) — AgentCore-hosted MCP server capability list
- AWS, [Bedrock Agents — Session attributes docs](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-session-state.html) — inbound / outbound auth propagation mechanism
- modelcontextprotocol.io, [Servers directory](https://modelcontextprotocol.io/servers) — community-maintained MCP server list; review this page before adopting

[← Previous: Agent Toolset Design](chapter-14.md) · [Next Part: Handoff and Mastery →](../part-7/intro.md)
