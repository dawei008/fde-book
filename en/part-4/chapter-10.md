# Chapter 10: Working in the Customer's VPC / Private Deployment / Offline Data Center

## Opening

```
A Chinese state-owned enterprise. Day one in the customer's data center:

  Customer security lead: "Our rules ——
    1. All code lives on our internal GitLab
    2. No ChatGPT, no Google
    3. No internet; pip install goes through our private PyPI mirror
    4. Servers are SSH-via-bastion only, no direct internet
    5. Data does not leave our data center
    6. Your Macs cannot connect to our network
       —— use this Windows workstation we provided
    7. The workstation cannot install non-whitelisted software
       (and the whitelist does not include VS Code's GitHub Copilot extension)"

The FDE is thinking: "What can I actually do?"

A month later her summary: "Turns out you can do anything,
the rhythm is just completely different — it isn't the SaaS-workflow rhythm.
The trick is being clear about what you can do and what has to be Air-gapped."

This chapter covers the FDE's concrete engineering moves
inside a customer VPC / private deployment / offline data center.
```

---

## 10.1 Three "Non-Cloud-Native" Customer Scenarios

```
        Non-SaaS customer deployments
        ─────────────────────────────────────────

  Scenario A: Customer VPC (cloud, but isolated)
    - Customer has their own VPC on AWS / Azure / Aliyun
    - Internet is gated through controlled NAT egress
    - Strict security groups + NACLs
    - Your code is deployed inside the customer's account

  Scenario B: Customer private cloud / on-prem data center
    - Customer runs their own K8s cluster / VMware
    - Some hosts have internet, some are pure intranet
    - Your code is deployed onto customer-owned machines

  Scenario C: Air-gap (fully offline)
    - No internet at all
    - Models / images / dependencies arrive via USB / bastion
    - Defense / military / parts of finance
```

**90% of B2B customers fall into A or B**, with A the most common.

---

## 10.2 Scenario A: Working Inside the Customer's VPC

### Key engineering moves

```
  1. Get an IAM role (not root — a scoped role)
  2. Sign in via AWS Identity Center / customer SSO
  3. Deployment target lives inside the customer's account + VPC
  4. Between your dev machine and the customer VPC, traffic goes through
     - VPN (Site-to-Site / Client VPN)
     - Bastion (Bastion Host / Session Manager)
     - Never direct
```

### AWS in practice: deploying a Bedrock app inside the customer's VPC

The single most important property is **"Bedrock traffic does not leave the customer's VPC."** Configuration:

```
        Customer VPC + Bedrock private path
        ───────────────────────────────────────────

  Customer VPC
    ├── Subnet A (private, application tier)
    │     ├── Lambda / ECS / EC2 (your application)
    │     │
    │     ↓ (VPC Endpoint)
    │
    ├── VPC Endpoint: bedrock-runtime
    │   (com.amazonaws.region.bedrock-runtime)
    │
    └── Traffic: app → VPCe → AWS Bedrock
              (does not leave the VPC, does not touch the internet)
```

Why a VPC Endpoint is required:

- The customer's security lead: "Every call must be auditable and blockable"
- VPC Endpoint = AWS private network = no public exposure
- CloudTrail + VPC Flow Logs make the whole path auditable

Minimum config:

```bash
# 1. Create the VPC Endpoint
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-xxx \
  --service-name com.amazonaws.us-east-1.bedrock-runtime \
  --vpc-endpoint-type Interface \
  --subnet-ids subnet-aaa subnet-bbb \
  --security-group-ids sg-yyy

# 2. The application calls Bedrock via SDK
import boto3
client = boto3.client('bedrock-runtime')
# The SDK routes through the VPCe automatically
# (DNS resolves to the VPCe's private IP)
```

> **AWS reference**: search "Bedrock VPC endpoints" and "AWS PrivateLink for Bedrock."

### Knowledge Bases / Agents go private too

```
  Bedrock Knowledge Bases
    - VPC Endpoint: bedrock-agent
    - Data source S3: VPC Endpoint: s3 (Gateway type)
    - OpenSearch Serverless: collection inside the customer's VPC

  Bedrock Agents
    - VPC Endpoints: bedrock-agent + bedrock-agent-runtime
    - Lambda tools: inside the customer's VPC
    - Customer internal API calls: invoked directly within the VPC
```

### SageMaker JumpStart — the fallback for self-hosted models

