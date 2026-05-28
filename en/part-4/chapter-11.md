---
title: "Chapter 11 — VPC, SSO, Compliance"
parent: "Part IV — Engineering for the Real Customer Environment"
nav_order: 3
---

# Chapter 11: Integrating with Legacy Systems — SSO / SCIM / API / Audit

Hesheng Precision Heavy Industries, Thursday afternoon of week 8.

The ticket Agent had been running in staging for three weeks. Chen Xue and two senior masters had run more than 60 real tickets through it; triage accuracy held at 94%. Zhou Mingyuan had made the call: "Get ready to launch before the November-end board meeting." I was just about to exhale. At 3 p.m. that afternoon, Gu Jianguo called me into the IT director's office. On his desk was an A4 printout — Hesheng's "Application Launch Security Admission Checklist," four questions:

```
  Q1  Does this Agent's user login go through our AD or your own accounts?
  Q2  When an employee leaves, can the Agent's access be auto-revoked within 24 hours?
  Q3  Who defines the Agent's permission boundary when it calls ERP / CRM? Who can change it?
  Q4  In the event of an incident, can audit logs trace down to who, when, what was called?
```

Of those four questions, I could only answer Q1 confidently in the moment. Q2 I had a plan in my head but had never wired SCIM. Q3 — we were using a single service account to call ERP from inside the Agent; "permission boundaries" weren't modeled at the Agent layer at all. Q4 — CloudTrail was on, but Bedrock prompt/response weren't being persisted.

That night I wrote those 4 questions on a whiteboard, and one realization landed — **this isn't "patch it before launch." It's 4 different things, and each one needs to start 3-4 weeks early**. My judgment error was in the Discovery phase, where I hadn't put "security admission" on the agenda. This is a mistake older FDEs make repeatedly: treating compliance as a checklist, only discovering at the last week before launch that it's a separate engineering track.

This chapter is the "start 4 weeks early" checklist. Four sections cover identity (SSO), lifecycle (SCIM), permission boundaries (API integration), audit and real-time guardrails. The last section walks through Hesheng's actual setup end to end.

---

## 11.1 Drawing the 4 Things on One Diagram

```
        Identity (Authentication) — "who are you?"
              ↓ SSO: SAML / OIDC / Kerberos
        ────────────────────────────────────────
        Lifecycle (Provisioning) — "who syncs joiners and leavers?"
              ↓ SCIM
        ────────────────────────────────────────
        Authorization — "what can you do?"
              ↓ IAM Role / RBAC / ABAC + Tag
        ────────────────────────────────────────
        Audit — "if something happens, can it be traced?"
              ↓ CloudTrail + Bedrock Logging + application logs
```

Four things, interlocked. Skip one and the enterprise launch doesn't pass. This isn't textbook talk — Gu Jianguo's checklist had exactly four questions mapping one-for-one to those layers. The next day I showed him the diagram and he pointed at it: "Right, these four. Skip one and our IT committee won't sign off."

> Lawrence in *FDE Rule Book* has the line "Identity is the new perimeter." Early on I thought it was marketing-flavored; after a few projects I understood — the customer's CISO never opens a meeting asking "how accurate is the model"; they ask "who originated this call, and can it be traced." All four things in this chapter are answers to that question.

---

## 11.2 SSO: Plug Into the Customer's IdP, Don't Build Your Own Accounts

Hesheng uses Okta as the corporate IdP, with AD providing internal-network authentication behind it; service engineers across all five overseas sites use the same Okta accounts. Gu Jianguo's hard requirement was: **don't make our people open a new account for your Agent**.

Reasonable. In every project I've been on, when an FDE in week 1 takes the shortcut of "username + password now, wire SSO later," week 8 always brings a major rewrite. The reason isn't technical — it's the cost of retraining users. The moment you ask users to remember a new password, the Agent is branded as "another external system," one step from being abandoned.

Protocol layer didn't take long:

- **OIDC**: built on OAuth 2.0, JWT format, the default for new projects. Okta supports it natively.
- **SAML 2.0**: universal across older IdPs (AD FS / OneLogin / older Okta), XML-based, complex but solid. If the customer is on SAML, don't push them to OIDC — risk doesn't justify the value.
- **Kerberos / LDAP**: the former is a Windows AD intranet protocol; the latter isn't SSO at all, it's directory lookup. Customers often conflate them with SSO; you have to disambiguate.

Hesheng went with OIDC because Okta defaults to OIDC, and I didn't need to switch protocols just to "look professional."

A full sign-in flow:

```
  1. Engineer opens "Hesheng Service Assistant", no session
  2. App redirects to Okta; Okta authenticates (password + Verify push)
  3. Okta returns ID token + Access token
  4. Gateway parses JWT: sub / email / groups
  5. Gateway passes the token through to the back-end Agent
  6. Agent uses groups for RBAC: which tickets this engineer can read
```

