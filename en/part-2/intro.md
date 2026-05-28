---
title: "Part II — Customer Discovery"
nav_order: 12
has_children: true
---

# Part II  Customer Discovery

The most expensive code on an FDE project is the code nobody wanted.

And "code nobody wanted" almost always traces back to one place — Discovery wasn't done deeply enough. The customer's PM says at kickoff "we want an agent that writes emails automatically," the FDE hears it and starts integrating tools and writing orchestration. Three weeks later, when it ships, the FDE finds the customer's actually urgent need was "Sales pushing data into ERP at month-end" — a tiny piece of automation that could've been finished in a morning.

This pattern recurs in the FDE community. The reason Discovery sits first in Chapter 1's four phases is exactly this: once you've drifted off course here, Scaffolding / Production / Handoff are all wasted on the wrong target.

---

A lot of engineers hear "Discovery" and the first reaction is "that's the PM's job." This book doesn't accept that division of labor. FDE Discovery isn't sitting in meetings listening to requirements and writing a PRD. It's bringing an engineer's eye onto the customer's site to **observe, quantify, and prototype** their real workflow — and out the other end, producing an Eval set that can be thrown into CI for scoring, and an SOW that can be signed.

Chapter 4 covers how to do Discovery. The key is "observe > ask" — there's almost always a gap between the workflow the customer describes and the workflow they actually run, and that gap is what the FDE is hired to close. This chapter gives the concrete observation postures, the questions that have to be asked, and how to turn what you see on site into a Discovery report you can take back to the team.

Chapter 5 covers how to translate the conclusions from Discovery into engineerable contract artifacts — Eval set v0.1, acceptance criteria, SOW. This chapter is the bridge from Part II into Part III: the Eval set is the input for Chapter 8's CI gatekeeper, and the SOW is the basis for Chapter 12's PoC pass/fail call in Part V.

---

The artifacts coming out of Part II (Eval set + acceptance criteria + SOW) are the inputs for every engineering action in Parts III–VII. If Discovery doesn't meet bar, every line of code that follows is wasted. So neither chapter is skippable.

---

[← End of Part I](../../part-1/chapter-03/) · [Next: Week One on the Customer's Site →](../chapter-04/)
