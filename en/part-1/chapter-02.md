---
title: "Chapter 2  The Three Iron Rules"
parent: "Part I — Role and Mindset"
nav_order: 2
---

# Chapter 2  The Three Iron Rules

Chapter 1 gave you a coordinate system — the shape of a day, the four phases of a project. But a coordinate system alone can't tell you **how to choose under tradeoffs.**

It's 2 a.m. You've just shipped an emergency fix. The customer's CTO wants to see a demo at 8 a.m. You have two choices: push the fix to staging tonight so the customer sees the real state, or freeze a known-good demo build, run the demo tomorrow, and ship the fix afterward. Which is right? (Hint: it depends on what you fixed last night. If you fixed something that scores on the Eval set, ship it. If you fixed an edge-case polish nobody asked for, wait. By the end of this chapter you'll see why.)

The customer's business head throws a new scenario at you mid-meeting and wants it "by tomorrow." Do you push back? How?

The customer's data has 5% dirty rows. Do you go back and put it on the team's backlog, or write a small handler on the spot?

These are the tradeoffs FDEs face every day. "Which phase, which task" from Chapter 1 doesn't answer them. What answers them is another set of things — the three iron rules.

These weren't invented by me. They're the same set of mental models repeatedly articulated by generations of FDEs across the industry, accumulated through scar tissue. Bob McGrew talked about the first rule on his Y Combinator interview. A. Lawrence writes the second one repeatedly in his *Forward Deployed Engineer Rule Book*. The third has been pushed by LLM-application teams at Anthropic, OpenAI, and similar shops in the last two years through public blog posts and engineering practice.

There's an order to them:

```
1. Sell the outcome, not the product   — decides what you do
2. Eval-driven                          — decides how you know it's done
3. Fix forward                          — decides where you fix problems
```

Why this order? Because the failure mode of each is different. Break the first, and **the project is pointed wrong** — 12 weeks of features no one wants. Break the second, and **the project is pointed right but you don't know how far you've gone** — six months in, the customer says "this isn't really working" and you have nothing to argue back with. Break the third, and **direction is right, progress is clear, but you can't fight the customer's fires** — they lose three deals in three weeks, and your trust budget is gone.

The first costs the most and is the hardest to recover from, so outcome ranks first. The second ranks second because its cost is "delayed exposure" — you spend three months before discovering you're off target. The third ranks third because the cost is "local trust" — you can lose one of the customer's small deals and still recover after a couple of slips.

This chapter walks through them one by one.

---

## 2.1  Sell the Outcome, Not the Product

The customer isn't paying because they want "an Agent." They're paying because they want:

- Month-end report on-time rate from 60% to 95%
- Customer ticket first-response time from 4 hours to 30 minutes
- Sales close-rate up by 5 percentage points

"Agent" is the means. Those three numbers are the end. **The FDE's job is to be accountable for the end, not the means.** That's the literal reading of Bob McGrew's "sell the outcome, not the product."

Why does this rule matter so much? Because if you sell the product, the customer evaluates you on "is the product good?" — unquantifiable, no terminal point. Today they think "it's okay," tomorrow a new account manager walks in and says "it's not smart enough." Nothing you do helps. If you sell the outcome, the customer evaluates you on "did the number get hit?" — quantifiable, with an endpoint, and aligned with you on goals.

### How this rule lands in conversations

Every conversation with the customer requires a small translation — taking "I want feature X" out of their mouth and translating it back into "what business outcome does feature X serve?" This translation has to become muscle memory.

Three common scenarios:

**Scenario 1: Customer adds a new requirement.**

Customer: "Can your thing also handle email?"

Wrong answer: "Sure, we can schedule it for next week."
Right reaction: figure out what business outcome adding email is meant to serve. This usually surfaces with one question — "Adding email is mainly to address what? Sales follow-up speed, customer service first-response time, something else?" Their answer determines your next move.

If their answer is "the median sales follow-up reply time," your reply becomes: "Let's check what the current median is, project where it'd land with email, then put it on the backlog."

