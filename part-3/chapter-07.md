# Chapter 7: 决策树 — RAG / Fine-tune / Prompting / Agent

## 开场

```
客户 CTO 说："我要做一个 AI 客服。"

新人 FDE 的反应：
  A) "好，我们做一个 RAG 把 FAQ 索引进来"
  B) "好，我们 fine-tune 一个模型在客户对话上"
  C) "好，我们用 GPT-4 + 多 Agent 协作"

老 FDE 的反应：
  "等一下 —— 您客服现在最大的痛点是什么？

   是回答不准（→ 可能 RAG）？
   还是答案对但太机械（→ 可能 prompting + few-shot）？
   还是要主动跨系统办事（→ 可能 Agent）？
   还是某个特定行业话术怎么都对不上（→ 可能 fine-tune）？

   不同痛点对应完全不同的解法，
   这一步选错，6 周白做。"

这一章的目标是：30 秒决定用哪个，10 分钟讲明白为什么。
```

---

## 7.1 四种解法的本质区别

```
              输入处理       知识来源        输出生成
              ─────────      ──────────      ──────────

  Prompting   原始 query     模型权重         模型直接生成
                            (训练时学到)

  RAG         query → 检索   外部知识库       检索 + 模型生成
                            (可更新)

  Fine-tune   原始 query     新权重           新模型生成
                            (你训出来的)

  Agent       query → 规划   工具调用结果     多步推理+综合
                            + 模型权重
                            + 知识库
```

简单理解：

- **Prompting** = "改提示词，模型自己懂"
- **RAG** = "把答案放进资料库，模型查"
- **Fine-tune** = "把答案教进模型脑子"
- **Agent** = "让模型自己用工具去办事"

---

## 7.2 主决策树

```
              客户的核心痛点
                    │
        ┌───────────┴───────────┐
        ↓                       ↓
    "答案不知道"             "答案知道但不对"
        │                       │
        ↓                       ↓
    需要外部知识？           风格 / 格式 / 行业话术问题？
        │                       │
        ├─是→ RAG               ├─是→ Prompting + Few-shot
        └─否→ Prompting         │     (90% 够用)
                                ↓
                            尝试无效？
                                │
                                ├─是→ Fine-tune
                                └─否→ 继续 Prompting

   "需要主动办事 / 跨系统"
        │
        ↓
    Agent (工具调用)
```

### 主路径解读

```
默认顺序：
  1. 先 Prompting（最便宜、最快）
  2. 不够 → RAG（加外部知识）
  3. 还不够 → Agent（让模型主动）
  4. 实在不行 → Fine-tune（最贵、最难维护）
```

**90% 的 LLM 应用，Prompting + RAG 已经够了**。Fine-tune 是最后的最后才考虑的方案。

---

## 7.3 RAG vs Fine-tune — 永恒的混淆

新手最容易搞错的是 RAG 和 Fine-tune 的边界。

```
                    RAG              Fine-tune
                    ─────────        ─────────

  解决什么            知识不在模型里    模型回答风格不对
                    数据频繁更新      术语 / 格式不规范
                    要可追溯引用      高频低复杂场景

  数据要求            文档（无标注）    高质量 Q&A 对
                    几百 - 几百万     几百 - 几万

  开发周期            1-2 周           4-8 周

  维护成本            更新文档即可      数据漂移要重新训

  可解释性            高（带引用）      低（黑盒）

  适合场景            知识库 / FAQ     垂直行业话术
                    动态业务规则      固定输出格式
                    合规要溯源        极致延迟（小模型）

  不适合场景          需要"风格"       数据频繁变
                    极高延迟要求      要溯源
                    微调更经济        预算紧
```

### 一个判断口诀

```
"事实 / 知识" 对错的问题      → RAG
"语气 / 风格 / 格式" 的问题   → Prompting → Fine-tune
"行动 / 跨系统" 的问题        → Agent
"延迟 / 成本" 的问题          → 模型选型 + 缓存（不一定改方法）
```

### 反例：误用 Fine-tune

> *某客户做"客服回答政策问题"。新人 FDE 直接 fine-tune 一个 7B 模型，3 周后上线。一个月后政策更新，模型答错被投诉。重新 fine-tune 又花 3 周。*
>
> *复盘：政策类问题 = 事实知识 = 应该用 RAG。RAG 改 KB 即可，不用重训。*

**FDE 失败模式**：把 RAG 问题当 Fine-tune 问题做。

---

## 7.4 RAG 内部的子决策

选定 RAG 之后，还有 4 个子决策：

### 子决策 1：分片粒度

