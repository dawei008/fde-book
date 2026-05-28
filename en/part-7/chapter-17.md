---
title: "Chapter 17 — The FDE's Next Step"
parent: "Part VII — Handoff and Continuity"
nav_order: 2
---

# Chapter 17: The FDE's Next Step

The day after the Hesheng contract ended, I didn't fly back to HQ. I stayed in Suzhou for three more days.

Not because there was project work left — I just wanted to pause. From Discovery to Handoff, eleven months, every week pushing some specific thing forward, like running a relay with no halftime. The day Hesheng went GA I wrote one line in Slack — "project is stable" — closed the laptop, and the next morning I woke up realizing one thing: this whole year I had never asked myself "where do I want to go next."

What I did over those three days in Suzhou was simple: reread the 200+ post-mortem entries I'd kept in my notebook and picked out 30 I still felt held up. Then I divided those 30 into two columns: "engineering" and "industry." When I was done, I saw two things — engineering had 22; industry had 8. I had thought I spent this year doing "LLM agents for manufacturing overseas service"; in fact 80% of my time went into general engineering capability: eval sets, canary, IaC, handoff. The remaining 8 were what I had actually learned at Hesheng over the year that wasn't transferable to another customer.

This chapter is about how the FDE walks the years afterwards. **The first 16 chapters assume you're inside some specific project**, going from Discovery to Handoff; this chapter assumes you've done 5+ projects and are starting to ask yourself less-urgent but important questions — where to next, whether to lead a team, whether the things in this book are everything FDE work covers.

If you're a 0-12 month FDE, you can skip this chapter for now — the things here don't apply until you've finished your first 3 projects, and reading them ahead of time will distract you on the first project. **The first year's key isn't planning 5 years out; it's finishing one project end to end.** But you can come back to this when the first year ends and you're entering the third project. By then this chapter will start to resonate.

This is also the book's last chapter. So I'll cover the book's own limitations along the way — what it doesn't cover, what it gets wrong, what will probably be rewritten in five years.

---

## 17.1 Year 1-3 Growth Is Non-Linear

The biggest illusion for a new FDE in year one is "linear growth" — thinking project 1 done = +1 ability, project 2 done = +1 more, three years = +3. I thought this in year one too; finishing project 3 I realized I was barely stronger than at the end of project 1.

Watching a dozen FDEs over the years, the three-year growth curve looks roughly like:

```
        FDE 3-year growth curve (subjective)
        ──────────────────────────────────────

  Capability
   ▲
   │                                    ╱─── Year 3
   │                                  ╱
   │                                ╱
   │                              ╱
   │                            ╱─── Late Year 2
   │                          ╱
   │                        ╱
   │     ─────────────────╱   ← First "sees the pattern" inflection
   │   ╱
   │  ╱──── Year 1
   │
   └──────────────────────────────────► Time
       Project 1   Project 2   Project 3   Project 4   Project 5
```

Year 1 is flat — you're learning the "basic capabilities" every project needs: how to navigate the AWS console, how to call Bedrock, how customer meetings run, how to read SOWs. Every project uses these; by the end of project 2 you've grown them; project 3 doesn't grow them further. In year 1 I was anxious about "I'm not getting stronger" — only later did I understand: year 1 is muscle-building; muscles aren't visible until they're built.

The inflection usually comes on project 3 or 4. **It isn't a moment of epiphany; it's the first time you "see the pattern" — you suddenly realize "wait, I've seen this on the previous customer; same class of problem."** Pattern extraction from Ch16 produces compounding here for the first time: you're no longer working "the Nth independent project"; you're "validating my templates on the Nth customer."

My own inflection was on the project before Hesheng — an underwriting RAG for an insurance company. In Discovery I was using the prototype of the same questionnaire I used at Hesheng, and I found that the customer's internal understanding of "prompt" was identical to Hesheng's — they also treated KB docs as prompts. **Two customers from totally different industries had the same mental model among their ops staff.** From that moment on I started believing in "patterns."

Mid-late year 2 you'll experience a particular fatigue — not physical, but the weariness of "I have to do Discovery again." That's a good sign. That weariness means you're starting to predict things, and what you can predict no longer feels novel. The pleasure of FDE work shifts from "solving problems" to "watching myself become a certain kind of engineer." If you're still in year 2, every Discovery still feels new, every handoff still leaves you wondering what to do — you aren't growing; you're repeating "doing it for the first time."

