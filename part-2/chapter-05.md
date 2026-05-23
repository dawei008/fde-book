---
title: "第 5 章 从需求到 SOW 与评估集"
parent: "Part II — 客户发现"
nav_order: 2
---

# Chapter 5: 从需求到验收 — 评估集 / 验收标准 / SOW

## 开场

```
Discovery 跑完两周，FDE 拿到三样东西：

  1. 一份 3 页 Discovery 报告（Ch 4 模板）
  2. 一句话的真实问题 + 一个 outcome 数字
  3. 50 条客户工单种子样本

她的老板问："好，下周可以开始写代码吗？"

她回答："还差三件物料 ——
        Eval 集 v0.1（把 outcome 翻译成可自动跑的考试卷）
        验收标准（客户和我们对'过线'的统一定义）
        SOW（把 12 周边界写死，避免范围蠕变）

        没有这三样，下周写代码就是凭信仰。"

她老板沉默 3 秒，说："那你这周加班把这三样写完。"

她说："这三样不是加班一周的工作 ——
       是我接下来 5 个工作日的全部工作。"

这一章讲：怎么把 Discovery 翻译成
       Eval 集 + 验收标准 + SOW 这三个工程合同物。
```

---

## 5.1 三个合同物的关系

```
            Discovery 报告
                  ↓
        ┌─────────┼─────────┐
        ↓         ↓         ↓
      Eval 集   验收标准    SOW
      (技术)    (业务)     (商务)
        │         │         │
        └────────▼─────────┘
              三者一致
                  ↓
              开工写代码
```

三者是**同一件事的三种语言**：

- **Eval 集**：工程师能跑的语言（输入 / 期望输出 / 通过条件）
- **验收标准**：客户能签字的语言（数字 + 时间 + 边界）
- **SOW**：法务能盖章的语言（范围 / 责任 / 付款 / 退出）

**三者不一致 = 项目内部对"成功"的定义不一致 = 后期一定有撕扯**。

---

## 5.2 Eval 集 v0.1 — 工程师的考试卷

### 为什么要有 Eval 集

回到铁律 3：没有 Eval 的 LLM 项目都是信仰项目。

Eval 集的作用：

1. **开发期间**：每个 PR 自动跑分，回归用
2. **上线前**：客户 sign-off 的"过线分数"
3. **上线后**：模型升级 / 数据漂移的早期预警
4. **Handoff 后**：客户自己能跑，不用依赖你

### Eval 集 v0.1 的最小结构

```
evals/
├── README.md                  # 怎么跑、怎么读结果
├── seed_samples.jsonl         # 50 条种子样本（来自 Discovery）
├── golden_set.jsonl           # 100 条带标准答案（人工标注）
├── adversarial.jsonl          # 30 条边角 / 攻击 / 异常输入
├── metrics.py                 # 评分函数（关键词、相似度、LLM-as-judge）
├── runner.py                  # 跑批入口
└── reports/                   # 历史跑分快照
```

### 一条 Eval 样本长什么样

以一个**保单条款问答**项目为例：

```json
{
  "id": "eval-007",
  "category": "重疾险-等待期",
  "input": {
    "user_question": "我刚买的重疾险，2 周后体检发现甲状腺结节，能赔吗？",
    "context_hint": "投保人的保单号：P-2024-XXX-001"
  },
  "expected": {
    "must_contain_keywords": ["等待期", "90 天", "180 天", "确诊时间"],
    "must_not_contain": ["不能赔", "肯定赔"],
    "min_relevance_score": 0.8,
    "reference_answer": "重疾险一般有 90-180 天等待期，等待期内确诊的疾病保险公司有权拒赔。具体以您的保单为准 ——"
  },
  "metadata": {
    "source": "客服工单 #2024-1042",
    "annotator": "李某（业务专家）",
    "difficulty": "medium",
    "weight": 1.0
  }
}
```

**关键设计点**：

- 不是只有 input/output —— 一条样本要带分类、来源、难度、权重
- 不是只有"标准答案" —— 关键词命中 + 不能出现的词 + 参考答案三层
- 不是一个分数 —— 多个 metric（关键词召回 / 语义相关性 / 安全性）合成

### 评分函数三种打法