That translation reframes the conversation from "should we add email" to "how do we keep pushing the number we already care about." The customer and you are back in the same coordinate system.

If they can't answer "for what business outcome" — that's a red light. The requirement isn't growing out of the workflow. It's invented in some demo or a meeting tangent. Things like that, even if built, won't get used.

**Scenario 2: Customer asks for a technical metric.**

Customer: "What's the actual RAG accuracy on this thing?"

Wrong answer: "0.83 on test, 0.78 in prod."
Right reaction: accuracy by itself means nothing to the customer. Your reply becomes: "0.78 RAG recall by itself isn't the right number. The thing you originally wanted to fix was account managers spending 4 minutes to find a clause — they're now averaging 28 seconds with RAG. That 28 seconds matches the 'within 30 seconds' you set."

That translation moves the conversation from "how accurate is the model" to "how far is the business problem from solved." The first is a technical parameter. The second is the outcome.

**Scenario 3: Customer gives a vague goal.**

Customer: "We want an AI-powered company-wide knowledge base."

Wrong answer: "Got it, we'll work up an architecture proposal."
Right reaction: vague goals never ship. Your reply becomes: "Company-wide knowledge base is too big as a target. Let's pick one specific thing — is it new-hire onboarding from 30 days down to 15, or customer service resolution rate from 65% to 80%? Pick one, ship a v1, and we'll come back for the rest."

This is the hardest of the three because you're rejecting the customer's original ask while offering a more reachable version. If they accept, your project just got a sharp boundary. If they insist on "all of it," you should recognize they're still in Discovery — the framework in Chapter 1.2 says you shouldn't be writing code yet.

### Friction with your own team and your boss

The hardest place to apply this rule isn't the customer — it's your own product and sales teams. They will repeatedly drill "sell the product" into you: "If the customer asks if we can do X, say yes." "Sign the contract first, then talk outcomes."

A simple defense: **don't let any conversation end on "feature discussion."** Whether the customer is requesting something, sales is making promises, or product is setting roadmap — pull the conversation back to "what outcome does this serve, and how do we measure it."

If you've taken over a project and a week in you can't connect to a single outcome number, that's a red flag. You're more likely in Discovery, not Scaffolding. The cost of stopping to align on outcomes now is far smaller than the cost of building the wrong project.

---

## 2.2  Eval-Driven

Once you have an outcome, the next question is how you know you're getting closer to it. That's the second iron rule.

The biggest difference between LLM systems and traditional software: **same input, output isn't guaranteed to be the same. A prompt that works today may break after a model upgrade.**

The engineering consequence: you can't decide whether the system is good by "I looked at it and it seemed okay." You need a fixed sample set + a script that runs a score, and every change runs through it. That's Eval-driven.

It's not "run the Eval after you finish coding." It's the inverse — **Eval first, then code.** The five concrete engineering practices:

1. **Build Eval set v0 in the first week.** 20–50 samples covering typical scenarios and the edge cases you can think of. First week, not pre-launch.
2. **Run Eval on every PR.** In CI, locally, doesn't matter — the rule is "code change must produce a number."
3. **Set a passing score.** The number written into the contract for customer sign-off, mapped to a specific threshold on the Eval set. Below threshold, no shipping.
4. **Continuously sample from production back into the set.** Real failure cases from production get sampled weekly and added to the Eval set. That's the live water source for the set.
5. **Model upgrade, prompt overhaul, dependency swap — re-run Eval.** Run the baseline before each big change, run the variant after. The diff makes itself visible.

### Cold-starting Eval set v0 from zero

The most common stuck point for beginners: "the customer hasn't even nailed down outcomes — where do I get 30 samples?"

A 0-to-30 process I've used myself, doable inside the first week:

1. **Pull 10 real samples from the customer's existing data.** Customer service tickets, historical Q&A logs, account-manager queries — anything the customer is already producing in normal work. If the customer can't even produce these 10, they're more likely still in Discovery and shouldn't be building the system yet.
2. **Write 10 edge-case samples yourself.** These aren't "typical" — they're "deliberately adversarial": colloquial phrasing, abbreviations, typos, long sentences, multi-step reasoning, samples whose answer is "I don't know" (many systems hallucinate hardest on those).
3. **Run it once and have the customer's business side look at the distribution.** This step is the key. When the customer sees what's in your test set, they're likely to say "this isn't our typical scenario" or "you missed an X-class question." Let them poke holes.
4. **Add 10 more based on the customer's pokes.** These 10 are samples the customer has signed off as representative.

Now you have 30. Doable inside a week.

The key to this process isn't "30 samples assembled" — it's **letting the customer participate in sample selection.** A customer who's helped pick samples won't later say "the Eval set itself is wrong" when looking at scores. That's the last landmine you want to step on at delivery time.

### What a minimal Eval set looks like

Suppose you're building Q&A on insurance policy clauses. Eval set v0 looks roughly like this:

```python
# evals/insurance_qa_v0.jsonl
// min_score = keyword-hit ratio threshold (0-1). E.g. 0.8 = at least 80% of keywords expected
{"input":"What's the typical waiting period on critical illness insurance?",
 "expected_keywords":["90","180","waiting period"],
 "min_score":0.8}

{"input":"Last year my checkup found a thyroid nodule. Can I still apply now?",
 "expected_keywords":["underwriting","disclosure","nodule"],
 "min_score":0.7}

{"input":"How much do I get back if I cancel within the cooling-off period?",
 "expected_keywords":["full refund","cooling-off"],
 "min_score":0.9}
# ... 30-50 samples
```

Two scoring layers. Machine runs keyword recall (30 seconds for a score). A business expert hand-grades 10 samples per week. Look at both numbers together. The machine score tells you whether a change broke any existing samples. The human score tells you how far you still are from the customer being satisfied.

More elaborate evaluation methods (LLM-as-judge, pairwise preference evaluation, agent trajectory evaluation) come in Chapter 8. For week one, you don't need that complexity. 30 samples + keyword matching is enough for you and your team to build the muscle memory of "change → run the number → decide whether to ship."

### Evaluation on AWS

If your project runs on AWS Bedrock, the platform ships with a few evaluation primitives that save you from rolling your own:

- **Bedrock Evaluations** — run model / RAG / Agent evaluations directly inside Bedrock. Supports machine evaluation, LLM-as-judge, and human evaluation modes.
- **Knowledge Bases Evaluations** — an evaluation flow purpose-built for RAG retrieval and generation quality.
- **Agent Evaluations** — evaluation across the agent's multi-step reasoning trajectory, with custom dimensions.

Practical advice: **use the console version in PoC** — near-zero cost, baseline running in 10 minutes, gives you and the customer a first number on day one. **Migrate to the code version once you enter Scaffolding** — pytest or open-source frameworks like deepeval, runnable in CI, version-controlled, capable of diffing scores across branches. **After launch**, use CloudWatch to collect real production samples and periodically feed them back into the Eval set. Specific APIs and console entries change with product iteration; check docs.aws.amazon.com.

### What "with Eval" and "without Eval" feel different in

The most concrete difference is the conversations in these moments:

| Moment | Without Eval | With Eval |
|---|---|---|
| Monday standup | "Last week's change felt about the same" | "Last week 0.81, this week 0.83, +2 points" |
| Customer asks "is the system good?" | Subjective, drifts every week | Customer sees a number weekly, defensible |
| Model vendor upgrade | Don't dare touch it, scared of breakage | Run Eval overnight, decide |
| Pre-launch sign-off | Demo luck | Number hit |
| Post-handoff | Customer has no idea | Customer can run Eval themselves |

The last row matters especially. **The Eval set isn't just a development tool — it's the core deliverable of Handoff.** What the customer takes when they accept the system isn't your beautiful code — it's the Eval set and a script to run it. That's their ability to keep telling whether the thing still works.