What does this mean for a 0-12 month FDE? It means don't panic about slow growth in your first two projects. **The output of those two projects isn't your capability curve; it's the training data for every project after.** Whether you can extract patterns from that training data on project 3 decides what the next five years of you look like.

If by project 5 you still don't see patterns — every customer feels "uniquely special" — it isn't that the projects are unique; it's that you aren't doing pattern extraction. Ask Ch16.7's four questions (what's the same / what could be saved / what's a warning / what didn't get pursued) at every project's end; three projects in, you can extract something. I've watched a few FDEs who "did 5 projects and stayed in place" — their common feature isn't weak technique; it's never sitting down to write a post-mortem at project's end. Each project ends, they go straight into the next one — heat hasn't faded before the next SOW takes over. That cadence looks diligent in the first two years; in year three you'll notice diligence has bitten you.

---

## 17.2 Three Forks After Project 5

After 5 projects — roughly 2.5 to 3 years in — FDEs usually face a career judgment: which path is next. Three common forks I've observed.

**One: stay in the field, climb to Staff / Principal FDE.** Same work shape — embedded with the customer, Discovery to Handoff — but more complex customers, larger contracts, higher chance of being assigned firefighter duty. Towards the end of my third project I saw a Principal FDE walk in — he did exactly what I did, but on day one of Discovery he identified the customer's compliance department as the project's hidden veto, and got us in front of compliance two weeks early. I couldn't have made that judgment; he could because he'd fallen into similar holes. **The Principal FDE's scarcity isn't technical depth; it's "seeing the hole 4 weeks earlier."** The bottleneck on this path is industry depth: if you change industries every 5 projects, by project 8 you're still "stepping on first-time holes" with no accumulation. The Principal path is essentially pulling "hole-detection speed" past a critical value — fast enough that customers pay you not to write code but to predict risks they themselves can't see.

In the last two weeks before the Hesheng contract closed, another project at the firm needed a fire rescue, and I was pulled in for a one-time "two-week diagnostic." A new FDE on that customer had been there three months — their Discovery report was thick but the project hadn't moved. Before going I read his report — solid, every use case listed, but no description of "which role inside the customer would actually work to this use case." That's where Discovery reports collapse most often.

Two days on customer site I found the hole. I could make that judgment because I had personally written the same kind of collapsed report — on year-one's insurance project I delivered "use cases complete but no people" too. Principal FDEs' "see the hole 4 weeks early" essentially means "I've seen this hole on myself." This path's prerequisite is your willingness to write down each project's failures — the more failures you've written, the more customer failures you can predict.

**Two: become an FDE team lead.** From mentoring 1-2 newcomers, gradually scaling to a small group of 5-10 FDEs. The most common misjudgment on this path is treating lead as "a more senior FDE" — assuming you keep doing projects and incidentally guide newcomers. That's not it. An FDE lead's core work changes in three ways: customer assignment (who fits which customer), project triage (which projects to call early), people growth (which FDE is at which stage, what kind of project they need next). All three are unrelated to writing code, and related to "judging the fit between people and projects."

I once watched the most painful FDE-to-lead transition in my circle. Year one he was still grabbing projects — 5 newcomers under him with no review, no mentorship, his own projects shallow. Year two he finally figured one thing out: **the lead's job is turning the newcomer's project into the newcomer's project**, not taking the newcomer's project over and doing it yourself. Easy to say, hard to do — it violates 5 years of engineer's muscle memory.

The hidden judgment in path two: are you willing to accept "I'm no longer the most-knowledgeable in the project." An IC FDE at the customer is always the deepest technically; an FDE lead's group will have newcomers who outpace you on some specific feature. Your value no longer comes from "I know more"; it comes from "I help the newcomer become the one who knows more." If the joy of engineering for you mainly comes from "I know more than others," path two will feel uncomfortable.

**Three: switch to vendor side** — from "delivering at the customer" to "building product at the AI platform company." Anthropic, OpenAI, the Bedrock team all hire "former-FDE PMs / SEs." Reason is direct: an FDE who's stepped into 5 customers' holes knows which features have real users and which docs get read. Bob McGrew, in his YC interview, mentioned that Palantir FDEs flowing into early OpenAI product teams is a relatively mature path — someone who has done customer landings can see "what's deployable" 2 years faster than a pure product background.

