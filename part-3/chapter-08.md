---
title: "第 8 章 评估先于代码"
parent: "Part III — 技术选型"
nav_order: 3
---

# Chapter 8: 先 Eval 再开发 — 实操指南

## 开场

```
PoC 第 5 周。FDE 在客户现场。

客户业务负责人："上周演示挺好的，但今天这个 demo 怎么答得不一样？"

FDE 翻 prompt commit 历史：周二改了 system prompt。
看 trace：上周对的那条今天答错了。

客户："你们平时不测试吗？"

FDE 沉默。

第二天他做了一件正确的事：
  把 200 条 Eval 集接进 CI，
  每个 PR 必须跑分，
  分数低于上周不能 merge。

从那以后，演示前一晚再也不慌了 ——
分数昨晚已经跑过了，今天客户问什么他都心里有底。

这一章讲：怎么把 Eval-driven 铁律
落成"日常工程纪律"而不只是口号。
```

---

## 8.1 Eval-Driven Development 的工程定义

```
        TDD (Test-Driven Development)         EDD (Eval-Driven Development)
        ────────────────────────────         ────────────────────────────

  写测试       先写 unit test               先写 Eval 样本
  跑测试       每个 commit 跑               每个 PR 跑（成本考量）
  失败处理      代码 fix                     prompt / RAG / 模型 fix
  覆盖率        line coverage                场景 coverage
  通过条件      二元（pass/fail）            阈值（score >= X）
  失败可重现    确定性                        概率性（要采样）
```

EDD 的特点 —— **概率性**：
- 同一个 input，不同时间跑可能不同 output
- 必须**多次采样取分布**，不是单次跑分
- "通过"不是 100%，是"达到约定阈值"

---

## 8.2 Eval 集的"金字塔结构"

```
                    └──── Production ────┘
                          (线上抽样回流)
                              ↑
                    ┌─── Adversarial ────┐
                    │   边角 / 攻击 / 越界 │  ~50 条
                    └────────────────────┘
                              ↑
                    ┌──── Golden Set ────┐
                    │   人工标准答案     │  100-300 条
                    └────────────────────┘
                              ↑
                    ┌────── Seed ────────┐
                    │   Discovery 收的   │  50 条
                    └────────────────────┘
```

四层各有用途：

```
  Seed:         快速 baseline（不用每次跑全集）
  Golden Set:   主力 Eval，每个 PR 跑
  Adversarial:  上线前必跑，回归用
  Production:   生产采样回流，发现新失败模式
```

**比例参考**：50 + 200 + 50 + 持续增长 ≈ 起步够了。

---

## 8.3 Eval 集的三种 metric 实操

### Metric 1: 规则打分（最便宜）

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

适用场景：必有词 / 黑名单 / 结构化输出 / 数字精确性。

### Metric 2: 语义相似度（中等成本）

```python
# metrics_semantic.py
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('BAAI/bge-m3')

def semantic_similarity(answer: str, reference: str) -> float:
    e1 = model.encode(answer)
    e2 = model.encode(reference)
    return cosine_similarity(e1, e2)
```

适用场景：开放问答的相关性。

**注意**：阈值 0.7 不绝对。每个项目自己校准 —— 拿 50 条人工标"对/错"的样本算 best-threshold。

### Metric 3: LLM-as-judge（最贵）

```python
# metrics_judge.py
JUDGE_PROMPT = """
你是一个评估专家。请判断下面"实际回答"是否符合"期望回答"的标准。

问题: {question}
期望回答: {reference}
实际回答: {actual}

打分 1-5：
1: 完全不符合
2: 部分相关但有重大错误
3: 大体正确但有小问题
4: 正确但表达可改进
5: 完美

只输出一个数字。
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

**坑**：

```
❌ 用被评估的同一个模型当 judge → 同源偏置
✅ 用更强的模型当 judge（如 Claude Opus 评 Sonnet）

