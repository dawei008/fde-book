---
title: "Chapter 7  RAG / Fine-tune / Agent Decision Tree"
parent: "Part III — Tech Stack Selection"
nav_order: 2
---

# Chapter 7  RAG / Fine-tune / Agent Decision Tree

Chapter 6 nailed down "whose model" (Hesheng case picked Claude Haiku 4.5 + Opus 4.6 fallback). But **the model is just the engine** — you still have to decide how to connect the customer's knowledge and workflow to it. That's what this chapter is about.

Four mainstream connectors:

- **Prompting** — only modify the prompt; the model answers from pretraining.
- **RAG** — index an external knowledge base; the model retrieves before answering.
- **Fine-tune** — train the customer's data into the model weights.
- **Agent** — let the model plan, call tools, perform multi-step reasoning.

The most common failure mode for beginner FDEs is hearing "build an AI assistant" and immediately stacking the most complex of the four — agent + RAG + fine-tune all together. Six weeks later you have an unmanageable monster, and on a specific question the customer asks, it does worse than ChatGPT with a plain prompt.

This chapter gives a **judgment order**: try prompting first; if not, add RAG; if not, add agent; only at the end, consider fine-tune. Validate each step with the customer's real data; only step down when the bar isn't met.

---

## 7.1  The essence of the four connectors

| Connector | Input handling | Knowledge source | Output generation | One-line take |
|---|---|---|---|---|
| **Prompting** | Raw query | Model pretrained weights | Direct generation | Change the prompt and let the model figure it out |
| **RAG** | query → retrieve | External knowledge base (updatable) | Retrieve + generate | Put the answer in a knowledge base; model looks it up and answers |
| **Fine-tune** | Raw query | New weights (you trained) | New model generates | Train the answer into the model's brain |
| **Agent** | query → plan | Tool-call results + model weights + KB | Multi-step reasoning + synthesis | Let the model use tools to get things done |

One thing to notice: **the four connectors aren't mutually exclusive.** Most production LLM apps are prompting + RAG; the more complex ones are prompting + RAG + agent. Fine-tune typically pairs with one of the first three; projects that ship purely on fine-tune are rare.

---

## 7.2  Decision order: try the cheap things first

The standard order I use during selection with a customer:

```
Default order:
  1. Prompting first  (cheapest, fastest)
  2. Not enough → add RAG (external knowledge)
  3. Still not enough → add Agent (let the model take action)
  4. Last resort → Fine-tune (most expensive, hardest to maintain)
```

**For 90% of LLM apps, prompting + RAG is enough.** Fine-tune is the option of last resort.

Why this order? Because the cost structure of the four is very different:

| Connector | Startup cost | Marginal cost | Maintenance cost |
|---|---|---|---|
| Prompting | A few hours of tuning | Per-call token cost | Edit the prompt (half hour) |
| RAG | Days to a week | Retrieval + call | Index rebuild (hours to a day) |
| Agent | Weeks | Multi-step + tool calls | Tool protocol upgrades + monitoring |
| Fine-tune | Weeks to months | Inference (self-host or managed) | Model retraining (days each) |

**The most important judgment isn't "which is most powerful," it's "can the customer's pain be solved with a cheaper connector?"** Try prompting; when prompting hits its ceiling, escalate. This is the concrete grounding of outcome-driven thinking — you're accountable for the result, not for "which complex stack we used."

---

## 7.3  How to decide which connector for the current pain

The four connectors map to four typical pain types. Decision logic:

**Question 1: Is the customer's pain "the model doesn't know the answer" or "knows but answers wrong"?**

If it's "doesn't know" — domain knowledge not in pretraining, latest data, customer-internal information — default to RAG. RAG's essence is "let the model look it up before answering."

If it's "knows but answers wrong" — answers feel mechanical, style is off, industry terminology used incorrectly — try prompting + few-shot first. Give the model 3–5 demonstration examples saying "this kind of question gets answered like this" — most style problems resolve here.

Back to the Hesheng ticket-triage example (Chapter 6): the pain is "the model should dispatch the ticket to the mechanical or electrical group." This is "knows but answers wrong" — the model fully understands the Chinese ticket text, but the dispatch logic is internal to the customer (which faults go to mechanical, which to electrical). Try prompting + few-shot — give the model 5–10 real dispatch demonstrations, then have it judge new tickets.

**Question 2: Tried prompting, accuracy can't go up — what to add?**

Look at why it can't go up.

If it's because **the prompt is too long / few-shot can't fit** — e.g., the customer has hundreds of fault codes, each with different processing flows, can't all fit in the prompt — escalate to RAG. Index the fault-code library as an external KB and retrieve the relevant ones into the prompt per query.

