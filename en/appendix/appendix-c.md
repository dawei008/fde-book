---
title: "Appendix C: Eval Set Templates"
parent: "Appendix"
nav_order: 3
---

# Appendix C: Eval Set Design Templates

> Eval templates for the four most common LLM task types:
> 1. RAG Q&A
> 2. Agent task execution
> 3. Text classification
> 4. Structured information extraction
>
> Each template includes a jsonl schema, field meanings, sampling strategy, evaluation method, and a CI example.

---

## C.1 Shared Design Principles

```
  4 layers of an eval set
        ──────────────────────────────────

  Seed Set       (5-20 cases)    hand-written, ultra-fast regression, never modified
  Golden Set     (100-300 cases) labeled by customer experts, acceptance baseline
  Adversarial    (50-150 cases)  counter-examples / edge / privilege-escalation
  Production     (streaming)     sampled from prod → weekly back-feed
```

**Common schema fields**:

```json
{
  "id": "unique stable id",
  "category": "case category for slicing",
  "input": "the input to the system",
  "expected": "what success looks like",
  "metadata": {
    "source": "where this case came from",
    "added_at": "2026-05-22",
    "reviewer": "reviewer email",
    "difficulty": "easy / medium / hard",
    "is_adversarial": false
  }
}
```

**Why jsonl, not csv**: nested fields, multi-line text, and long prompts are routine — CSV escaping becomes a nightmare.

---

## C.2 Template 1: RAG Q&A Eval

### Schema

```jsonl
{
  "id": "rag-001",
  "category": "policy_lookup",
  "input": {
    "question": "Does the customer's health insurance plan include a hospitalization daily allowance? Policy number P20240315-001"
  },
  "expected": {
    "must_contain_keywords": ["hospitalization daily allowance", "USD 30/day", "30 days"],
    "must_not_contain": ["excluded", "not covered"],
    "reference_doc_id": "POL-HC-002-v3.pdf",
    "reference_section": "Chapter 3, Clause 2",
    "reference_answer": "Includes a hospitalization daily allowance of USD 30 per day, up to 30 days"
  },
  "metadata": {
    "source": "customer business expert 2026-05",
    "difficulty": "medium"
  }
}
```

### Evaluation logic (Python pseudocode)

```python
def evaluate_rag(case, system_output):
    score = {}

    # 1. Hard rules — keywords
    score['kw_match'] = all(
        kw in system_output['answer']
        for kw in case['expected']['must_contain_keywords']
    )
    score['no_forbidden'] = all(
        kw not in system_output['answer']
        for kw in case['expected']['must_not_contain']
    )

    # 2. Did we retrieve from the right source (the most common RAG bug)
    score['retrieval_correct'] = (
        case['expected']['reference_doc_id']
        in [d['doc_id'] for d in system_output['retrieved_docs']]
    )

    # 3. Semantic similarity (embedding cosine)
    score['semantic_sim'] = cosine(
        embed(case['expected']['reference_answer']),
        embed(system_output['answer'])
    )

    # 4. LLM-as-judge (most expensive, reserve for hard cases)
    if case['metadata']['difficulty'] == 'hard':
        score['llm_judge'] = call_judge(
            question=case['input']['question'],
            reference=case['expected']['reference_answer'],
            actual=system_output['answer']
        )

    return score
```

### Sampling strategy

```
  Seed Set:
    - Top 5 most-frequent questions (the ones business asks every day)
    - 5 explicit counter-examples (must never get wrong)

  Golden Set 200 cases — recommended mix:
    - 60% mainstream questions (high-frequency cases per business expert)
    - 20% edge cases (cross-policy / multi-insured / historical policy)
    - 10% long-tail rare questions
    - 10% counter-examples (privilege-escalation / PII / things it shouldn't answer)

  Adversarial 50 cases:
    - rephrased / misspelled / alternate terms
    - prompt injection
    - cross-domain (asking about a competitor's insurance)
```

### CI threshold