I haven't walked path three myself, but people I know who have share one common feeling: vendor-side satisfaction is different from FDE satisfaction. FDE is "this month I'll close out this customer's thing" — done, you see them launch, use it, like it. Vendor PM is "this feature, six months out, will be used by thousands of FDEs" — done, you don't necessarily see which specific customer succeeded because of it. The former is immediate feedback, the latter delayed. Neither is good or bad; you have to choose. The vendor-side path requires tolerance for that delay.

Path three has a hidden cost: you lose real contact with customer sites. After two years on the vendor side, your sense of "how customers actually work" starts going abstract — not because you forgot, but because customers are also changing and you aren't there. The dozens of product updates AWS posts to What's New each month are feedback FDEs stepped through one customer at a time; if you switch to vendor side and want to keep judgment sharp, proactively find chances back on site — even just two days riding along with an FDE, listening through one full Discovery interview, is more useful than 50 PRD reviews in the office.

There is no "right" path among the three. I'm currently doing a hybrid of one and two (still doing projects while mentoring 2 newcomers), but that choice is because I haven't tired of customer sites. The day I start to gag at "doing another Discovery interview," I'll switch to two; the day I start thinking "this feature should live in Bedrock, not be hand-written by me," I'll consider three. **The judgment criterion for career direction isn't which path is more advanced; it's whether you can still tolerate the thing you most hate doing right now, five years out.**

There's also a path I didn't list separately but worth mentioning: **go back to being a pure-engineering IC** — i.e., stop doing FDE, return to a SaaS company or big-tech product engineering team, write code, do tech, no longer face customers. This isn't uncommon among FDEs, especially after 3-4 years when "I don't enjoy dealing with people" hits. Nothing wrong with it — FDE isn't the "advanced form" of the engineer; it's "another form." If after 5 projects the happiest two hours of your week are with Slack closed writing code, you probably aren't long-term suited to FDE. Lawrence in *FDE Rule Book* puts it bluntly: "Not everyone should be an FDE, and that's a feature, not a bug." — the scarcity of this profession comes precisely from the fact that not all engineers fit it.

---

## 17.3 The Real Step-Down From FDE to FDE Manager

Path two (lead to manager) is the path most FDEs take, and the one with the biggest step-down. This section unpacks it.

The first step-down is **time allocation shifting from "project time" to "non-project time."** An IC FDE spends 80% of the week on a specific project: code, traces, customer meetings, eval. A manager spends 80% on "management actions": 1:1s, post-mortems, customer assignment, people evaluation, upward reporting. Year one the biggest pain for managers is "this week I produced no code." It's not that there's no output; the form has changed from commits to "5 FDEs' 5 projects all moving forward on time." That output adds up at year-end, but not on a Tuesday afternoon.

The second step-down is **the object of judgment shifting from "customers" to "the FDEs themselves."** An IC FDE judges "what should this customer do" — Discovery thoroughness, tech selection, handoff readiness. A manager judges "which FDE fits which customer" — A fits manufacturing not finance; B is strong in Discovery but tends to drag in Handoff; C is a newcomer who can't be thrown at the customer with the most senior decision-makers. **This judgment doesn't require engineering experience; it requires reading people.** A strong-engineering FDE who can't read people, transitioning to manager, will repeat the same mistake for two years — assigning projects to "the strongest FDE technically" rather than "the FDE most fit for that customer."

The third step-down is **you can't be the firefighter anymore.** An IC FDE seeing a project about to crash thinks "I'll go help" — write prompt, sit in customer meetings, fix IaC. A manager seeing the same situation should think first "which FDE can support, do I rotate someone."

The moment a manager rushes onto the field, the other 4 projects have no one minding them. This is the most counter-instinctive thing for an engineer — there's a problem you could solve in front of you, and your job is not to solve it. The first time you hold yourself back is the real entrance exam for the manager track. People who transitioned well all said the same: their first holding-back evening they sat in the office until 10, knowing they could fix it in 3 hours but the newcomer would take 3 days — and they didn't rush in. From that night on they were truly managers.

