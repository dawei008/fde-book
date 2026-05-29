---
title: "Chapter 17 — Project Handoff"
parent: "Part VII — Handoff and Continuity"
nav_order: 1
---

# Chapter 17: Project Handoff

Suzhou Hesheng Precision Heavy Industries, overseas business unit, week 11 after phase-two GA.

The phase-two parts-ordering + cross-site coordination agent had been running steadily for two and a half months. The Bedrock Agent runs in ap-southeast-1; of the 14 tools, 12 are Hesheng-specific (Ch14), 3 external SaaS go through stateful MCP on AgentCore (Ch15). Eval-v3 has 200 cases, runs weekly in CI, passes at 92%. The phase-one Haiku triager is still running as fallback for phase two — the signature on the A4 in Ch6 has held for an entire year.

In a weekly sync Zhou Mingyuan dropped a line: "The FDE contract ends end of December. Next year we want to take this over ourselves." Chen Xue and Gu Jianguo were both there; nobody picked up the thread — but that line was Hesheng's final exam for both phases.

The next eight weeks are my answer to that exam.

---

## 17.1 Handoff Isn't the Demo After Launch

Lots of FDE handoffs make the same mistake: scheduling handoff after launch as a closing ceremony. The customer's ops team gathers, the FDE reads a deck, an acceptance form gets signed, the contract closes. Three months later, customer ops can't change a prompt; they call back; the FDE flies out again.

That isn't a handoff. That's an FDE treating the project as their project.

The engineering definition of handoff is one sentence: **the customer can run this system independently without you**. That sentence unpacks into four observable capabilities:

```
        Whether handoff is really done — four things:

  1. The customer can independently change a config and deploy it
     —— prompt / KB data / model id, change one, canary out

  2. The customer can independently read traces and find root cause
     —— accuracy drop, they don't pick up the phone first

  3. The customer can independently run an eval
     —— before upgrading models / changing prompt, they have data first

  4. The customer can independently handle the top 5 failure types
     —— P1 stops the bleeding in 5 minutes, not escalates first
```

All four in place — handoff is done. Miss one, you'll be called back next quarter.

None of these are things that "just teach them after launch" can teach. They're designs from project day one — built so the customer can take this over later. Discovery's interview pool must include the receiver-to-be; Scaffolding's code style must match what they can maintain; Production's alerts must go to the customer's on-call channel — not to my own Slack. Handoff is design, not closing ceremony.

The way I do this at Hesheng is to count down 8 weeks from GA. From GA forward, handoff is on the clock; one milestone per week; in the final week the customer drives, I sit in the back row.

---

## 17.2 The 8-Week Countdown

The countdown's starting point is a simple list — who is the customer's receiver, where are the capability gaps, which gap each week fills.

The receivers at Hesheng were chosen before GA:

- **Wang Lei**, ops on Gu Jianguo's IT team, 5 years AWS experience, can write Python but not deeply. Owns D1 (Bedrock config / VPC endpoint / IAM policy).
- **Shen Jia**, product manager on the after-sales business systems team, reports to Chen Xue, Python beginner-level. Owns D2-D4 (prompt / KB maintenance / agent orchestration logic / updates to the 5 Ch16 Skills).
- **Zhang Wei**, an overseas service engineer turned internal data analyst, writes SQL not code. Owns D5 (run eval / dashboards / failure post-mortems).

These three profiles set the capability gaps I had to fill: Wang Lei doesn't need AWS basics, but does need Bedrock-specific traps; Shen Jia needs "how to safely change a prompt" — not prompt engineering, but how to validate after changing through eval, then ship; Zhang Wei needs to learn how to read traces, how to write CloudWatch Logs Insights queries.

These three gaps aren't my guesses; in week 2 after GA I had each of them do a "if I take over now" hands-off drill. Given a real alert (error rate climbed from a 0.4% baseline to 1.2%), they were each given 30 minutes to operate independently. Results:

- Wang Lei found Bedrock's service status page but didn't realize that when cross-region inference profile breaks, you need to look at the other region's health.
- Shen Jia changed the prompt correctly but pushed straight to production canary without running eval.
- Zhang Wei navigated from dashboard to trace but couldn't read the tool call's input/output JSON.

These three specific stuck points became the training targets for the next 8 weeks. **Handoff isn't "explain it once and we're done"; it's "the specific stuck point passes after practice."**

The countdown:

```
  T-8   Capability assessment + training plan locked
  T-7   Runbook v1 + dashboard permissions for everyone
  T-6   Wang Lei drives a prompt canary release (I ride along)
  T-5   Shen Jia drives a KB incremental update + eval rerun
  T-4   Zhang Wei drives a failure post-mortem (real alert from last week)
  T-3   Three of them collaborate on a simulated failure (I inject an error)
  T-2   Three of them independently handle a real alert (I'm absent, review after)
  T-1   Full pair: I sit half a day with each, watch their full workflow
  T     Contract ends. I rotate to on-call, fully exit after 4 weeks
```