```yaml
# .github/workflows/rag-eval.yml
- name: Run RAG eval
  run: |
    python eval/run_rag.py --set golden --output result.json
    python eval/check.py \
      --result result.json \
      --thresholds \
        kw_match>=0.95 \
        retrieval_correct>=0.92 \
        semantic_sim>=0.80 \
        llm_judge>=0.85
```

---

## C.3 Template 2: Agent Task Execution Eval

### Schema

```jsonl
{
  "id": "agent-claim-001",
  "category": "auto_settle_simple",
  "input": {
    "claim_id": "CLM-2026-001",
    "user_message": "I want to claim USD 80 for last week's outpatient visit",
    "context": {
      "customer_id": "C123",
      "policy_id": "P-OPD-001"
    }
  },
  "expected": {
    "task_completed": true,
    "tool_calls": [
      {"tool": "get_policy", "params_must_include": ["P-OPD-001"]},
      {"tool": "validate_amount", "params_must_include": [80]},
      {"tool": "create_settlement", "must_appear": true}
    ],
    "tool_calls_must_not": ["transfer_funds"],
    "final_state": {
      "claim_status": "approved",
      "approved_amount": 80
    },
    "max_steps": 8,
    "max_cost_usd": 0.05
  },
  "metadata": {
    "difficulty": "easy"
  }
}
```

### 5-dimension evaluation

```
  1. Task completion
     final_state == expected.final_state ?

  2. Path reasonableness
     Do tool_calls satisfy "must / must-not" constraints?
     Is the step count ≤ max_steps?

  3. Tool-call correctness
     Are the parameters of each tool call correct?

  4. Side effects
     Did it call any tool on the must_not list?
     Did it pollute external state?

  5. Cost
     Total tokens / dollars ≤ max_cost_usd?
```

### Python evaluator

```python
def evaluate_agent(case, trace):
    """trace is the agent's full execution trace"""
    tool_calls = trace['tool_calls']

    # 1. Task completion
    task_done = trace['final_state'] == case['expected']['final_state']

    # 2. Tool sequence
    must_tools = case['expected']['tool_calls']
    must_present = all(
        any(
            tc['tool'] == m['tool']
            and all(p in tc['params'] for p in m.get('params_must_include', []))
            for tc in tool_calls
        )
        for m in must_tools
    )

    # 3. Forbidden tools
    forbidden_used = any(
        tc['tool'] in case['expected']['tool_calls_must_not']
        for tc in tool_calls
    )

    # 4. Steps / cost
    within_steps = len(tool_calls) <= case['expected']['max_steps']
    within_cost = trace['total_cost_usd'] <= case['expected']['max_cost_usd']

    return {
        'task_done': task_done,
        'must_tools_present': must_present,
        'no_forbidden': not forbidden_used,
        'within_steps': within_steps,
        'within_cost': within_cost,
        'overall_pass': all([
            task_done, must_present, not forbidden_used,
            within_steps, within_cost
        ])
    }
```

### Sampling strategy

```
  Golden 100 cases — recommended mix:
    - 40% standard cases (simple cases the agent can complete autonomously)
    - 30% cases that should be escalated to HITL
    - 15% abnormal inputs (missing fields / ambiguous referents)
    - 15% counter-examples (privilege-escalation / injection / adversarial)
```

---

## C.4 Template 3: Classification / Routing Eval

### Schema

```jsonl
{
  "id": "intent-001",
  "category": "core_intents",
  "input": {
    "user_message": "I just had a car accident, what should I do?"
  },
  "expected": {
    "intent": "claim_intake",
    "confidence_min": 0.8
  },
  "metadata": {
    "difficulty": "easy"
  }
}
```

### Evaluation metrics

```python
# Multi-class classification
from sklearn.metrics import classification_report, confusion_matrix

y_true = [c['expected']['intent'] for c in cases]
y_pred = [run_classifier(c['input']) for c in cases]

print(classification_report(y_true, y_pred))
print(confusion_matrix(y_true, y_pred))

# CI threshold: macro F1 >= 0.85, per-class recall >= 0.80
```

### Key sampling

