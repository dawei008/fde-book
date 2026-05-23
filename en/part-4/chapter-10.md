---
title: "Chapter 10 — Scaffolding and the Development Loop"
parent: "Part IV — Engineering for the Real Customer Environment"
nav_order: 2
---

# Chapter 10: Scaffolding and the Development Loop

Suzhou Hesheng Precision Heavy Industries, overseas business unit. Monday morning, week 4.

The architecture sheet from Chapter 6 had three signatures on it. The data map from Chapter 9 was drawn. Bedrock was wired up, eval was running, the KB had its first 1,500 PDFs loaded. By rights this was supposed to be the week the actual work began.

I opened the IDE intending to refactor the 200 lines of dispatcher code, and I couldn't save — VS Code on the customer's workstation didn't have permission to write to `~/.vscode-server`. I switched to SSH and connected to the customer's jump host; the jump host's Python was 3.8.10, and I'd been on 3.11 locally — pydantic v2 wouldn't install. I tried `pip install`, and got "PyPI mirror internal address invalid, please contact IT."

By noon I hadn't changed a single line of code.

This chapter is about that situation: **when the customer's environment chops your "save and see results in a few minutes" rhythm into "two-hour approval cycles," how do you keep pushing the project forward**.

It's three sections. Section 1 is on what scaffolding actually is — not "build the code skeleton," but turning Discovery's conclusions into a minimum loop that can be iterated on continuously. Section 2 is on what the inner loop gets beaten into inside a customer environment, and a set of engineering moves to keep yourself shipping. Section 3 is on staging and hot fix — the part of the work that only really begins after launch.

---

## 10.1 Scaffolding Isn't Building a Skeleton, It's Building the Iteration Loop

A lot of people doing FDE work for the first time produce a README, a Hello World endpoint, and a demo script that runs locally as their "scaffolding." The boss takes a look, says "looks good," and the project moves to the next phase.

That's tutorial-speak scaffolding. The real scaffolding phase **doesn't produce code, it produces the shortest path that takes "I changed one line of code" all the way to "the business side sees the effect in the real environment"**. Every segment of that path has to be runnable inside a working day.

At the end of week 2 on the Hesheng project I drew a workflow diagram that listed every step between "I edit one line of prompt" and "Chen Xue clicks open a ticket at her desk and sees the result":

```
  I edit a line of the prompt
    ↓
  Run eval-v0 locally (10 cases)         ← 30 seconds
    ↓
  Push to the customer's GitLab
    ↓
  Customer's internal GitLab CI runs eval-v1   ← 4 minutes
    ↓
  Build image, push to Harbor             ← 6 minutes
    ↓
  ArgoCD deploys to staging               ← 3 minutes
    ↓
  Chen Xue clicks open a ticket on staging and sees the result ← 30 seconds
```

End to end, that path can run in 15 minutes. Those 15 minutes are this project's inner loop.

In the scaffolding phase, my big-ticket time isn't on writing business code, it's on making sure those 15 minutes can actually run. The line items are mundane:

- Who approves project permissions on the customer's GitLab; who adds the CI runner; how credentials are injected
- It takes 1-3 days to get a Harbor namespace approved, so file the request early
- Who has permission to edit the staging cluster's ArgoCD application template
- Whether the 10 rows of eval-v0 data can go in the repo, or whether they have to live in the customer's object storage
- Whether my IDE's SSH-through-jump-host setup can use Remote Container

None of these items is hard, but each one needs a specific person at the customer to stamp it. If you don't trigger these flows in week 1, week 4 turns out the way my Monday morning did — everything is one step short.

I make a habit of starting a sheet in week 2: left column is "step in the inner loop," right column is "blocked on whom, needs what action," and I walk through it with Gu Jianguo once a week. The day every item on that sheet turns green is the day scaffolding actually begins. Before that, all the code is preparatory — you think you're developing, you're really moving infrastructure.

> Lawrence in *FDE Rule Book* has a line I keep coming back to: "The first thing you build for a customer is not the product, it's the loop." It doesn't translate cleanly, but it means: the first thing you build for a customer is not the product itself; it's the loop in which the product can be iterated.

### The "done" criterion for scaffolding

People often ask me "when is scaffolding done?" There's no silver-bullet answer, but I use three signals:

**One, can a new feature go from idea to a clickable page on staging in 30 minutes.** Not tests passing, not deploy succeeded — the business side can click on staging and see the effect. If they can't, the inner loop isn't standing yet.