T-3's simulated failure is the critical milestone. If the three together can't pass, handoff doesn't close on schedule — I made this clear to Zhou Mingyuan in week 1, and wrote "handoff admission threshold" into the SOW amendment.

---

## 17.3 The Runbook Isn't a Document, It's a Practice Book

A Runbook isn't written for the customer to refer to; it's written for them to follow. The difference: a reference can be "complete" — list every possibility; a practice book must be "good enough" — every line maps to a specific operational action, every line operated by the customer at least once.

Hesheng's Runbook splits into 6 sections:

```
  1. System architecture diagram (one page; mark each component's account / region / VPC)
  2. Deploy + rollback SOPs (command-level; every line copy-pastable)
  3. Top 10 failures + handling flow
  4. Eval trigger conditions + how to run + threshold meanings
  5. Configuration items list (which value lives in which file; what to do after editing)
  6. Escalation paths (when to call whom; including AWS support tier and contacts)
```

Section 3, Top 10 failures, is the body of the Runbook. The 10 aren't imaginary; they're picked from real customer incidents during the 11 production weeks. Each follows this format, length capped at one screen:

```
═══════════════════════════════════════════════════════════════════
  SOP-003: Agent tool-call rate suddenly drops
═══════════════════════════════════════════════════════════════════

  Symptom: dashboard "tool_call_count_per_session" drops from baseline 3.2 to 1.1
           often paired with rising "agent_returned_text_only" ratio

  Step 1: Check Bedrock model availability
    Console → Bedrock → Cross-region inference → us.anthropic.claude-haiku-4-5
    If shown throttled → go to Step 2
    If normal → go to Step 3

  Step 2: Switch to fallback inference profile
    In Parameter Store change ACTIVE_PROFILE to FALLBACK_PROFILE
    Path: /hesheng/agent/active_profile
    Effective: < 1 minute (Lambda reads on next cold start)

  Step 3: Look at agent trace
    CloudWatch Logs Insights:
      filter @logStream like /agent-orchestrator/
      | filter @message like /tool_selection/
      | stats count() by tool_name, action
    If "no_tool_selected" share > 30% → go to Step 4

  Step 4: Check prompt
    git log --oneline -5 -- prompts/
    Did the last 3 commits touch system prompt?
    Yes → ./scripts/rollback.sh prod --to-prev
    No → escalate (Step 6)

  Step 5: Run eval-v3 to confirm recovery
    ./scripts/run_eval.sh prod --suite=v3
    Pass rate back > 90% → write incident report
    Pass rate still < 90% → escalate

  Step 6: Escalate
    Slack: #hesheng-fde-oncall
    Urgent (P1): Zhou Mingyuan + Wang Lei phone call
    AWS Support: Business tier, case + Bedrock label
═══════════════════════════════════════════════════════════════════
```

A principle for writing Runbooks: **every SOP, after you write it, have the customer's receiver do it themselves without you demonstrating**. Whatever runs through stays; what doesn't, go fix the doc. The 10 SOPs got revised at least three times this way.

Section 4 (eval) matters more than it looks. The most common mistake the customer will make after taking over: "edited the prompt, shipped it directly" — not because they don't want to run eval, but because eval has cost (time / token / mental load), and at the moment of an urgent fix, the first instinct is to skip it. So the opening line of section 4: "Any change to prompt / KB / model id requires eval-v3 to run before canary release. **No exceptions.** For P1 emergency fixes, run eval-v3-smoke (30-case quick set, 5 minutes)."

That sentence pairs with SOP-003's Step 5 above. At this density, the customer will follow it.

---

## 17.4 Eval Set and Runbook Must Run Independently

This is one I learned the hard way.

A previous 16-week project, I wrote a Runbook at handoff, handed off the eval set, and considered the docs complete. Six months later the customer's engineers tried to run eval — couldn't. The script depended on a conda env I had locally; the docker image didn't have it; a few fixtures referenced a file in my own S3 bucket whose permissions had expired; the Runbook said "follow section 6.2's steps" — section 6.2 was actually in another doc on my laptop, never merged into delivery.

The customer spent three weeks getting the env running. Since then I've made "runs independently" a hard handoff metric.

Specifically: in T-4 I run a "sandbox drill":

1. In the customer's account, open a brand-new AWS account (not region — account).
2. Hand Wang Lei a `git clone`, a README, and the Runbook — **only these**.
3. Have him deploy the whole system from scratch, run an eval, ship a prompt change.
4. I sit next to him but don't guide; I just record where he gets stuck and which sentence in the doc is inaccurate.