```
  - At least 30 cases per intent (oversample when imbalanced)
  - Confusion classes with "asymmetric business cost" must be labeled separately
    e.g. claim_intake misclassified as general_query → bad customer experience
         general_query misclassified as claim_intake → wasted human effort
         the former costs more, so it must be tested explicitly
```

---

## C.5 Template 4: Structured Extraction Eval

### Schema

```jsonl
{
  "id": "extract-invoice-001",
  "category": "ocr_invoice",
  "input": {
    "image_url": "s3://bucket/invoice-123.png",
    "ocr_text": "..."
  },
  "expected": {
    "invoice_no": "INV-2026-0312",
    "total_amount": 1280.50,
    "currency": "USD",
    "issue_date": "2026-03-12",
    "vendor": {
      "name": "ABC Trading Co., Ltd.",
      "tax_id": "91110000XXXXXXXX"
    }
  },
  "metadata": {
    "difficulty": "medium",
    "image_quality": "good"
  }
}
```

### Field-level evaluation

```python
def field_level_eval(case, output):
    expected = case['expected']
    score = {}
    for field in flatten(expected).keys():
        e = get(expected, field)
        a = get(output, field)
        if isinstance(e, str):
            score[field] = (e == a)
        elif isinstance(e, (int, float)):
            score[field] = abs(e - a) / max(abs(e), 1) < 0.001
        elif isinstance(e, dict):
            # Nested, recurse
            ...
    return score

# Total score = weighted average of key fields
weights = {
    'invoice_no': 1.0,
    'total_amount': 1.0,    # critical, must be numerically exact
    'currency': 0.5,
    'issue_date': 0.8,
    'vendor.name': 0.6,
    'vendor.tax_id': 1.0    # compliance requirement
}
```

---

## C.6 A Complete Eval Project Layout

```
project/
├── eval/
│   ├── datasets/
│   │   ├── seed.jsonl              (10 cases, version-locked)
│   │   ├── golden_v1.jsonl         (200 cases, expert-labeled)
│   │   ├── golden_v2.jsonl         (250 cases, later additions)
│   │   ├── adversarial.jsonl       (50 cases)
│   │   └── prod_sampled_2026w20.jsonl  (weekly back-feed)
│   ├── runners/
│   │   ├── run_rag.py
│   │   ├── run_agent.py
│   │   └── run_classifier.py
│   ├── judges/
│   │   ├── llm_judge_prompts.yaml
│   │   └── rules.py
│   ├── reports/
│   │   ├── 2026-05-22_release_v1.2.html
│   │   └── ...
│   └── README.md
└── .github/workflows/
    └── eval.yml
```

---

## C.7 Labeling Workflow — Make Customer Experts Productive

```
        Step 1: FDE prepares 100 seed questions
               (drawn from customer docs / historical tickets / support logs)

        Step 2: Business expert labels in Streamlit / Excel
               (UI shows the question + your draft answer + the expected revision)

        Step 3: Two-person review
               (one expert labels + another samples 20% to double-check)

        Step 4: Lock and version (golden_v1)

        Step 5: Monthly increment
               (problematic prod cases → adversarial set)
```

**Key insight**: business experts don't write answers — they **review answers and define the acceptance criteria**.

---

## C.8 Eval Set Lifecycle Management

```
  An eval set is not "build once and shelve" — it is a living artifact.

  Rules:
    - Add 20-50 cases per month (from prod / bugs / new requirements)
    - Audit quarterly (any stale cases / wrong answers?)
    - Never delete seed cases (unless that business is decommissioned)
    - Major version bump → new collection; archive the old one as a baseline
```

---

## C.9 An Eval Checklist

Pre-release verification:

```
  □ Every seed case passes
  □ Golden set primary metrics ≥ thresholds
  □ Adversarial counter-examples are rejected at least 90% of the time
  □ Cost metrics ≤ budget
  □ Latency metrics ≤ SLO
  □ All slices (senior / junior / high-value / low-value customers) pass
  □ No regressions vs the previous release
```

---

[← Previous appendix: Comparison Matrix](appendix-b.md) · [Next appendix: Customer Onboarding Pack →](appendix-d.md)