❌ 单次跑就当结论 → 概率性导致波动
✅ 同一条样本采样 3-5 次取平均

❌ Judge prompt 太松 → 4-5 分泛滥
✅ 给 judge 看 1-2 个反例校准
```

### 三种合成

```
total_score = 0.3 * rule_score
            + 0.3 * semantic_score
            + 0.4 * judge_score
```

权重根据项目调，不是死的。

---

## 8.4 把 Eval 集接进 CI — 实操

### 文件结构

```
my-llm-app/
├── src/
│   ├── prompt.py          # prompt 模板
│   ├── retriever.py       # RAG 检索
│   └── ...
├── evals/
│   ├── golden_v0.2.jsonl  # 200 条
│   ├── adversarial.jsonl  # 50 条
│   ├── metrics.py         # 评分函数
│   ├── runner.py          # 跑批
│   └── reports/           # 历史快照
├── .github/
│   └── workflows/
│       └── eval.yml       # CI 配置
└── eval_threshold.toml    # 阈值配置
```

### `eval_threshold.toml` 长这样

```toml
[golden_v0.2]
total_score = 0.85
top20_keywords = 0.95
p95_latency_ms = 3000

[adversarial]
safety_score = 1.0  # PII / 越权 100% 拦
refusal_rate = 1.0  # 应该拒答的全部拒答
```

### CI 跑分（GitHub Actions 例）

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

**关键点**：

- PR 改 prompt / 改 retriever 都触发
- 不达标 → block merge
- PR 评论里直接看分数和 diff

### AWS 实操：用 Bedrock Evaluations 做 PR 守门员

```
        CI 集成 Bedrock Evaluations
        ─────────────────────────────────────

  Step 1: 把 Eval 数据集存到 S3
          s3://my-bucket/evals/golden_v0.2.jsonl

  Step 2: PR 触发 → CI 调用 Bedrock CreateEvaluationJob API
          (Python boto3)

  Step 3: poll job 状态（轮询或 EventBridge）

  Step 4: 拿 result S3 path，读 metrics

  Step 5: 比较 baseline，输出报告，决定 merge

  好处:
    - 不用自己维护评测基础设施
    - LLM-as-judge 直接用 Bedrock built-in
    - 大数据量（>500）也能跑
```

最小代码骨架：

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

> **AWS 知识参考**：搜 "Bedrock CreateEvaluationJob API" 与 "Bedrock evaluation built-in metrics"。

---

## 8.5 跑分的"分布"思维

LLM 评估有概率性。**单次跑分不是结论**。

### 必做的 3 件事

```
1. 同一条样本跑 N 次（N=3-5）
   取平均 + 方差 + 最差值

2. 看分布而不是均值
   均值 0.85 但 P10 是 0.3 → 危险（有 10% 用户体验极差）

3. 关注 regression
   不是只看"分数 ≥ 阈值"，
   还要看"和上一版相比，哪些样本掉分了"
```

### 一份好的 Eval 报告长这样

```
══════════════════════════════════════════════════════════
Eval Report — golden_v0.2
PR: #1234 (改 retriever 召回 top_k 5→8)
日期: 2026-05-22

总分: 0.872 ↑ +0.012 vs main (0.860)
通过: ✅ (阈值 0.85)
─────────────────────────────────────────────────────────
分维度:
  keyword_recall:   0.91 ↑ (+0.03)
  semantic_sim:     0.78 → (=)
  llm_judge:        0.86 ↓ (-0.02)
─────────────────────────────────────────────────────────
分类:
  high_freq (top 20):  0.95 ↑
  long_tail:           0.82 →
  adversarial:         0.99 →
─────────────────────────────────────────────────────────
Regression (掉分 > 0.1):
  eval-013: 0.85 → 0.42 (semantic_sim)
    问题: "重疾险等待期" 召回带回了寿险条款
    建议: rerank or 加 metadata filter

  eval-047: 0.78 → 0.55 (llm_judge)
    问题: 答案变长，judge 觉得"重点不突出"
    建议: prompt 里加"用 3 句话以内回答"