The fourth step-down is **judgment feedback cycles get longer.** An IC FDE's judgment (does this prompt change move accuracy) usually has feedback in 1-2 hours — run an eval and you know. A manager's judgment (assign A to the finance customer, keep B in manufacturing) has a feedback cycle of 3-6 months — you wait for the project to play out before you know the assignment was right. This cycle makes the first year hardest — you've made 10 calls, and by September you can't tell which were right. Engineers used to instant feedback can easily slip into self-doubt in this cycle. The manager path requires accepting in advance that "the judgments I make today won't be evaluable for half a year."

In the final month before Hesheng's contract ended, the firm started talking with me about "leading a 3-person group next year." I almost said yes; I declined. The reason wasn't "I don't want to lead people" — I realized I had something unfinished at the IC stage: industry depth was still between Level 1 and Level 2. If I switched to manager now, my future newcomers would do manufacturing projects; my own industry judgment wasn't at Level 3, so my project assignments would be off. **It isn't that you can't switch; the timing should be set by your capability curve, not by when the company offers.** I don't talk about this often; writing it here as a reference for FDEs facing the same call.

The FDEs I've watched transition most smoothly all share one move: **they "deliberately mentor a newcomer" in the last six months of their IC stage.** Not passive mentorship — actively pair an entire project end to end, Discovery to Handoff, with the newcomer driving and themselves only stepping in when blocked. After half a year they're acclimated to "things could be faster, but I don't take over." Manager year one's pain halves.

If you're an IC FDE considering manager next year — don't wait for the offer to start practicing. Start mentoring a newcomer next project, give yourself a low-cost rehearsal. If after six months "watching someone go slow" is unbearable, you're probably not for it. If "watching the newcomer grow" feels better than writing a great prompt yourself, you'll likely enjoy this path.

---

## 17.4 The 3 Levels of Industry Depth (How Hesheng Took Me from Level 1 to Level 2)

Career forks done; back to capability itself. Last section said "industry depth determines what you look like in 5 years" — this section unpacks what industry depth looks like.

I observe industry depth as three levels:

```
        Level 1: Understand the jargon
        ──────────────────────────────
  Conduct conversations inside the customer with no jargon barrier
  Example (manufacturing overseas service): "dispatch / parts / ticket / SLA"
  Time to invest: 3-6 months, mostly by hanging around customer sites

        Level 2: See the business flow
        ──────────────────────────────
  Draw the customer's main business flow, know who owns each step
  and where the typical bottlenecks are
  Predict which links are LLM-risky, which low-risk
  Example: "don't fully automate dispatch on day 1, start with 5%
            high-frequency low-risk cases"
  Time to invest: 1-2 years, usually after 2-3 same-industry projects

        Level 3: Have judgment
        ──────────────────────────────
  Tell the customer "don't do this" and offer angles they haven't seen
  Speak industry trends in front of customer leadership; the customer
  starts treating you as "one of us"
  Time to invest: 3-5 years, 5+ projects in the same industry
```

After Hesheng I'm between Level 1 and Level 2. Level 1 I have — overseas service's "dispatch / parts / SLA / cross-site coordination" terms I can hold in conference room conversations directly without Chen Xue translating. But Level 2 I'm halfway: I can draw Hesheng's one customer's business flow clearly, but I haven't seen the commonalities of "manufacturing overseas service" as an industry. To see the commonalities takes 1-2 more same-industry customers.

Level 3 is the qualitative shift. A Level 3 FDE isn't "doing projects" — they're "the customer's industry consultant." Customer leadership invites them out to dinner not to discuss the project, but to hear them talk industry trends. FDEs at this level don't find customers via their resume; customers find them. I've seen one with 6 years of insurance — half their projects each year are old customers proactively coming back for "we want to do the next phase," the other half are referrals: "this peer mentioned you." **That state isn't because his technique is strong; it's because he's accumulated the reputation of "this person understands insurance" inside the industry — and reputation can't be substituted by technical capability.

