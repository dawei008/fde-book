---
title: "Chapter 16 — Skill: Packaging Customer Expertise for Agents"
parent: "Part VI — Agents and MCP"
nav_order: 3
---

# Chapter 16: Skill — Packaging Customer Expertise for Agents

Hesheng Suzhou plant floor, week 5 after phase-two GA. Master Wang stood beside the dispatch desk and said: "Your agent dispatches fast, but there's one class of tickets it can't learn — overseas tickets in local-language phrasing. I looked at 12 today, agent got 3 wrong, all written by Vietnamese engineers; they say 'machine doesn't work,' which actually means 'servo alarm.' Before I retire, can you teach this to it?"

Master Wang has been a senior maintenance engineer at Hesheng for 28 years; he retires year-end. He's brought this up twice. First answer: "I'll add the cases to KB" — done; agent improved slightly, not robustly. Second: "I'll fold it into the system prompt" — prompt grew to 6,000 tokens, and both hits and misses got more random.

By the third time he asked I was already thinking about another shape. In early 2026 Anthropic promoted **Skill** to a first-class concept across Claude Code, the Claude Agent SDK, and the Claude API. This chapter is about how to use it — not prompt, not tool, not MCP. A different way to install "expertise" into an agent.

---

## 16.1 The Real Difference Between the Three Shapes

Chapter 14 covered Tool, Chapter 15 covered MCP. This chapter adds Skill — three in parallel. New FDEs mix them up the first time. The opening table I always draw for customer engineers:

| Shape | What it is | Who writes it | When it loads | One-liner |
|---|---|---|---|---|
| **Tool** | An atomic capability (API call, SQL, file read) | You | Exposed to the model on every inference | The model calls one per reasoning step |
| **MCP server** | A standardized interop wrapping for a group of tools | Someone else writes; you connect | Connected via the MCP protocol | Lets you use tools other people wrote |
| **Skill** | A package of "expertise" — prompt + flow + templates + scripts, loaded on demand | You or the customer's domain expert | The model decides whether to load by description | Like installing a job-specific SOP into the agent |

Three engineering distinctions:

**Tool is a stateless capability.** `query_tickets()` runs once, returns SQL rows. The model can compose tools into complex action, but each tool does one small thing.

**MCP server is the remote-publishing form of tools.** Underneath it's still tools, just protocol-wrapped — instead of writing your own Salesforce client, you connect to someone's Salesforce MCP server and you have a set of Salesforce tools.

**Skill is not capability — it's knowledge.** It tells the agent: "when you see problems of class X, think in pattern Y, write to template Z, follow flow W." A Skill itself executes nothing; it directs the model how to use existing tools / knowledge.

The cleanest test: you want the agent to **do one more thing** → Tool. You want the agent to **plug into an external system** → MCP. You want the agent to **learn one way of working** → Skill.

---

## 16.2 The Shape of a Skill

A Skill is a directory containing one `SKILL.md`, possibly with co-located scripts, templates, and reference material. `SKILL.md` looks like this:

```markdown
---
name: hesheng-overseas-triage
description: Use this when triaging tickets from Hesheng's overseas service
  stations (Singapore / KL / Bangkok / Jakarta / HCMC). Covers local-language
  patterns, regional fault codes, and dispatch rules that differ from
  domestic triage. Activate when a ticket's `site_id` is overseas.
---

# Hesheng Overseas Triage

When a ticket comes from an overseas station, three things differ from domestic
triage:

## 1. Phrasing patterns

Vietnamese / Indonesian engineers often describe symptoms in non-technical
phrases. Translate before classifying:

- "machine stopped" / "máy không chạy" → check for servo alarm first, not "stuck"
- "screen black" / "màn hình tắt" → power supply OR display board
- "wrong sound" → bearing OR spindle (need site to confirm)

(Full mapping in `glossary-overseas.md`)

## 2. Regional fault codes

JG-A6 in HCMC ships with firmware variant v3.2.1, which adds alarm codes
ALM 7100-7199 not in the domestic table. When you see ALM 71xx, route to
HCMC-local electrical team, not Suzhou.

## 3. Dispatch rules

Overseas dispatch is constrained by visa + parts inventory:
- Tickets needing parts not in regional warehouse → escalate to Suzhou
  before dispatching local engineer
- Tickets needing engineers from another country → check
  `regional-visa-table.csv` (this directory) for current visa policy
```

Two facts about Skills that get missed most often:

**First, the entry point is the description field.** When the model decides which Skills to load, it reads each Skill's description. Whether the description is well-written directly determines the Skill's hit rate. The description is not for humans — it's for the model. It must be specific enough about "when to trigger" that the model can decide based on the user input.

**Second, a Skill consumes tokens only when loaded.** The Skill systems in Claude API / Agent SDK / Claude Code first scan every Skill's description (short), decide which ones to load, and only then read the body + co-located files into context. This means you can register dozens of Skills without paying for dozens of Skill prompts — only the matching few enter the prompt.

