---
title: "Chapter 12 — PoC to Production"
parent: "Part V — Going Live and Operating"
nav_order: 1
---

# Chapter 12: PoC to Production — What Makes It, What Stalls Out

Suzhou Hesheng Precision Heavy Industries, overseas business unit. Wednesday afternoon, week 10.

The ticket Agent had been running on staging for nearly five weeks. The architecture sheet from Chapter 6 was still pinned to my desk; eval-v1 (200 cases) from Chapter 8 ran daily in CI; on the four items from Chapter 11 (SSO/SCIM/IAM/audit), Gu Jianguo had ticked every box on his A4 sheet last Wednesday. Chen Xue and senior masters had run more than 60 real tickets through it; triage accuracy 94%. The board wanted to see results by end of November — eight weeks left.

That afternoon I thought we were aligning on the launch timeline. Zhou Mingyuan closed the conference room door, three sheets of paper on the table: contract appendix, IT committee's "launch admission checklist," a draft SLA from the overseas business unit. He said: "I think the Agent is good enough. But next Monday I have to answer three questions in front of the executive committee. One, how do I know it's truly ready? Two, if something goes wrong after launch, how do I roll it back? Three, what do we actually pay for the first year, and on what basis?"

These three questions map to this chapter's three things — **pass-line conditions** (what counts as "good enough"), **rollback playbook** (what to do when things break), **contract structure** (how the money flows). I didn't have full answers for him that afternoon. What follows is what I actually did over the following week, and looking back from after launch, what was right and what nearly went wrong.

---

## 12.1 PoC Isn't a Rehearsal for Production, It's the Trailer for Production

Lawrence in *FDE Rule Book* has a line I keep using: "The PoC is not the project — it's the trailer for the project." Operationally that means: PoC-stage engineering metrics differ from production by an order of magnitude or two. You can't expect "this demo runs well, just ship it as-is."

I've personally lived through the accident of treating PoC as production, and I've seen the same scenario described by Conikeec in *FDE Playbook* — demo phase has no monitoring wired, no load testing done, no architecture review with customer IT, contract signed, and then IT lists dozens of changes and consumes most of the project's remaining time. Every veteran FDE has a version of this story.

But on the Hesheng project I didn't let that happen. The reason is that during Discovery (Chapter 3) I drew a "what's different between PoC and production" comparison table. That table helped me hold "primary picks haiku not opus" in Chapter 6's selection, helped me pull "security admission" into the agenda 4 weeks early in Chapter 11, and what it has to answer in week 12 here is Zhou Mingyuan's first question — **the definition of "good enough"**.

```
                  PoC standard          Production standard
                  ─────────             ─────────
  Concurrency       Single user        ~100 QPS (Hesheng's target)
  Availability      "demo runs"        99.5% monthly
  Latency           P50 5s acceptable  P95 < 3s
  Fault tolerance   Restart on error   Auto-retry + isolate + fallback
  Observability     console print      Full-trace + cost
  Permission        FDE has admin      RBAC + 24h offboarding
  Release           "I edit prompt by hand"   CI/CD + canary + rollback
  Customer          FDE on site        Customer ops on-call independently
```

This table isn't for the customer — it's for me. Every two weeks I run it, looking at how far staging is from production. By week 10 the gaps were in four buckets: **load test never done**, **no canary**, **no rollback drilled**, **SLA numbers not signed by customer**. Eight weeks to fill these four buckets.

---

## 12.2 Five Hard Thresholds: What Numbers Define Pass-Line

I wrote the definition of "good enough" into the contract appendix as five lines, each with a number, a measurement method, and a signing party. None of the five — no GA from me. Anthropic's stance in [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) is consistent on this — before launch you must have quantifiable pass-line conditions, otherwise the team will drift in "let's tune a bit more" forever.

```
  ┌────────────────────────────────────────────────────────────────┐
  │ Dimension   Threshold                Measurement                │
  ├────────────────────────────────────────────────────────────────┤
  │ Accuracy    eval-v1 dispatch ≥ 0.92  CI daily, 3-day rolling   │
  │             fault type ≥ 0.80                                   │
  │                                                                 │
  │ Performance P95 < 3s @ 100 QPS       Production-like load test, │
  │             cold-start first call < 5s    30 min stable         │
  │                                                                 │
  │ Cost        Per ticket ≤ ¥0.05       Monthly extrapolation     │
  │                                       ≤ 90% of contract budget  │
  │                                                                 │
  │ Observability Calls 100% to CloudTrail, Bedrock invocation logs │
  │             10% prompt/response sample, 30-day staging access  │
  │                                                                 │
  │ Canary      1/10/50/100% switchable, drilled rollback once     │
  └────────────────────────────────────────────────────────────────┘
```