If it's because **the prompt is correct but the model output is still inconsistent** — same ticket asked twice yields two different dispatches — this is the model's "pattern coverage" problem. Try adding more explicit rules in the prompt ("if the ticket contains alarm codes 4501–4999, electrical group"); if still not, consider fine-tune.

**Question 3: The customer's need isn't "answer questions" but "do things automatically" — what then?**

Go agent. "Do things automatically" is characterized by: the model needs to **call external tools** (query APIs, write to databases, send emails), and **steps are dynamic** (not a fixed pipeline; the model decides next-step from previous-step results).

But beware — many customers say "I want an agent" but the actual requirement is "I want a fixed-flow automation." Those are handled with prompting + workflow orchestration (Step Functions, Airflow); no LLM planning needed. **Test:** if you can draw a flowchart enumerating every possible execution path, you don't need an agent. If the branches explode beyond what you can draw, an agent earns its complexity.

Hesheng's ticket triage: pure classification, no agent needed. If phase two expands to "triage + auto-call ERP for parts inventory + auto-send acknowledgement to customer" — that's an agent.

**Question 4: When do you actually need fine-tune?**

Three scenarios:

- **Style / jargon never matches**: prompting plus all the few-shot in the world can't reach the target style. Common in legal, medical, other heavily specialized domains.
- **Latency / cost won't add up**: your prompt is too long (thousands of tokens), call frequency is high, paying the prompt cost every call is unacceptable. Fine-tune compresses knowledge into weights; the prompt can shrink to a few hundred tokens.
- **Private deployment + strict data sensitivity**: customer doesn't allow data to be sent to any external API (even a "private cloud" Bedrock-style one), it has to run in their own data center — typically paired with fine-tune.

90% of LLM projects don't fit any of those three. Fine-tune is the terminal option, not the default.

---

## 7.4  Walking through Hesheng's decision

Back to Chapter 6's Hesheng ticket triage. Chapter 6 nailed model selection; this chapter decides how to connect the customer's ticket data:

**Step one:** try prompting + few-shot.

Have the model judge mechanical vs. electrical from the ticket text. Stuff the prompt with 10 real dispatch demonstrations (5 mechanical + 5 electrical). The bench in Chapter 6 already ran — haiku at 100% on 10 samples. Says the dispatch logic is solvable with prompting.

**Question:** Chapter 6's bench was 100% on 10 samples. Will it hold on 200?

That measurement happens during Scaffolding. It's the v0 → v1 expansion of the Eval set; Chapter 8 covers it. The most important judgment at this step: **at minimum 100% on 10 samples means this path is viable** — don't rush to RAG or agent. Push prompting to v1.0 first; if the bar isn't met, go down.

**Step two:** decide whether to add RAG.

Hesheng's tickets have characteristics: alarm codes (`ALM 4501`), machine model references (`JG-A6`), specific fault types. The model's pretraining doesn't have Hesheng's alarm code table, no JG-series machine fault crosswalk — these are customer-internal knowledge.

But can the prompt hold them? Hesheng's alarm code table is about 200 codes — fitting them all in is roughly 3,000–4,000 tokens. Claude Haiku 4.5's context is 200K, easily fits. The 1-hour prompt cache from Chapter 6 means a long system prompt won't be paid for every call.

**Conclusion:** phase one, no RAG. Stuff alarm codes and machine-model fault tables into the system prompt. The 1-hour prompt cache makes this efficient.

When does RAG become necessary? Two situations:

- Customer's alarm code table grows to thousands and won't fit in prompt
- Customer adds scenarios needing retrieval over historical maintenance records (e.g., "how were similar faults handled in the last six months") — that's a real RAG scenario

**Step three:** decide whether to add agent.

Hesheng phase one's scope is just "triage" — given a ticket, output a structured judgment (dispatch group + fault type + priority). No "call external tools" requirement.

If phase two expands to "after triage, auto-call ERP for parts inventory" — that's agent. But phase two isn't in phase-one scope.

**Conclusion:** phase one is prompting only. No RAG, no agent. Simplest architecture, lowest cost, easiest for the customer's engineers to maintain.

---

## 7.5  Key engineering decisions for RAG (if you go there)