Steps 5-6 are where this section is actually valuable — **the JWT must propagate all the way to the Agent's interior; it must NOT be stripped at the gateway and replaced by a service account**. This is the prerequisite for whether 11.4's audit can trace down to a specific person.

Hesheng's AWS account already has IAM Identity Center (formerly SSO) wired to Okta. Gu Jianguo set this up last year, which I could plug right into. What we did was short:

```
  1. Created a Permission Set "BedrockAgentUser" in Identity Center
       - Allows invoke_agent only on our agent ID
       - No permission to modify Agent config, no permission to call other models
       - Condition added: only from Hesheng's enterprise network range

  2. Bound the Permission Set to the Okta group "okta-group-svc-engineer"

  3. After the engineer signs in, Identity Center issues short-lived
     credentials via STS AssumeRoleWithSAML (1h expiry)

  4. App calls invoke_agent with sessionAttributes:
     {user_id, group, region}
```

Step 4's `sessionAttributes` is a native Bedrock Agent field that gets persisted in the invocation log — that's the data source for "who initiated this" in the audit layer. I missed this the first time I wired this up; it was Q4 that forced it out.

If the customer is on Azure AD: same as Identity Center, SAML/SCIM, slightly more complex configuration but the same path. If it's pure AD with no IdP: use AD Connector or AWS Managed AD, and have Identity Center treat AD as the directory source. If the customer has no IdP at all — flip the question and ask "why is this Agent being delivered to a customer with no IdP" — usually that means compliance requirements are very low, which is a different problem.

---

## 11.3 SCIM: Departing Employees Must Be Invalidated Within 24 Hours

Q2's hard target is "within 24 hours." Hesheng is a manufacturer, engineer churn isn't high, but across 5 overseas sites a few transitions happen each year. Their HR system is Workday; offboarding flows Workday → Okta → all downstream apps — they call it "unified deprovisioning."

If the Agent isn't on SCIM, after Workday updates and Okta disables the user, **but the user's existing session in our App can still call the Agent until the token expires** — which can stretch past 24 hours. SCIM closes that gap.

Strip the protocol spec and SCIM is a set of REST + JSON:

```
  POST    /scim/v2/Users         create
  PATCH   /scim/v2/Users/:id     modify (group change, disable)
  DELETE  /scim/v2/Users/:id     delete
  GET     /scim/v2/Users/:id     read
```

Okta pushes changes to downstream apps via this interface in the same second a user is disabled.

I don't recommend writing SCIM endpoints from scratch. The protocol spec isn't complicated but it's verbose — schema validation, attribute mapping, bulk operations, JSON Path syntax for PATCH — you can stand it up in two weeks, then need another two weeks to hit interop across IdPs. The customer upgrades Okta, you redo the compatibility work.

For Hesheng's first phase we used the SCIM endpoint built into IAM Identity Center. Identity Center is already on Okta SCIM; we just needed our App's internal user state to treat Identity Center as single source of truth:

```
  Workday → Okta →(SCIM)→ Identity Center
                                ↓
                         App-internal user table
                       (synced from Identity Center)
                                ↓
                         Engineer's session
```

The last sync hop uses a simple strategy: every `invoke_agent` call, the App gateway hits Identity Center to check if the user is still active, with 60s local cache. The engineer barely notices the difference; the worst-case offboarding latency is 60s — far better than 24 hours.

If the customer's IdP doesn't connect to Identity Center (e.g., a self-hosted OIDC), there are several SCIM gateway products available (Okta SCIM Gateway, SCIMer); paying to save time is a reasonable call.

Before launch I force one end-to-end test: create user in Workday → wait for Okta sync → user signs in and calls Agent ✓ → mark user terminated in Workday → call Agent again within 60 seconds → expect 401. The artifact is a screenshot + timestamp, **handed directly to the customer's security audit**. That's how I answered Q2 later on.

---

## 11.4 API Integration: User Context Must Propagate to ERP

Q3 is harder than the first two. It's not a protocol question — it's an **architectural choice**.

Hesheng's ticket Agent has to call three legacy systems: ERP (SAP, SOAP), CRM (Salesforce, REST), MES (in-house HTTP+XML). My initial approach was a service account — the Agent internally uses one fixed SAP user `bedrock-agent-svc` to call ERP, and what customer data it can read is controlled by the Agent's code logic. This **looks clean at the Agent layer**, but Gu Jianguo asked "who defines the permission boundary" — what he wanted wasn't "Agent code controls it"; what he wanted was **the permission boundary is controlled by IAM/AD, and changes to Agent code can't bypass it**.

