---
title: "part-3/chapter-08.md"
nav_exclude: true
search_exclude: false
---

# Chapter 8: Eval First, Code Second — A Practical Guide

## Opening

```
PoC, Week 5. The FDE is on-site.

Customer business owner: "Last week's demo looked great, but
why does today's demo answer differently?"

The FDE flips through the prompt commit history: system prompt
was changed Tuesday. Looks at the trace: a query that was right
last week is wrong today.

Customer: "Don't you people test?"

The FDE says nothing.

The next day he does the right thing:
  wires 200 Eval samples into CI,
  every PR must run the score,
  any score below last week's blocks merge.

From then on, the night before a demo is no longer panic —
the score ran last night, and whatever the customer asks
today, he knows where the answer stands.

This chapter: how to turn the Eval-driven rule
into "everyday engineering discipline" rather than a slogan.
```

---

## 8.1 The Engineering Definition of Eval-Driven Development

```
        TDD (Test-Driven Development)         EDD (Eval-Driven Development)
        ────────────────────────────         ────────────────────────────

  Write tests   write unit tests first        write Eval samples first
  Run tests     every commit runs them        every PR runs them (cost)
  On failure    fix the code                  fix prompt / RAG / model
  Coverage      line coverage                 scenario coverage
  Pass cond.    binary (pass/fail)            threshold (score >= X)
  Reproducible  deterministic                 probabilistic (must sample)
```

EDD's defining trait — **probabilistic**:
- Same input, different times, different outputs
- You **must sample multiple times and take the distribution**, not a single run
- "Pass" isn't 100%; it's "meets the agreed threshold"

---

## 8.2 The "Pyramid Structure" of an Eval Set

```
                    └──── Production ────┘
                          (live sampling feedback)
                              ↑
                    ┌─── Adversarial ────┐
                    │   edge / attack /   │  ~50 items
                    │   out-of-bounds     │
                    └────────────────────┘
                              ↑
                    ┌──── Golden Set ────┐
                    │   human-labeled    │  100-300 items
                    │   reference        │
                    └────────────────────┘
                              ↑
                    ┌────── Seed ────────┐
                    │   collected during │  50 items
                    │   Discovery        │
                    └────────────────────┘
```

Each layer has its own use:

```
  Seed:         quick baseline (don't run the full set every time)
  Golden Set:   primary Eval, runs on every PR
  Adversarial:  must-run before launch, used for regression
  Production:   live sampling feedback, surfaces new failure modes
```

**Reference proportions**: 50 + 200 + 50 + continuously growing ≈ enough to start.

---

## 8.3 Three Metrics for an Eval Set, in Practice

### Metric 1: Rule-Based Scoring (cheapest)

```python
# metrics_rule.py
def keyword_recall(answer: str, expected_keywords: list) -> float:
    hits = sum(1 for kw in expected_keywords if kw in answer)
    return hits / len(expected_keywords)

def blacklist_pass(answer: str, blacklist: list) -> bool:
    return not any(bw in answer for bw in blacklist)

def json_schema_valid(answer: str, schema: dict) -> bool:
    try:
        data = json.loads(answer)
        jsonschema.validate(data, schema)
        return True
    except Exception:
        return False
```

Use cases: required terms / blacklist / structured output / numeric exactness.

### Metric 2: Semantic Similarity (medium cost)

```python
# metrics_semantic.py
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('BAAI/bge-m3')

def semantic_similarity(answer: str, reference: str) -> float:
    e1 = model.encode(answer)
    e2 = model.encode(reference)
    return cosine_similarity(e1, e2)
```

Use case: relevance for open-ended Q&A.

**Note**: 0.7 is not an absolute threshold. Calibrate per project — take 50 human-labeled "right/wrong" samples and compute the best threshold.

### Metric 3: LLM-as-judge (most expensive)

```python
# metrics_judge.py
JUDGE_PROMPT = """
You are an evaluation expert. Decide whether the "actual answer" below
meets the standard set by the "expected answer".

Question: {question}
Expected answer: {reference}
Actual answer: {actual}

Score 1-5:
1: completely wrong
2: partially relevant but with major errors
3: largely correct, minor issues
4: correct, expression could improve
5: perfect

Output a single number only.
"""

def llm_judge(question, reference, actual, judge_model="claude-3-5-sonnet"):
    response = bedrock.invoke_model(
        modelId=judge_model,
        body=json.dumps({
            "messages": [{"role": "user", "content": JUDGE_PROMPT.format(...)}]
        })
    )
    score = int(response['content'][0]['text'].strip())
    return score / 5.0
```

**Pitfalls**:

```
❌ Use the same model being evaluated as the judge → same-source bias
✅ Use a stronger model as judge (e.g., Claude Opus judging Sonnet)

❌ Treat a single run as the verdict → probabilistic noise
✅ Sample 3-5 times per item and average

❌ Judge prompt too lenient → 4-5s flood the report
✅ Show the judge 1-2 negative examples for calibration
```

### Combining the Three

```
total_score = 0.3 * rule_score
            + 0.3 * semantic_score
            + 0.4 * judge_score
```

Weights are tunable per project, not fixed.

---

## 8.4 Wiring the Eval Set into CI — Practice

### File Layout

```
my-llm-app/
├── src/
│   ├── prompt.py          # prompt template
│   ├── retriever.py       # RAG retrieval
│   └── ...
├── evals/
│   ├── golden_v0.2.jsonl  # 200 samples
│   ├── adversarial.jsonl  # 50 samples
│   ├── metrics.py         # scoring functions
│   ├── runner.py          # batch runner
│   └── reports/           # historical snapshots
├── .github/
│   └── workflows/
│       └── eval.yml       # CI config
└── eval_threshold.toml    # threshold config
```

### `eval_threshold.toml` Looks Like This

```toml
[golden_v0.2]
total_score = 0.85
top20_keywords = 0.95
p95_latency_ms = 3000

[adversarial]
safety_score = 1.0  # PII / out-of-scope must be 100% caught
refusal_rate = 1.0  # must refuse everything that should be refused
```

### CI Scoring (GitHub Actions Example)

```yaml
# .github/workflows/eval.yml
name: Eval on PR

on:
  pull_request:
    paths:
      - 'src/**'
      - 'evals/**'

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install deps
        run: pip install -r requirements.txt

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_EVAL_ROLE }}
          aws-region: us-east-1

      - name: Run Eval
        run: python evals/runner.py --suite golden_v0.2

      - name: Check thresholds
        run: python evals/check_threshold.py --report evals/reports/latest.json

      - name: Comment on PR
        if: always()
        uses: actions/github-script@v7
        with:
          script: |
            const report = require('./evals/reports/latest.json');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `Eval Score: ${report.total_score} (threshold ${report.threshold})\n${report.summary}`
            });
```

**Key points**:

- PR changes to prompt / retriever both trigger
- Below threshold → block merge
- The score and diff land directly in the PR comments

### AWS Hands-On: Bedrock Evaluations as the PR Gatekeeper

```
        Integrating Bedrock Evaluations into CI
        ─────────────────────────────────────

  Step 1: Store the Eval dataset in S3
          s3://my-bucket/evals/golden_v0.2.jsonl

  Step 2: PR triggers → CI calls Bedrock CreateEvaluationJob API
          (Python boto3)

  Step 3: Poll job status (polling or EventBridge)

  Step 4: Read the result S3 path, parse metrics

  Step 5: Compare to baseline, emit a report, decide on merge

  Benefits:
    - No need to maintain your own evaluation infrastructure
    - LLM-as-judge uses Bedrock's built-in
    - Works at large scale (>500 samples)
```

Minimal code skeleton:

```python
import boto3

bedrock = boto3.client('bedrock')

def trigger_eval(model_arn, dataset_s3_uri, output_s3_uri):
    job = bedrock.create_evaluation_job(
        jobName=f"pr-eval-{commit_sha}",
        roleArn=os.environ['EVAL_ROLE_ARN'],
        evaluationConfig={
            'automated': {
                'datasetMetricConfigs': [{
                    'taskType': 'QuestionAndAnswer',
                    'dataset': {'name': 'golden', 'datasetLocation': {'s3Uri': dataset_s3_uri}},
                    'metricNames': ['Accuracy', 'Robustness', 'Toxicity']
                }]
            }
        },
        inferenceConfig={
            'models': [{'bedrockModel': {'modelIdentifier': model_arn}}]
        },
        outputDataConfig={'s3Uri': output_s3_uri}
    )
    return job['jobArn']
```

> **AWS reference**: search "Bedrock CreateEvaluationJob API" and "Bedrock evaluation built-in metrics".

---

## 8.5 The "Distribution" Mindset for Scoring

LLM evaluation is probabilistic. **A single score is not a verdict.**

### Three Things You Must Do

```
1. Run the same sample N times (N=3-5)
   Take mean + variance + worst case

2. Look at the distribution, not just the mean
   Mean 0.85 but P10 of 0.3 → dangerous (10% of users have a terrible time)

3. Watch for regressions
   It's not just "score >= threshold" —
   also "compared to the previous version, which samples lost points"
```

### What a Good Eval Report Looks Like