How to deepen from Level 1 to Level 2? At Hesheng over the year, the things I did that worked, in retrospect: read one piece of public material on Hesheng's industry each month (industry association reports, public-company annual reports, similar overseas firms' financials); have regular meals with Chen Xue, the business "old hand," and listen to her describe how manufacturing overseas service evolved over the past 10 years; in every project post-mortem reserve a section called "what new industry understanding did I gain this time." Each move alone looks small; the year accumulated, I could speak "three future trends in Southeast Asian manufacturing overseas service" at a Singapore customer's board — Zhou Mingyuan said afterwards "your section was clearer than our own BD." That moment I knew I had the beginning of an industry sense.

Nabeel Qureshi in *Reflections on Palantir* is precise on this: Palantir FDEs with 5+ years find their value isn't technical — it's "the customer shows them numbers their own board doesn't see" — i.e., the customer treats them as "one of us." That state isn't bought by selling tech; it's earned by year-on-year demonstration of "I understand your industry, your situation, your difficulties." Conikeec's *FDE Playbook* has a similar formulation: "earn the right to disagree" — you have to first prove inside the customer that you understand the industry before they'll listen to "don't do this." Both lines look abstract; after 5 projects they're concrete: customers start showing you what they used to hide, and you've reached the doorway of Level 3.

If you're 0-12 months in, do you need to "lock in" an industry now? My take: don't rush. On project 1 you probably don't yet know whether you like the industry. **Take 2 different-industry projects in parallel in year 1**, then compare which one made you want to read more of its material, talk more with its business side — the one you "actively want to know more about" is the direction worth depth. If neither industry gets you to actively want more, wait another year. **Industry choice isn't a week-1-of-employment decision; it's a year-2 decision.**

Industry depth has a hidden bonus: it immunizes you against "AI-tool replacement anxiety."

In 2025-2026 the FDE community has people anxious — Cursor / Copilot / Claude Code each generation is stronger; will FDE be replaced? My take is the opposite: general engineering capabilities (writing code, calling APIs, building scaffolding) are indeed being compressed by AI tools, but **"customers' distrust of LLMs" and "industry's dirty data / compliance boundaries"** — those AI tools cannot replace. The former requires half a year on the customer side to earn trust; the latter requires 5 years of industry experience to develop judgment.

A Level 3 finance FDE won't be replaced by AI tools because what they sell isn't "I can write code" — it's "judgment in finance." A pure-engineering FDE will worry — because what they do AI tools really do increasingly well. The countermeasure isn't "anxious, learn the new tool"; it's "pick an industry early, deepen early." However strong AI tools become, "customer leadership invites you to dinner to hear industry trends" — that they can't do.

---

## 17.5 What a Week Looks Like 5+ Projects In

The third 5 years I haven't walked, can't write. But what a week looks like for a 5+-project FDE I can sketch from my current state — gives a 0-12 month you a concrete shape for "future me three years out."

After Hesheng my week looks like this:

```
        Current (5+ project FDE) week composition
        ─────────────────────────────────────

  - Main project (newly signed customer, in Discovery):    50%
       Customer interviews / desk-shadowing / eval-v0
  - Old customer on-call (Hesheng 8-week warranty):        10%
       Slack Q&A + one phone Q&A + one small change
  - Internal mentor (1 newcomer FDE):                      15%
       1:1, post-mortem, review their Discovery report
  - Pattern extraction + internal wiki:                    10%
       Refining the prior project's outputs into reusable templates
  - External community + industry sense:                   10%
       Read industry material, occasionally write a blog post, peer chat
  - Self-learning (new LLMs / new AWS features):            5%
       Not for the project — to know what next-gen FDEs should know
```

This proportion is completely different from year one. In year one I was 90% on the main project, 10% catching up on basics. **5+ projects in, main project time drops to 50%** — not because I've devalued the project, but because "old customer + newcomer + pattern extraction" three things squeeze in. None of these existed in year one, but each has become "non-negotiable" by 5+.

Old-customer on-call's 10% looks small, but its "mind share" is bigger than the time share. A P2 alert from an old customer in Slack can cut into Discovery's continuous thinking on the main project. So that 10%'s real feel is "main project gets interrupted now and then." What I learned: concentrate on-call response into two windows daily (10-11 AM and 4-5 PM), not Slack-watching outside that — except P1. Not perfect, but better than constant interruption.

