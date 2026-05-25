# Ch11 — VPC endpoint as the Bedrock model allow-list

## What this demo proves

The Lambda has IAM `bedrock:*` on `*`. It still cannot call Opus 4.7.
The denial comes from the VPC interface endpoint's resource policy,
which only allows the Haiku 4.5 inference profile (and the foundation
model ARNs it routes to).

That is the Ch11 claim in one runnable artefact: **at the network layer,
"only this model" is enforceable, deterministic, and auditable** —
without trusting application code, agent frameworks, or every IAM
permission set in the org.

> ⚠️ **Production warning**: this demo deliberately gives the Lambda
> IAM role `bedrock:*` on `*` so the network layer is the **only**
> variable. **Never configure IAM that wide in production.** The
> defense-in-depth pattern is **both layers strict** — IAM restricting
> modelId AND endpoint policy restricting modelId. If either layer is
> misconfigured the other still blocks the request. This demo only
> exercises the network half so the chapter's claim ("network is
> independent of IAM") is unambiguous.

```
Outcome (auditor): "AI traffic stays in VPC and only calls one model"
Customer:          Hesheng海外服务部, ap-southeast-1, 等保三级, PII rules
Harness (Ch11):    VPC + interface endpoint + endpoint policy + Lambda
                   in private subnet -> AccessDenied with endpoint-cited reason
```

## Scope

| In demo | Out of demo (discussed in the chapter) |
| --- | --- |
| VPC + private subnet, no IGW/NAT | KMS CMK on Bedrock | 
| `bedrock-runtime` interface endpoint | Cross-region replication |
| Endpoint policy restricting inference profile | IAM Identity Center / SCIM |
| Lambda in private subnet, real Converse calls | PII redaction at Guardrails (see Ch13) |
| Allowed vs denied call comparison | Octopus tenant onboarding |

The SSO / IDP federation half of Ch11 needs IAM Identity Center in the
test account and 15+ minutes of click-ops for SCIM tokens; it does not
fit a 30-minute teardown budget. The chapter covers it textually with
console screenshots; this demo just cements the network-layer half.

## Files

```
ch11-vpc/
├── Makefile
├── lambda/handler.py        # Bedrock Converse caller (zip-packaged)
├── scripts/
│   ├── up.py                # provision VPC, subnet, SG, endpoint, Lambda
│   ├── run.py               # invoke Lambda for haiku + opus, compare
│   ├── down.py              # tear down in reverse order
│   └── verify_down.py       # assert no leftover resources
└── src/ch11_vpc/state.py    # shared resource-id state
```

All five files are well under 200 lines.

## Run

```bash
make up    # ~90s: VPC, subnet, SG, endpoint (waits for available), Lambda
make run   # ~10s: two real Bedrock Converse calls via the endpoint
make down  # ~120s: ENI cleanup is async and dominates teardown
make verify-down
```

## Real evidence (from this run)

```
Test 1 (haiku via VPC endpoint): SUCCESS
  response: 'VPC_OK'  (in=15 out=7)

Test 2 (opus via VPC endpoint): EXPECTED_DENIED
  error: AccessDeniedException
    User ... is not authorized to perform: bedrock:InvokeModel on
    resource: ...inference-profile/us.anthropic.claude-opus-4-7
    because no VPC endpoint policy allows the bedrock:InvokeModel action
```

The phrase **"no VPC endpoint policy allows ..."** is the smoking gun:
AWS itself attributes the denial to the endpoint policy, not to IAM.
That is the auditable artefact.

## Cost

| Item | Rate | This run |
| --- | --- | --- |
| VPC + subnet + SG | $0 | $0 |
| Interface endpoint | $0.01/h | ~$0.005 (30 min) |
| Lambda invocations | free tier | $0 |
| Bedrock haiku tokens | <100 | <$0.001 |
| **Total** | | **< $0.05** |

## Idempotency

`up.py` reads `data/ch11-state.json`. Re-running picks up existing IDs and
only creates what's missing — useful when an SG-create error halts the
script mid-way (which happened the first time: AWS rejects `<` and `>`
in SG descriptions).

## Real gotchas hit during build

1. **Security group description charset.** AWS rejects `<` `>` and many
   ASCII punctuation chars. The valid set is documented but easy to
   miss. Took one retry.
2. **Endpoint policy must allow both the inference profile ARN and the
   foundation model ARNs it routes to.** Allowing only the profile
   resource isn't enough — Bedrock also performs an action-on-FM check
   internally. The policy in `up.py` lists both.
3. **ENI cleanup is async.** Lambda VPC ENIs and endpoint ENIs both
   linger 30-90s after their parents are deleted. `down.py` polls
   `describe_network_interfaces` before trying to delete the SG.
4. **`PrivateDnsEnabled=True` is non-negotiable.** Without it the
   default boto3 endpoint URL `bedrock-runtime.<region>.amazonaws.com`
   resolves to public IPs that the Lambda (no IGW) can't reach, and
   the call hangs the full 30s timeout instead of failing cleanly.

## Why not EC2 + SSM?

The original brief listed EC2/SSM as primary. Lambda is strictly
better here:

- no AMI/SSM-agent dance, no key-pair, no boot wait
- charged per-ms vs per-hour
- ENI cleanup happens automatically when the function is deleted
- the "in private subnet, no public IP" property is identical for the
  endpoint-policy test we want to run

The only thing Lambda gives up vs EC2 is interactive shell-driven
exploration. That is not what this demo is for.
