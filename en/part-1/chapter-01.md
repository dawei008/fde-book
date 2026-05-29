---
title: "Chapter 1  The Real FDE Workflow"
parent: "Part I — Role and Mindset"
nav_order: 1
---

# Chapter 1  The Real FDE Workflow

The first week into an FDE job, the biggest source of confusion is rarely "I don't know the tech." It's not knowing where the time is supposed to go.

Does meeting with the customer count as work? Does writing a demo count as delivery? Does spending a morning labeling 50 Eval samples count as real work? Does pulling the customer's Ops into a channel to configure SSO fall inside the FDE remit?

That's the question this chapter answers. It doesn't teach any specific technology. The point is to build a coordinate system — "what should I be doing right now?" — before you open the IDE. Every later chapter assumes you already have it.

I'll walk you through the shape of a single FDE day first, then lay out the four phases a project goes through end to end.

---

## 1.1  A Day in the Life

The day below isn't any one company's real schedule. It's several B2B AI projects' "actual workdays" compressed into one. If you do FDE work, some of your days will look exactly like this.

```
Tuesday, on the customer's site.

09:00  Slack ping — "RAG recall dropped from 0.82 to 0.61 overnight"
09:30  Scrolled through traces. 78 of 200 failed requests trace back
       to entries the customer added last week
       — the business team uploaded new data without syncing the KB
10:00  Standup with the customer's business PM: they want 4 new intents
13:30  Write the 4 prompt variants for this afternoon's demo, run them
       on the Eval set first — you do not freestyle in front of the customer
15:00  Demo. The customer throws 2 new scenarios on the spot. You don't engage head-on
       — "Let me pull this through Eval and come back tomorrow with a pass/fail call"
17:00  Decompose those 2 scenarios into 20 new Eval samples
17:30  Canary the ingest fix from last night to 10% traffic
18:00  Daily report: progress / 3 things for tomorrow / 1 risk
```

A few moments in this day are worth slowing down on:

**The 09:30 triage.** Using traces to attribute 200 failed requests to a single root cause is a standard engineering action. It just happens in a Slack channel, with the customer as the audience instead of your PR reviewer.

**13:30, running 4 prompt variants on the Eval set.** This is the move that distinguishes an FDE from a "presales demo engineer." You're not adjusting things live in front of the customer; you've already run the variants, looked at the numbers, and picked the best one to bring on stage. This will reappear over and over — it's the smallest unit of evaluation-driven development.

**15:00, refusing to engage head-on when new requirements land mid-meeting.** This is judgment. If you say "great, I'll have it ready this afternoon," your next project may already be doomed. The FDE rhythm in conversation is "I'll answer you with the Eval set," not "I'll give it a try."

If you count the hours actually spent typing in an IDE, it's less than half a day. Across the FDE projects I've been on, coding time stays steady at 25–35%. In the occasional Discovery week, it can drop to 10%. But **the rest of the time isn't wasted.** Triage, writing Evals, qualifying requests, canary releases — every one of these is an engineering action. They just don't take the form of writing code.

Once that lands, "less than half a day on code" stops being a source of anxiety. That's the shape of the work.

---

## 1.2  The Four Phases of a Project

Pulling the camera back from "a day" to "a project." From kickoff to steady state, an FDE project roughly walks through four phases.

```
        Week 1-3            Week 4-7           Week 8-10          Week 11-12
        ─────────           ─────────          ──────────         ─────────
        Discovery           Scaffolding        Production         Handoff
        Find the real       Build the minimum   Ship + stabilize  Hand it to
        problem             closed loop                           the customer
```

The timeline is just a reference. To estimate roughly where your project will land, look at three variables:

- **Is the data already on the customer's cloud and accessible?** If yes, save 1–2 weeks. If no, add 2–4 weeks (data egress / network whitelisting / DBA approvals).
- **Does it require an on-prem deployment or a compliance review?** (Common in finance, healthcare, government.) If yes, add 4–8 weeks.
- **How many decision-making layers are inside the customer?** A single department that can decide for itself usually clears 6–10 weeks. Group IT / Risk / Legal review usually starts at 12 weeks. Cross-BU, possibly half a year.

The specific number of weeks doesn't matter. What matters is that **each of the four phases has one identifiable thing it's doing.**

**Discovery** is the phase most worth spending time on. You're doing one thing — translating "we want to build an AI assistant" out of the customer's mouth into "which role, in which workflow, needs to solve which specific problem; what does success look like; what number measures it."

Why is this phase the most expensive? Because most projects veer off course here, and the cost of veering doesn't surface until Scaffolding or Production. The customer's PM says "we want an agent that writes emails automatically" — you hear it, you start integrating tools, writing orchestration logic. Three weeks later, when you ship, you find out the customer's actually urgent need was "Sales pushing data into ERP at month-end," a tiny piece of automation you could've finished in a morning. This pattern recurs in the FDE community for one reason every time: Discovery wasn't done deeply enough.