Newcomer mentorship's 15% has the most non-linear return — first three months you can't see the gain (the newcomer is still learning); month 6 onwards you can feel your own judgment "ruminated" through their questions. The newcomer asks "why must Discovery include shadowing"; you're forced to explain it cleanly — and you understand it deeper too. Mentoring isn't one-way output; it's two-way polishing. Conikeec in *FDE Playbook* writes about this — his line: "the FDE who mentors learns more than the FDE who is mentored." Before Hesheng I didn't quite believe it; after I do.

If you're 0-12 months and looking at this distribution, the right reaction is "oh, three years out I'll look like this" — not "I have to do this now." Year one still keep main project at 90%; that's your foundation-building window. **Three years out look back at this distribution, if your work is still 90% on a single main project, you probably haven't done Ch16's pattern extraction** — the 30% "non-main project time" has gone missing.

---

## 17.6 Five Things This Book Doesn't Cover

This is the book's last chapter, and the right place to discuss its limitations.

**One, the book barely covers multimodal.** The projects I've personally done are mostly text (Hesheng phases one and two were both text-only); the methodology in this book — Discovery, eval sets, agent orchestration, Handoff — is from text scenarios. If your project is primarily image / video / audio (medical imaging, industrial QA, content moderation), the engineering mindset here still applies, but the specific tech-selection portions (Ch6/7/8) need a different stack. How to label multimodal eval sets, orchestrate agents, do canary releases — that's another book.

**Two, the book's customers are mid-sized enterprises.** Hesheng is a synthetic case, but the customer profile it represents — annual revenue from hundreds of millions to a few billion, 50-200 IT staff, has its own AWS account but no dedicated AI team — is the majority among projects I've worked on. The Ch9-Ch13 stack (data / network / identity / audit / deployment) defaults to "customer has IT but no specialized ML/AI team." If your customer is a big firm (with their own AI infra team, doing model serving in-house, requiring open-source + private deployment) or a small one (5-person startup, no IT at all), the engineering moves here need significant adjustment.

**Three, the book barely goes deep on compliance details.** Compliance I touched on briefly in Ch10 around identity and audit, but didn't unpack GDPR, MLPS, HIPAA, SOC2, or other concrete frameworks. The reason is compliance details change quickly by region and industry — Singapore's PDPA differences from EU GDPR, how HIPAA actually lands for an LLM application in healthcare, China MLPS 2.0 Level 3's new interpretations for generative AI — each needs its own chapter, and rewrites every six months.