The difference between these two decides life and death in audit scenarios. If the Agent uses a service account to call ERP, when an auditor asks "why can Zhang San see Wang Wu's tickets," your only answer is "our code is written that way" — the customer's security lead will see this as you handing him an infinitely-explainable space. If the Agent propagates Zhang San's identity into ERP and ERP itself denies it, the auditor goes straight to the ERP access log — **the responsibility boundary is clean**.

Hesheng's final architecture for this phase:

```
        Bedrock Agent (calling tool)
              ↓ function call (with user JWT)
        Lambda Adapter
              ↓ STS AssumeRole + on-behalf-of
              ↓ translate to SOAP/XML/REST
        SAP / Salesforce / MES
              ↓ each system's RBAC decides what's readable
        Adapter de-identifies → returns to Agent
```

The Adapter layer's responsibilities are all engineering-meaningful:

- **Protocol translation**: SAP's SOAP envelope shouldn't be visible to the Agent. The Agent sees JSON, always.
- **Identity propagation**: take user_id from the JWT and exchange it for the corresponding SAP user token (Hesheng uses SAP Principal Propagation). Salesforce uses OAuth on-behalf-of.
- **Failure fallback**: legacy systems going down can't drag down the Agent. Each Adapter has timeout (5s in the contract) + circuit breaker (open for 60s after 10 consecutive failures) + degraded return.
- **dry-run mode**: pre-launch demos must never write real data. Adapter defaults to dry-run; write operations return a simulated success. In week 8 Chen Xue accidentally clicked "dispatch" during a demo — because of dry-run, no real dispatch happened.

Four principles I uphold on every project, all reflections from real holes I've fallen into: **call read APIs first** (write APIs must have a written sign-off from the customer's business side before launch); **always idempotency keys** (Agents will retry; legacy systems aren't necessarily idempotent); **always timeouts + circuit breakers** (Hesheng's SAP occasionally stalls for 30s; without a breaker it would drag the whole Agent down); **always dry-run** (the final pre-launch rehearsal defaults to dry-run; the business side clicks every button themselves before going live).

---

## 11.5 Audit: Five Specific Questions, 5-Minute Answers

Q4 was the one I felt least solid on that day. I'd flipped Bedrock's invocation logging on, but what the customer's security lead wanted wasn't "the toggle is ON" — he wanted these 5 questions answerable in 5 minutes:

```
  Q-A  Who did what?           → user_id + action + resource
  Q-B  When?                   → timestamp (UTC, microsec)
  Q-C  From where?             → IP + User-Agent + session_id
  Q-D  What was the result?    → success / failure + summary
  Q-E  What entitled them to do it at the time?  → role / policy snapshot
```

Q-E is the easy one to forget — what the auditor needs to see is the user's permissions at the moment of the incident, not today's permissions. So **permission changes themselves must also be audited**.

Hesheng landed three layers of logs, each with a distinct role:

```
  Application logs (App writes)  → CloudWatch → S3 (archived after 1 wk)
                                  → Athena queries by trace_id / user_id / time
                                    Answers Q-A / Q-B / Q-C

  CloudTrail (AWS writes)        → S3 (Object Lock + KMS, 7 yrs)
                                  → Security Hub alerts
                                    Answers Q-E (IAM role + policy snapshot)

  Bedrock Invocation Log         → CloudWatch + S3 (full prompt + response)
                                    Answers the "what did the model say" portion of Q-D
```

Hesheng is B2B manufacturing, but they have to comply with **China MLPS Level 3** — audit logs must be **tamper-proof**. Under S3 Object Lock in Compliance mode, even the root account can't delete objects within retention; combined with KMS encryption (CMK held by Gu Jianguo, not by our team), the resulting picture is: our FDE team **writes** audit logs but **can't delete them**, Hesheng IT holds the keys but **can't modify** logs that have been written, customer auditors have read access. This separation of powers is what "audit trustworthiness" actually means on Gu Jianguo's checklist.

Cross-border data also gets cut here. Hesheng's business covers Southeast Asia, and tickets contain contact details for customers in Vietnam, Indonesia, and Malaysia. Several Southeast Asian countries have data localization (Indonesia PP 71/2019, Vietnam Cybersecurity Law); Gu Jianguo and I had already aligned in Chapter 9 — **customer data does not leave ap-southeast-1**. Implementation: Bedrock goes through ap-southeast-1's VPC endpoint; the S3 buckets for app logs and Bedrock Logging are in ap-southeast-1, and the bucket policy denies cross-region GetObject; CloudTrail is multi-region but the landing bucket is in ap-southeast-1. Cross-region inference profile (used by 4.6/4.7) is a hidden trap — it processes prompts cross-region in us-east-1. We confirmed with Gu Jianguo: Hesheng's first phase only uses the 4.5 family (no cross-region), 4.6/4.7 will be evaluated in the next phase.