This is the fundamental difference from "stuff it into the system prompt." System prompt pays full token cost on every call; Skill is on-demand. Hesheng's example: previously stuffing 6,000 tokens into every triage call, now only overseas tickets (~30% of total) load this 1,500-token Skill; domestic tickets go the regular path. Token cost dropped by roughly half.

---

## 16.3 Decision Tree: Tool / MCP / Skill

The decision tree I give customer engineers — every time they want to "make the agent learn to do X," they walk it:

```
What new thing should the agent know how to do?
    │
    ├─ Is it "call an external API / database"?
    │      Yes → write a Tool
    │      └ Already written by someone else?
    │            Yes → connect to an MCP server
    │            No → write your own Tool (Lambda / function)
    │
    ├─ Is it "follow a way of working / write to a template"?
    │      Yes → write a Skill
    │
    └─ Is it "learn a body of knowledge / a lookup table"?
           Yes → check size
                Small (< 4000 tokens) → put in system prompt or Skill body
                Large → use RAG / KB
```

Concretely for Hesheng's overseas triage problem:

- "Know Vietnamese phrasing equivalents" — knowledge, but bundled with the judgment "when to translate, when not" → **Skill**
- "Look up what ALM 71xx means" — a table lookup → existing KB tool (already exists)
- "Decide whether a ticket goes to local dispatch" — a judgment by chapter and verse → **the chapter and verse in a Skill** + existing dispatch tool

The "expertise" Master Wang wants to leave behind is a hybrid: part knowledge (dialect map), retrievable; part judgment (when to escalate to Suzhou by visa), only humans understand. Skill formalizes the latter so the agent walks the rules.

---

## 16.4 The Description Is the Skill's Trigger Surface

Whether a Skill is well-written shows first in whether its description is precise. I've seen new FDEs get this wrong over and over.

Too broad:

```yaml
description: A skill for handling tickets.
```

The model sees this and almost any ticket triggers — you write 12 Skills with descriptions like this; every call loads all of them; token cost explodes and they conflict.

Too narrow:

```yaml
description: Use when ticket text contains "máy không chạy".
```

Only an exact phrase triggers — any variant (synonym, misspelling, other language) misses. The model sees this description and the judgment surface is too small; on regular tickets it never even thinks of loading this Skill.

**Right shape:**

```yaml
description: Use this when triaging tickets from Hesheng's overseas service
  stations (Singapore / KL / Bangkok / Jakarta / HCMC). Covers local-language
  patterns, regional fault codes, and dispatch rules that differ from
  domestic triage. Activate when a ticket's `site_id` is overseas.
```

Three properties:

1. **Explicit trigger condition**: "overseas service stations" + "site_id is overseas" — the model can decide directly from ticket metadata
2. **Multiple scenarios but cohesive**: dialect, codes, dispatch — three things all in the "overseas triage" cluster
3. **Mutually exclusive with other Skills**: doesn't collide with "domestic triage" or "parts ordering"

After writing a description, I run a test: combine it with all other Skills' descriptions in a mock prompt; give the model 20 tickets; watch which it picks. If hit rate is below 90% (should-have-loaded-but-didn't, or shouldn't-have-but-did), revise the description.

This step is more worth your time than writing the body. Body wrong → fix body. Description wrong → the model never loads your Skill at all; it doesn't matter how good the body is.

---

## 16.5 Publishing Skills in the Customer Environment

Where does this Hesheng Skill get published? Three deployment shapes for three customer scenarios:

**Scenario A: Claude Code users** (FDE + customer engineers, locally)

Skills live at `~/.claude/skills/<name>/SKILL.md`. Claude Code scans on startup; matching descriptions get loaded. Good for development — FDE writes a Skill at the customer's desk, immediately tests in their own Claude Code, ships only when right.

**Scenario B: Agents deployed via Claude Agent SDK** (production agents)

Skills are baked into the agent's container image at a conventional path (e.g., `/app/skills/`). The agent loads on startup. Versioning rides with the image; rollback means going back one image. Hesheng's phase-two Skill takes this path.

**Scenario C: Direct calls to the Anthropic API** (app layer calls Claude API)

The app layer concatenates Skill body into the system message or uploads via the Files API. More primitive than the previous two; the app code has to manage "when to load which Skill." Less automated, but most flexible.

Hesheng is scenario B. Our publish flow:

```
Dev:    FDE writes Skill in their Claude Code; tests description hits
        ↓
Merge:  PR into main; /skills/ has lint check (description ≥ 30 chars)
        ↓
Eval:   CI runs eval-v3 + overseas subset (10 overseas tickets);
        hit rate must be ≥ 90%; accuracy must be ≥ baseline + 5pp
        ↓
Image:  After merge, GitHub Actions builds image, pushes to ECR
        ↓
Canary: AgentCore Runtime cuts 5% traffic to new image; observe 24h
        ↓
Full:   Dashboard metrics show no regression → 100%
        ↓
Old:    Old image retained 7 days for one-click rollback
```

This is essentially the same pipeline as Chapter 13's prompt canary release — the difference is Skill changes are "heavier" (body + co-located files), so they ride container images instead of Parameter Store.