─────────────────────────────────────────────────────────
P95 latency: 2.4s ↑ (+0.3s, top_k 增加导致)
Cost / query: $0.0021 ↑ (+12%)
══════════════════════════════════════════════════════════
```

**FDE 看 Eval 报告应该比看代码 diff 还多**。

---

## 8.6 生产采样回流 — 闭环

```
        生产 → Eval 集的回流闭环
        ─────────────────────────────────

  线上请求
      ↓
  Logging (CloudWatch / LangFuse)
      ↓
  采样规则:
    - 1% 随机采样
    - 100% 用户点踩样本
    - 100% 模型 confidence 低样本
    - 100% 失败 / 超时样本
      ↓
  人工 / LLM 二次审核
      ↓
  补到 Adversarial / Golden Set
      ↓
  下个 PR 的 Eval 集自动覆盖到这些新样本
```

**没有这个闭环 → Eval 集会过时 → Eval 跑分高但生产掉链子**。

---

## 8.7 Eval 集的反模式

```
❌ Eval 集 = 训练集 / Few-shot 例子
   → 数据泄露，分数虚高

❌ 100% 都是"应该回答对"的样本
   → 模型学会"什么都答"，不会拒答

❌ Eval 集只有 FDE 写
   → 业务专家不认 = 客户验收时发现"对的题客户不要"

❌ 阈值定 100%
   → 永远过不了线 = 失去 Eval 的意义

❌ 阈值不动 6 个月
   → 业务在变，Eval 阈值要跟着调

❌ Eval 跑分昂贵就只在上线前跑
   → 退化成"验收测试"，失去开发约束作用
```

---

## 关键引用

> "*If you don't have an eval set, you don't have a system — you have a hope.*"
> — Anonymous FDE, *The FDE Playbook*, 2025

> "*Looking at evals is more important than looking at the model output.*"
> — Anthropic internal best practice, 2025

> "*Eval is a discipline, not a deliverable.*"
> — AWS GenAI Innovation Center, 2025

---

## 动手清单

接到新项目第 3 周必做：

1. **建 evals/ 目录**：jsonl 样本 + metrics.py + runner.py
2. **接 CI**：PR 必跑 Eval（先跑 50 条 seed，回归通过 5 分钟内）
3. **写 eval_threshold.toml**：明确阈值
4. **接 LLM-as-judge**（用 Bedrock 内置或 Claude Opus）
5. **生产 logging 接好**（一开始就要，不要事后补）
6. **每周一开始 review Eval 报告**：看 regression 和分布
7. **每月扩 Eval 集 +20-50 条**（来自生产采样）

---

## 反模式清单

- ❌ **Eval 等到上线前才补**（违反 Eval-driven 铁律）
- ❌ **Eval 跑分只看均值**（忽视长尾用户体验）
- ❌ **Eval 报告只发给 FDE**（应该客户、业务、老板都看）
- ❌ **不接生产采样回流**（Eval 集会越来越脱离生产）
- ❌ **每次模型升级不跑 Eval**（升级带的回归是最危险的）
- ❌ **Eval 失败就降阈值**（应该 fix 模型 / prompt 让分数回来）

---

## 与下一 Part 的关系

到这里 LLM 应用主线的 Scaffolding 阶段闭环：你有了**模型 + 框架 + Eval 守门员**。

下一 Part 切到**数据驱动主线**（也是 LLM 主线绕不开的部分）—— 客户的真实数据栈、VPC / 私有部署、和遗留系统的集成。这是 Palantir / AWS GenAIIC 风格 FDE 的主战场。

[← 上一章: 决策树](chapter-07.md) · [下一 Part: 数据与集成 →](../part-4/intro.md)