Every line needs a specific number. **Where does 0.92 come from?** From Chen Xue and Master Wang — they said when senior masters dispatch by hand, error rate is 7-8%. The Agent has to at least match. **Where does 3 seconds come from?** Manual dispatch in ERP averages 2.5 seconds; if the Agent is within 0.5 seconds of that, it feels "about the same"; over 3 seconds and the dispatchers complain. **Where does ¥0.05 come from?** Chapter 6's selection table had primary+fallback hybrid at $0.63/1k tickets; at a 7-yuan exchange rate that's ¥0.044, with a 10% buffer rounded to ¥0.05.

Numbers aren't pulled out of thin air; every line has a source. The customer can challenge your numbers, but they can't say "you have no numbers."

Once written into the appendix, ownership of each item is clear: accuracy and cost belong to me (FDE team), performance and canary jointly to me and Gu Jianguo, observability to Gu Jianguo. Whichever line misses, the corresponding owner explains. That's much more concrete than "we're all responsible for the project together."

> A mistake I've made before is writing these five items as "review once before launch." Result: in the launch week we discovered eval wouldn't move, jammed in two weeks of last-minute optimization, the team burned the candle. This time I wrote the five into CI — they ran daily, daily we saw how far we were from pass-line. **Pass-line conditions aren't a pre-ship checklist; they're the project's daily dashboard from week 4.**

---

## 12.3 Four Canary Tiers and One Rollback Drill

Zhou Mingyuan's second question — what to do when something breaks. This section is the answer.

Canary's purpose isn't "phased launch" in the trivial sense. Its real value is giving you a **reversible gradient**: 1% breaking won't hurt customers, 10% surfaces the edges under real traffic, 50% validates capacity. Between each tier there has to be observation time — not "shift and move on."

I designed Hesheng's four tiers like this:

```
  ┌─────────┬────────┬──────────────┬─────────────────────────┐
  │ Tier    │ Hold    │ Routing       │ Promotion criteria      │
  ├─────────┼────────┼──────────────┼─────────────────────────┤
  │ 1%      │ 48 hours│ Random sampling│ Error rate < 1%, P95 met│
  │         │        │              │ business-side spot check 20│
  │                                  │ tickets, no errors        │
  │                                                            │
  │ 10%     │ 5 working days │ By region, Jakarta first │ eval CI stable 3 days│
  │                                          cost curve within budget │
  │                                                            │
  │ 50%     │ 1 week  │ Add Kuala Lumpur│ Customer ops handled 1 alert │
  │         │        │              │ independently, no rollback │
  │                                                            │
  │ 100%    │ -      │ Full           │ -                       │
  └─────────┴────────┴──────────────┴─────────────────────────┘
```

**Why start with Jakarta?** Chen Xue chose. Jakarta has medium ticket volume, the most junior dispatchers, and a few past dispatch errors — meaning that site has the highest tolerance for the Agent (manual makes mistakes too), and incidents "look less out-of-place." Which customer pocket to canary in first isn't a technical decision, it's a business decision; the FDE doesn't make this call for the customer.

**The rollback playbook has to be drilled, not just written down.** Week 11 I sat with Gu Jianguo one evening and ran a complete "pretend something broke" on staging:

```
  T+0:00   Manually set KB retrieval timeout to 200ms (normally 800ms),
           injecting failures
  T+0:02   Alert fires: error rate jumps from 0.4% to 19%
  T+0:03   on-call gets PagerDuty
  T+0:05   Gu Jianguo looks at dashboard, locates "KB call timeout"
  T+0:07   Decision: 1% → 0%, full cutover to old system (manual dispatch)
  T+0:08   Cutover complete, error rate falls
  T+0:30   Root-cause review, write 5-line incident note
```

