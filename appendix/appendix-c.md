---
title: "附录 C 评估集模板"
parent: "附录"
nav_order: 3
---

# 附录 C: 评估集设计模板

> 给 4 个最常见 LLM 任务类型的 Eval 模板：
> 1. RAG 问答
> 2. Agent 任务执行
> 3. 文本分类
> 4. 结构化信息抽取
>
> 每个模板包含 jsonl schema、字段含义、采样策略、评估方式、CI 例子。

---

## C.1 共通设计原则

```
  4 个层次的 Eval 集
        ──────────────────────────────────

  Seed Set       (5-20 条)    手工写, 极快回归, 永不动
  Golden Set     (100-300 条) 客户专家标注, 验收基线
  Adversarial    (50-150 条)  反例 / 边界 / 越权
  Production     (流式)        线上采样 → 周度回灌
```

**通用 schema 字段**:

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

**为什么是 jsonl 而不是 csv**：嵌套字段 / 多行文本 / 长 prompt 都常见，csv 转义噩梦。

---

## C.2 模板 1: RAG 问答 Eval

### Schema

```jsonl
{
  "id": "rag-001",
  "category": "policy_lookup",
  "input": {
    "question": "客户购买的健康险是否包含住院津贴？保单号 P20240315-001"
  },
  "expected": {
    "must_contain_keywords": ["住院津贴", "200元/天", "30天"],
    "must_not_contain": ["免责", "不包含"],
    "reference_doc_id": "POL-HC-002-v3.pdf",
    "reference_section": "第三章第2条",
    "reference_answer": "包含住院津贴，标准为每天 200 元，最长 30 天"
  },
  "metadata": {
    "source": "客户业务专家 2026-05",
    "difficulty": "medium"
  }
}
```

### 评估逻辑（Python 伪代码）

```python
def evaluate_rag(case, system_output):
    score = {}

    # 1. Hard rules — 关键词
    score['kw_match'] = all(
        kw in system_output['answer']
        for kw in case['expected']['must_contain_keywords']
    )
    score['no_forbidden'] = all(
        kw not in system_output['answer']
        for kw in case['expected']['must_not_contain']
    )

    # 2. 检索源对不对（最常见的 RAG 错）
    score['retrieval_correct'] = (
        case['expected']['reference_doc_id']
        in [d['doc_id'] for d in system_output['retrieved_docs']]
    )

    # 3. 语义相似度（embedding cosine）
    score['semantic_sim'] = cosine(
        embed(case['expected']['reference_answer']),
        embed(system_output['answer'])
    )

    # 4. LLM-as-judge（最贵，留给关键案例）
    if case['metadata']['difficulty'] == 'hard':
        score['llm_judge'] = call_judge(
            question=case['input']['question'],
            reference=case['expected']['reference_answer'],
            actual=system_output['answer']
        )

    return score
```

### 采样策略

```
  Seed Set:
    - 最高频 5 个问题 (业务最常问的)
    - 5 个明确反例 (绝不能答错的)

  Golden Set 200 条 = 这样配比:
    - 60% 主流问题 (业务专家说的高频 case)
    - 20% 边界情况 (跨保单 / 多保人 / 历史保单)
    - 10% 长尾稀有问题
    - 10% 反例 (越权问题 / PII 问题 / 不该回答的)

  Adversarial 50 条:
    - 改写 / 拼错 / 换术语
    - 注入 (prompt injection)
    - 跨域 (问别家保险公司)
```

### CI 阈值

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

## C.3 模板 2: Agent 任务执行 Eval

### Schema

```jsonl
{
  "id": "agent-claim-001",
  "category": "auto_settle_simple",
  "input": {
    "claim_id": "CLM-2026-001",
    "user_message": "我要报销上周的门诊医药费 580 元",
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

### 5 维评估

```
  1. 任务完成度
     final_state == expected.final_state ?

  2. 路径合理性
     tool_calls 是否满足"必须 / 不能"约束？
     步数是否 ≤ max_steps？

  3. 工具调用正确性
     每次工具的参数对不对？

  4. 副作用
     有没有调到 must_not 列表的工具？
     有没有产生外部状态污染？

  5. 成本
     总 token / 美元 ≤ max_cost_usd？