**If the customer is air-gapped** (common in finance / healthcare): copy the pipeline; swap ECR for the customer's internal registry; swap AgentCore Runtime for the customer's K8s. This abstraction holds completely offline — Skill is just files; no external dependencies.

---

## 16.6 Skill vs Bedrock Agent Action Group / Agent Toolset

Two AWS-side concepts whose names look like Skill but are not Skill — FDEs run into this on first contact:

**Bedrock Agent Action Group** is Bedrock Agents' tool grouping — register multiple Lambdas under one agent following an OpenAPI schema; the agent runtime handles tool routing. Action group is a **container of tools**, not knowledge. Same idea as the action-group concept in Chapter 14's Strands agent (application-level), just a different wrapping layer.

**Agent Toolset** is the broader term — the set of tools exposed to an agent. It's the topic of all of Chapter 14, not a specific product.

**Difference from Skill**: Skill packs "by what method to do things"; the previous two pack "what things can be done." A single agent can have Action group (=tools) + Skill (=method) at the same time:

```
Hesheng phase-two agent
├─ Tools (14, wrapped via action group):
│   ├─ query_tickets, lookup_alarm_code, ...
│   └─ stateful MCP: salesforce_search, salesforce_update
│
└─ Skills (5, in Anthropic Skill form):
    ├─ hesheng-domestic-triage
    ├─ hesheng-overseas-triage  ← Master Wang's
    ├─ hesheng-parts-ordering-sop
    ├─ hesheng-customer-receipt
    └─ hesheng-incident-postmortem
```

Both coexist, no conflict — tools are hands and feet, Skills are the SOP cards in the brain. On every inference the model combines both: tool descriptions tell it what's possible; loaded Skills tell it how to proceed.

---

## 16.7 The 5 Skills That Hesheng Phase Two Settled On

The 5 Skills that stabilized over Hesheng's year. Each maps to a specific "customer expertise" — a way of working that originally lived in one veteran's head:

| Skill | Source | Problem it solves |
|---|---|---|
| **hesheng-domestic-triage** | Chen Xue + dispatch leads | Dispatch rules across the 5 domestic stations; A/B/C customer priority |
| **hesheng-overseas-triage** | Master Wang | Overseas dialect; JG-A6 overseas firmware ALM 71xx; cross-border dispatch under visa / parts constraints |
| **hesheng-parts-ordering-sop** | Warehouse manager | Warehouse priority on parts (transfer first, then purchase); thresholds for emergency markups |
| **hesheng-customer-receipt** | Overseas sales | Tone and template for Vietnamese / Indonesian customer reply emails (not literal translation) |
| **hesheng-incident-postmortem** | Me | Postmortem method extracted from Chapter 13's incident timeline workflow |

Writing these 5 Skills took roughly two weeks. **The real workload isn't writing — it's finding** — finding 5 actual experts inside Hesheng, sitting with each for 4-6 hours, extracting their judgment patterns line by line, having them review them one by one. The first draft of each Skill was mine; sign-off had to come from the source expert — what's in the Skill is their judgment, not mine.

Master Wang's was the most interesting. My first draft turned his "first check whether it's a servo alarm" into a single rule. He read it and said: "No. This rule only holds for the Vietnam station; the engineers in Ho Chi Minh City say 'servo' when they actually mean 'pneumatic' — they don't distinguish locally." That's when I realized Skills must be subdivided by station. The final hesheng-overseas-triage has a section split across 5 stations of dialect maps.

**Most valuable judgment in this section**: a Skill is the engineering move that formalizes "the way of working in a veteran's head." It's not the FDE inventing prompts — the FDE can't invent this kind of method, hasn't worked 28 years in this industry. The essence of a Skill is the FDE acting as **editor of the method**, not author of the method.

---

## 16.8 Closing

Chapter 14 gave Tool. Chapter 15 gave MCP. This chapter gave Skill. Three shapes side by side — decomposing the abstract question of "how does an agent extend" into three concrete forms: capability, interop, expertise.

Hesheng phase two's agent stays stable not because any one shape dominates, but because the three each manage their own slice: 14 tools as hands and feet, 5 Skills as SOP cards in the brain, stateful MCP attaching Salesforce and ServiceNow. Chapters 14 / 15 / 16 together are the full picture of a real production agent.

The next Part enters handoff — Master Wang's Skill is written down, the agent learned it, but the day he retires, can the customer's receiver maintain this Skill? That's Chapter 17.

---

## Public references for this chapter

- Anthropic, [Claude Skills documentation](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) — official Skill definition, frontmatter spec, loading mechanism
- Anthropic engineering blog — *Equipping agents for the real world with Agent Skills* — the Skill vs prompt engineering argument
- Anthropic, [Claude Agent SDK documentation](https://docs.claude.com/en/api/agent-sdk/overview) — Skill loading in the SDK layer

---

[← Part VI Intro](../intro/) · [Previous: MCP Integration](../chapter-15/) · [Next Part: Handoff and Continuity →](../../part-7/intro/)