```
┌──────────────────────────────────────────────────────────┐
│ 1. 规则打分（最便宜，最稳）                              │
│    - 关键词命中 / 黑名单未命中 / JSON Schema 校验         │
│    - 适合：必有/必无的硬约束                              │
│    - 不适合：自然语言流畅度、风格                         │
├──────────────────────────────────────────────────────────┤
│ 2. 语义相似度（中等成本）                                │
│    - cosine(embedding(answer), embedding(reference))     │
│    - 适合：开放问答的相关性检验                           │
│    - 不适合：精确数字、列表完整性                         │
├──────────────────────────────────────────────────────────┤
│ 3. LLM-as-judge（最贵，最灵活）                          │
│    - 用 GPT-4 / Claude / Bedrock 判断答案对不对           │
│    - 适合：风格、复杂判断、多维度打分                     │
│    - 不适合：被 judge 的模型自己当 judge（同源偏置）      │
└──────────────────────────────────────────────────────────┘
```

**实操建议**：三层都用，权重不同。规则 30% + 相似度 30% + LLM-as-judge 40%。

### AWS 实操：用 Bedrock Evaluations 跑 Eval

如果你的应用跑在 AWS 上（Bedrock + Knowledge Bases + Agents），可以直接用 **Amazon Bedrock Evaluations** 在控制台 / API 里建 Eval job：

```
        Bedrock Evaluations 三种 Job 类型
        ─────────────────────────────────────────────

  1. Model Evaluation
     评估单个基础模型的输出（不带 RAG / Agent）
     → 用于选模型（Claude vs Llama vs Titan）

  2. Knowledge Base Evaluation
     评估 RAG 系统的"召回质量 + 生成质量"
     → 自动计算 Context Relevance / Answer Faithfulness

  3. Agent Evaluation
     评估 Agent 多步推理路径的正确性
     → 关键指标：步骤数、工具调用准确率、最终输出
```

最小可跑的 Bedrock Eval 流程：

```
Step 1: 把 jsonl 数据集传到 S3
        s3://my-bucket/evals/insurance-qa-v01.jsonl

Step 2: 在 Bedrock 控制台创建 Evaluation Job
        - 选 evaluation type（Model / KB / Agent）
        - 选 evaluator（Built-in / LLM-as-judge / Human）
        - 选 metrics（Accuracy / Robustness / Toxicity / 自定义）

Step 3: Job 跑完后看 Report
        - 总分 + 分维度分数
        - 失败样本列表（CSV 下载）
        - Trace 链路（Agent / KB 用得上）

Step 4: 把 Report 接入你的 CI
        - Bedrock Eval API 在 PR 触发时跑
        - 不过线 → block merge
```

> **AWS 知识参考**：在 docs.aws.amazon.com 搜 "Amazon Bedrock evaluation jobs" 与 "Knowledge Base evaluation"。Evaluations 入口：Bedrock console → Inference and Assessment → Evaluations。

### 反例：Eval 集做错的常见姿势

```
❌ 用培训数据当 Eval 集
   → 模型记住了答案，分数虚高

❌ 全是"客户最爱问的"问题
   → 缺边角，上线后被边角问题打爆

❌ 只有"成功样本"，没有"应该拒答"的样本
   → 模型乱答 PII / 越权问题

❌ 一条样本一个分数
   → 没法定位是召回错还是生成错

❌ Eval 集只在客户 demo 前跑一次
   → 失去了"开发约束"的意义
```

---

## 5.3 验收标准 — 客户的签字栏

### 验收标准 = "数字 + 时间 + 边界"

不能含糊。要写得让法务能用、客户能签、工程能验。

### 一个反例和一个正例

❌ **含糊版**（90% 的合同长这样）：

```
"系统应能准确回答客户的保单咨询问题，
 准确率应达到行业领先水平。"
```

→ 没法验：什么叫准确？什么叫领先？谁判？

✅ **可验版**：

```
验收标准 v1.0
────────────────────────────────────────────────────────

环境：客户 staging（与生产同等数据，匿名化处理）
评估集：v0.1 共 200 条（客户业务专家共同标注）

通过条件（同时满足）：
  1. 整体准确率 ≥ 85%（关键词召回 + 语义相关 + LLM-judge 综合）
  2. 高频问题（top 20 问题）准确率 ≥ 95%
  3. 安全性指标：拒答 PII / 越权问题 100%
  4. 性能：P95 响应时间 ≤ 3 秒
  5. 持续 7 天无人工干预、自动跑分稳定

不达标的处理：
  - 单项不达标 → 修复后重跑
  - 整体不达标 → 双方协商：延期 OR 砍范围

验收节点：
  - Day 60：中期检查（达成 70% 即可）
  - Day 84：正式验收

验收负责人：
  - 客户方：[业务总监姓名] + [IT 总监姓名]
  - 我方：[FDE 姓名] + [Tech Lead 姓名]
```

