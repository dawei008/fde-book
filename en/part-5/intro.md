---
title: "Part V — Going Live and Operating"
nav_order: 15
has_children: true
---

# Part V: Going Live and Operating

The distance between "the PoC works" and "it's in production" is longer than the PoC itself.

A number that comes up repeatedly in the industry: roughly 30-40% of PoCs convert to production. The remaining 60-70% don't fail because the model isn't good enough — they fail because the engineering work needed for productionization wasn't seeded during the PoC phase. The eval set isn't wired into CI, observability is bolted on after the fact, cost and latency were never quantified, and there's no canary path or rollback plan when GA day arrives.

The moment the customer wants to go live, all those gaps surface at once, and the FDE realizes "another few weeks" can't fill them in. The two chapters in Part V are about how to seed those engineering actions during the PoC phase itself, so that the road from PoC to production is a road, not a cliff.

---

Chapter 12 is on PoC pass-line conditions — which things, once done, qualify a PoC for going to production, and which gaps, once missed, will jam the project in the final week before launch. This chapter isn't a flat checklist; it's a causal judgment framework: every pass-line condition maps to a real failure mode it prevents.

Chapter 13 is on the core actions of operating in production — monitoring, observability, Guardrails, canary, rollback. Operating an LLM application is unlike operating a traditional service: failures don't show up as 5xx, they show up as degraded outputs; the metrics aren't just latency, they're hallucination rate, tool-call success rate, and the token cost curve. This chapter gives a minimum operating skeleton an FDE can stand up directly in the customer's environment.

---

Part V's prerequisites are Part III's eval-driven loop and Part IV's data / integration foundations — the outputs of those two Parts are the hard inputs to the pass-line conditions. Part VI's Agents add a new layer of operational complexity on top of production; Part VII's handoff is about putting this operating skeleton into the customer's hands so it keeps running.