If your project does need RAG (Hesheng phase one doesn't, but many LLM application projects do), the key decision points are below.

### Chunking strategy

Chunking is the easiest place to mess up RAG. Two common errors:

- **Too granular**: 500 tokens per chunk, retrieval returns incomplete fragments, the model answers from broken information.
- **Too coarse**: 4,000 tokens per chunk, token cost explodes, and the model's ability to focus across long context degrades.

Practical experience: **chunk by document structure first** (chapter, paragraph) preserving semantic completeness; **chunk long paragraphs again at 800–1,500 tokens** with 100–200 token overlap to prevent information cuts. Bedrock Knowledge Bases ships hierarchical chunking by default — saves you from rolling your own.

### Retrieval method

Three mainstream:

- **Dense retrieval (vector similarity)**: embed query and docs, compute cosine. Strong for semantic match (synonyms, paraphrases). Weak on exact-keyword matches (people, product IDs, error codes).
- **Sparse retrieval (BM25)**: traditional keyword matching. Strong on exact keywords, weak on semantics.
- **Hybrid retrieval**: dense + sparse in parallel, results merged. Standard in most production RAG systems.

For Hesheng's alarm-code-bearing scenario: pure vector retrieval would miss alarm codes. Hybrid is required. Bedrock Knowledge Bases now natively supports hybrid search — one config flag.

### Reranking

Top 10 retrieved docs almost always include several irrelevant ones. Stuffing all of them into the prompt wastes tokens and disrupts the answer.

Add a reranking layer — use a small model (Cohere Rerank, Bedrock's built-in rerank) to rescore top 10, pick top 3–5 into the prompt. This step measurably improves answer quality at minimal cost (rerank calls are an order of magnitude cheaper than generation calls).

### Evaluation

RAG evaluation is harder than pure prompting. Two independent dimensions:

- **Context Relevance**: are the retrieved docs actually relevant to the query? Retrieval system's responsibility.
- **Answer Faithfulness**: is the generated answer grounded in the retrieved docs, or hallucinating? Generation system's responsibility.

Both scored separately. Bedrock Knowledge Bases Evaluation has these two built-in. Chapter 8 expands on evaluation methodology.

---

## 7.6  Common fine-tune misjudgments

Closing with several common fine-tune misjudgments to keep beginner FDEs from going down the wrong path:

**Misjudgment 1: customer asks "can you train an exclusive model on our data"**

Their actual intent is usually "make the model understand our business." That can be achieved by RAG, by prompt + few-shot, or by fine-tune. The customer doesn't care about technique — they care about effect. **Try the first two; only escalate to fine-tune when needed** — same outcome, 90% less work for the first two.

**Misjudgment 2: fine-tune solves "hallucination"**

It doesn't. Fine-tune changes the model's output style and domain adaptation; it doesn't change its tendency to fabricate facts. Factual accuracy is solved by RAG (anchor the model to real docs) and guardrails (have it admit when it doesn't know), not by fine-tune.

**Misjudgment 3: fine-tune is one-and-done**

Wrong. Fine-tuned models have a "maintenance cycle" — when the customer's business changes, new data arrives, base model upgrades, you'll need to re-fine-tune. Each cycle takes days to weeks; that's ongoing burden for the customer. That's the core reason to keep fine-tune to a minimum — **it creates a class of long-term debt at the customer's site.**

**Misjudgment 4: fine-tune is necessarily more accurate than RAG**

Not necessarily. On many tasks, RAG + a strong model beats a fine-tuned smaller model. Fine-tune's advantage is latency and cost, not accuracy. If your customer isn't latency-sensitive, RAG is almost always the better choice.

---

## 7.7  AWS implementation cross-reference

If the project runs on Bedrock, services for each connector:

| Connector | Primary AWS service | Operational note |
|---|---|---|
| **Prompting** | Bedrock model + 1h prompt cache | Long system prompt → enable cache, save money |
| **RAG** | Bedrock Knowledge Bases + OpenSearch / pgvector | Default hybrid search + reranking |
| **Agent** | Bedrock AgentCore (refer to Chapter 6 §6.4 on whether to upgrade to Level 2 orchestration) | Phase one with single agent + single tool doesn't need AgentCore |
| **Fine-tune** | Bedrock Custom Models / SageMaker JumpStart | Prefer LoRA fine-tuning on Bedrock; don't spin up SageMaker training jobs from scratch |

Each row needs its own engineering expansion. Knowledge Bases hands-on lives in Chapter 9 (data engineering). Agent toolset design is Chapter 14. Fine-tune dataset prep is at the end of Chapter 9. This chapter only decides **which connector to use**; it doesn't expand the implementation of each.

---

## Closing

This chapter gives a judgment order: prompting first, RAG if not, agent if not, fine-tune as last resort. Validate each step with the customer's real data; step down only when the bar isn't met.

Hesheng phase one lands on prompting alone — no RAG, no agent, no fine-tune. The least "AI-looking" plan, but the most likely to deliver inside 12 weeks.

The next chapter handles the last D5 question — evaluation and observability. Chapter 6 picked the model, this chapter picked the connector, the next decides **how you know you're doing it right.** That's the last piece of the FDE puzzle, and the easiest for new FDEs to underestimate.

---

## Public references for this chapter

- Anthropic / OpenAI engineering blogs — prompting-first, then RAG, then fine-tune ordering methodology
- Lewis et al., *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks* (2020) — the original RAG definition
- AWS Bedrock docs — product specs for Knowledge Bases, AgentCore, Custom Models