This drill surfaced three things. One: the PagerDuty alert rule had a hole — the error rate was a 5-minute moving average, so going from 0.4% to 19% took 90 seconds to fire, not much faster than my estimate. We changed it to a 1-minute window + 3% threshold. Two: the "cutover to old system" button was originally inside an SSO MFA-required console; at 2 a.m. on-call took 4 minutes flipping through MFA tokens. We later turned the rollback into a Slack `/rollback` command, backed by a pre-signed Lambda — rollback to 0% no longer requires opening the console. Three: "cutover to old system" means returning to fully manual dispatch, and the overseas night-shift dispatcher is one person — his workload doubles. We had not thought about this.

The third one made my heart sink. **Rollback isn't "flipping a switch" — rollback is returning the customer's operational state to an older version, and that older version has to actually be able to handle the traffic right now.** Chen Xue and I recalculated and pushed the 100% canary to a window where Indonesia's daytime shift had enough coverage. This isn't in textbooks, but every veteran FDE has hit it once.

I think rollback drills matter as much as load testing. The FDE community calls "deliberately break the system once" a chaos drill, and Anthropic's agent docs also recommend running a full-flow "pretend an alert fires." Writing docs alone isn't enough — in the docs you can write "rollback in 5 minutes," in the drill you'll discover that at 2 a.m. logging into the console and flipping MFA took 4 minutes.

---

## 12.4 Three Reviews — Customer IT / Legal / Security

Business satisfaction during PoC ≠ project can launch. Chapter 11 already had Gu Jianguo handle "security." But IT and legal — those two reviews — I only caught up on in week 10.

**IT committee review.** Hesheng's IT committee meets monthly; I caught the last meeting of week 10. Three deliverables: architecture diagram (Bedrock VPC endpoint + Identity Center + ECS dispatcher), change impact analysis (which existing systems this launch affects), disaster recovery plan (RTO < 30 minutes, RPO < 5 minutes). My first review tripped on change impact — I hadn't noticed that when the ticket Agent calls ERP, it triggers an old webhook on the ERP side that, in an edge case, creates duplicate dispatch records. The IT committee asked me back in two weeks.

This is something a veteran FDE should anticipate; I've added it to my own mistakes list: **any "we'll just call your API" must include full end-to-end validation inside the customer's systems**. Customer webhooks, transaction idempotency, message replay strategies — these are FDE pitfalls.

**Legal review.** The "AI service terms" appendix is what legal cares about most. Three things must be in writing:

- **Data ownership** — does Hesheng's ticket data go into Bedrock training? No ([Bedrock's data protection docs](https://docs.aws.amazon.com/bedrock/latest/userguide/data-protection.html) are clear — customer prompts and completions are not used by AWS to train foundation models). I lifted that line straight into the contract with the URL attached.
- **Error liability boundaries** — if the Agent misroutes and causes loss, who covers it? We landed on "direct costs from Agent errors (re-dispatch travel, second part shipping) covered by us; indirect losses (customer downtime, reputation) negotiated bilaterally." We went 5 rounds with Hesheng's legal on this.
- **Data residency** — does cross-region inference (us-east-1 for the 4.6 model) take customer ticket data out of Singapore? Yes. I can't change that. What I can do is write it plainly and let customer legal decide "accept" or "reject." Hesheng legal accepted — on condition that Bedrock invocation logs land in the Singapore region and are queryable.

The biggest lesson legal review gave me — **don't try to "skirt around" or "be vague about" any question the customer can ask**. What legal is most allergic to is vagueness; a clean "we can't do X" is far better than hedging.

**Security review.** Chapter 11 walked Gu Jianguo through this. I added one extra: attaching a summary of Anthropic's [Responsible Scaling Policy](https://www.anthropic.com/responsible-scaling-policy) to the contract — when customer security asks "has the model been red-teamed," that's the public reference.

---

## 12.5 How Money Flows in the Contract

Zhou Mingyuan's third question — how much for the first year, on what basis. This is the most uncomfortable section in real FDE work. But if you don't align with the customer on the money's logic, the first month's bill will start a fight you can't recover from.

For Hesheng I used a "three-tier" structure: **implementation fee + monthly service fee + usage tiers**.

```
  Implementation   One-time ¥X    Covers 12 weeks of delivery (Discovery → launch)
                                   Milestone payment: 30% kickoff + 40% staging + 30% GA

  Monthly service  ¥Y / month     FDE on-call, eval maintenance, monthly review
                                   Year-1 includes 4 on-site visits

  Usage tier       Per-ticket monthly < 5k/month: included in monthly
                                   5k-20k:  ¥0.05 / ticket
                                   > 20k:   ¥0.04 / ticket (declining)
                                   > 50k triggers architecture review
```

I can explain why each tier is cut this way.

**Implementation fee** — fixed for the contract period. The customer fears "scope creeps and they keep paying." The FDE side fears "scope creeps and they keep building." The negotiation lands on writing milestones in stone and tying each to a checklist (Discovery's 5 deliverables, staging passes the five hard thresholds, GA is canary at 100%). Miss a checklist, miss a payment.

**Monthly service** — keeps the FDE team's on-call capability alive. You can't skip it; skipping it means "launch and abandon." But it has to earn its keep — so "4 on-site visits" is in writing. The customer knows what they're buying.

**Usage tier** — this is the new model. Traditional software is sold by license; AI applications priced by call volume make sense (the cost is per-call anyway). The three-tier structure has two intents: low usage doesn't make the customer feel "I paid for nothing" (it's included in monthly); high usage actively triggers an architecture review (over 50k tickets/month may warrant re-architecting, e.g., switching everything to haiku without opus fallback).

A pit I've fallen into in past projects: not writing fallback ratio drift into the contract. After launch a wave of "weird tickets" hit (e.g., a new equipment model just imported), fallback (opus) trigger ratio went from the expected 5% to 22%, per-ticket cost spiked to ¥0.13, monthly bill 60% over budget. Customer leadership got angry over the bill, both sides spent time explaining. This time at Hesheng I wrote into the contract appendix: "fallback trigger rate > 12% auto-alerts + suspends service awaiting human confirmation" — gives me an emergency brake, gives the customer a psychological ceiling.

I sent the three-tier structure to Zhou Mingyuan as an Excel; he read it for five minutes. "Implementation is 20% more than the ISV's quote. Monthly is 30% less. No one prices usage like this." I said: "Implementation is more because we're embedded with you for 12 weeks, not delivering against tickets. Monthly is less because our marginal cost lives mostly in Bedrock usage, not licenses. Usage per-call because that's the real cost structure of an AI application."

He signed.

> I didn't invent this pricing — it's stitched from Palantir's early "embedded consultant + platform fee" model (Nabeel Qureshi describes a similar structure in *Reflections on Palantir*) and modern AI applications' per-call billing. The principle is to compute "FDE human time" and "AI's variable cost" separately. Mash them together and either the customer feels gouged or you take a loss.

---

## 12.6 The Last Two Weeks Before Launch

Weeks 11 and 12 were the most intense weeks on the Hesheng project. Looking back, the cadence:

```
  W11 Mon    Jakarta 1% canary launches
  W11 Tue-Wed Hold, business spot-checks 20 tickets
  W11 Thu    Rollback drill (the one in 12.3)
  W11 Fri    Post-mortem + fix the three findings from the drill

  W12 Mon    10% canary (Jakarta full)
  W12 Tue-Wed Hold, eval CI watched for 3 days
  W12 Thu    50% canary (add Kuala Lumpur + Bangkok)
  W12 Fri    100% canary
              3 p.m.: Zhou Mingyuan / Chen Xue / Gu Jianguo sign GA
              on the contract

  W13 Mon    Handoff begins (Chapter 17)
              I start handing the work to customer ops
```

In these two weeks my standard day: 30 minutes on the dashboard at 9 a.m. (error rate, P95, cost curve, eval rolling average), morning with Gu Jianguo handling overnight alerts (don't take the call, watch how he handles it), afternoon with Chen Xue running ticket spot-checks (she picks 30, we look together at whether the Agent's dispatch reasoning is sound), evening writing a 5-line note for any incident into the project doc.

**The FDE's role in the two weeks before GA isn't "burn the midnight oil fixing bugs"; it's "shadow customer ops onto the job."** Bugs by this point should be mostly washed out by eval and load testing. The real work in these two weeks is hardening "can the customer maintain it without me."

This goes back to what Chapter 1 keeps emphasizing — knowing which phase you're in. Two weeks before launch, if you're still writing new features, the prior phase wasn't done, and the project probably won't last long.

---

## 12.7 A Few Less-Visible Details That Saved Me

After writing the six sections, I looked back at my pre-launch dashboard watchlist and noticed a few items that don't appear on any "launch checklist" template, but each saved me at least once.

**One, cold start latency.** Bedrock's first call to a model has cold-start latency, especially during low-traffic overnight windows. Our dispatcher added a "ping the primary model every 5 minutes" keep-warm — costs an extra few tens of yuan per month, saves the overnight dispatcher's repeated "stuck" complaints.

**Two, prompt version stamped into every log line.** We went through 14 versions of the prompt. CloudTrail logs the modelId, but which prompt version is only visible in our application logs. Writing `prompt_version=v14` directly into the structured log lets you trace "why was this ticket misrouted at the time" back to that version's prompt.

**Three, canary ratio kept by the dispatcher, not just the routing layer.** Our canary is in the dispatcher — bucketed by ticket_id hash. But the customer's load balancer sees request counts, not "percentages." The dispatcher writes its own `routing_decision_log`; we reconcile daily: today should be 50%, actually shipped X%. Once we found actual was 38% — root cause was a class of ticket IDs hashing unevenly. The routing layer won't tell you this.

**Four, fallback isn't just opus.** Our "everything broke" fallback is to forward the original ticket to the manual queue + send the customer an "AI unavailable, transferred to human" notice. Technically simple (one SQS queue + an email), but the IT committee made this a hard requirement. When the Agent goes fully down, it can't return 500; there has to be an end-user-facing graceful degradation.

**Five, week-1 on-call FDE in the customer's timezone.** Hesheng's overseas sites: Jakarta is 1 hour ahead of Singapore, Ho Chi Minh same as Singapore, Kuala Lumpur same as Singapore; the earliest dispatcher comes on at 7:30. In week 1 of GA I had myself up by 7:00 watching the dashboard until their lunch. Technically unnecessary (monitoring fires alerts), but week 1 of customer ops independently handling an AI system, they need to know "if I @ in the channel, someone responds immediately." After that week, they have it.

These five items don't fit in my "five hard thresholds," but they should be in my personal project runbook. Every FDE accumulates their own version after a few projects — and the differences between FDEs' versions are larger than the commonalities. That's what makes this work interesting.

---

## 12.8 Launch Day

W12 Friday 3 p.m., conference room. Zhou Mingyuan, Chen Xue, Gu Jianguo, three people.

The contract appendix's last page has the GA signing fields. Three fields for three things — Zhou Mingyuan signs "business pass-line" (Chen Xue and senior masters spot-checked 100 tickets, OK), Chen Xue signs "business acceptance" (she confirms the Agent can move into the overseas business unit's daily workflow starting next Monday), Gu Jianguo signs "ops acceptance" (he confirms he can independently operate the on-call flow, monitoring, rollback playbook).