```
══════════════════════════════════════════════════════════
Eval Report — golden_v0.2
PR: #1234 (changed retriever top_k 5→8)
Date: 2026-05-22

Total: 0.872 ↑ +0.012 vs main (0.860)
Pass:  ✅ (threshold 0.85)
─────────────────────────────────────────────────────────
By dimension:
  keyword_recall:   0.91 ↑ (+0.03)
  semantic_sim:     0.78 → (=)
  llm_judge:        0.86 ↓ (-0.02)
─────────────────────────────────────────────────────────
By category:
  high_freq (top 20):  0.95 ↑
  long_tail:           0.82 →
  adversarial:         0.99 →
─────────────────────────────────────────────────────────
Regressions (drop > 0.1):
  eval-013: 0.85 → 0.42 (semantic_sim)
    Issue: "critical illness waiting period" recall returned life-insurance clauses
    Suggested: rerank or add metadata filter

  eval-047: 0.78 → 0.55 (llm_judge)
    Issue: answer got longer; judge says "main point not prominent"
    Suggested: add "answer in 3 sentences max" to prompt
─────────────────────────────────────────────────────────
P95 latency: 2.4s ↑ (+0.3s, due to higher top_k)
Cost / query: $0.0021 ↑ (+12%)
══════════════════════════════════════════════════════════
```

**An FDE should look at Eval reports more often than at code diffs.**

---

## 8.6 Production Sampling Feedback — Closing the Loop

```
        Production → Eval set feedback loop
        ─────────────────────────────────

  Live request
      ↓
  Logging (CloudWatch / LangFuse)
      ↓
  Sampling rules:
    - 1% random sampling
    - 100% of user thumbs-down samples
    - 100% of low-model-confidence samples
    - 100% of failed / timed-out samples
      ↓
  Human / LLM secondary review
      ↓
  Add to Adversarial / Golden Set
      ↓
  Next PR's Eval set automatically includes the new samples
```

**Without this loop → the Eval set ages → high Eval scores yet production drops the ball.**

---

## 8.7 Eval-Set Anti-Patterns

```
❌ Eval set = training set / few-shot examples
   → data leakage, inflated scores

❌ 100% of samples are "should answer correctly"
   → the model learns to "answer everything", never refuses

❌ The Eval set is written by the FDE alone
   → business experts don't endorse it; customer rejects "right" answers at acceptance

❌ Threshold set at 100%
   → never passes = the Eval loses its meaning

❌ Threshold is frozen for 6 months
   → business changes; the threshold needs to move with it

❌ Eval scoring is expensive, so only run it before launch
   → degenerates into "acceptance testing", loses its developmental discipline
```

---

## Key Quotes

> "*If you don't have an eval set, you don't have a system — you have a hope.*"
> — Anonymous FDE, *The FDE Playbook*, 2025

> "*Looking at evals is more important than looking at the model output.*"
> — Anthropic internal best practice, 2025

> "*Eval is a discipline, not a deliverable.*"
> — AWS GenAI Innovation Center, 2025

---

## Action Checklist

Must-dos in Week 3 of a new project:

1. **Set up the evals/ directory**: jsonl samples + metrics.py + runner.py
2. **Wire it into CI**: every PR runs Eval (start with 50 seed samples; regression pass within 5 minutes)
3. **Write eval_threshold.toml**: explicit thresholds
4. **Wire up LLM-as-judge** (Bedrock built-in or Claude Opus)
5. **Wire up production logging** (from day one — don't bolt it on later)
6. **Review Eval reports every Monday morning**: look at regressions and distribution
7. **Grow the Eval set by 20-50 samples each month** (sourced from production sampling)

---

## Anti-Pattern Checklist

- ❌ **Filling in Eval only before launch** (violates the Eval-driven rule)
- ❌ **Looking only at the mean** (ignores long-tail user experience)
- ❌ **Eval reports go only to the FDE** (customer, business, manager should all see them)
- ❌ **No production sampling feedback loop** (the Eval set drifts away from production)
- ❌ **Skipping Eval on every model upgrade** (upgrade-induced regressions are the most dangerous)
- ❌ **Lowering the threshold when Eval fails** (you should fix the model / prompt to bring the score back)

---

## Relation to the Next Part

The LLM-application track's Scaffolding stage closes here: you have **a model + a framework + an Eval gatekeeper**.

The next Part shifts to the **data-driven track** (which the LLM track also can't avoid) — the customer's real data stack, VPC / private deployment, and integration with legacy systems. This is the main battlefield of Palantir-style and AWS GenAIIC-style FDEs.

[← Previous: Decision Tree](chapter-07.md) · [Next Part: Data and Integration →](../part-4/intro.md)
