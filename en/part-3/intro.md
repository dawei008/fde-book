---
title: "Part III — Tech Stack Selection"
nav_order: 13
has_children: true
---

# Part III  Tech Stack Selection

Discovery is done. The FDE has the outcome, Eval set v0.1, and SOW in hand. The Monday after, the customer's CTO asks a very concrete question: which model are you using, where will it run, how do you call it, who orchestrates.

At this moment, beginner FDEs most often fall into two pits. One is over-selection — two weeks of cross-comparing five vector stores, three Agent frameworks, four LLMs, a stack of meetings, and not a single line of business code. The other is zero-selection — grab the stack you know best and start, only to find six weeks later that the choice was wrong, and rollback cost is huge.

Part III gives a third path: split "tech stack" into five independent dimensions and lock them in order, turning week-one selection into a controllable engineering task instead of an endless debate.

---

Chapter 6 covers locking the model, hosting, and orchestration on a single page in week one. The core is a five-dimensional structural diagram (D1 hosting, D2 model, D3 invocation pattern, D4 orchestration, D5 evaluation), where upper layers depend on lower ones — so you must lock from bottom to top. The chapter uses a manufacturing customer case (Suzhou Hesheng Precision Heavy Industries) for demonstration. AWS Bedrock is the platform we work on, but the selection framework is platform-independent.

Chapter 7 covers the D3 invocation-pattern layer — RAG / Fine-tune / Prompting / Agent, which to use, and what signals trigger a switch. This chapter doesn't give "who's better" judgments. It gives a decision tree: data update frequency, answer determinism, inference budget, compliance constraints — combine these dimensions and you naturally land on one of the patterns. After this chapter, the next time someone says "we should use an Agent," you'll know how to push back.

Chapter 8 covers D5 — evaluation and observability. The hard part of evaluation isn't tooling, it's discipline: actually wiring the Eval set into CI, running scores on every PR, blocking merges when scores drop below last week. This chapter takes Part I, Chapter 2's Eval-driven iron rule and grounds it in concrete engineering actions. It's the hinge between Part III and Part V's productionization.

---

Part III's input is Part II's Eval set and SOW. Its output is a minimum closed loop that can score, demo, and continue iterating. Part V's productionization and Part VI's Agent work both build on this loop.