**Two, can the eval score run in CI and fire on every PR.** This is the output from Chapter 8. If you're still at "I'll run bench.py locally by hand," scaffolding isn't done — your optimizations don't have an objective answer to "did this make it better or worse."

**Three, can the business side click around on staging on their own.** Not you opening the screen and showing her — she has her own account, opens it herself, gives feedback herself. Chen Xue's feedback drove 70% of the direction of my fixes in the following three weeks; if she can't reach staging, my development is happening in a vacuum.

On the Hesheng project all three signals turned green on Wednesday of week 5. From week 1 to mid-week 5 — over those four-and-a-bit weeks — I wrote less than 800 lines of business code, but once the inner loop was up, the 2,000+ lines I wrote in weeks 6-8 each had eval and feedback underneath. The cost of editing those 2,000 lines was an order of magnitude lower than the first 800.

This is hard for newer FDEs to accept. At the end of week 4, Zhou Mingyuan asked me once: "What have you been doing this past month? Your PR list looks short." I opened the "inner loop blockers" sheet — 27 items, 22 green, 5 in motion. I told him: "Each of these 22 items used to be a potential one-week slip. Once they're all green next week, our pace will visibly speed up." By the end of week 5 he'd noticed the pace shift on his own and never asked again.

### Dev velocity is not LOC, it's loop count

Another way to gauge scaffolding completion is to count loops. In FDE work, a "loop" is one full pass of "hypothesis → eval → decision" — not one commit, not one deploy, but one "I thought X was the problem, ran eval, saw Y, decided to change to Z."

Weeks 6-8 at Hesheng I counted my own loops: 14 in week 6, 19 in week 7, 22 in week 8. By LOC the three weeks were similar, but doubling the loop count meant every segment of the inner loop was running smoother. LOC can drift by less than 10% week-to-week, but loop count can swing by 50%+ — the latter is the real measure of dev velocity.

In my own company, on a normal day I can do 5-8 loops. At a tier-A customer, in week 1 even one loop a day is hard; once scaffolding is done you can stabilize at 3-5. From 1 to 5 — that's what the scaffolding phase is actually doing.

---

## 10.2 Inner Loops in an Environment That Keeps Interrupting You

The environments FDEs work in never run as smoothly as your own company. Local dev machine permissions are restricted, the VPN flutters, the jump host has latency, dependencies don't install, GitHub doesn't reach. These aren't sporadic failures, they're daily life.

I split customer environments into three tiers, and the inner loop looks different in each:

```
        Tier A: Customer's cloud VPC (most common)
          - Customer has an AWS / Aliyun account
          - I sign in with an IAM role they provide
          - Egress controlled by NAT + security group
          - My own Mac connects to the customer VPC through VPN
          - Inner loop: local IDE → push customer GitLab → CI → staging
          - Realistic pace: 15-30 minutes

        Tier B: Customer's private cloud / on-prem
          - Customer has their own K8s / VMware
          - I have to use their Windows workstation
          - SSH through the jump host into the internal network
          - Inner loop: IDE on jump host → internal GitLab → internal Jenkins → staging
          - Realistic pace: 30-60 minutes, dependencies break the loop often

        Tier C: Air-gap (fully offline)
          - No internet, everything goes in by USB
          - There is no "pip install" step in the inner loop
          - Realistic pace: 1-2 hours, with weekly batch sync back to HQ for review
```

Hesheng is tier A, and the inner loop is reasonably intact. But even in tier A, in the first month I kept tripping on these details:

**The Bedrock VPC endpoint must be opened first.** ECS runs in the private subnet; calling Bedrock by default goes through NAT, which gets called out by the customer's security audit. In week 1 I had Gu Jianguo create the `bedrock-runtime` interface endpoint, opened 443 in the security group, and added an endpoint policy restricting `modelId` to the approved few. This step was also called out in Chapter 6 as part of D1 lock-in. Its meaning for the inner loop is that every call from my first line is already aligned with the production security model — I won't suddenly discover in week 8 that "it runs locally but staging denies it."

**KB / Agents must also stay on the private network.** The RAG from Chapter 9 — KBs hitting OpenSearch Serverless go through the public internet by default. You have to enable a VPC access policy on the collection and pin the endpoint to the staging subnet. The first time I didn't configure it, the eval ran locally but timed out on staging. This kind of "environment difference" bug is the most expensive class in the inner loop — because you can't reproduce it locally.

