---
title: "appendix/appendix-c.md"
nav_exclude: true
search_exclude: false
---

# Appendix C: Eval Set Design Templates

> Eval templates for the four most common LLM task types:
> 1. RAG question answering
> 2. Agent task execution
> 3. Text classification
> 4. Structured information extraction
>
> Each template includes a jsonl schema, field semantics, sampling strategy, evaluation method, and CI example.

---

## C.1 Common Design Principles

```
  Four tiers of Eval sets
        ──────────────────────────────────

  Seed Set       (5-20 cases)   handwritten, ultra-fast regression, never edited
  Golden Set     (100-300)      annotated by customer SMEs, the acceptance baseline
  Adversarial    (50-150)       counterexamples / edge cases / privilege escalation
  Production     (streaming)    sampled from prod → re-injected weekly
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

**Why jsonl rather than csv**: nested fields, multi-line text, and long prompts are common — csv escaping turns into a nightmare.

---

## C.2 Template 1: RAG QA Eval

### Schema

```jsonl
{
  "id": "rag-001",
  "category": "policy_lookup",
  "input": {
    "question": "Does the customer's health insurance include hospitalization allowance? Policy number P20240315-001"
  },
  "expected": {
    "must_contain_keywords": ["hospitalization allowance", "200 RMB/day", "30 days"],
    "must_not_contain": ["excluded", "not covered"],
    "reference_doc_id": "POL-HC-002-v3.pdf",
    "reference_section": "Chapter 3, Clause 2",
    "reference_answer": "Includes hospitalization allowance at 200 RMB per day, up to 30 days."
  },
  "metadata": {
    "source": "Customer SME 2026-05",
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

    # 2. Was the retrieval source correct? (the most common RAG failure)
    score['retrieval_correct'] = (
        case['expected']['reference_doc_id']
        in [d['doc_id'] for d in system_output['retrieved_docs']]
    )

    # 3. Semantic similarity (embedding cosine)
    score['semantic_sim'] = cosine(
        embed(case['expected']['reference_answer']),
        embed(system_output['answer'])
    )

    # 4. LLM-as-judge (most expensive — reserve for key cases)
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
    - The 5 most frequent questions (the ones the business asks most)
    - 5 explicit counterexamples (the ones we must never get wrong)

  Golden Set 200 cases — split like this:
    - 60% mainstream questions (high-frequency cases the SME named)
    - 20% edge cases (cross-policy / multi-insured / historical policies)
    - 10% long-tail rare questions
    - 10% counterexamples (out-of-scope / PII / things we should refuse)

  Adversarial 50 cases:
    - Rephrasing / typos / synonym swaps
    - Prompt injection
    - Cross-domain (asking about another insurer)
```

### CI thresholds

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
    "user_message": "I want to claim last week's outpatient medication expenses, 580 RMB",
    "context": {
      "customer_id": "C123",
      "policy_id": "P-OPD-001"
    }
  },
  "expected": {
    "task_completed": true,
    "tool_calls": [
      {"tool": "get_policy", "params_must_include": ["P-OPD-001"]},
      {"tool": "validate_amount", "params_must_include": [580]},
      {"tool": "create_settlement", "must_appear": true}
    ],
    "tool_calls_must_not": ["transfer_funds"],
    "final_state": {
      "claim_status": "approved",
      "approved_amount": 580
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

  2. Path soundness
     Do tool_calls satisfy the "must / must-not" constraints?
     Is the step count ≤ max_steps?

  3. Tool-call correctness
     Are the parameters of each tool call right?

  4. Side effects
     Did it call any tool on the must-not list?
     Did it cause any external state pollution?

  5. Cost
     Total tokens / dollars ≤ max_cost_usd?
```

### Python evaluator

```python
def evaluate_agent(case, trace):
    """trace is the agent's full execution trajectory"""
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
  Golden 100 cases — split like this:
    - 40% standard cases (simple cases the agent should auto-complete)
    - 30% HITL cases (where escalation is the correct outcome)
    - 15% abnormal inputs (missing fields / ambiguous reference)
    - 15% counterexamples (out-of-scope / injection / adversarial)
```

---

## C.4 Template 3: Classification / Routing Eval

### Schema

```jsonl
{
  "id": "intent-001",
  "category": "core_intents",
  "input": {
    "user_message": "My car was in an accident — what do I do?"
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

### Metrics

```python
# Multi-class classification
from sklearn.metrics import classification_report, confusion_matrix

y_true = [c['expected']['intent'] for c in cases]
y_pred = [run_classifier(c['input']) for c in cases]

print(classification_report(y_true, y_pred))
print(confusion_matrix(y_true, y_pred))

# CI thresholds: macro F1 ≥ 0.85, per-class recall ≥ 0.80
```

### Key sampling

```
  - At least 30 cases per intent (upsample if imbalanced)
  - Confusion classes with asymmetric business cost get tagged separately
    e.g. claim_intake misclassified as general_query → poor customer experience
         general_query misclassified as claim_intake → wasted human effort
         The first is more costly; test it heavily.
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
    "currency": "CNY",
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
            # nested, recurse
            ...
    return score

# Total = weighted average across critical fields
weights = {
    'invoice_no': 1.0,
    'total_amount': 1.0,    # critical — numbers must be exact
    'currency': 0.5,
    'issue_date': 0.8,
    'vendor.name': 0.6,
    'vendor.tax_id': 1.0    # compliance-critical
}
```

---

## C.6 A Full Eval Project Layout

```
project/
├── eval/
│   ├── datasets/
│   │   ├── seed.jsonl              (10 cases, version-locked)
│   │   ├── golden_v1.jsonl         (200 cases, SME-labeled)
│   │   ├── golden_v2.jsonl         (250 cases, follow-on additions)
│   │   ├── adversarial.jsonl       (50 cases)
│   │   └── prod_sampled_2026w20.jsonl  (weekly re-injection)
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

## C.7 Annotation Workflow — Getting Customer SMEs to Work Efficiently

```
        Step 1: FDE prepares 100 seed questions
               (drawn from customer docs / historical tickets / support logs)

        Step 2: SMEs annotate in Streamlit / Excel
               (UI shows the question + your draft answer + their revisions)

        Step 3: Two-person review
               (one SME labels + a second one re-checks 20%)

        Step 4: Commit + version-lock (golden_v1)

        Step 5: Monthly increments
               (production cases that went wrong → adversarial set)
```

**Key**: SMEs are not writing answers. They are **proofreading answers and codifying the judgment criteria**.

---

## C.8 Eval Set Lifecycle Management

```
  An Eval set is not "build once and shelve it" — it's alive.

  Rules:
    - Add 20-50 new cases per month (from prod / bugs / new requirements)
    - Quarterly audit (any stale cases / wrong answers?)
    - Never delete the seed (unless that line of business is retired)
    - Major version upgrade → new set, keep old one as the baseline
```

---

## C.9 An Eval Checklist

Pre-release, must-check:

```
  □ Every seed case passes
  □ Golden set headline metric ≥ threshold
  □ Adversarial counterexamples refused at ≥ 90%
  □ Cost metric ≤ budget
  □ Latency metric ≤ SLO
  □ Slices (returning / new / high-value / low-value customers) all pass
  □ Compared to previous version → no regressions
```

---

[← Previous Appendix: Comparison Matrix](appendix-b.md) · [Next Appendix: Customer Kickoff Pack →](appendix-d.md)