**Scaffolding** turns the conclusions of Discovery into the smallest working version. "Smallest" is load-bearing here — not a demo, but a small system that can be run against an Eval set for a score, and that one or two people from the customer's business side can actually use for a week. The most common mistake at this phase is **treating a demo as Scaffolding.** A demo gets shown to the executive once and then it's over. Scaffolding is something a real user runs for over a week and that you can keep collecting feedback from. The engineering bar is very different. The most important artifact out of Scaffolding isn't code — it's **Eval set v0 + a script that runs the score**. Without those two, none of the optimization that comes later has a direction.

**Production** scales "two or three users for a week" up to "tens of users for a few months." The bulk of the work here isn't new features. It's **resilience to operational deformation and to faults.** The customer's network will jitter. Upstream data will be dirty. Someone will paste a 10,000-character ticket from Excel into your input box. You'll spend most of Production handling these edge cases and adding monitoring. New feature velocity drops noticeably. This is the first phase where FDEs feel "the work has turned into operations" — that's not a perception, that's literally what's happening.

**Handoff** is the most underestimated phase. The customer being able to use the system ≠ the customer being able to maintain it. If Handoff is done badly, six months later the system breaks at the customer's site, no one knows how to fix it, and it gets quietly retired. That whole quarter of work was wasted. The artifacts of this phase are runbooks, training materials, code permissions for the customer's internal owner, and a release process. If you're still writing new features in Handoff, it's pretty much guaranteed the project won't last.

### The boundaries between the four phases are blurry

Discovery never "ends" — even in Production you'll discover new customer pain points; the Eval set never "feels enough" — six months after launch you'll still be adding samples. But **each phase has a primary task, and most of your time should be on that primary task.**

In Discovery, most of your time should be talking to people and watching how the customer actually works — not writing code. In Scaffolding, most of your time should be running Evals, tuning prompts, fixing retrieval — not preparing customer demos. In Production, most of your time should be on traces, edge bugs, monitoring. In Handoff, most of your time should be writing docs, training the customer's engineers, transferring permissions and release process.

If your week's time allocation doesn't match the phase you think you're in, that's a signal — either you've **misjudged the phase**, or **you're avoiding the hardest thing about the current phase**.

### How to tell which phase you're in

Across the projects I've been on, the most common failure mode is misjudging the phase — thinking you're in Scaffolding when you're still in Discovery, ending up building a pile of features no one wants. This has happened to me more times than I'd like to admit.

Ask the four questions below in order. The first one you can't answer "yes" to is the phase you're actually in:

1. **Is "success" defined as a specific number for the customer?** Not "we want an AI assistant to improve efficiency" — but "ticket triage accuracy 90%, mean handle time down 30%." If no, you're in Discovery. Don't write code.

2. **Do you have an Eval set you can score the current version against?** Not "the customer thinks it's pretty good" — but a fixed sample set + a script that can tell you in 30 minutes whether v0.3 is better or worse than v0.2. If no, you're in Scaffolding. Build the Eval set first, then prepare the demo.

3. **Have real users on the customer's side used it in production for at least a week?** Not "tried it" — but it's part of the workflow they can't function without. If no, you're in Production. Focus on stability and monitoring.

4. **Is there someone inside the customer who can run it without depending on you?** Including releases, fixing edge bugs, adding new intents, watching dashboards. If no, you're in Handoff. Write runbooks and run training.

All four "yes" — the project is done. Run a postmortem and extract lessons (covered in Chapter 17).

The cost of misjudging is asymmetric. **If you think you're in Scaffolding but you're actually in Discovery, you'll waste weeks building unwanted features. If you think you're in Discovery but you're actually in Scaffolding, you'll lose at most two extra days talking to the customer.** When in doubt, judging "one phase earlier" is the safer bet.

A real example to make this stick: a customer PM handed me a "detailed requirements doc" in week 2 — a 20-page Word doc listing 38 intents with 3–5 dialog examples each. My read at the time: "the customer has thought it through, we can move into Scaffolding." I started building retrieval and routing. Week 5 demo, the customer says "this isn't what we wanted." On postmortem: those 20 pages were the customer PM's own draft. Front-line operators had never seen it. 12 of the 38 intents weren't part of their actual workflow. The cost of my misjudgment was three weeks scrapped and rebuilt. Two extra days putting that doc in front of front-line operators would've prevented it. The cost-benefit is completely asymmetric.

---

## 1.3  Where the Time Should Go

This section gives three simple self-check questions. Asking yourself once every two weeks beats any project management tool.

**One: how many hours over the last two weeks went to "non-coding engineering"?** That includes Discovery interviews, Eval labeling, reading customer business docs, writing runbooks, scanning traces for patterns. These are all engineering work, just not typing code.