**SageMaker JumpStart is the fallback.** Some customers don't allow Bedrock and require "the model must be self-hosted." For those scenarios I pull a Llama 3.1 / Qwen image from SageMaker JumpStart, deploy it to a SageMaker endpoint inside the customer's VPC, and the SDK call is the same — only the endpoint name changes. The inner loop doesn't change; only the model hosting underneath swaps. We didn't need this on Hesheng — Zhou Mingyuan greenlit Bedrock in week 2. But I know that for the next customer who blocks Bedrock, this path works.

**Eval running fast is a hidden prerequisite for the inner loop.** Eval-v0 is just 10 rows, 30 seconds per run. But eval-v1 has 200, and the first run took 11 minutes. CI taking 11 minutes means I'm waiting 11 minutes after every push to know whether there was a regression — that pulls the inner loop from 15 minutes to over 25. At the end of week 6 I did two things to bring it down to 4 minutes: route the eval calls through Bedrock's Flex service tier (higher throughput cap, half price), and run the full set only on the prompt paths that changed while sampling everywhere else. This kind of engineering optimization looks unglamorous, but it's the real bottleneck for dev velocity.

### Engineering moves when the inner loop breaks

Things will break. I've collected a few moves, ordered by how often they apply:

**One, separate "code that can run offline" from "code that must run on the customer's network."** Prompt templates, utility functions, data schemas, eval scoring logic — all of these can run on my own Mac without the customer's network. The only things that must run on customer infra are calls to Bedrock + the KB + the customer's ERP. I structure the code in two layers: anything mockable locally is mocked, so I can spend 70% of the day pushing forward without being on the customer's VPN. That ratio started at 30% and was at 70% by the end of week 3.

**Two, every prompt lives in the repo, not in Slack.** This came from an air-gap customer, but it applies in every tier. The customer's security audit doesn't accept "the FDE was just trying something" — every prompt and every change must be recorded in the repo. I commit one prompt edit at a time, even if it's just "added a sentence saying don't output markdown." Three months later, `git blame` lets me reconstruct the bug behind every prompt change.

**Three, request the pip / npm allow-list in week 1.** The customer's private PyPI mirror is almost certainly incomplete. Pydantic, boto3, langfuse, every little tool — list them all in week 1 and hand IT one batch to approve. Far less painful than chasing them one by one in week 4. Sounds like common sense, but I still trip over some weird package on every new project.

**Four, simplify recurring problem features.** From an air-gap customer I learned a rule: fewer dependencies are safer. Debugging a third-party library inside a customer environment costs 5-10x what it costs at home — you can't search Stack Overflow, you can't browse GitHub issues, you can't pull its source into your IDE and step through. After a third-party library has caused trouble twice, I start considering whether 200 lines of my own code can replace it. Chapter 6's "Level 0 first" judgment is rooted in this same reasoning.

**Five, batch-sync code back to HQ for review and backup every weekend.** Customer-network isolation means the code only exists on the customer side. If their disk dies, or your access is revoked, three months of work is gone. My habit is to zip the code up before leaving on Friday and ship it back through the customer's "egress software process" to a private repo at HQ as a cold backup. An older FDE on an air-gap customer taught me this — his exact words were "the customer's IT team isn't your colleague; they have their own KPIs, and on any given day they can perfectly reasonably revoke your access."

> Conikeec in *FDE Playbook* calls this class of moves "defensive engineering" — not about writing pretty code, but about preserving your ability to keep shipping inside the uncontrollables of a customer environment.

### Signs you're already in an anti-pattern

I've seen these inner-loop anti-patterns over and over; listing them:

- **Local SaaS API, swap to private deployment at launch.** Model behavior differences, context window differences, tool-call format differences — any one of them can make staging behave wildly different. The first row on Chapter 6's architecture sheet is "D1 lock-in" specifically to avoid this.
- **No VPC endpoint, going out through NAT.** Works short-term, gets red-flagged by the customer's security audit. Every project, in week 1, I draw a single diagram of every external traffic flow with a corresponding endpoint or NAT, and have Gu Jianguo sign off.
- **Installing third-party deps without filing software ingress.** Customer IT warns once, revokes your dev-machine access the second time.
- **Downloading customer data to a local machine for analysis.** This is the #1 compliance incident; I've personally seen someone get escalated by their PM to the customer's CIO over it. Customer data stays on the customer side; analysis stays on the customer side; results may be exported after de-identification — that's the line.

