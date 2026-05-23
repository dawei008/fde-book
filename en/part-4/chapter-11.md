---
title: "part-4/chapter-11.md"
nav_exclude: true
search_exclude: false
---

# Chapter 11: Integrating with Legacy Systems — SSO / SCIM / API / Audit

## Opening

```
An insurance customer. The FDE demos successfully in Week 8, gets ready to ship in Week 10.
The customer's IT director asks four questions; the FDE can't answer three of them on the spot:

  Q1: Does login go through our AD or through your own accounts?
  Q2: When an employee leaves, how does Agent access get revoked automatically?
  Q3: When the Agent calls our ERP API, who decides the permission boundary?
  Q4: If something goes wrong, can the audit log trace it to a specific call?

The FDE goes back, writes those four questions on the whiteboard, and realizes ——
SSO / SCIM / authorization / audit are 4 different things,
and none of them is something you can "patch in right before launch."

She replans:
  Week 11: SSO + SCIM
  Week 12: authorization boundaries + audit
  → Launch slips by 2 weeks

Her manager: "Should have done this 4 weeks earlier."
She says: "Now I know."

This chapter is the "do it 4 weeks earlier" checklist.
```

---

## 11.1 How the Four Things Relate

```
        Identity (Authentication)
           "Who are you?"
              ↓
        SSO (Single Sign-On)
        OAuth / SAML / OIDC
              ↓
        ──────────────────
              ↓
        Authorization
           "What can you do?"
              ↓
        RBAC / ABAC / Policy
              ↓
        ──────────────────
              ↓
        Lifecycle (Provisioning)
        "Who keeps user create/update/delete in sync?"
              ↓
        SCIM
              ↓
        ──────────────────
              ↓
        Audit
        "When something happens, who did it?"
              ↓
        Audit log + tamper-proof + queryable
```

The four interlock. Miss one and an enterprise launch will not pass review.

---

## 11.2 SSO — Plugging into Customer AD / Okta / Identity Center

### Protocol cheat-sheet

```
  SAML 2.0
    - The default for legacy enterprise IdPs (AD FS / Okta / OneLogin)
    - XML-based, complex but stable

  OIDC (OpenID Connect)
    - The identity layer on top of OAuth 2.0
    - JSON / JWT, modern-friendly
    - Recommended for new projects

  Kerberos
    - The internal protocol of Windows AD
    - Common on large-enterprise intranets in China

  LDAP
    - Not SSO; it's a directory query protocol
    - But many customers use it interleaved with the above
```

### Sample flow (OIDC)

```
        Typical OIDC login flow
        ────────────────────────────────────

  1. User visits your Agent
  2. Your app redirects to the customer IdP (AD / Okta)
  3. Customer IdP authenticates the user (password / SMS / Yubikey)
  4. IdP returns ID token + Access token
  5. Your app parses the token:
     - sub: user ID
     - email: email address
     - groups: department / role
  6. Use the token to call your backend / Agent
  7. The backend uses group / role for authorization
```

### AWS in practice: IAM Identity Center + Bedrock Agent

```
        Three IAM Identity Center integrations
        ──────────────────────────────────────

  Pattern 1: Customer brings their own IdP (Okta / Azure AD)
    - Sync users into Identity Center via SAML / SCIM
    - Identity Center assigns IAM roles to users

  Pattern 2: Customer uses AD (Active Directory)
    - AD Connector or AWS Managed AD
    - Users sign in to AWS with their AD account

  Pattern 3: Customer has no IdP (small org)
    - Identity Center's built-in user management (not recommended)
```

Minimum config:

```
1. Enable Identity Center (at the Organization level)

2. Connect the customer IdP:
   - Exchange SAML metadata
   - Attribute mapping (email, groups)

3. Auto-sync via SCIM:
   - Customer IdP create/update/delete → automatically synced to Identity Center

4. Permission Sets:
   - "BedrockAgentUser" → only invoke a specific Agent ID
   - "BedrockAgentAdmin" → can modify Agent configuration

5. Agent invocation:
   - User → your app → STS AssumeRoleWithSAML
     → temporary credentials → invoke_agent (with session_attributes)
```

> **AWS reference**: search "AWS IAM Identity Center external IdP" and "Bedrock Agent identity context."

---

## 11.3 SCIM — User Lifecycle Sync

### Why SCIM is needed

```
  Without SCIM:
    Employee leaves in the customer HR system
       → manual ticket to IT
       → IT manually deletes the account in 5 systems
       → your Agent is the 6th system, and it gets forgotten
       → the ex-employee can still use the Agent to call ERP

  With SCIM:
    HR system records the leave (Workday / SAP HCM)
       → IdP auto-syncs (Okta / Azure AD)
       → SCIM protocol → your system
       → your system disables the account in seconds
```

