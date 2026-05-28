---
title: "Chapter 6  Week-One Tech Stack Selection"
parent: "Part III — Tech Stack Selection"
nav_order: 1
---

# Chapter 6  Week-One Tech Stack Selection

Suzhou Hesheng Precision Heavy Industries, Overseas Business Unit, conference room. Day 8 of the project.

Hesheng's machine exports route mainly through Southeast Asia — Singapore main warehouse, Kuala Lumpur, Bangkok, Jakarta, Ho Chi Minh City — five sites, 48 deployed field engineers. Three years ago they migrated MES, CRM, and ticketing to AWS Singapore region. The board wants to see the ticketing Agent in production by end of November.

CTO Zhou Mingyuan flips on the projector, three vendor proposals in hand. "They all say RAG + Agent. What are you going to do? I have to lock this with the board on Monday."

Chen Xue is the business owner for after-sales systems. Without looking up: "I only care about 95% dispatch accuracy. I can't read architecture diagrams."

Gu Jianguo, IT lead, is more direct: "I only care that this thing runs in our existing AWS account and doesn't open a second vendor relationship. Audit just got cleaned up last year."

Thirty minutes scheduled. I have to answer five questions on a single page: where does the model live, whose model, how do we call it, who orchestrates, how do we verify. All three people's questions need answers.

---

## Splitting "tech selection" into independently decidable dimensions

A lot of FDEs trip in week one because they treat "tech stack" as a single blob. Conference-room debates like "LangChain or LangGraph" — they don't resolve, because the question is meaningless on its own. Until you've decided where the model lives and whose model it is, you can't pick the orchestration framework.

I split it into five dimensions, bottom-up:

```
        ┌────────────────────────────────────────────────┐
        │ D5  Evaluation / observability                 │  ← Chapter 8
        │     How do you know it's getting better        │
        └────────────────────┬───────────────────────────┘
                             │
        ┌────────────────────┴───────────────────────────┐
        │ D4  Orchestration                              │  ← Section 6.4
        │     Who strings prompt, tool, retry, log       │
        └────────────────────┬───────────────────────────┘
                             │
        ┌────────────────────┴───────────────────────────┐
        │ D3  Invocation pattern                         │  ← Chapter 7
        │     RAG / Tool use / Agent / Fine-tune         │
        └────────────────────┬───────────────────────────┘
                             │
        ┌────────────────────┴───────────────────────────┐
        │ D2  Model selection                            │  ← Sections 6.2, 6.3
        │     Which one / which combination              │
        └────────────────────┬───────────────────────────┘
                             │
        ┌────────────────────┴───────────────────────────┐
        │ D1  Hosting plane                              │  ← Section 6.1
        │     Where the model is deployed,               │
        │     where data flows                           │
        └────────────────────────────────────────────────┘
```