Three signatures together — miss one, no GA.

After signing, Zhou Mingyuan asked one last question: "When you start handoff next week, can our people catch it?" I answered: "Gu Jianguo and Chen Xue have been doing 90% of the work for the past six weeks. From next week on, I'm basically an observer." He nodded: "Good. I'll report the launch at the board next Wednesday."

5 p.m. I left Hesheng's Suzhou office. Year-one contract live.

But this chapter isn't the endpoint. The next chapter is on the things **no one tells you in advance** about life after launch — how the noise floor of monitoring is set, how I handled a day where cost overran budget by 30%, in which week the first real rollback happened.

---

## Public references cited in this chapter

- A. Lawrence, *Forward Deployed Engineer Rule Book* (2025) — origin of "PoC is the trailer for the project"
- Conikeec, *The FDE Playbook: A Practitioner's Field Manual* (2025, Substack) — failure modes during the PoC stage
- Anthropic, [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) (2024) — engineering practice of quantifiable pre-launch pass-line conditions
- Anthropic, [Responsible Scaling Policy](https://www.anthropic.com/responsible-scaling-policy) — referenced in security review
- AWS Bedrock docs, [Data Protection in Amazon Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/data-protection.html) — customer data ownership clause
- Bob McGrew @ Y Combinator (2025) — "sell outcomes, not products" reflected in the three-tier contract structure
- Nabeel Qureshi, *Reflections on Palantir* — prototype "embedded consultant + platform fee" model behind the three-tier pricing

[← Part V Intro](../intro/) · [Previous: VPC, SSO, Compliance](../../part-4/chapter-11/) · [Next: Monitoring and Guardrails →](../chapter-13/)