### The SCIM protocol

```
  At its core: REST API + JSON Schema

  Endpoints (you implement):
    POST /scim/v2/Users         (create user)
    PATCH /scim/v2/Users/:id    (update user)
    DELETE /scim/v2/Users/:id   (delete user)
    GET /scim/v2/Users/:id      (read user)

  Bidirectional sync:
    Push: IdP → your system (create / update / delete)
    Pull (optional): your system → IdP (reverse sync)
```

### FDE practical notes

```
  ✓ Prefer off-the-shelf
    - AWS IAM Identity Center ships a SCIM endpoint
    - Auth0 / Okta SCIM templates
    - Don't write an identity system from scratch

  ✓ Mandatory test cases
    - create → log in → change group → verify permissions changed
      → delete → verify cannot log in

  ✓ Log every SCIM call
    - Customer audit will ask "when was this employee disabled?"
```

---

## 11.4 API Integration — Calling the Customer's Legacy Systems

```
        Four "interface shapes" of legacy systems
        ─────────────────────────────────────────

  Shape 1: REST / OpenAPI (modern)
    - Call directly
    - Usually OAuth 2.0 / API Key auth

  Shape 2: SOAP / WSDL (traditional enterprise)
    - XML envelopes
    - Heaps of enterprise middleware
    - In Python: the zeep library

  Shape 3: Direct database access (anti-pattern but common)
    - Customer hands you a read-only Oracle / SQL Server account
    - High risk; avoid if you can

  Shape 4: File drops (oldest)
    - SFTP shared folders
    - CSV / XML on a schedule
    - Business-critical time windows
```

### Design pattern: how an Agent calls legacy systems

```
        Agent → Tool → Adapter → legacy system
        ──────────────────────────────────────

  Agent (Bedrock / LangGraph)
       ↓ (function call)
  Tool (Lambda / your code)
       ↓ (uses the SDK or a customer-provided client)
  Adapter (a thin translation layer)
       ↓
  Legacy system (SAP / Oracle / SOAP)

  Why an Adapter:
    - The legacy protocol does not leak into the Agent
    - Agent upgrades / legacy upgrades stay decoupled
    - One place for fallback / retry / circuit breaker
```

### Four engineering signals

```
  ✓ Always call a read API first
    - Write APIs need customer sign-off before they ship

  ✓ Always use an idempotency key
    - Retrying the same operation must not double-execute

  ✓ Always have timeout + circuit breaker
    - When the legacy system dies, it must not drag you down with it

  ✓ Always have a dry-run mode
    - Demos / tests must not actually write
```

---

## 11.5 Audit Logs — "Can You Prove It?"

```
        The 5 questions in a compliance audit
        ──────────────────────────────────────

  Q1: Who did what?
      → user_id + action + resource

  Q2: When?
      → timestamp (UTC, microseconds)

  Q3: From where?
      → IP + User-Agent + session_id

  Q4: With what result?
      → success / failure + summary of returned content

  Q5: Who was authorized to do this at the time?
      → role / policy snapshot at that moment
```

### Four engineering requirements for audit logs

```
  1. Immutable
     - WORM (Write Once Read Many) storage
     - S3 Object Lock / CloudTrail

  2. Correlatable
     - trace_id stitches together all related logs
     - From user action → API call → DB query → model call

  3. Queryable
     - "Stored" is not enough; you must be able to "query it back out"
     - Recommended: CloudWatch Logs + Athena queries

  4. Retention
     - Compliance typically demands 90 days / 1 year / 7 years (industry-dependent)
     - Don't forget archival (S3 Glacier)
```

### AWS in practice: CloudTrail + CloudWatch + Athena

```
        Typical audit architecture for an FDE project
        ─────────────────────────────────────────────

  Application → app logs (with trace_id)
                   ↓
  CloudWatch Logs (1 week → archive to S3)
                   ↓
  Athena (query by trace_id)

  AWS API → CloudTrail (every AWS API call)
                   ↓
  S3 (Object Lock + KMS encryption)
                   ↓
  Athena queries / Security Hub alerts

  Bedrock invocations → Bedrock Model Invocation Logging
                   ↓
  CloudWatch / S3
                   ↓
  Audit: "What did user X ask the Agent at time T, and what did it answer?"
```

Minimum switches to flip:

```
1. CloudTrail Multi-Region Trail (mandatory on)
   - All management events
   - Data events for S3 / Lambda (as needed)
   - Insight events (anomaly detection)
   - Add Object Lock to prevent deletion

2. Bedrock Model Invocation Logging
   - Bedrock console → Settings → Enable
   - Destination: CloudWatch + S3
   - Captures full prompt + response

3. Application logging conventions:
   - Every log line carries trace_id (X-Ray / OpenTelemetry)
   - user_id (taken from the IAM context)
   - action + resource_arn
```