**验收标准的 5 个必有要素**：

| 要素 | 含义 |
|---|---|
| 数字 | 一个或多个具体阈值（accuracy ≥ X%、P95 latency ≤ Y ms） |
| 时间 | 评估窗口、稳定时长、验收日期 |
| 集合 | 在哪个数据集上算（评估集 v0.X） |
| 环境 | 在哪个环境跑（dev / staging / prod 影子流量） |
| 不达标处理 | 谁有权延期、谁有权砍范围 |

---

## 5.4 SOW — 商务的合同物

SOW (Statement of Work) 是把 outcome / 验收标准 / 时间 / 钱写成法律文件。

**FDE 不需要写所有条款**，但**必须写其中 4 段**，否则后面会被范围蠕变拖死：

### 必须由 FDE 起草的 4 段

#### 1. Scope (做什么 / 不做什么)

```
Scope (in)：
  - 保单条款 RAG 问答（v0.1 评估集 200 条覆盖范围内）
  - 客户经理 Web 端调用（OpenAPI v1）
  - CloudWatch 监控接入
  - 一次 Handoff 培训（4 小时）

Scope (out)：
  - 移动端集成（客户自行做）
  - 多语言支持（仅中文）
  - 投保前的销售话术（不在范围内）
  - 历史数据迁移（客户自行准备数据）
```

**Scope (out) 比 Scope (in) 还重要**。

#### 2. Deliverables (交付物清单)

```
D1: Discovery 报告 (Week 2)
D2: Eval 集 v0.1 (Week 3)
D3: 可演示 Demo + 评估报告 (Week 6)
D4: 生产部署 + 监控仪表盘 (Week 10)
D5: Runbook + Eval v1.0 + 4 小时培训 (Week 12)
```

每个交付物都要有**接收人 + 接收方式 + 接收标准**。

#### 3. Acceptance Criteria (验收标准 — 直接复用 5.3 的)

#### 4. Change Management (变更管理)

```
变更触发条件：
  - 客户提出新需求 → 走变更流程
  - 客户业务方向变化 → 走变更流程

变更流程：
  Step 1: 客户提变更请求（书面）
  Step 2: FDE 评估变更对范围 / 时间 / 预算的影响
  Step 3: 双方在 5 个工作日内决定
        Option A: 接受变更 → 修订 SOW + 调整时间表 + 调整预算
        Option B: 推迟到 Phase 2
        Option C: 不做

无变更流程的口头需求 → 不进入 backlog
```

**没有变更流程 = 客户每周都给你新需求 = 项目永远不结束**。

### 一个真实反例

> *某 FDE 接了一个 12 周的项目，SOW 里写了 "AI 助手帮助销售提高效率"。第 4 周客户加了"也帮采购部用一下"，FDE 没拒绝。第 8 周采购部说"我们要的不是这个"，要重做。第 12 周到了交付不了。*
>
> *复盘发现：原始 SOW 没写 Scope (out)，没写变更流程。"销售" 和 "采购" 是两个工作流，本来不该混。*

**这是 FDE 项目失败模式 #1**：Scope 没写死。

---

## 5.5 三者怎么互相校验

写完 Eval 集 + 验收标准 + SOW，做一次**三向对照**：

```
        ┌────────────────────────────────────────┐
        │  问题                                  │
        ├────────────────────────────────────────┤
        │  1. Eval 集里的 metric 在验收标准里有吗？│
        │     —— 没有就加                        │
        │                                        │
        │  2. 验收标准的"过线分数"能用 Eval 集    │
        │     算出来吗？                         │
        │     —— 不能就改 metric                  │
        │                                        │
        │  3. SOW 的 Deliverables 每一项都有     │
        │     验收标准吗？                       │
        │     —— 没有就补                         │
        │                                        │
        │  4. SOW 的 Scope (out) 在 Eval 集里    │
        │     真的没出现吗？                     │
        │     —— 出现就移除                       │
        │                                        │
        │  5. SOW 的变更条款能 cover Eval 集     │
        │     更新吗？                           │
        │     —— 不能就补                         │
        └────────────────────────────────────────┘
```

跑完这 5 个对照，你的项目地基才算稳。

---

## 5.6 一个完整的小例子（端到端）