```
        粒度选择
        ─────────────────────────────────

  按句子 (50-100 tokens)
    → 召回准但语境少
    → 适合：FAQ、短答案

  按段落 (200-500 tokens)
    → 平衡（最常用）
    → 适合：知识库、文档问答

  按章节 (1000-3000 tokens)
    → 上下文完整但召回模糊
    → 适合：法律、合同分析

  按文档 (整篇)
    → 用长上下文模型（Claude 200K）
    → 适合：少量大文档、合同审阅
```

### 子决策 2：检索策略

```
  纯向量检索 (semantic)
    → 优势: 语义理解强
    → 劣势: 关键词命中弱

  纯关键词检索 (BM25)
    → 优势: 精确匹配
    → 劣势: 语义弱

  混合检索 (Hybrid: semantic + BM25 + rerank)
    → 优势: 综合最强
    → 劣势: 复杂度高
    → 推荐: 生产用这个
```

### 子决策 3：rerank 要不要加

```
            加 rerank 的信号
            ─────────────────

  ✓ Top-10 召回包含正确答案，但 top-3 不包含
  ✓ 业务对召回精度敏感（法律 / 医疗）
  ✓ 文档量 > 10K
  ✓ 预算允许（每次查询 +1 次模型调用）

  → 满足任意 2 条加 rerank
```

### 子决策 4：索引更新频率

```
  T+1 (T+1 索引)
    → 文档晚一天可见
    → 简单（每天 batch）

  T+1h (近实时)
    → 一小时延迟
    → 需要增量索引管道

  实时
    → 写入即可查
    → 复杂度高，慎用
```

### AWS 实操：Bedrock Knowledge Bases 一站式 RAG

```
        Bedrock Knowledge Bases 架构
        ─────────────────────────────────────

  数据源: S3 / Confluence / Salesforce / Web
            ↓
  Bedrock 自动:
    - 切片（chunking strategy 可配置）
    - Embedding（Titan Embed v2 / Cohere Embed）
    - 写入 vector store（OpenSearch Serverless 默认）
            ↓
  Retrieve API:
    - retrieve(query, top_k)
    - retrieveAndGenerate(query, model)
            ↓
  生成 + 引用
```

最小可跑配置：

```
1. 创建 KB:
   - Bedrock console → Knowledge bases → Create
   - Data source: S3 bucket
   - Chunking: default (300 tokens, 20% overlap)
   - Embedding: Titan Embed v2

2. Sync data:
   - 一键 sync，几分钟到几小时（看数据量）

3. Test query:
   - retrieveAndGenerate(query="...", modelArn="claude-3-5-sonnet")
   - 输出带 citation
```

> **AWS 知识参考**：搜 "Amazon Bedrock Knowledge Bases setup"，看最新支持的数据源类型。

---

## 7.5 Agent — 什么时候上

Agent ≠ "复杂的 RAG"。Agent 的价值是**主动调用外部工具完成任务**。

```
        Agent 的判断信号
        ─────────────────

  ✓ 任务需要 2 步以上"决策 + 行动"
  ✓ 需要调用外部 API / 数据库 / 系统
  ✓ 输入不能直接映射到一个固定答案
  ✓ 单一 prompt + RAG 已尝试无效

  → 满足 3 条以上考虑 Agent
```

### Agent 的三种典型形态

```
1. Reactive Agent (单步工具)
   query → LLM 决定调用哪个工具 → 执行 → 返回

   适合: 简单查询（"我的订单到哪了"）
   工具数: 5-20

2. ReAct Agent (多步循环)
   query → LLM 思考 → 调工具 → 看结果 → 再思考 → ...

   适合: 多步骤任务（订单 + 物流 + 退款）
   工具数: 10-50

3. Multi-agent (多智能体)
   master agent 拆任务 → 子 agent 各自执行 → 汇总

   适合: 跨部门复杂流程
   工具数: 50+
```

### Agent 的失败模式

```
❌ 工具数 > 30 → 模型选错工具的概率剧增
❌ 工具描述不严谨 → Agent 调错或漏调
❌ 没有 fallback → 一步错全错
❌ 没有 trace → 失败定位不到
❌ Multi-agent 套娃 → 调试地狱
```

**FDE 的 Agent 经验法则**：先做单 Agent + 工具增强，单 Agent 撑不住再上 Multi-agent。

### AWS 实操：Bedrock Agents 起步

```
Bedrock Agents 的核心组件
─────────────────────────────────

1. Agent: 总入口（绑定一个基础模型）
2. Action Groups: 工具集
   - Lambda function (你的代码)
   - OpenAPI schema (描述工具)
3. Knowledge Bases: 关联 RAG
4. Guardrails: 输入输出过滤
5. Memory: 跨会话状态（新功能）
```