> **AWS reference**: search "CloudTrail data events," "Bedrock model invocation logging," "S3 Object Lock."

---

## 11.6 Guardrails — Auditing the Agent's Behavior

It isn't only humans auditing the Agent; the Agent itself needs real-time inspection:

```
        Bedrock Guardrails: 5 categories of intercept
        ─────────────────────────────────────────────

  1. Content filter (harmful / violent / hateful / sexual content)
  2. Topic filter (forbidden topics)
  3. PII filter (national IDs / phone numbers / emails auto-redacted)
  4. Word filter (company-banned words / competitor names / internal codes)
  5. Contextual grounding (answers must be grounded in the knowledge base)
```

### Configuration approach

```
  PoC stage:
    ✓ Turn on PII filter
    ✓ Turn on Content filter (medium strength)

  Pre-production:
    ✓ Add Topic filter (business red lines)
    ✓ Add Word filter (company-confidential terms)
    ✓ Add Grounding (mandatory for any RAG application)

  Post-launch:
    ✓ Monitor Guardrail intercept counts
    ✓ Too many intercepts → adjust thresholds or rewrite prompts
    ✓ Too many leaks → add rules
```

> **AWS reference**: search "Bedrock Guardrails." It can be used independently of a model, or attached to an Agent.

---

## 11.7 A Complete Integrated Example

```
  Customer scenario: an insurance company's sales-assistant Agent

  Identity layer:
    - Sales reps SSO in with their AD account
    - Identity Center + SAML connects to customer AD

  Lifecycle:
    - HR offboards → AD disables → SCIM syncs → Agent is unavailable instantly

  Authorization layer:
    - "Sales rep" role: can only see their own customers' policies
    - "Manager" role: can see policies across the team
    - Implemented with ABAC: tag-based access control

  Agent calling legacy systems:
    - Calls ERP (SOAP) → Lambda Adapter → SAP RFC
    - Calls CRM (REST) → Lambda → Salesforce API
    - Every call carries user context (not a service account)

  Audit:
    - CloudTrail: AWS API
    - Bedrock Logging: prompt + response
    - App logs: trace_id stitches everything together
    - Audit window: 7 years (insurance industry)
    - Storage: S3 Object Lock + KMS

  Guardrails:
    - PII filter: customer national ID / bank card auto-redacted
    - Topic filter: no investment advice (compliance requirement)
    - Grounding: answers must be based on product documentation
```

---

## Key Quotes

> "*Identity is the new perimeter — and it's the first thing the customer's CISO will ask about.*"
> — A. Lawrence, *FDE Rule Book*, 2025

> "*Audit is not a feature — it's the only proof you have when something goes wrong.*"
> — AWS Well-Architected, 2025

> "*If your Agent can't tell who's asking, it shouldn't answer.*"
> — Anthropic enterprise best practices, 2025

---

## Action Checklist

When you start an enterprise project, weeks 1-2 must include:

1. **Draw a "four-things diagram"**: SSO / SCIM / authorization / audit, current state of each
2. **Get 30 minutes with the customer's security lead**: which IdP they use, MLPS level, audit requirements
3. **Get an SSO test account** (SAML metadata or OIDC client credentials)
4. **Wire up Identity Center + SCIM** (do not write an identity system from scratch)
5. **Enable CloudTrail + Bedrock Invocation Logging in week one**
6. **Every Agent tool that calls a legacy system goes through an Adapter** (no direct connections)
7. **At minimum, configure Bedrock Guardrails with PII + Content filters**
8. **Write an "audit-log query SOP"** so you can hand it over the moment a customer audit shows up

---

## Anti-Pattern Checklist

- ❌ **Running every call under a service account** (audit can't trace it back to a specific user)
- ❌ **Departed employees not auto-disabled on your side** (compliance incident)
- ❌ **Agent talks SOAP directly to a legacy system** (tightly coupled, no fallback)
- ❌ **Audit logs that operations staff can delete** (instant audit fail)
- ❌ **Unredacted PII flowing into Bedrock invocation logs** (GDPR / MLPS incident)
- ❌ **No dry-run mode for write APIs** (a demo nukes production data)
- ❌ **Postponing Guardrails** (one incident costs far more than the configuration time)

---

## Bridge to the Next Part

The full foundation for "the FDE working in a real customer environment" is now in place: data stack, network isolation, identity and audit. The next Part crosses the hardest chasm of all — **PoC → production**: how to actually ship stably after the demo, control cost, and run canaries with rollback.

[← Previous: Working in the Customer's VPC](chapter-10.md) · [Next Part: PoC → Production →](../part-5/intro.md)