If the customer won't even let you use Bedrock ("must be self-hosted"), use SageMaker JumpStart:

```
  SageMaker JumpStart one-click deploy:
    - Llama 3.1 / Qwen / Mistral images
    - Deploys to a SageMaker endpoint inside the customer's VPC
    - Private endpoint, no public exposure
    - Entirely inside the customer's account
```

---

## 10.3 Scenario B: Customer Private Cloud / On-Prem Data Center

### A typical day

```
        A typical day
        ────────────────────────────────────────

  7:30  Arrive at the customer's building, badge + face scan + bag X-ray
  8:00  Up to the FDE work area on the second floor of the data center
  8:30  Boot the customer-issued Windows workstation
        - No Outlook (use the customer's webmail)
        - No Slack (use the customer's internal comms tool)
        - VS Code installed, but no Copilot
  9:00  ssh through the bastion → customer K8s
        - First check overnight alerts
  10:00 Negotiate today's deployment window with customer ops
  ...
  17:00 Push today's code to the customer's GitLab
        SAST / DAST scan runs on push
  18:00 Write the daily report and head home
```

### Key engineering configuration

```
  Code hosting:
    - Customer-internal GitLab / Gitea / Gerrit
    - No pushes to GitHub

  CI/CD:
    - Customer-internal Jenkins / GitLab CI / ArgoCD
    - No GitHub Actions / CircleCI

  Image registry:
    - Customer-internal Harbor / Quay
    - Base images (Python / Java) must come from the customer's mirror

  Dependency management:
    - pip / npm / maven point to the customer's private repository
    - You must produce a manifest; the security lead will scan it

  Model storage:
    - Model weights live in the customer's object store (MinIO / Ceph / OSS)
    - You cannot pull from HuggingFace directly

  Monitoring:
    - The customer's Prometheus + Grafana
    - You cannot connect Datadog / NewRelic
```

### How a model "gets in"

```
        The flow for bringing model weights inside
        ──────────────────────────────────────────

  Step 1: From the corporate side, the FDE downloads the weights
          from HuggingFace (Llama / Qwen / Mistral)

  Step 2: Virus scan + license check + security audit

  Step 3: Run the customer's "software-admission process"
          - One "model admission application"
          - Model description + license + scan report
          - Wait for approval (1-3 weeks, varies)

  Step 4: After approval, the customer permits USB or private-line transfer

  Step 5: Land in the customer's object store + register in their model repo
```

**The FDE must trigger this process in Week 1.** Otherwise you'll hit Week 6 only to discover the model still hasn't arrived = project slips.

---

## 10.4 Scenario C: Air-Gap (Fully Offline)

### A real story

> *An FDE deployed an LLM at a fully offline customer. Day one she discovered ——*
>
> *the company-issued laptop's git still had a GitHub remote. She ran git push without changing the origin.
> The customer's security lead replied within seconds: "Your laptop is now quarantined for 24 hours of observation."*

The defining traits of Air-gap:

```
  ✓ No internet at all
  ✓ All code / tooling / images come in on USB or via a trusted ferry
  ✓ Traffic between your local machine and customer machines goes through
    a "ferry box"
  ✓ Every action that enters the customer network is audited
```

### The first three days' checklist

```
  Day 1: Build the USB package
    - Python / Node / Docker images
    - All your code + dependencies (pip download / docker save)
    - Model weights
    - VS Code + offline extensions
    - Documentation (RFCs / designs / data dictionaries)

  Day 2: USB security check + admission
    - The customer audits your USB
    - The customer installs it on their internal ferry machine
    - Ferry scan + quarantine observation + delivery into the intranet

  Day 3: Internal-network PC receives the materials, work begins
```

### Engineering discipline

```
  ✓ Every prompt lives in the repo (no "I'll figure that out later")
  ✓ Don't assume ChatGPT / Claude is around to help debug
  ✓ Bring your own "offline reference":
    - HuggingFace cache
    - PyPI mirror
    - Offline docs (pip download docs)
  ✓ For features that keep breaking → simplify the design, no exotic deps
  ✓ At the end of each week, batch the latest code back to corporate
    (review + backup)
```

---

## 10.5 Engineering Notes for Private LLM Deployments

Not cloud SaaS LLMs — **self-hosted Llama / Qwen / Mistral**:

### Pick the model size