I recommend cutting this cross-border line in week 2 of every FDE project with the customer's legal + security leads — don't drag it to the launch week.

---

## 11.6 Guardrails: Real-Time Constraints on the Agent Itself

People audit the Agent; the Agent's own output also needs real-time auditing — that's the layer LLMs added. Bedrock Guardrails is exactly this. Of the 5 categories, Hesheng's first phase enabled 4:

- **PII filter**: ID numbers / bank cards / phone numbers auto-redacted. The contract clause "PII must not enter call logs" is backed by this.
- **Content filter**: harmful / violent / hateful / sexual content. Industrial scenarios rarely trigger it, but it's on as a baseline.
- **Word filter**: Hesheng has a few internal product code names that must never appear in customer-visible replies.
- **Contextual grounding**: answers must be based on the KB — required for any RAG application. The "fault cause" and "spare-part model" the Hesheng ticket Agent gives engineers translate into actions on site; if the Agent fabricates a part model that doesn't exist and the engineer can't find it in the warehouse, that's a direct field incident.

In week 2 after launch, Guardrails fired 11 times: 9 were PII false positives (a serial number "SN20250912" in a ticket got tagged as an ID number), and 2 were genuine PII leaks (an engineer pasted a screenshot containing an ID card while forwarding a ticket on Slack). For the false positives we tuned the regex allow-list; for the real leaks we wrote them up in the monthly security report — the customer's security lead proactively sent Zhou Mingyuan a "+1" that month.

---

## 11.7 Stitching 11.2-11.6 Together: Hesheng's Phase Security Architecture

Friday of week 8, the four-thing plan as one diagram for Gu Jianguo:

```
Identity:
  Engineer → Okta (OIDC + Verify) → Identity Center
        → Permission Set: BedrockAgentUser → STS short-lived credentials (1h)

Lifecycle:
  Workday termination → Okta SCIM → Identity Center disable
        → App gateway rejects this user's invoke within 60s

Permission boundary:
  Agent invoke (with user JWT)
        → Lambda Adapter (protocol translation + identity propagation)
        → SAP / Salesforce / MES (each with its own RBAC)
        → de-identified return

Audit:
  App log (trace_id) → CloudWatch → S3 → Athena
  CloudTrail            → S3 (Object Lock + KMS, 7 yrs)
  Bedrock Logging       → CloudWatch + S3
  Cross-border constraint: all data stays in ap-southeast-1

Agent itself:
  Guardrails: PII + Content + Word + Grounding
```

Gu Jianguo nodded after reading: "This will pass our IT committee meeting in early November." Chen Xue confirmed the business flow doesn't change (engineer still signs into Okta, opens the App, asks about a ticket). Zhou Mingyuan exhaled — he had been worried security admission would push the board demo back two weeks.

It actually slipped 1 week, because the SCIM end-to-end test caught a throttling issue in Identity Center (syncing 200+ users at once returned 429), and we needed three days to rework it as batched syncs. Compared to walking into the wall unprepared, 1 week is a good outcome.

---

## Wrapping Up

I couldn't answer 3 of the 4 questions that day not because I'd never touched the technologies, but because **I hadn't put "security admission" on the Discovery agenda**. This class of problem is an independent engineering track on the customer side; it needs 3-4 weeks of cross-department alignment — HR / legal / security / IT committee / business side all have to weigh in. If the FDE doesn't actively trigger this track in week 1, week 8 is going to crash into it. My habit now is to take 30 minutes in week 2 with the customer's security lead and walk through the current state of these 4 things: which IdP, SCIM connected or not, identity propagation on API calls or not, audit retention window. 30 minutes saves you several future redo cycles. If the security lead says "we have nobody who specifically owns this" — that's a red light, meaning either compliance has to be cut back this phase (hard) or the SOW has to explicitly add this workload. The next Part walks into the gap from PoC to production; "go-live" there means everything from this chapter is already done.

---

## Public references cited in this chapter

- A. Lawrence, *Forward Deployed Engineer Rule Book* — "Identity is the new perimeter" section
- AWS docs — *IAM Identity Center external IdP*, *Bedrock Agent identity context*
- AWS docs — *CloudTrail data events*, *Bedrock model invocation logging*, *S3 Object Lock*
- AWS docs — *Bedrock Guardrails* (5-category interception + contextual grounding)
- IETF RFC 7643 / 7644 — *SCIM Core Schema* and *SCIM Protocol*
- Okta docs — *SAML / OIDC / SCIM provisioning*
- China MLPS Level 3 public clauses (GB/T 22239-2019)
- Indonesia PP 71/2019, Vietnam Cybersecurity Law (public data localization compliance materials)

[← Previous: Scaffolding and the Development Loop](../chapter-10/) · [Next Part: PoC → Production →](../../part-5/intro/)