---

## 2.3  Fix at the Customer's Site

You know what to build, and you know how to measure whether it's done. The remaining question: when something breaks, where do you fix it?

The third rule, repeated by Lawrence in his book: *Don't carry the problem back to HQ. Fix it at the customer site.*

This sounds tautological — "what's the difference where you fix it?" — but the underlying philosophy is fundamental. **An FDE is not "front-line presales + back-line R&D" in two stages. The FDE on the front line is presales, R&D, and Ops at the same time.**

If your first reaction to a problem is "I'll go back and open a Jira and have HQ schedule it," you've already retreated to "implementation engineer." That role exists, but it isn't FDE.

### What "fix on site" actually looks like

Two scenarios capture the gap between "fix on site" and "carry it back to HQ."

**RAG recall suddenly drops.** One day customer Ops complains "the system's been answering off-topic more and more" and you open the trace and see recall went from 0.82 to 0.61 overnight.

Carry-it-back: send an email to HQ, file a ticket on the backlog, "next sprint." The customer uses an increasingly bad version for the next week. Every day someone vents about it. Two weeks later you ship the fix; the customer has already mentally given you a zero.

Fix on site: same day, scan the trace and attribute (e.g., the customer added new data last week without syncing the KB). That night, write a one-line re-ingest script + a 5-minute SOP, drop both in the customer's Ops channel. Next morning recall is back to 0.81. In parallel, schedule the proper fix (auto-listening for data source changes) into next week's PRs. **Firefighting now + permanent fix in parallel.** The customer never feels that bad week.

**Customer Compliance asks about a detail your architecture doesn't cleanly handle.** Like which components PII flows through, whether there are logs, retention period.

Carry-it-back: "I'll check with the security team and get back to you next week." Next week the customer has run three internal meetings, and by the time you reply, they're seriously evaluating whether to switch vendors.

Fix on site: open the architecture diagram on the spot, trace the specific data flow they asked about. Where you can answer, answer clearly. Where you're not sure, mark it on the spot as "I'll confirm within 24 hours." Send a revised architecture diagram via email before the meeting ends, including the specific notes on that flow. **Don't let the customer leave the room carrying uncertainty.**

What both have in common: **neither problem has a perfect solution at the moment**, but in both you started moving inside the customer's field of view immediately. The customer's trust in an FDE isn't built on "problems never happen." It's built on "when problems happen, you're there handling them."

### A counterexample

Lawrence tells a customer story in his book: an FDE deploying on-site finds 5% of the data is dirty (mixed encodings). He opens a ticket back to HQ and waits three weeks. R&D replies "the general fix needs a refactor." By week four, the customer has lost patience and the project stalls.

The colleague who took over wrote a 30-line transformer to handle that 5% on day one. Day two, the data flowed; the project restarted.

The lesson isn't "don't open tickets." It's **tickets and on-site fixes should run in parallel**: a small patch for dirty data to keep the customer's data flowing, the proper general fix as a real PR on the backlog. Customer patience is finite. Each extra week of waiting drops their confidence — not in that specific bug, but in "can this team handle our problems."

### What you need configured to "fix on site"

To fix on site, an FDE needs a few tools configured. Missing any of them, and you regress from FDE back to implementation engineer:

- **Deployment permission to the customer's environment** (at least staging). If even staging requires the customer's IT to run a process, your fix will always lag the customer's patience.
- **Direct push permission to your repo's main branch** (CI-protected). If a one-line fix needs CTO review, your hot fix is always "tomorrow's problem."
- **At least one channel that lets you hot-fix to production**: Lambda, sidecar container, config service, feature flag — pick one.
- **A "patch script directory."** Some same-day, possibly-throwaway Python scripts and shell one-liners. Not "real code," but the muscle of Fix Forward.

If any of the above is missing, **a non-trivial part of your FDE work simply cannot be Fix Forward.** If you don't have these in week one, week one is when you start actively fighting for them — both with the customer and with your own org. Wait until week three and the other side will think "this isn't permission an FDE should have anyway." The negotiation cost doubles.