If your customer is in a compliance-heavy industry (finance/healthcare/government), this book is the baseline, not the endpoint. **The best way to learn this layer is to sit down with your customer's legal / risk department for an afternoon** — far more effective than reading 100 pages of regulation. AWS itself periodically posts compliance-related capabilities on What's New (e.g., Bedrock Guardrails, CloudTrail Lake's compliance audit scenarios) — those public materials are starting points for compliance, but always only starting points.

**Four, the book uses AWS as a demo platform.** All hands-on portions in this book illustrate with Bedrock + AgentCore + IAM, but the FDE work core mindset isn't tied to AWS — Discovery, eval sets, handoff, pattern extraction hold across any cloud and any LLM platform.

If you're FDE-ing on Azure or GCP, swap Bedrock for Azure OpenAI or Vertex AI, swap IAM for Entra ID or GCP IAM — the judgment logic in the text doesn't change. AWS appears in this book because it was Hesheng's cloud — not because AWS is the optimal choice for FDEs. There's no "AWS beats X" comparison anywhere here, because the book's purpose is to teach FDE workflow, not to do platform selection. Platform selection is something the FDE does on customer site, referencing the customer's existing cloud stack, compliance requirements, commercial relationships — none of which is in this book.

**Five, the book is written on the 2025-2026 tech stack.** This is the most important point and the easiest to miss. The specific tech in this book — Bedrock Agent, AgentCore, stateful MCP, Claude 4.5 / 4.6 — is the early-2026 form of AWS's products. In three years those names and forms will all change. But **the shape of FDE work won't change** — whether customers will use LLMs, plug in agents, do RAG, those details will change; but customers' "the business side can't say what they want," "IT doesn't understand business," "no one maintains it 3 months after launch" — those are constants of corporate organization, persisting through three generations of AI tech. The chapters on tech stack will be rewritten in 5 years; the methodology chapters will mostly still hold.

After writing those five I considered: the limitations probably exceed five. There's another I hesitated on: **the book essentially covers FDE work under one cultural setting** — customers in China, Singapore, or Southeast Asian mid-sized firms, meetings in Chinese with occasional English, decision style consensus-leaning. If your customer is in the US/EU (decisions more direct, "no" said more cleanly than here), or in Japan (decision cycles much longer, requires layered nemawashi), the Discovery durations, handoff cadences, and customer dialogue styles in this book all need substantial localization. I don't have the confidence to write this well; left to future FDE peers from more varied cultural backgrounds to fill in.

---

## 17.7 To the You Reading This Now

This section was originally going to be "N pieces of advice for entry-level FDEs"; I deleted halfway through — list-style advice has no use after reading; it just looks useful.

Compressing it to a paragraph.

If you're a 0-12 month FDE, every methodology in the 16 chapters of this book is "method for doing work," not "method for being a person." The "method for being a person" in FDE work I can't write down, but I can tell you one thing: your biggest output in your first 5 projects isn't the code given to the customer; it's the notebook for yourself. **Write down "what did I learn this time" at the end of every project** — not for the company wiki, not for the boss, for the you three years from now. Three years from now you'll reread and know what kind of FDE you became, more accurately than any resume.

Over the year at Hesheng I wrote 200+ such entries. The 16 chapters of this book are reworked from those entries. Every judgment, every anti-pattern, every "I've stepped in this hole before" you read here comes from those notes. **This book itself is a pattern-extraction product** — only the object is my own 5 years of projects, not one customer.

If you can keep writing notes for 5 years, you'll have your own book by then. The judgments in it will differ from mine — they should, because the projects you did and I did differ; the customers, the industries, the LLMs of the time, all differ.

But the writing style should be the same: first person, coherent narrative, specific to customer names and decision points, no empty pep talk, no "I should do thus and such" — only "this time I did this, got that right, got that wrong, what to do next time." The core of this writing isn't literary technique; it's honesty toward yourself and your readers — every sentence corresponds to something you actually did, a hole you stepped in, a judgment you revised.

I started writing notes in year one; most of what I wrote then is embarrassing on rereading — many judgments written too absolutely, many observations later proven wrong. But **those embarrassing notes are the root of my current judgment.** If I hadn't written them down, in years two and three I would have had nothing to negate — people can't negate things in their head with no concrete shape. Putting a judgment to paper is the prerequisite for it to be revised later.

After this book, I plan to write a second. Its title: "FDE Conversations With Customer Leadership" — this book covers engineering moves; that one wants to cover how to talk with the customer's CEO, with their compliance, with their business owners. That's something I learned at Hesheng over the year that wouldn't fit into these 17 chapters — it's an independent topic. If three years from now you write your book, you'll find FDE has at least five topics each worth a book of their own: technique, conversation, compliance, commercials, team. This book covers the first.

After writing the year of Hesheng, when I open the book's table of contents again, it feels like a snapshot of "my own FDE workflow" — some judgments in the snapshot I'll disagree with myself in three years; some anti-patterns will have crisper formulations; some chapters in five years I'll delete and rewrite. That's the state I hope for. A 2026 FDE book unchanged in 2030 isn't well-written; it means the field stalled. I hope when you reread this book three years from now, you can margin-note "this paragraph is outdated" — that's how this book completes its mission.

By then this book can be tossed.

Every judgment I made over the year, every anti-pattern I wrote, every hole I stepped in — I hope they get superseded, rewritten, negated in your book five years from now.

---

## Public references cited in this chapter

- A. Lawrence, *Forward Deployed Engineer Rule Book* (2025) — borrowed framing of Principal FDE's "see the hole 4 weeks early"
- Conikeec, *The FDE Playbook: A Practitioner's Field Manual* (2025, Substack) — pattern extraction and the third-project inflection
- Bob McGrew @ Y Combinator (2025) — interview on FDEs moving to vendor side
- Nabeel Qureshi, *Reflections on Palantir* — origin of Palantir FDE culture's "industry sense"
- AWS What's New (2026) — Bedrock / AgentCore / cross-region inference profile and other public release materials matching the book's tech stack

Full bibliography and links in the *References* section at the end of the book.

[← Previous: Project Handoff](../chapter-16/) · [Back to Contents](../../README/)