The hardest one to remember is the first. SaaS APIs locally are a delight; everyone wants to start that way. The price is paid in full in week 8 — and week 8 is usually the week the customer's leadership sees the first demo.

What I did at Hesheng was, in week 1, wire my own Mac through to the customer's Bedrock VPC endpoint (VPN + STS assume role), so my local dev hits the customer account's models directly. My dev path is now identical to the staging path. The first wire-up took most of a day, and over the next 12 weeks I never tripped on a "runs locally, doesn't run on customer side" bug. A one-time up-front cost in exchange for zero environment-difference bugs later — that math checks out.

---

## 10.3 Staging Deployment and the Hot Fix Lane

After scaffolding is done and the inner loop runs, the next gate is staging. Staging isn't "the last check before launch" — staging is the most underrated part of FDE work. It's where the business side actually uses the system, and it's the first dress rehearsal for "can the customer maintain this."

Staging on the Hesheng project ended up looking like this:

```
  Staging cluster (customer's ap-southeast-1 ECS)
    ↓
  Domain: agent-staging.hesheng.internal
    ↓
  Access: customer-internal VPN + Identity Center SSO
    ↓
  Data: ticket DB mirror + full KB + ERP read-only
    ↓
  Logs: CloudWatch Logs + Langfuse self-hosted
    ↓
  Eval: eval-v1 runs automatically on every deploy, results posted to Slack
```

I started building this from week 4; Chen Xue could use it in week 5; in week 7 Master Wang and two other senior service engineers were added. By the time we demoed in week 8, staging had accumulated more than 600 real call records, each with a trace, token usage, and a "right / wrong / passable" three-tier label from the engineers.

Those 600 records were the fundamental reason the week 8 demo landed. **Zhou Mingyuan asked "why 95% accuracy?" — I opened Langfuse and showed him 600 real ticket traces. This wasn't a demo; it was a tool already in use.**

### A few key points about staging

**One, staging uses real data.** A lot of people put de-identified or synthetic data on staging, then on launch day discover edge cases the synthetic data never hit. My recommendation is to mirror the ticket DB, hash PII fields (customer names, phone numbers), and keep the rest. Staging like that reflects production behavior. On compliance, sit down with the customer's legal team and tighten staging access to FDE + a few core business people.

**Two, staging must have a "retract" capability.** When the business side hits some wrong conclusion on staging, can you immediately retract that record so it doesn't get logged into the KB? Can you one-click rollback a bad prompt version? I wired both into staging in week 4. Retract isn't as critical as in production, but it determines whether the business side trusts staging enough to "use it freely." Chen Xue triggered two wrong outputs on staging in week 6; each time I retracted them within 30 seconds. Starting in week 7 she clicked around more aggressively, and feedback volume went from ~20 a week to ~90 a week — that data curve maps directly to whether the retract capability is in place.

**Three, staging is the rehearsal stage for the hot fix lane.** When something breaks in production some day after launch, the path from "alert received" to "fix deployed" is something you must have rehearsed on staging.

### The hot fix lane

Three weeks after launch on a Tuesday afternoon, Chen Xue @ed me in Slack: "Ticket T-2026-0531 was misrouted; the customer has already complained to Director Zhou."

The path from that message to the fix landing in production:

```
  14:32  Got @ed
  14:35  Opened Langfuse, saw the trace, located the issue:
         KB retrieval recall was wrong
         (the ticket said "spindle vibration" but was retrieved as "spindle replacement")
  14:48  Reproduced on staging, confirmed: chunking split the alarm code
         into the next chunk so the prompt's context was incomplete
  14:55  Changed chunking strategy (800 token → 1200 token + 500 overlap)
  15:02  Pushed, CI ran eval-v1, all 7 historically similar tickets passed
  15:08  Staging deploy done; had Chen Xue re-run T-2026-0531 on staging — OK
  15:14  ArgoCD pushed to production at 5% canary
  15:30  Canary stable, rolled to 100%
  15:35  Replied Chen Xue in Slack: "Fixed, T-2026-0531 confirmed correct, traffic at 100%."
```

The whole hot-fix lane: 1 hour 3 minutes. That time isn't because I'm fast — it's because the inner loop + staging + eval-v1 we built in the first 8 weeks each played their part on this path. If any of the three hadn't been built right, this hot fix would have likely taken a full day.