```
                    GPU configuration → recommended model
                    ─────────────────────────────────────

  4× A100 80G        Llama 3.1 70B half precision / Qwen2 72B
  2× A100 80G        Llama 3.1 70B AWQ 4-bit / 32B models
  1× A100 80G        Llama 3.1 8B / Qwen2 14B
  1× A100 40G        7B / 8B models
  No GPU             Don't force an LLM; use a cloud API
```

### Inference engines

```
  vLLM (recommended)
    - PagedAttention, memory-efficient
    - OpenAI-compatible API
    - High QPS

  TGI (HuggingFace)
    - Easy to start
    - Good streaming output

  TensorRT-LLM (NVIDIA)
    - Peak performance
    - Long ramp-up

  llama.cpp
    - Runs on CPU / Mac
    - Tiny footprint
```

### Deployment architecture

```
  Standard K8s + vLLM architecture:
    ─────────────────────────────────

  Ingress (internal LB) → API Gateway (auth + rate-limit)
                              ↓
                         vLLM Pods (HPA)
                           (1 GPU per pod)
                              ↓
                         Model weights (PVC / S3 / OSS)

  Monitoring: Prometheus + Grafana (token/sec, GPU util)
  Logging:    Loki / customer ELK
```

### Privatizing Eval / Trace

```
  Cloud SaaS:           Private deployment:
  ───────────           ─────────────────────
  LangFuse Cloud    →   LangFuse self-hosted
  LangSmith         →   Phoenix (Arize, open source)
  Bedrock Eval      →   Custom Python scripts + dbt
```

---

## 10.6 Compliance Checklist (private deployment / common in China B2B)

```
        Compliance cheat-sheet
        ─────────────────────────────────────

  Cross-border data:
    - Chinese customers' data cannot leave the country
    - Model weights can usually be imported (depends on license)

  China MLPS (等保):
    - MLPS 2.0 Level 3 / Level 4 = many constraints
    - Audit + deployment process is what affects FDE work most

  GDPR / SOC 2:
    - Data classification + access auditing
    - PII protection

  PCI DSS (financial):
    - Payment data encryption + network isolation

  HIPAA (healthcare / US):
    - PHI data + audit trail

  CSA STAR (enterprise cloud):
    - Cloud-provider qualification
```

**The FDE's strategy**: compliance is not something one FDE can solve, but **the FDE has to surface these requirements during Discovery**. Otherwise you'll get to deployment, find out "X isn't allowed," and the whole architecture has to be redone.

---

## Key Quotes

> "*The customer's network is the customer's contract — disrespect it once, lose the project.*"
> — A. Lawrence, *FDE Rule Book*, 2025

> "*Architecture changes when the GPU lives in the customer's data center.*"
> — Palantir FDE training, 2024

> "*PrivateLink is the most underused service among new AWS users.*"
> — AWS Solutions Architects, 2025

---

## Action Checklist

When you start a non-SaaS customer project, Week 1 must include:

1. **Draw a network topology diagram**: customer VPC / private cloud / Air-gap; how traffic enters and leaves
2. **Get your IAM / SSO identity** (don't borrow someone else's account)
3. **Stand up VPC Endpoints** (at minimum: Bedrock + S3 + CloudWatch)
4. **Trigger the software-admission process** (model / tools / dependencies in one batch — earlier is better)
5. **Run a "hello world" by Friday** (a simple application calling Bedrock or a self-hosted model from inside the customer's VPC)
6. **Draw a data-flow diagram**: which data may enter, which may not, with PII tags
7. **Get 30 minutes of coffee with the customer's security lead** (this person decides whether the next 12 weeks go smoothly)

---

## Anti-Pattern Checklist

- ❌ **Develop locally with SaaS APIs and switch to private only at deploy** (behavior diverges sharply; you discover too late that it can't ship)
- ❌ **No VPC Endpoint, egress via NAT** (compliance audit finding #1)
- ❌ **Install software before applying for admission** ("I'll just install it" gets purged within seconds)
- ❌ **Download customer data to your laptop for analysis** (compliance incident #1)
- ❌ **Push code to GitHub** (the customer forbids external repos)
- ❌ **At an Air-gap customer, expecting ChatGPT to help write code** (24-hour quarantine)

---

## Bridge to the Next Chapter

Data and network are sorted. The last front is integration with the customer's existing systems — SSO / SCIM / API / audit. The next chapter covers the engineering patterns for plugging into legacy systems.

[← Previous: The Customer Data Stack](chapter-09.md) · [Next: Integrating with Legacy Systems →](chapter-11.md)
