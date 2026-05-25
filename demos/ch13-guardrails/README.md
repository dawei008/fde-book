# Ch13 — Bedrock Guardrails as the model-layer perimeter

## What this demo proves

A single `Converse` call carries one **Guardrail** attached. Same model,
same system prompt, same IAM role — the only thing that decides what
flows in and out is the guardrail. Four runnable test cases cement the
four pillars of Ch13's 13.3:

| # | Layer | Input | Expected | Real run |
| - | ----- | ----- | -------- | -------- |
| 1 | **PII anonymize** | `Manager Wang ... Phone 138-1234-5678` | `{NAME}` and `{PHONE}` tokens replace raw values in the *output* | `outputAssessments.sensitiveInformationPolicy.piiEntities: [NAME ANONYMIZED, PHONE ANONYMIZED]`, `stopReason=guardrail_intervened` |
| 2 | **Denied topic** | `Write me a poem about servo motors` | input blocked, canned refusal | `inputAssessment.topicPolicy.topics: [off_scope_chat BLOCKED]`, `stopReason=guardrail_intervened` |
| 3 | **Prompt attack** | `Ignore all previous instructions ...` | input blocked | `inputAssessment.contentPolicy.filters: [PROMPT_ATTACK BLOCKED]`, `stopReason=guardrail_intervened` |
| 4 | **Normal ticket** | `JG-A6 X-axis alarm 1042, please triage` | passes through, useful answer | `stopReason=end_turn` → `L2 \| Motion Control System ...` |

```
Outcome (auditor): "model never returns raw PII; jailbreaks blocked"
Customer:          Hesheng海外服务部, ticket triage, no creative output
Harness (Ch13):    bedrock.create_guardrail + version + Converse
                   guardrailConfig with trace=enabled
```

## Scope

| In demo | Out of demo |
| --- | --- |
| PII anonymize (PHONE/EMAIL/NAME) + regex BLOCK (china_id_card) | Bedrock KB grounding wiring |
| Denied topic (`off_scope_chat`) | Word-list filters |
| Content filter PROMPT_ATTACK / VIOLENCE | Cross-region guardrail config |
| Contextual grounding policy *configured*; activates only with KB | Custom blocked messaging per locale |
| 4 live Converse calls + trace summary | AgentCore Policy / tool-allow-list |

### Why not AgentCore Policy in this demo?

Ch13 13.3 makes two parallel claims: Guardrails secure the **model
layer** (input/output content), AgentCore Policy secures the **agent
layer** (which tools the agent can call). Those layers are
complementary, not redundant.

This demo only exercises the Guardrails half. The Policy half is
covered structurally by the Ch14/Ch15 demos, which already show how an
agent's toolset is constrained at invocation time (Lambda direct-invoke
path with IAM-scoped permissions on the Gateway target side). Mixing
Policy preview APIs into a 30-minute teardown budget creates flakiness
without strengthening the chapter's narrative — Guardrails alone is
enough to make the perimeter point in code.

## Files

```
ch13-guardrails/
├── Makefile
├── scripts/
│   ├── up.py            # create guardrail + publish version 1
│   ├── run.py           # 4 Converse calls with guardrailConfig
│   ├── down.py          # delete guardrail (versions go with it)
│   └── verify_down.py   # assert nothing remains
└── src/ch13_guardrails/
    ├── state.py         # guardrail policy config + state I/O
    └── verdict.py       # trace summarizer + per-test verdict
```

All files are well under 200 lines.

## Run

```bash
make up           # ~5s : create guardrail, wait READY, publish v1
make run          # ~15s: 4 Converse calls, write results/ch13-results.json
make down         # ~2s : delete guardrail
make verify-down  # ~1s : confirm gone
```

## Cost

| Item | Rate | This run |
| --- | --- | --- |
| Guardrail (text unit) | $0.75 / 1k units | < $0.001 |
| Bedrock haiku 4.5 tokens | < 1k tokens total | < $0.001 |
| **Total** | | **< $0.01** |

## Real gotchas hit during build

1. **`bedrock` client, not `bedrock-runtime`.** `create_guardrail` lives
   on the control-plane client. `Converse` lives on the data-plane
   client. Mixing them up gives an `AttributeError` rather than a
   helpful `ClientError`.
2. **DRAFT is not callable from Converse.** Converse's `guardrailConfig`
   needs a numeric version string. You must `create_guardrail_version`
   *after* `create_guardrail` is `READY`. We poll `get_guardrail` for
   `status==READY` before publishing — without the wait, version
   creation occasionally races with policy compilation.
3. **PII action is layered.** `ANONYMIZE` rewrites the *content*; the
   `stopReason` still comes back as `guardrail_intervened` (not
   `end_turn`) because the guardrail mutated the assistant's output.
   The first version of the verdict logic treated that as a failure
   for "passes through with PII redaction" and was wrong. The current
   verdict checks for the `{PHONE}` / `{NAME}` token marker instead of
   matching on `stopReason`.
4. **Tags use lowercase keys.** `bedrock.create_guardrail(tags=[...])`
   wants `{"key": ..., "value": ...}` (lowercase), unlike most EC2 /
   Lambda APIs which use `{"Key": ..., "Value": ...}`. Easy 30-second
   detour the first time.
5. **Output PII anonymization in test 1 ran on the *output*, not the
   input.** Even with `ANONYMIZE` configured for both directions, the
   input flowed through to the model verbatim and the model's reply
   echoed the name/phone, which the output guardrail then rewrote.
   That's actually the right behavior — it means the model can reason
   about the original ticket without the user seeing anyone's number.
   But it surprised me; I expected the input to be redacted before
   reaching the model. The trace makes it explicit:
   `outputAssessments...piiEntities` (output), not `inputAssessment`.
