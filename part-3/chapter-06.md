# Chapter 6: 技术栈速决矩阵 — 模型 / 框架 / 数据库 / 编排

## 开场

```
新人 FDE 第一次做 PoC。

她在 Notion 上画了一张选型表：
  - LLM: GPT-4o vs Claude 3.5 vs Llama 3.1 vs Bedrock Titan vs ...
  - 向量库: Pinecone vs Weaviate vs OpenSearch vs pgvector vs ...
  - 编排: LangChain vs LlamaIndex vs LangGraph vs 原生 ...
  - Agent 框架: AutoGen vs Bedrock Agents vs CrewAI vs ...

每个候选都列了 8 个维度（性能 / 成本 / 社区 / 安全 / 部署 ...）。

10 天后，她还在选型。一行业务代码没写。

她老板把表抢过去画了 4 个叉，说：
"这 4 个候选你直接砍。剩下的 1-2 个用 1 周跑通 v0.1 看 Eval 分。
 不要在选型上花超过 1 周。"

她照做了。第 4 周客户已经看到 demo。

这一章给的不是"完美选型"，而是"可以 30 分钟决定、6 周内能改回来"
的 working set。
```

---

## 6.1 选型的两个原则

### 原则 1：选"足够好"，不选"最好"

LLM 工程的特点：
- 半年内技术栈大变
- 选型再"完美"，半年后都要重选
- **选型成本 = 选错代价 + 替换代价**

→ 选"30 分钟能上手 + 1 周内能切换"的方案，胜过"最优方案"。

### 原则 2：先看约束，再看候选

```
                    约束优先级
                    ─────────────

  1. 客户合规 / 部署形态（VPC / 离线 / 云）
     → 砍掉 60% 候选

  2. 数据敏感度 / PII
     → 砍掉一半剩余

  3. 预算 / token 月度上限
     → 决定模型档位

  4. 团队熟悉度
     → 决定框架选择

  5. 性能 / 体验目标
     → 微调具体配置
```

**新手错误**是从第 5 条开始选；老手从第 1 条开始砍。

---

## 6.2 模型选型矩阵

```
                    场景 → 推荐 default 模型
                    ─────────────────────────

  通用对话 / RAG / 客服      → Claude Sonnet (Bedrock 上首选)
                              或 GPT-4o-mini (低成本)

  代码生成 / 复杂推理        → Claude Opus / GPT-4o

  超长文档（>50K token）     → Claude (200K context)

  低延迟 / 高 QPS            → Haiku / GPT-4o-mini / Llama 3 8B

  完全离线 / 私有化           → Llama 3 / Mistral 自部署

  中文优先 / 国内合规         → 通义千问 / 文心 / DeepSeek

  Embedding                  → Bedrock Titan Embed v2 (英文 + 多语)
                              或 BGE-M3 (中文优先)
```

### 选模型的 5 个判断问题

```
1. 部署形态？
   云上托管能用 → Bedrock / OpenAI / Claude API
   必须在客户 VPC → Bedrock VPC endpoint / SageMaker JumpStart
   离线 → 自部署 Llama / Qwen

2. 单次请求平均输入长度？
   <8K  → 任何模型
   8-32K → 优先 Claude / Bedrock
   >32K  → Claude 200K / Gemini 1M

3. 月度预算？
   <$1k → 一定要用 mini / haiku 档
   $1-10k → 主力 mini，复杂场景升级
   >$10k → 可以 default sonnet/4o

4. 输出 JSON / 结构化的需求强吗？
   强 → 优先 OpenAI / Claude（有 strict mode / tool use）

5. 业务语言？
   纯英文 → GPT-4o / Claude
   纯中文 → 国产模型
   混合 → Claude / Gemini / 通义
```

### AWS 实操：在 Bedrock 上做模型选型 baseline

```
Step 1: 用 Bedrock playground 跑 5 条种子样本
        - Claude 3.5 Sonnet
        - Claude 3 Haiku
        - Llama 3.1 70B
        - Mistral Large
        - Titan Text Premier
        肉眼看一遍输出质量

Step 2: 在 Bedrock Evaluations 创建一个 Model Evaluation Job
        - 数据集: 50 条 seed
        - Evaluator: built-in (accuracy + robustness)
        - Compare 多个模型

Step 3: 看输出报告
        - 总分排序
        - 单价排序
        - 选 "性价比最高 + 能 cover 90% 用例" 的那个

Step 4: 把这个模型作为 default
        其他模型作为升级路径（"复杂查询走 Opus"）
```

> **AWS 知识参考**：在 docs.aws.amazon.com 搜 "Bedrock supported foundation models" 与 "Bedrock model invocation pricing"。

---

## 6.3 框架选型矩阵

