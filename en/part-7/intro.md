---
title: "Part VII — Handoff and Continuity"
nav_order: 17
has_children: true
---

# Part VII: Handoff and Continuity

A lot of FDE projects "go live," then three months later slide into a half-dead state — the customer's ops team doesn't really understand the system, so every time something breaks they call the original FDE; no one on the FDE side has taken over either, so the project-specific prompts, data, and accumulated landmines all live inside one person's head; when the customer asks "can you do the next project," the FDE themselves can't say clearly what's reusable and what would have to be rewritten from scratch.

This state isn't an isolated incident — it's one of the standing failure modes of the FDE industry. The root cause isn't that engineering wasn't done well on launch day; it's that "handoff" was never designed in as a part of the project from day one.

The two chapters in Part VII handle this, and pull the lens out from the single project to the FDE's own long-term capability building.

---

Chapter 16 is on project handoff. Handoff isn't "push the code to the customer's git, write a README" — it's about getting a specific person or team inside the customer to be able to keep maintaining, change prompts, add new evals, and locate root causes during incidents after the FDE leaves. This chapter walks through the deliverables (runbook, training materials, permissions handover, launch process) and also how to abstract this project's engineering experience into assets the next project can reuse.

Chapter 17 is on the FDE's own next step. After finishing a project, the FDE's capability stack shouldn't just be "one more customer case study" — it should grow on both axes of the T-shape: engineering depth (model / system / data) and industry depth (the know-how of one or two verticals). This chapter offers a framework for taking stock of where you are now and planning what's next.

---

Part VII's prerequisite is the entire output of every prior Part — handoff quality is the final aggregate of every phase's quality. Once you're done reading, the FDE moves into the next project, and the cycle repeats.

---

[← End of Part VI](../../part-6/chapter-15/) · [Next: Project Handoff →](../chapter-16/)