D1 determines D2's option set (which models exist in that region). D2 determines D4's complexity (if a Haiku handles 95% of tickets, you don't need multi-agent orchestration). So the five dimensions aren't parallel — they have an order.

In the 30 minutes, I'll lock D1, D2, D4. D3 and D5 stay for the next two chapters.

---

## 6.1  D1: Wire the first call inside the customer's existing AWS account

I asked Gu Jianguo to pull the existing AWS account architecture diagram. A draw.io diagram with poor readability, but enough:

- Primary region: ap-southeast-1 (Singapore)
- VPC: dual-AZ, ECS in private subnets (CRM, MES) and RDS
- Egress through NAT; SaaS integrations through external whitelists
- IAM via Identity Center wired to Okta SSO
- No Bedrock usage, no model access ever opened

D1 in week one isn't "Bedrock vs. SageMaker." It's making the customer's existing account configuration capable of running the first Converse call. This step is often underestimated.

Three concrete things:

**One: open Bedrock model access.** Bedrock is off by default per account, and each model needs a separate request. In Singapore, Anthropic's Claude 4.5 series approves quickly. The 4.6 series requires going through a cross-region inference profile (cross-region into us-west-2 or us-east-1), which needs the customer to approve "is this traffic allowed cross-region." Gu Jianguo ran a 30-minute internal process and approved it.

**Two: set up Bedrock VPC endpoint.** ECS runs in private subnets — either go through NAT to call Bedrock's public endpoint, or configure a VPC endpoint. Gu Jianguo insisted on the endpoint, on the basis that traffic stays inside the VPC and an endpoint policy can constrain modelId. I supported it because it sets up the first safety guardrail along the way.

**Three: run a hello world call end-to-end.** Literally `boto3.client('bedrock-runtime').converse(...)` against haiku once and see what comes back. Looks unnecessary, but it pays back the next day at demo by surfacing every "credentials / endpoint / model ID / IAM policy" pothole at once. The first time I ran it I hit two potholes (see 6.3).

D1 locked isn't "which vendor track" — it's "the customer's account has the network/IAM/quota readiness for everything D2–D5 will need downstream." Once this is done, the ticketing Agent has a foundation.

> Two Bedrock capabilities the later chapters will use, mentioned here so we're not scrambling later. One is the Reserved/Priority/Flex three-tier service levels Bedrock introduced in November 2025 — production real-time goes Priority, batch Eval goes Flex (half price). The other is the prompt cache, which got extended from 5 minutes to 1 hour in January 2026 — for ticketing-style workloads with long system prompts and short user inputs, this matters a lot. Both are post-launch optimizations, no need to wire them in week one.

---

## 6.2  D2: Whose model

I never answer "which model is best" in a selection meeting. The question has no answer — it depends on your data.

But Hesheng's conference room is exactly where Zhou Mingyuan is asking it. What do I have? Ten customer tickets.

On day six I asked Chen Xue and Master Wang (a senior maintenance engineer) each to pick ten "most representative" historical tickets. The two had overlap and disagreement. I deduplicated the union of 20 down to 10:

- Five from mechanical group, five from electrical group (covering both dispatch destinations)
- At least one a junior would dispatch wrongly (Chen Xue flagged T-2018)
- At least one with dialect/colloquial wording ("the master says that thing's done for" — from Master Wang)
- At least one with alarm codes (`ALM 4501`, `Alarm 1042`)

Chen Xue and Master Wang double-blind labeled. Disagreements went to Chen Xue. Ten labeled in 30 minutes.

These ten are eval-v0. Too small for any scientific conclusion, but enough — enough to lock "primary model" in the conference room.

Two samples:

```json
{"id": "T-2025-Q4-0142",
 "ticket": "Customer report: JG-A6 5-axis machining center, X-axis positioning anomaly, machined parts tolerance exceeds 0.08mm, X-axis servo motor overheating Alarm 1042 detected. Engineer onsite requested.",
 "expected_team": "Electrical",
 "expected_fault_type": "Servo system"}

{"id": "T-2025-Q4-2018",
 "ticket": "New apprentice operating: he says ALM 4501 alarm on screen, can't move. I checked, coolant level is low. I had him add coolant, still alarming. Sensor broken?",
 "expected_team": "Electrical",
 "expected_fault_type": "Sensor"}
```

Full ten in repo `demos/ch6-stack/data/eval-v0.jsonl`.

---

## 6.3  Run a benchmark on the customer's data

Day seven I ran a baseline. Four candidates on Bedrock: claude-haiku-4-5, claude-sonnet-4-6, claude-opus-4-6, amazon nova-pro. Three calls per ticket per model.

Hit two potholes worth recording.

**Pothole one:** Anthropic's models on Bedrock can't be invoked with on-demand model IDs. First run, every Claude returned:

```
ValidationException: Invocation of model ID anthropic.claude-opus-4-6
with on-demand throughput isn't supported. Retry your request with the
ID or ARN of an inference profile that contains this model.
```

This is a hard requirement after Bedrock pushed cross-region inference. Claude models must use an inference profile ID like `us.anthropic.claude-opus-4-6`. Nova works either way, but I went with profiles for consistency.

```python
MODELS = {
    "claude-haiku-4-5":  "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "claude-sonnet-4-6": "us.anthropic.claude-sonnet-4-6",
    "claude-opus-4-6":   "us.anthropic.claude-opus-4-6",
    "nova-pro":          "us.amazon.nova-pro-v1:0",
}
```

Hesheng's primary region is Singapore, but I ran this benchmark in us-east-1 because all four candidates are directly available there. The Singapore region didn't have everything open at the time — would've required cross-region inference profiles. The point of this step is to confirm "which model is good enough" — region availability is a secondary fit check at landing time. I explained it to the customer the same way.

**Pothole two:** Claude 4.6 series no longer accepts `temperature` on the Converse API:

```
ValidationException: `temperature` is deprecated for this model.
```

The old script wrote `inferenceConfig={"temperature": 0.0}` and immediately broke. Branch by model:

```python
def inference_config(model_id):
    cfg = {"maxTokens": 200}
    if "4-6" not in model_id:
        cfg["temperature"] = 0.0
    return cfg
```

Neither pothole was discoverable from docs. I hit them by running the actual code. That's exactly why on the customer's network in week one, you have to run hello world end-to-end.

The call body is simple:

```python
client = boto3.client("bedrock-runtime", region_name="us-east-1")

def call(model_id, ticket):
    t0 = time.perf_counter()
    resp = client.converse(
        modelId=model_id,
        messages=[{"role": "user",
                   "content": [{"text": PROMPT.format(ticket=ticket)}]}],
        inferenceConfig=inference_config(model_id),
    )
    return {
        "text": resp["output"]["message"]["content"][0]["text"],
        "in_tokens": resp["usage"]["inputTokens"],
        "out_tokens": resp["usage"]["outputTokens"],
        "elapsed_ms": (time.perf_counter() - t0) * 1000,
    }
```

Full code: repo `demos/ch6-stack/scripts/bench.py`.

The numbers (2026-05-23, us-east-1, 30 calls per model):

| Model             | Dispatch accuracy | Fault-type accuracy | P50 latency | P90 latency | $/1k tickets |
| ----------------- | ----------------- | ------------------- | ----------- | ----------- | ------------ |
| claude-haiku-4-5  | 100%              | 40%                 | 784ms       | 918ms       | $0.37        |
| claude-sonnet-4-6 | 93%               | 40%                 | 1340ms      | 1997ms      | $1.10        |
| claude-opus-4-6   | 100%              | 40%                 | 966ms       | 2383ms      | $5.63        |
| nova-pro          | 90%               | 40%                 | 498ms       | 536ms       | $0.27        |

Total run cost ~$0.50.

I printed the table and brought it into the conference room. Chen Xue scanned: "Why is fault-type 40% across the board? All four the same?"

A good question. Four candidates all stuck at 40% on fault type — that's almost certainly an eval design problem, not a model capability problem. I went back later to look: Chen Xue labeled with "servo system," but models often output "servo motor." Semantically the same, character string different. Chapter 8 expands on this — it isn't what this selection meeting needs to solve, but it has to be acknowledged.

On dispatch accuracy, haiku at 100% looks best, but within ten samples' ±10% error band, all four candidates are roughly hitting bar. Ten samples tell me "all four enter the candidate pool," not "haiku beats opus." Distinguishing them needs 200+ samples.

What actually drives the call is latency and cost:

- nova-pro P90 is 0.5s, opus-4-6 is 2.4s. 5x. Dispatcher experience changes from "instant" to "wait a moment."
- Unit price nova-pro $0.27 vs opus-4-6 $5.63. At 230 tickets/day annualized, $25 vs $516.

Hesheng's tickets are 95% simple triage. I don't need opus on every one. Final recommendation: primary + fallback.

```
primary:   claude-haiku-4-5  (95% simple tickets)
fallback:  claude-opus-4-6   (5% complex tickets)

Upgrade conditions: ticket length > 200 chars OR contains alarm code OR customer tier = A

Mixed cost:    0.95 × $0.37 + 0.05 × $5.63 = $0.63 / 1k tickets
Mixed latency: 0.95 × 0.92s + 0.05 × 2.4s   = 0.99s
```

This is 9x cheaper than all-in opus, 70% more expensive than all-in haiku, but the accuracy ceiling reaches opus-level.

> Six months ago you'd have written a routing layer for this primary+fallback yourself. In May 2026 Bedrock launched the Advanced Prompt Optimization and Migration Tool, which auto-runs cross-model A/B and outputs latency and cost comparisons. If you're doing exactly the experiment in 6.3, you can save some manual work. But for teaching, I still recommend writing your own bench.py — you need to know what every line does. Tooling comes later.

Back in the conference room. I read the table to Zhou Mingyuan. He nodded: "I can sell this to the board." Chen Xue: "5% complex tickets to opus — what stops the upgrade condition from misfiring and routing simple ones to opus too?" Me: "We'll walk through the upgrade router after I write Ch7." Gu Jianguo: "This cross-region inference profile thing — can we pull it back to Singapore?" Me: "Yes. Bedrock's Singapore region has the entire Claude 4.5 series open now; 4.6 go cross-region. We'll do another regional fit check before landing — the difference is mainly latency, doesn't affect the selection logic."

D2 locked.

---

## 6.4  D4: When you don't need a framework

Day two, Zhou Mingyuan came over: "I had the team look at LangGraph. Heard it's pretty good. Should we just bring it in?"

I said no. Not because LangGraph is bad — because Hesheng doesn't need it for this phase.

Across the agent projects I've worked on, the share of projects that introduced a framework in week one and where the customer's own engineers could maintain it independently six months later is under 50%. Frameworks aren't worthless — but their value only surfaces once project complexity actually warrants them. Before that, introducing a framework adds a layer of learning burden and a class of debug blind spots for the customer.

I split agent orchestration into three levels:

**Level 0: direct boto3, write the dispatcher yourself.**
200 lines of Python. State is request-level, every call computes from scratch. Logs to CloudWatch Logs, metrics emitted by hand. Capable of: triage, routing, simple RAG, tool use.

**Level 1: lightweight agent SDKs (Strands, LangGraph, AutoGen).**
500 lines. Framework manages dialog stack, tool-call traces, retries. Capable of: everything above plus multi-step planning and tool chaining.

**Level 2: managed agent platforms (AgentCore).**
1000+ lines plus a heap of config. Platform handles session, policy, observability. Capable of: long sessions (hour-to-day scale), cross-team collaboration, complex approval flows.

Hesheng's tickets close in 30 minutes; single agent, single tool (KB retrieval); only one team modifying code in phase one. This is textbook Level 0. I had the team write 200 lines straight; reassess upgrades in six months.

Three signals to verify the call:

```
Two or more must hold → consider Level 2 (AgentCore):

  A. Single user's session state needs to span more than 8 hours
     e.g., agent waits for customer to upload a doc; 6 hours later
     customer uploads, agent picks up

  B. Agent calls 5+ tools, at least one needing admin approval
     e.g., parts ordering needs supervisor approval, agent pauses

  C. 4+ teams modifying the same agent simultaneously
     e.g., after-sales/sales/IT each contributing tools, needing
     policy isolation between them
```

Hesheng meets none. That's the engineering reason for recommending Level 0, not intuition.

If at some point Hesheng meets the criteria — say phase two integrates parts ordering (signal B), and adds sales (signal C) — I'd reassess. AgentCore has done a lot of solid work this past year. As of May 2026 it ships 11 capabilities total (the official list on the FAQ):

- **Runtime** — serverless deployment of agents / MCP servers, 8-hour long tasks, bi-directional streaming, session isolation, VPC connectivity
- **Gateway** — convert REST APIs / Lambdas / existing MCP servers into MCP-compatible tools in one click
- **Memory** — cross-session context storage
- **Browser** — cloud browser for the agent to operate websites
- **Code Interpreter** — sandbox running Python / JS / TS
- **Identity** — integrates Cognito / Okta / Entra ID, manages agent credentials
- **Observability** — Trace, debug, CloudWatch GenAI dashboard in one
- **Evaluations** — LLM-judge + code evaluators, 5 evaluation modes (online / on-demand / batch / dataset / simulation). See Ch8
- **Policy** — Cedar natural-language policy authoring, gates tool-call layer (different from Bedrock Guardrails which gates content)
- **Agent Registry** (preview) — central catalog inside an enterprise to publish / approve / discover agents / tools / MCP servers. See Ch15
- **Optimization** (preview) — auto-generate prompt / tool-description improvement candidates from production traces, plus A/B validation. See Ch13

For Hesheng phase two I ended up using 5 of them: Runtime, Gateway, Identity, Observability, Evaluations. Browser / Code Interpreter didn't fit our workflow; Policy wasn't worth it because writing rules by hand for 14 tools was simpler; Registry and Payments are preview, so they don't enter the production path; Memory wasn't needed because our sessions don't require cross-session persistence.

The judgment logic matters — AgentCore's 11 capabilities aren't a checklist where "you must use them all". It's "adopt as needed". Each capability comes with a specific engineering reason. In phase three, when Hesheng's group needs multi-BU coordination, Registry will become mandatory; for a financial customer running workflows that need supervisor approval, Policy will become mandatory. For phase one, Level 0 remains the default starting point.

If you want details on each capability's boundary, `research/whats-new-2026.md` in the repo lists every Bedrock + AgentCore update from November 2025 to May 2026; `research/agentcore-2026-features.md` is the per-item summary of all 11 capabilities.

---

## 6.5  What gets handed across the conference table

Back to that 30-minute meeting in week one. What I handed Zhou Mingyuan was an A4 page:

```
Hesheng Precision Heavy Industries · Overseas Ticketing Agent v1 selection
─────────────────────────────────────────────────────────────────────────

D1 Hosting:    AWS ap-southeast-1 (existing account)
               Bedrock VPC endpoint + Identity Center ready
               Claude 4.5 series native; 4.6 via cross-region inference

D2 Models:     primary  claude-haiku-4-5
               fallback claude-opus-4-6  (length>200 / has alarm code / A-tier)
               Estimate $0.63/1k tickets, P50 1s, dispatch accuracy ≥ 95%

D3 Pattern:    RAG + tool use, no agent                     (Ch 7)

D4 Orchestration: boto3 + 200-line dispatcher                (this Ch 6.4)
                  Reassess upgrade against A/B/C signals in 6 months

D5 Eval:       eval-v0 (10 samples) → eval-v1 (200 samples)  (Ch 8)
               Four pre-launch must-dos in Ch 8

Locked through: 2026-08-23 (3 months)        Zhou Mingyuan ____
                                             Chen Xue       ____
                                             Gu Jianguo     ____
```

Three signatures landed. This page is my talisman for the next three months — every time someone asks "why not opus," "why not agent," I pull the page out. All three of them signed it.

---

## Pitfalls I stepped on this chapter

In order:

Day three, I started writing the bench script before reading the IAM architecture diagram. I used my own AWS account credentials. Day five Gu Jianguo pushed me the customer's account architecture, and I discovered the endpoint policy only allows specific modelIds. None of my scripts ran on the customer's account. **Get the customer's account architecture diagram on day one of week one.**

Day six, I had Chen Xue label eval alone. She said "close enough is fine." I later learned she wasn't familiar with electrical-group alarm codes, and she had T-2018 mislabeled. **Eval labeling has to be double-blind**, ideally business owner + front-line engineer.

Day seven, when running bench, I copied a 6-month-old script directly and ran into the inference profile and temperature potholes back-to-back, costing 40 minutes. **In week one you have to run every candidate model end-to-end on the customer's network** — not from the README, actually run it.

Day eight, in the conference room, I almost said "haiku at 100% beats opus." If I hadn't glanced at the data once more before going in and remembered the ±10% error, I'd have said it. **Ten samples can tell you all four candidates pass; they can't tell you who's better.**

---

## Next chapter

D3 is unresolved: RAG, Tool use, Agent, fine-tune — which?

Hesheng has 5,000 PDFs (product manuals + historical ticket archive + maintenance knowledge base), and Zhou Mingyuan's instinct is "let's start with RAG." Is that right? That's the next chapter.

[← Part III Intro](../intro/) · [Previous: From Requirements to SOW and Eval Set](../../part-2/chapter-05/) · [Next: RAG / Fine-tune / Agent decision tree →](../chapter-07/)