```
                    场景 → 推荐框架
                    ─────────────────────────

  纯 RAG, 一次性问答         → 直接 Bedrock Knowledge Bases
                              或 LlamaIndex

  RAG + 多步流程             → LangChain (Python) / LangGraph

  Agent (工具调用 + 多轮)     → LangGraph 或 Bedrock Agents

  Agent 多智能体协作         → AutoGen / CrewAI / LangGraph

  生产级控制流（要稳定）      → 不用 LangChain，用原生 SDK + 状态机

  企业集成 / MCP             → Bedrock Agents + MCP / Anthropic SDK
```

### 框架选择的 3 个权衡

```
                  开发速度 ←─────→ 生产稳定性
                  ←────────────→
                  LangChain        原生 SDK
                  快、坑多          慢、稳

                  社区生态 ←─────→ 一致性
                  ←────────────→
                  LangChain        Bedrock Agents
                  插件多            一致 + 受限

                  调试可见 ←─────→ 框架抽象
                  ←────────────→
                  LangFuse / Phoenix    LangChain 内部链
```

### 实操建议（按阶段）

```
PoC 阶段（W1-W6）：
  - 选最快出 demo 的：LangChain / LlamaIndex / Bedrock KB
  - 优先用 SaaS：Bedrock 全家桶 + LangFuse Cloud

中期（W7-W12, 进生产前）：
  - 把链路里"最关键的 3 步"换成原生 SDK + 状态管理
  - 监控接好（Trace, Eval, Cost）
  - 不可靠的 LangChain 组件换掉

生产期（M3+）：
  - 90% 的代码是你自己的，框架只用关键节点
  - Frame work 升级 = 不能再阻塞业务
```

---

## 6.4 向量库选型矩阵

```
        ┌──────────────────────────────────────────────────┐
        │                  规模 vs 部署矩阵                │
        ├──────────────────────────────────────────────────┤
        │  规模           托管          自部署              │
        │  <1M            pgvector*     pgvector            │
        │  1-10M          OpenSearch    Weaviate / Milvus   │
        │  10-100M        Pinecone /    Milvus / Vespa      │
        │                 OpenSearch                        │
        │  >100M          专门评估      专门评估             │
        └──────────────────────────────────────────────────┘
        * 客户已经有 PG → 优先 pgvector 不要新引入服务
```

### 选向量库的 4 个判断

```
1. 客户已经在用什么？
   → 已有 PG → pgvector (省运维)
   → 已有 ES/OpenSearch → 直接用 OpenSearch vector
   → 已有 Bedrock KB → Bedrock 后端默认 OpenSearch Serverless

2. 数据更新频率？
   → 静态 (月级) → 任何方案
   → 高频 (秒级) → Pinecone / Weaviate / OpenSearch

3. 元数据过滤需求？
   → 复杂多维 → OpenSearch / Weaviate
   → 简单 → 任何方案

4. 部署形态？
   → 云上 SaaS 可 → Pinecone (最省心)
   → 客户 VPC → OpenSearch / pgvector / 自部署 Weaviate
   → 离线 → Milvus / FAISS
```

### AWS 实操：选 Bedrock Knowledge Bases 的后端

```
                    Bedrock Knowledge Bases 后端选择
                    ─────────────────────────────────

  OpenSearch Serverless (默认)
    - 0 运维，按使用量收费
    - 适合 PoC 和中等规模
    - 起步成本约 $345/月（最低 OCU）

  Aurora PostgreSQL with pgvector
    - 客户已有 Aurora PG → 直接接
    - 适合规模 <10M chunks

  Pinecone
    - 跨账号 / 多区域容易
    - 高 QPS 场景

  Redis Enterprise Cloud
    - 低延迟（<10ms）
    - 但成本高
```

> **AWS 知识参考**：搜 "Bedrock Knowledge Bases supported vector stores" 看最新支持矩阵。

---

## 6.5 编排 / 工作流选型

LLM 应用上线后，最难的不是"模型对不对"，是"流程稳不稳"。

```
                    场景 → 推荐编排
                    ─────────────────────────

  单步 LLM 调用              → 不需要编排（直接 SDK）

  Sequential 多步             → LangGraph / 原生 async

  并行 + 汇聚                 → LangGraph / Step Functions

  跨服务长流程（>5 分钟）     → AWS Step Functions
                              或 Temporal

  Agent 自主多步              → LangGraph / Bedrock Agents

  人在回路（HITL）             → Step Functions + SQS
                              或 Temporal signals
```

### 一个判断：什么时候从 LangGraph 升级到 Step Functions

```
触发升级的信号：
  ✓ 单次执行 > 5 分钟
  ✓ 需要持久化中间状态
  ✓ 需要重试 / 断点恢复
  ✓ 需要审计 / 可视化执行历史
  ✓ 流程涉及多个服务（不止 LLM）

满足任意 2 条 → 用 Step Functions
都不满足 → 用 LangGraph 即可
```

---

## 6.6 监控 / Trace 选型

LLM 应用没有 Trace = 没法 debug = 没法迭代。