把第 4 章的 Discovery 报告 + 这一章的三个合同物串起来：

```
─── Discovery 输出 ───────────────────────────────────────

真实问题：
  客户经理找一份保单条款的中位时间是 4 分 30 秒，
  每月发生 1.2 万次。

期望 outcome：
  3 个月内中位时间降到 30 秒以内。

种子样本：
  客服工单导出 1000 条 → 业务专家筛 50 条 representative。

─── Eval 集 v0.1 ─────────────────────────────────────────

数据集：seed_samples (50) + golden_set (150) = 200 条
metrics:
  - keyword_recall (规则)
  - semantic_similarity (cosine, 0.7+)
  - llm_judge_accuracy (Bedrock Claude)
评分公式: 0.3 * keyword + 0.3 * sim + 0.4 * judge
通过分: 0.85

─── 验收标准 ─────────────────────────────────────────────

环境: 客户 staging（脱敏数据）
通过条件:
  1. Eval 总分 ≥ 0.85
  2. Top 20 高频问题分 ≥ 0.95
  3. P95 latency ≤ 3s
  4. 中位时间从 4:30 降到 ≤ 30s（实际样本统计）
  5. 7 天稳定无人工干预
验收日: 第 84 天

─── SOW 关键段落 ─────────────────────────────────────────

Scope (in):
  - 保单条款 RAG (中文)
  - Web 端 OpenAPI
  - CloudWatch 监控
  - 4 小时 Handoff 培训

Scope (out):
  - 移动端 / 多语言 / 销售话术 / 数据迁移

Deliverables:
  D1 Discovery 报告 (W2)
  D2 Eval v0.1 (W3)
  D3 Demo (W6)
  D4 生产部署 (W10)
  D5 Runbook + Eval v1.0 + 培训 (W12)

变更流程:
  书面 → FDE 5 工作日评估 → 修订 SOW

总预算: ¥XX
首付/中付/尾付: 30/40/30
```

**这一套合同物 + Discovery 报告 = 你接下来 12 周的工作图纸**。

---

## 关键引用

> "*If you can't write the eval set, you don't understand the problem yet.*"
> — Conikeec, *The FDE Playbook*, 2025

> "*Scope creep is not a customer problem; it's a contract problem.*"
> — A. Lawrence, *FDE Rule Book*, 2025

> "*Acceptance criteria is the only piece of the contract the engineer must own.*"
> — AWS GenAI Innovation Center, internal training, 2025

---

## 动手清单

跑完 Discovery 之后，第 3 周必做的 7 件事：

1. **从 50 条种子扩到 200 条**（业务专家共同标注）
2. **写 metrics.py**（至少 3 种打分：关键词 / 相似度 / LLM-judge）
3. **写 runner.py 跑通一次 baseline**（无优化版本作为下限）
4. **起草验收标准 v1.0**（5 个必有要素）
5. **起草 SOW 的 4 段**（Scope / Deliverables / Acceptance / Change）
6. **5 项三向对照**（5.5 节）
7. **客户业务方 + 客户 IT 方 + 你公司商务方三方过会签字**

---

## 反模式清单

- ❌ **Eval 集留到上线前才补**（违反 Eval-driven 铁律）
- ❌ **验收标准写"行业领先水平"等无法度量的话**（无法验 = 无法过）
- ❌ **SOW 没写 Scope (out)**（范围蠕变 #1 来源）
- ❌ **没写变更流程**（客户每周加需求，永远做不完）
- ❌ **Eval 集 = 训练集**（数据泄露，分数虚高）
- ❌ **三者不一致就开工**（项目内部对"成功"定义不同 = 后期撕扯）
- ❌ **Eval 集只让 FDE 标注**（没有业务专家校准 = 模型对了客户也不认）

---

## 与下一 Part 的关系

到这里 Discovery 阶段彻底闭环：你有了**真实问题 + outcome 数字 + 50 条种子 + 200 条 Eval 集 + 验收标准 + SOW**。

下一 Part 进入 **Scaffolding（脚手架）阶段**。从 Week 3 开始，FDE 用 6 周时间搭出**第一个能演示、能跑分、能让客户摸到形状**的最小闭环。第 6 章先讲：**LLM 应用的整体技术栈** —— 你应该用什么模型、什么框架、什么部署形态、为什么。

[← 上一章: Discovery](chapter-04.md) · [下一 Part: 脚手架 →](../part-3/intro.md)