**The inner loop pushes staging deploy under 8 minutes** — which is why I could have Chen Xue re-run at 15:08. **Eval-v1 runs in CI automatically** — so 6 minutes after my 15:02 push I knew 7 similar tickets all passed and this fix didn't regress. **Staging uses real data** — so "reproducing on staging" is a real question, not "build a test case."

> Bob McGrew at YC had a line: "Most production bugs are not new failures, they're old failures that scaffolding didn't surface." The "chunking splits the alarm code" issue I hit on that hot fix — when I post-mortemed it, eval-v1 had no sample where the alarm code lived on a chunk boundary. After the fix, the first thing I did was add T-2026-0531 to eval-v1 as case 251. Same class of bug won't make it to the customer side again.

### How the hot fix lane gets rehearsed

For compliance-strict customers, "Tuesday afternoon push to production" simply isn't allowed. Most customers will require hot fix to go through a simplified approval flow: one on-call SRE + one FDE, no full change-request workflow. That simplified lane has to be negotiated with customer IT before launch, written into the runbook, and rehearsed at least once.

Hesheng's simplified lane was negotiated jointly by Gu Jianguo and me in week 9. We made a bet at the time: before the week-11 launch, we'd run a fire drill — deliberately introduce a P0 bug on staging and walk the entire hot-fix lane end to end, target time 1 hour. The first run was 1h 47m, mostly stuck on approvals (the on-call SRE was a colleague who wasn't at his desk). We adjusted the flow and the second run was 52 minutes. When T-2026-0531 broke production three weeks later, the fix took 1h 3m — that number isn't a coincidence; it was rehearsed.

If you remember one thing from this chapter: **the hot fix lane isn't built after launch — it's stood up during scaffolding and rehearsed over and over on staging**. Building it after the first real incident is too late.

### Two lessons from fire drills

I wrote up a small post-mortem after the Hesheng fire drills. Two lessons most useful for the next project:

**One, don't tell the business side ahead of the drill.** On the first drill I gave Chen Xue a heads-up "we're going to drill an incident this afternoon"; she happened to have her phone right there and replied to the @ within seconds. In a real incident the business side is "just back from a meeting and seeing a stack of messages in the channel." On the second drill I didn't tell her, and she saw the @ 14 minutes later — that's the real start of the flow. Drills should be as honest as possible about timing.

**Two, always re-watch the trace after the drill.** On the first drill we shipped the fix and stopped — never reviewed. On the second I had everyone sit down and walk through the Langfuse trace; we discovered that during the hot fix window the KB had 3 empty retrievals, papered over by a code fallback so they never surfaced. Those 3 empty hits were caused by KB index inconsistency during the deploy window. That hidden bug is only visible in a post-incident trace review. Reviewing is the other half of the drill.

---

## Wrapping Up

From week 1 to week 8 on the Hesheng project, the bulk of my time wasn't spent "writing an LLM application" — it was spent standing up the inner loop, building staging, drilling the hot fix lane. These moves don't look glamorous on a resume; nothing as eye-catching as "we used RAG." But they're the fundamental reason the project crossed from demo to production without crashing.

When you start week 1 on your next project, you can ask yourself a simple question: **how many blockers sit between "I edit one line of prompt" and "the business side sees the result in the real environment, and I haven't unlocked them yet."** List them one by one, find the right person at the customer, unlock them one by one. Push it through until all three signals turn green by the end of week 5; that's when scaffolding is actually done. Before that, all the code is preparatory. The next chapter, on integrating with legacy systems — SSO, SCIM, API, audit — has a lot of content rooted in the same underlying logic: if you don't unlock these blockers, the inner loop will never run smoothly inside the customer's environment.

---

## Public references cited in this chapter

- A. Lawrence, *Forward Deployed Engineer Rule Book* (2025) — "The first thing you build for a customer is not the product, it's the loop."
- Conikeec, *The FDE Playbook: A Practitioner's Field Manual* (2025, Substack) — "defensive engineering" section
- Bob McGrew @ Y Combinator (2025) — relationship between staging and production bugs
- AWS official docs: Bedrock VPC endpoints / PrivateLink for Bedrock / SageMaker JumpStart private deployment — factual basis for the D1 paragraph
- Nabeel Qureshi, *Reflections on Palantir* — on why "defensive engineering" inside customer environments is the FDE's hidden core capability

Full bibliography and links in the *References* section at the end of the book.

[← Previous: Customer Data Stack](chapter-09.md) · [Next: Integrating with Legacy Systems →](chapter-11.md)