```

### Python 评估器

```python
def evaluate_agent(case, trace):
    """trace 是 agent 的完整执行轨迹"""
    tool_calls = trace['tool_calls']

    # 1. 任务完成
    task_done = trace['final_state'] == case['expected']['final_state']

    # 2. 工具序列
    must_tools = case['expected']['tool_calls']
    must_present = all(
        any(
            tc['tool'] == m['tool']
            and all(p in tc['params'] for p in m.get('params_must_include', []))
            for tc in tool_calls
        )
        for m in must_tools
    )

    # 3. 禁用工具
    forbidden_used = any(
        tc['tool'] in case['expected']['tool_calls_must_not']
        for tc in tool_calls
    )

    # 4. 步数 / 成本
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

### 采样策略

```
  Golden 100 条 = 这样配比:
    - 40% 标准用例 (能自动完成的简单 case)
    - 30% 需要 HITL 的 case (期待 escalate)
    - 15% 异常输入 (缺字段 / 模糊指代)
    - 15% 反例 (越权 / 注入 / 对抗)
```

---

## C.4 模板 3: 分类 / 路由 Eval

### Schema

```jsonl
{
  "id": "intent-001",
  "category": "core_intents",
  "input": {
    "user_message": "我的车出事故了，怎么办？"
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

### 评估指标

```python
# 多类别分类
from sklearn.metrics import classification_report, confusion_matrix

y_true = [c['expected']['intent'] for c in cases]
y_pred = [run_classifier(c['input']) for c in cases]

print(classification_report(y_true, y_pred))
print(confusion_matrix(y_true, y_pred))

# CI 阈值: macro F1 ≥ 0.85, 每类 recall ≥ 0.80
```

### 关键采样

```
  - 每个意图至少 30 条 (不平衡时上采样)
  - 业务上"代价非对称"的混淆类要单独标注
    例: claim_intake 误判为 general_query → 客户体验差
        general_query 误判为 claim_intake → 浪费人工
        前者代价高, 必须重点测
```

---

## C.5 模板 4: 结构化抽取 Eval

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
      "name": "ABC 商贸有限公司",
      "tax_id": "91110000XXXXXXXX"
    }
  },
  "metadata": {
    "difficulty": "medium",
    "image_quality": "good"
  }
}
```

### 字段级评估

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
            # 嵌套, 递归
            ...
    return score

# 总分 = 关键字段加权平均
weights = {
    'invoice_no': 1.0,
    'total_amount': 1.0,    # 关键，数字必须准
    'currency': 0.5,
    'issue_date': 0.8,
    'vendor.name': 0.6,
    'vendor.tax_id': 1.0    # 合规要点
}
```

---

## C.6 一个完整 Eval 项目结构

```
project/
├── eval/
│   ├── datasets/
│   │   ├── seed.jsonl              (10 条, 锁版)
│   │   ├── golden_v1.jsonl         (200 条, 业务专家标)
│   │   ├── golden_v2.jsonl         (250 条, 后续追加)
│   │   ├── adversarial.jsonl       (50 条)
│   │   └── prod_sampled_2026w20.jsonl  (周度回灌)
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

## C.7 标注流程 — 让客户业务专家高效干活

```
        Step 1: FDE 准备 100 个种子问题
               (从客户文档 / 历史工单 / 客服日志抽)

        Step 2: 业务专家在 Streamlit / Excel 上批
               (UI 上展示问题 + 你的初步答案 + 期待修改)

        Step 3: 双人 review
               (一个专家批 + 另一个抽 20% 复核)

        Step 4: 入库 + 锁版 (golden_v1)

        Step 5: 每月增量
               (出问题的线上 case → adversarial 集)
```

**关键**：业务专家不是写答案，是**校对答案 + 标判定标准**。

---

## C.8 Eval 集生命周期管理

```
  Eval 集不是"做完一次就放着"，而是活的。

  规则:
    - 每月新增 20-50 条 (来自线上 / bug / 新需求)
    - 每季度审计一次 (是否有过时 case / 错答案)
    - 永远不删 seed (除非该业务下线)
    - 大版本升级 → 新建集合, 旧集合保留为基线
```

---

## C.9 一份 Eval 检查清单

发布前必查：

```
  □ Seed 集每条都过
  □ Golden 集主指标 ≥ 阈值
  □ Adversarial 反例至少 90% 拒绝
  □ 成本指标 ≤ 预算
  □ 延迟指标 ≤ SLO
  □ 切片 (老人 / 新人 / 高价 / 低价 客户) 都过
  □ 与上一版本对比 → 没有回归
```

---

[← 上一附录: 对比矩阵](../appendix-b/) · [下一附录: 客户启动包 →](../appendix-d/)