If you've just transitioned into FDE and have none of the four right now — don't panic. That's the common starting state, not personal failure. Boundary negotiation for these four (how to safely give an FDE staging deploy on the customer side, how to get main push on your own side) involves organizational trust building, which Chapter 11 covers. What you need to do in this chapter: **write these four down as "things that must be solved within the first month"** — not as "things that should already be there."

---

## 2.4  How the Three Relate

The three aren't laid out flat. They're a judgment chain.

```
    Sell the outcome   →   decides what you do
           ↓
      Eval-driven      →   decides how you know it's done
           ↓
     Fix forward       →   decides where you fix problems
           ↓
     outcome achieved
           ↓
     (next outcome)
```

Rule one decides "what" — without an outcome, anything you do is wasted. Rule two decides "how done" — without an Eval, you and the customer both go on feel and end up unable to settle anything. Rule three decides "where" — fixing not at the customer's site is not FDE.

Back to the four phases of Chapter 1. **The rule easiest to break is different in each phase.** In Discovery, the easiest violation is rule one — taking the customer's "feature" as the outcome and just building it. In Scaffolding, the easiest violation is rule two — treating the demo as "done" and signing off without an Eval set. In Production, the easiest violation is rule three — pushing production issues back to HQ and making the customer wait.

Knowing your phase tells you which rule to be most vigilant about right now. That's the real reason why phase judgment in Chapter 1 matters.

---

## 2.5  How to Sell the Three Rules to Your Team and Your Customer

In real work you have to "sell" these three to several roles:

- Your own product and sales team (who keep drilling "sell the product" into you)
- The customer's project manager (who keeps pushing "ship the feature" at you)
- The customer's CTO (who keeps pushing "AI strategy" at you)

Recite the rules in front of each role at least once to head off the most common misreads. A reusable script:

> "First thing I do on this project is nail down a number — for example, account manager median time-to-clause from 4:30 down to 30 seconds. Then I'll build an 80-sample Eval set, run scores weekly. No PR merges to main without passing Eval. Three months from now, what you'll see when I deliver isn't 'an AI system' — it's the number 'median 4:30 → 27 seconds.'"

After this, the customer usually agrees. If they don't agree, the problem is bigger — the customer doesn't know what outcome they want. You should run Discovery first (Chapter 4), not start writing code.

---

## Closing

Back to the three scenarios from the chapter opener:

- **Push the 2 a.m. fix to staging?** Depends on whether what you fixed scores on the Eval set (push, let the customer see real state) or whether it was an edge polish nobody asked for (wait, don't add risk to the demo). This is rule one + rule two combined: you're accountable for Eval-set progress, but disciplined against "self-congratulatory improvements" outside the outcome.
- **Take a new requirement on the spot?** Don't engage head-on. Translate it into "what outcome does this serve," then answer with data. This is rule one + the engineering action of "push back with data."
- **5% dirty data — fix on site or send back?** Fix it on site with a 30-line patch to firefight, schedule the general PR on the backlog. Two parallel tracks. That's rule three.

The three rules aren't abstract commandments. They're judgment yardsticks for the concrete tradeoffs an FDE faces every day.

The next chapter pulls the camera back one more step — the same FDE role, doing "LLM application projects" vs. "data delivery projects" (the former is accountable to the model, the latter to the data schema and pipelines), takes very different actions, but the core of the three iron rules is identical. Knowing when to switch postures is something you'll start using from week one of your first project.

---

## Public references for this chapter

- Bob McGrew @ Y Combinator (2025) — source interview for "Sell the outcome, not the product"
- A. Lawrence, *Forward Deployed Engineer Rule Book* (2025) — earliest systematic articulation of Fix Forward
- Anthropic / OpenAI engineering blogs — public material on evaluation-driven LLM application development

Full bibliography and links in the *References* at the end of the book.