What's a healthy ratio? There's no golden number, but you can ask the inverse: if you spent **almost no time** over two weeks on these things — only IDE time and meetings — you've likely turned the project into "remote outsourcing." The customer hands you specs, you write code, no judgment or observation of your own enters the picture. That's not an FDE. That's a contractor running tickets.

**Two: how many times in the last two weeks did you walk over to the customer's desk or canteen on your own?** Not in a meeting, but going over yourself. Watching front-line staff actually use the product. Having lunch with someone in Ops, Customer Success, Sales. Sitting at a workstation Friday afternoon and watching the last two things they do before shutting down their laptop.

Zero is a red line — your "understanding of the customer" is becoming abstract. What you're seeing is what the customer's leadership wants you to see, not the actual workflow. There's a phrase in the FDE community for this: "immerse before you judge." Get into the customer's actual work first, then make technical decisions.

**Three: in the last month, did you push back on any of the customer's requirements or proposed solutions?** Not bickering — pushing back with data. "The customer wants company-wide multi-agent collaboration. Looking at their data integration state, I'm recommending we start with a single agent + tool calling." Or: "The customer wants self-service analytics for everyone. I ran 50 samples — the model gets 60% accuracy on understanding their reports. Let's serve one specific role first."

If you didn't push back at all in a month, you've quietly degraded into "senior implementation engineer" — the customer says it, you build it, no judgment is being applied. Pushing back here doesn't mean defying the customer. It means "I have a better proposal, and I'll show you with data."

What counts as "data"? The most common kinds:

- **Cost modeling.** Compute token usage, API unit price, and QPS for each candidate solution. Example: the customer wants on-prem deployment of a 70B open-weight model; you compute their QPS and show that managed API serves the same load for a fraction of the monthly ops cost of running it themselves.
- **Latency measurement.** Test end-to-end latency under the customer's real network conditions. Example: the customer wants two external data sources hitting in real time. You measure, and adding the second source pushes P95 from 1.2s to 4s — past their SLA.
- **Small-sample evaluation.** Run candidate solutions against a 30–50 sample set, give an accuracy comparison. 30 isn't enough to publish a result, but it's enough to say "this option is clearly worse than that one."

All three of these can be produced in one to two days. Every time the customer says "we want to do X," spend at least two hours on one of these before deciding to go along or push back.

If you can't do these three things in a month, you need to actively reset the tempo of the work. If you can't do them in three months, you should seriously reconsider whether this job is the right fit.

---

## Closing: Why phase judgment matters this much

This chapter gives a coordinate system: the shape of a day, the four phases of a project, a biweekly self-check. But it doesn't answer the most important question — **why is the cost of misjudging the phase so high?**

The short version: there are a few "iron rules" in FDE work, and breaking any of them costs you the customer's trust. And **the rule that's easiest to break is different in each phase.** In Discovery, the easiest one to violate is "sell the outcome, not the product." In Scaffolding, the easiest is "Eval before code." In Production, the easiest is "fix at the customer's site, don't carry the problem back to HQ." If you don't know which phase you're in, you don't know which rule to be most vigilant about right now.

The next chapter unpacks those three iron rules. After reading it, come back and re-read this chapter's four phases — why they're divided this way will become a lot clearer.

---

## Further Reading

**On the name "FDE."** It's not a universal title across the industry. Palantir uses it as a core role title (the term was born there). Engineers doing AI delivery work go by different titles at different companies — Solutions Architect, Customer Engineer, Delivery Consultant, Deep Learning Architect, all of them. This book uses "FDE" because it most precisely captures the essence of the role: "embedded with the customer, accountable for the outcome." Your title may say something else, but if your work matches the rhythm in 1.1, this book applies.

**On the difference between LLM-application FDEs and data-delivery FDEs.** The same FDE title masks very different tech stacks across companies. The LLM-application track (most AI-app companies) spends most of the week on prompts, traces, Evals, retrieval. The data-delivery track (Palantir-style data-platform and ontology work) spends most of the week on ETL, data modeling, data validation. Same mindset (embedded, accountable) but **different muscles** (tech stack and tooling). Worth knowing: **even within a single project, different phases call for different postures.** Discovery skews toward data delivery (reading schemas, mapping workflows). After Scaffolding, things shift toward LLM application (prompt tuning, token cost). When you walk into your next project and find yourself doing things you've never touched, no need to panic. Switch posture, not mindset.

**Public references for this chapter:**
- A. Lawrence, *Forward Deployed Engineer Rule Book* (2025) — the four-phase naming in 1.2 borrows from this taxonomy
- Conikeec, *The FDE Playbook: A Practitioner's Field Manual* (2025, Substack) — describes a similar phase model
- Bob McGrew @ Y Combinator (2025) — the source interview for "Sell the outcome, not the product"
- Nabeel Qureshi, *Reflections on Palantir* — an internal view of Palantir's FDE working model

Full bibliography and links in the *References* at the end of the book.

---

[← Part I Intro](../intro/) · [Next: The Three Iron Rules →](../chapter-02/)