At Hesheng Wang Lei took 1.5 days, got stuck at 11 points. The two worst:

- The IaC has a Bedrock model access state dependency. Under a new account, model access defaults to off, but our CDK doesn't auto-enable it (must be enabled by hand in the console). The Runbook had this step but in section 5 "configuration items"; Wang Lei reading in deploy order didn't reach it. Fix: move that line to Step 1 of section 2 "deploy SOP."
- A customer email field in the eval golden set was redacted (compliance requirement), but the redaction script was something I ran by hand — not in IaC. Under a new account, eval errors with "email format invalid." Fix: write the redaction into a CDK custom resource that runs at deploy time.

After those 11 fixes, Zhang Wei ran from scratch — this time 4 hours.

**Eval set and Runbook must run independently** — the criterion is the sandbox drill passing. The criterion isn't doc completeness or process completeness; it's "ran from zero successfully."

---

## 17.5 The Final Week's Pair

In T-1 I did one thing: sat half a day each with the three of them, working through every real piece of work they got that week.

Not training, not demo — pair. I sat next to them, they worked normally, and I only spoke when they got stuck — and even then, didn't give the answer; instead I asked back: "what data did you just look at; what should you look at now?"

This week's design comes from reading Conikeec's *FDE Playbook*. He describes Palantir handoff's last week with a phrase: "shadowing in reverse" — for the first six weeks, the customer follows the FDE; in the last week, the FDE follows the customer. That reverse shadowing is the final test of whether handoff actually took.

Hesheng's most valuable discovery that week was Shen Jia's workflow. When she edits prompts, she doesn't actually edit the system prompt I wrote — she edits the "business glossary" in the KB. I hadn't realized that for Hesheng's ops people, "prompt" and "KB doc" are the same thing in their mental model — they think as long as the agent "sees" the right description, it'll act accordingly. That mental model isn't wrong, but it means in my Runbook the KB maintenance section needs to be promoted in priority and the prompt section can be simplified.

In T-1 I rewrote section 5 of the Runbook (configuration items) to treat KB doc versions equally with prompts — all KB changes go through git commit + eval + canary. Shen Jia's downstream work follows that path.

Without that week's pair, this mental-model gap would never have been visible. The Runbook would have been written in my "prompt first, KB second" order; Shen Jia would have followed but inefficiently, error-prone — three months later it'd become "the customer didn't use the tool well." Actually, the tool's shape didn't fit the customer.

---

## 17.6 Phase 2 Boundaries

The day the contract ends, Zhou Mingyuan asked me: "After phase two, next year we want to do a sales agent on Salesforce — can your firm continue?"

This isn't a handoff question; it's a commercial one — but it has to be answered during handoff because the answer affects handoff boundaries.

My judgment: Hesheng's handoff completion means Hesheng can independently run **the current system**, not that they can independently do the next phase. The next phase is a new project — redo Discovery, realign outcomes, sign a new SOW. Handoff cannot slide into "well, they can always ask me later" — that isn't handoff; that's the engineer becoming a part-time consultant.

Zhou Mingyuan and I agreed on three things:

1. **Current system on-call**. After contract end I have an 8-week on-call window: P1 4-hour response, P2 24-hour. After 8 weeks, fully off; further requests go through commercials.
2. **Next phase Discovery**. If Hesheng wants the sales agent next year, our firm can take it, but we run Ch4's full Discovery — starting from a week of desk-shadowing. Not "extend the current agent."
3. **Code IP**. The code, prompts, eval set, and Runbook for this system all belong to Hesheng. Our firm retains only "experience" (the patterns covered in 17.7), no code.

Item 1 is handoff's hard boundary — within 8 weeks it's "extended warranty"; after 8 weeks the customer's problems are the customer's problems. Item 2 prevents "the next phase becomes free overtime." Item 3 is a compliance matter, but also engineering — once handed off, the customer can change anything without coming back to ask us.

These three were written into a "Handoff Completion Acknowledgement," with three signature fields: Zhou Mingyuan, Chen Xue, Gu Jianguo. This sheet plays the same role as the A4 in Ch6 — it's the talisman in every "whose problem is this" conversation later.

---

## 17.7 Project Post-Mortem and Pattern Extraction

The week the contract ended I didn't immediately move into the next project. I held five days for post-mortem.

Post-mortem isn't writing a deck; it's answering four questions:

```
  Q1: What work on Hesheng would be "basically the same on another customer"?
       → Source of templates

  Q2: What work "took a lot of time but could be saved next time"?
       → Source of tooling / scaffolding

  Q3: What was "easier than I thought, harder than I expected"?
       → Source of warnings, things to ask in next Discovery

  Q4: What "I did wrong but the customer didn't pursue"?
       → Most expensive class of experience
```

What I extracted from Hesheng:

**Q1 outputs (templates)**: an overseas-service Discovery questionnaire for manufacturing (the 28 items from Ch4 with 5 overseas-specific additions — timezone, cross-region data compliance, native language vs working language); a Bedrock Agent + AgentCore stateful MCP IaC starter (CDK, 500 lines, with Hesheng business specifics stripped); an Eval CI starter (GitHub Actions + bedrock-runtime + three tiers smoke/full/regression).

**Q2 outputs (scaffolding)**: an MCP server health-check script (born from the OAuth token expiry incident in Ch15); a Lambda template for Bedrock cross-region inference profile auto-switching (born from the region jitter incident in Ch13); a Runbook Markdown + Mermaid template (10 SOPs in standard format).

**Q3 outputs (warnings)**: customer ops mental-model differences (the prompt vs KB finding from 17.5), written as a card "ask these 3 questions to gauge how the customer understands prompts"; customer receiver capability assessment (the hands-off drill from 17.2), written as a reusable 30-minute test sheet.

**Q4 outputs (most expensive)**: in Hesheng phase one's eval-v0 labeling I let Chen Xue do it alone (the trap at end of Ch6); only by phase two did we add double-blind. With a less forgiving customer this would have crashed phase one. I wrote it as a "Discovery must-do 5" card; item 1 says "eval labeling is double-blind from day 1."

These outputs don't go into my own Notion; they're merged into the company internal wiki. Each is tagged with origin (Hesheng phase one Ch6 / phase two Ch14 / Handoff Ch17) and the problem it solves. The next FDE picking up an insurance or manufacturing-overseas-service project starts here — not from zero, but on top of Hesheng's year of experience.

In *Reflections on Palantir* Nabeel Qureshi describes Palantir's FDE culture: every project, FDEs do an internal share — not "we won," but "what was our most expensive lesson this time." That culture holds for AI-application FDEs too. Win stories: colleagues nod. Hole stories: colleagues avoid the same hole. **What's most valuable isn't the success story; it's the failure written clearly.**

---

## Holes I've Stepped In on This Topic

This chapter mostly covered what we did right at Hesheng. But the holes I stepped in on prior projects are also worth recording.

The first time I did handoff, I scheduled it after launch by two weeks. Result: those two weeks customer ops was busy supporting the launch, no time for training; training pushed to week three, by then launch had stabilized, customer urgency was gone, training quality suffered. **The handoff countdown has to start from an early production milestone, not after launch.** Starting from GA at Hesheng was learned from that hole.

The second time I wrote an 80-page Runbook, considering it complete. Three months later the customer told me: they had never read it through; every time something broke, they ctrl-F searched for keywords. **Runbook length isn't a quality metric; executable density is.** Hesheng's Runbook capped at 22 pages, every SOP one screen.

The third time, in handoff week I taught too much — covering "everything you might possibly need." The customer's engineer told me afterwards: "I nodded at everything you taught, but forgot it once back." **Handoff doesn't teach knowledge; it teaches muscle memory.** At Hesheng I had each of the three practice 1-2 things, but each thing 4+ times.

The fourth time (didn't fall in but came close): at Hesheng, T-3's simulated failure took the three of them 50 minutes to handle, slower than my expected 20. I had the urge to say "close enough; close handoff on schedule." But mapping that to 17.1's four capabilities — independently handle top 5 failure types — 50 minutes vs 20 minutes of bleeding is the gap of tens of minutes of real customer business loss. I added a week; in T-2 they did it in 18 minutes. **The handoff admission threshold cannot be lowered at the last moment.** If I had lowered it, three months later when that failure actually happened, the customer would take 50 minutes to stop the bleeding, and I'd be called back.

---

## Next Chapter

Hesheng's project closes the loop end-to-end here, from Discovery through Handoff. From Ch4 to Ch17 it took me a year; what's been written down is the year's actual moves and judgments.

But FDE as a profession isn't stacking experience project after project — that just lets you do "more" projects, not "different" projects. The next chapter is on the FDE's own long-term growth: how to layer industry depth onto engineering depth, how to avoid becoming a "senior implementation engineer" by your third or fifth similar project.

---

## Public references cited in this chapter

- A. Lawrence, *Forward Deployed Engineer Rule Book* (2025) — the framework "handoff is design, not event"
- Conikeec, *The FDE Playbook: A Practitioner's Field Manual* (2025, Substack) — "shadowing in reverse" framing for the final pair week
- Nabeel Qureshi, *Reflections on Palantir* — origin of Palantir's FDE post-mortem culture of "talk holes, not wins"

Full bibliography and links in the *References* section at the end of the book.

[← Part VII Intro](../intro/) · [Previous: Skill — Packaging Customer Expertise for Agents](../../part-6/chapter-16/) · [Next: The FDE's Next Step →](../chapter-18/)
