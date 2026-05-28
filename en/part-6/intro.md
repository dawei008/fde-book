---
title: "Part VI — Agents and MCP"
nav_order: 16
has_children: true
---

# Part VI: Agents and MCP

Across 2025-2026, the meaning of "Agent" inside enterprise projects compressed into one specific thing — not chat Q&A, but actually getting the model to run errands across systems. Open PRs, move CRM records, read ERP, drive a browser, work a terminal, chain multiple internal APIs to close a ticket.

Once that lands in a customer environment, the FDE immediately hits a few new engineering problems: how many tools should the model actually be exposed to, how do you draw the sandbox and permission boundary, how do you resume a multi-step task after it breaks, how does MCP coexist with the customer's existing RBAC and audit. None of the earlier Parts touched these.

The two chapters in Part VI handle these Agent-era engineering questions.

---

Chapter 14 is on Agent toolset design. The most common anti-pattern is "more tools is better" — wrapping all fifty APIs from the customer's systems as tools and dumping them on the model. The result is the model picking the wrong tool, filling the wrong arguments, getting the call sequence backwards. This chapter is about designing a toolset by "enough + won't go wrong," how to draw the sandbox boundary, and how to keep recoverable intermediate state when a multi-step task fails.

Chapter 15 is on MCP (Model Context Protocol) and enterprise integration. MCP has become the de facto standard for connecting Agents to enterprise tools, but there's still a meaningful gap between "install an MCP server" and "run it safely under the customer's compliance architecture" — identity propagation, permission narrowing, audit landing, network isolation. This chapter is about wiring MCP into the customer's existing SSO / RBAC / audit stack, not standing up a parallel permission world next to it.

---

Part VI's prerequisites are everything Part III (Eval) + Part IV (data / integration) + Part V (productionization) produced — Agents can't go live without an eval set, are just demos without the data foundation, and won't hold up without the operating skeleton. Part VII covers how to hand all of this off to the customer.

---

[← End of Part V](../../part-5/chapter-13/) · [Next: Agent Toolset Design →](../chapter-14/)