```
                    场景 → 推荐 trace
                    ─────────────────────────

  PoC + 快速看一眼           → LangFuse Cloud / LangSmith Cloud
                              （5 分钟接好）

  企业 + 数据不出域          → LangFuse 自部署
                              或 Phoenix (Arize)

  深度集成 AWS                → CloudWatch + X-Ray + Bedrock 内置

  Agent 多步可视化            → LangSmith / Phoenix
                              （专门做 Agent 路径可视化）
```

### 必须 trace 的 4 个维度

```
  1. Latency（每一步耗时）
  2. Cost（input/output token + 模型）
  3. Quality（Eval 分数 + 用户反馈）
  4. Error（失败堆栈 + 上下游关联）
```

### AWS 实操：Bedrock + CloudWatch + X-Ray 一站式

```
        ┌───────────────────────────────────────┐
        │ Application                            │
        │   ↓ (invoke Bedrock model)            │
        │ Bedrock                                │
        │   ↓ (auto emit metrics)               │
        │ CloudWatch Metrics:                    │
        │   - Invocations                        │
        │   - InvocationLatency                  │
        │   - InputTokenCount / OutputTokenCount │
        │   - InvocationClientErrors             │
        │   ↓                                    │
        │ CloudWatch Logs:                       │
        │   - Bedrock Model Invocation Logging   │
        │     (打开后记录所有 prompt/response)   │
        │   ↓                                    │
        │ X-Ray Tracing:                         │
        │   - 跨服务 trace（Lambda → Bedrock）   │
        └───────────────────────────────────────┘
```

打开 Bedrock Model Invocation Logging：

```
Bedrock console → Settings → Model invocation logging
  ✓ Enable
  ✓ Destination: CloudWatch Logs (or S3)
  ✓ Log: Text + Image data (按需)
```

> **AWS 知识参考**：搜 "Bedrock model invocation logging" 与 "CloudWatch metrics for Bedrock"。

---

## 6.7 一张总速决表（30 分钟决定）

```
┌─────────────────────────────────────────────────────────────────┐
│  约束 / 场景               default 选型                          │
├─────────────────────────────────────────────────────────────────┤
│  云上 + 中等规模 RAG     │ Bedrock + Claude Sonnet              │
│                          │   + Knowledge Bases (OpenSearch)     │
│                          │   + LangFuse Cloud                   │
│                          │   + CloudWatch                       │
├─────────────────────────────────────────────────────────────────┤
│  客户 VPC + 严合规       │ Bedrock VPC endpoint                 │
│                          │   + Aurora pgvector                  │
│                          │   + LangFuse 自部署                  │
│                          │   + KMS + CloudTrail                 │
├─────────────────────────────────────────────────────────────────┤
│  完全离线 / 国产化       │ Qwen / DeepSeek + vLLM 自部署        │
│                          │   + Milvus 集群                      │
│                          │   + 自建 Phoenix trace                │
├─────────────────────────────────────────────────────────────────┤
│  Agent 自动化            │ Bedrock Agents OR LangGraph          │
│                          │   + Step Functions (长流程)          │
│                          │   + Lambda (工具)                    │
│                          │   + DynamoDB (状态)                  │
└─────────────────────────────────────────────────────────────────┘
```

**60% 的项目可以直接套用上面 default 之一**。把节省的时间花到 Eval / Discovery / Handoff 上。

---

## 关键引用

> "*The best stack is the one your team can debug at 2am.*"
> — A. Lawrence, *FDE Rule Book*, 2025

> "*Don't pick the most powerful model — pick the cheapest one that passes eval.*"
> — Bob McGrew @ YC, 2025

> "*If your stack diagram has more than 7 boxes, you're going to lose at handoff.*"
> — AWS GenAI Innovation Center, 2025

---

## 动手清单

接到一个新 LLM 项目第 3 周必做的 6 件事：

1. **写 5 句话约束**：部署形态 / 数据敏感度 / 预算 / 团队熟悉度 / 性能目标
2. **从 6.7 速决表选 1 个 default 配置**（30 分钟内）
3. **用 default 跑通 50 条种子的 baseline**（不调优，只跑通）
4. **在 Bedrock Evaluations 跑 2-3 个候选模型 A/B**
5. **接好 trace（LangFuse 或 CloudWatch）** —— 不接以后没法 debug
6. **写一份"选型决策备忘"**：今天选了什么，砍了什么，1 个月后什么信号触发重选

---

## 反模式清单

- ❌ **选型超过 1 周**（PoC 死在选型环节）
- ❌ **选型时只看 benchmark 不看部署形态**（合规一卡全废）
- ❌ **从 LangChain 一路用到生产**（链路抽象在生产期会反咬）
- ❌ **不接 trace 直接上 demo**（出问题没法定位）
- ❌ **每个项目都重新选型**（同一公司应该有 default 模板）
- ❌ **追"最新最强"模型**（半个月就改一次，团队精疲力尽）

---

## 与下一章的关系

这一章给了"该用哪个工具"。下一章给"该用哪种解法" —— 同一个问题，是用 RAG / Fine-tune / Prompting / Agent 哪一种？什么时候切换？

[← Part III 导读](intro.md) · [下一章: 决策树 →](chapter-07.md)