最小可跑流程：

```
Step 1: 写一个 Lambda 函数（一个工具）
        例: get_order_status(order_id) → 返回订单状态

Step 2: 写 OpenAPI schema 描述这个 Lambda
        - paths: /get_order_status
        - parameters: order_id
        - responses: { status: string, eta: string }

Step 3: Bedrock console → Agents → Create
        - Foundation model: Claude 3.5 Sonnet
        - Instructions: "你是订单客服助手 ..."
        - Action group: 关联上面的 Lambda

Step 4: Test in Agent playground
        "我的订单 #1234 到哪了？"
        Agent: 自动调 Lambda → 返回结构化答案
```

> **AWS 知识参考**：搜 "Bedrock Agents quick start"。

---

## 7.6 一张总决策表

```
┌──────────────────────────────────────────────────────────────────┐
│  典型场景               推荐解法                                  │
├──────────────────────────────────────────────────────────────────┤
│  内部知识库问答         RAG (Bedrock KB + Sonnet)                │
│  FAQ 客服               RAG + 简单 Prompting                     │
│  合同 / 文档审阅        Long-context Prompting (Claude 200K)     │
│  代码生成 / Review       Prompting + Few-shot (Opus / GPT-4)      │
│  跨系统订单查询         Reactive Agent (Bedrock Agents)          │
│  跨部门工单流转         ReAct Agent + 5-10 工具                  │
│  邮件自动回复           RAG + Prompting + Style Few-shot         │
│  特定行业术语翻译        Fine-tune (LoRA on Llama 3 8B)          │
│  监管报告自动生成        RAG + 多步 Prompting + 规则校验          │
│  研究 / 信息搜集         Multi-agent (CrewAI / LangGraph)        │
└──────────────────────────────────────────────────────────────────┘
```

**80% 的真实项目落在前 5 行**。

---

## 7.7 切换信号

实操中很难一次选对，要会读"切换信号"：

```
现在用 Prompting，发现：
  ✓ Eval 分卡在 70% 不上去
  ✓ 需要外部知识反复查询
  → 切到 RAG

现在用 RAG，发现：
  ✓ 召回对，但答案风格 / 格式难调
  ✓ Few-shot 加多了 prompt 太长
  → 加 Fine-tune（轻量 LoRA）

现在用 RAG，发现：
  ✓ 用户开始问"帮我做 X"而不是"X 是什么"
  ✓ 需要写入 / 修改外部系统
  → 升级到 Agent

现在用 Agent，发现：
  ✓ 工具数 < 10 但准确率 < 80%
  ✓ Trace 显示调错工具频繁
  → 退回 Prompting + 模板（不要硬上 Agent）
```

**FDE 的功夫在"会切换"上**。

---

## 关键引用

> "*Most LLM problems are not LLM problems — they're product problems.*"
> — A. Lawrence, *FDE Rule Book*, 2025

> "*Try prompting first. Always.*"
> — OpenAI internal best practices, 2025

> "*Fine-tuning is the last 10% you do for the last 10% of cases.*"
> — AWS GenAI Innovation Center, 2025

---

## 动手清单

接到新项目时，第一周必做：

1. **用 5 句话写下客户痛点**，对照 7.2 决策树定位主路径
2. **跑 10 条种子做 Prompting baseline**（不要直接上 RAG）
3. **如果 baseline 分数 < 70%，加 RAG 跑一次对比**
4. **写一份"为什么不上 Fine-tune"的备忘**（默认不上，要上必须有强理由）
5. **如果客户提"Agent"，先问 7.5 的 4 条信号**
6. **每两周回顾切换信号**，不要硬撑

---

## 反模式清单

- ❌ **客户说"AI 客服"就直接上 Agent 多智能体**（80% 用 RAG 就够）
- ❌ **遇到任何不准就加 Fine-tune**（Fine-tune 不解决知识更新问题）
- ❌ **同一项目里同时上 RAG + Fine-tune + Agent**（无法定位问题来源）
- ❌ **不做 baseline 直接上复杂方案**（不知道复杂方案值不值）
- ❌ **看到工具列表>10 就强行 Multi-agent**（先看单 Agent 行不行）
- ❌ **追新框架（CrewAI / AutoGen）放生产**（PoC 可以，生产慎重）

---

## 与下一章的关系

这一章给了"用哪个解法"。下一章讲：**所有解法都需要先把 Eval 集变成 CI 守门员，再进入开发** —— 这是 Eval-driven 铁律的具体落法。

[← 上一章: 技术栈速决矩阵](chapter-06.md) · [下一章: 先 Eval 再开发 →](chapter-08.md)
