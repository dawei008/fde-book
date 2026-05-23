---
title: "附录 B 比较矩阵"
parent: "附录"
nav_order: 2
---

# 附录 B: 模型 / 框架 / 平台对比矩阵

> 附录 A 是"广度速查"，本附录是"深度对比"。当你在某一类工具里要做严肃决策时，看这里。

---

## B.1 主流大模型 — 9 维对比

| 维度 | Claude 3.5 Sonnet | Claude 3 Opus | Claude 3 Haiku | GPT-4o | GPT-4o-mini | Llama 3.1 70B | Qwen 2.5 72B | DeepSeek V3 |
|---|---|---|---|---|---|---|---|---|
| 上下文 | 200K | 200K | 200K | 128K | 128K | 128K | 128K | 128K |
| 输出 token | 8K | 4K | 4K | 16K | 16K | 8K | 8K | 8K |
| 中文 | 强 | 极强 | 一般 | 强 | 良好 | 一般 | 极强 | 极强 |
| 推理 | 极强 | 顶级 | 一般 | 极强 | 良好 | 良好 | 良好 | 极强 |
| 工具调用 | 极强 | 极强 | 良好 | 极强 | 极强 | 良好 | 良好 | 良好 |
| 多模态 | 视觉 | 视觉 | 视觉 | 视觉+音频 | 视觉 | 文本 | 视觉 | 文本 |
| 价格(输入/M tok) | $3 | $15 | $0.25 | $5 | $0.15 | 自部署 | 自部署 | $0.27 |
| 价格(输出/M tok) | $15 | $75 | $1.25 | $15 | $0.6 | 自部署 | 自部署 | $1.1 |
| Bedrock 可用 | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌(亚马逊云科技中国可)| ❌ |

**FDE 决策模式**:

```
  企业默认: Claude 3.5 Sonnet (Bedrock) — 平衡 + AWS 原生
  高 QPS:   Claude 3 Haiku 或 GPT-4o-mini
  最高质量: Claude 3 Opus (judge / 关键路径)
  中文 + 私有: Qwen 2.5 72B 或 DeepSeek V3 自部署
  欧洲合规: Mistral Large
```

---

## B.2 RAG 框架对比

| 维度 | LangChain RAG | LlamaIndex | Haystack | Bedrock KB | 自建 |
|---|---|---|---|---|---|
| 上手速度 | 中 | 快 | 中 | 极快 | 慢 |
| 文档解析 | 中等 | 强 (LlamaParse) | 强 | 中等 | 自定 |
| Chunking 策略 | 多 | 多 | 多 | 默认 + 自定 | 自定 |
| 检索策略 | 多 | 极多 | 多 | hybrid (OS) | 自定 |
| Rerank | 接 Cohere/外部 | 内置 + 外部 | 内置 | 接 Cohere | 自定 |
| 增量更新 | 自己写 | 自己写 | 自己写 | 自动 (S3) | 自定 |
| 多源融合 | 强 | 极强 | 中 | 中 | 自定 |
| 生产成熟度 | 中 | 中 | 高 | 高 | 取决于团队 |
| 锁定风险 | 低 | 低 | 低 | 高 (AWS) | 无 |

**经验**:
- PoC: LlamaIndex 最快出 demo
- 生产 + AWS: Bedrock KB（4 周省下一半工程）
- 长期复杂 RAG: 自建（用 Bedrock 做检索层 + 自己控编排）

---

## B.3 Agent 框架对比

| 维度 | LangGraph | Bedrock Agents | AutoGen | CrewAI | OpenAI Assistants | 原生 SDK 状态机 |
|---|---|---|---|---|---|---|
| 编程模型 | 状态图 (DAG) | 配置式 | 多 agent 对话 | 角色扮演 | API + 状态服务 | 完全自定 |
| 工具集成 | 自由 | Action Group | 自由 | 自由 | 内置 + Function | 自由 |
| 长任务 | LangGraph Cloud | 配 Step Functions | 弱 | 弱 | 内置线程 | 自定 |
| HITL | 内置 interrupt | 工程化弱 | 中 | 弱 | 弱 | 自定 |
| 可观测 | LangSmith | CloudWatch + Trace | 自定 | 自定 | OpenAI dashboard | 自定 |
| 锁定风险 | 中 | 高 (AWS) | 低 | 低 | 高 (OpenAI) | 无 |
| 适合规模 | 小到大 | 中 + AWS 客户 | 研究 / 实验 | 内容生成 | 个人助理 | 高复杂度 |

**经验**:
- 客户在 AWS + 业务流不复杂 → Bedrock Agents
- 客户多云 + 业务流复杂 → LangGraph
- 关键路径 + 严谨 → 原生 SDK + 状态机

---

## B.4 向量库对比 — 6 个生产维度

| 维度 | Pinecone | Weaviate | Milvus | OpenSearch | pgvector | Chroma |
|---|---|---|---|---|---|---|
| 部署 | SaaS | SaaS + OSS | OSS (K8s) | AWS / OSS | PG 插件 | OSS / 本地 |
| 单库规模 | 10亿+ | 10亿+ | 100亿+ | 10亿+ | 1亿 | 千万 |
| Hybrid 检索 | 支持 | 支持 | 支持 | 极强 | 弱 (需扩展) | 弱 |
| 元数据过滤 | 强 | 强 | 强 | 极强 | 极强 (SQL) | 中 |
| 多 modal | 中 | 强 | 中 | 中 | 弱 | 弱 |
| 增量 / 更新 | 容易 | 容易 | 容易 | 容易 | 极容易 (UPDATE) | 容易 |
| VPC 内部署 | Private 版 | 自托管 | 自托管 | 自托管 / Serverless | RDS / Aurora | 自托管 |
| 成本 | 高 | 中 | 中 (运维成本) | 中 | 极低 (PG 已有) | 极低 |
| 客户已有 | 通常没有 | 通常没有 | 通常没有 | 部分 AWS 客户 | **大量客户已有 PG** | 通常没有 |

**FDE 经验决策**:

```
  客户已有 PG / Aurora     → pgvector (零额外工具)
  客户在 AWS + 中等规模    → OpenSearch Serverless
  规模 > 5 亿               → Milvus 或 Pinecone
  PoC / 小项目              → Chroma
  最省心 / 预算够          → Pinecone
```

---

## B.5 Eval 工具对比

| 维度 | Bedrock Evaluations | LangFuse | Phoenix | DeepEval | Promptfoo | Ragas |
|---|---|---|---|---|---|---|
| 形态 | AWS 托管 | OSS + Cloud | OSS | Python lib | YAML CLI | OSS |
| Eval 范围 | Model / KB / Agent | LLM 全栈 | LLM 全栈 | 单测嵌入 | 提示对比 | RAG 专项 |
| LLM-as-judge | 内置 | 支持 | 支持 | 支持 | 支持 | 支持 |
| 自动指标 | BLEU / ROUGE / 准确率 | 自定 | 自定 | 内置很多 | 自定 | RAG 6 指标 |
| 数据集管理 | S3 jsonl | UI + API | UI | 代码 | YAML | 代码 |
| 在线 trace | 否 (静态) | 强 | 强 | 否 | 否 | 否 |
| CI 友好 | 中 | 中 | 中 | 强 | 极强 | 中 |
| 成本 | 按 token + judge | OSS 免 / Cloud 收 | OSS 免 | OSS 免 | OSS 免 | OSS 免 |

**典型组合**:

```
  LangFuse (trace + 在线) + Promptfoo (CI) + Bedrock Evaluations (合规验收)
```

---

## B.6 部署平台对比 — LLM 应用维度

| 维度 | Lambda | ECS Fargate | EKS | SageMaker Endpoint | Step Functions |
|---|---|---|---|---|---|
| 启动延迟 | 冷启动 100ms-3s | 容器启动秒级 | Pod 秒级 | 启动秒级 | 编排开销 |
| 单次最长 | 15min | 无 | 无 | 无 | 1年 |
| 并发模型 | 自动 | 自管 | 自管 | 自管 | N/A |
| 适合 | 单次 LLM 调 / 简单 Agent | 长 server / MCP | 复杂集群 | 自部署模型 | 长流程 / HITL |
| 成本特征 | 用多少付多少 | 按容器 | 按节点 | 按 endpoint | 按状态转移 |
| 状态 | 无状态 | 无状态 / EFS | StatefulSet | 无状态 | 状态在 SF |
| 镜像大小 | 250MB / 10G(image) | 大 | 大 | 大 | N/A |

**经验**:
- 简单 RAG / API → Lambda
- MCP server / Agent 服务 → ECS Fargate
- 长流程 + HITL → Step Functions + Lambda
- 自部署 70B+ 模型 → SageMaker / EKS + GPU

---

## B.7 编程语言 / 运行时

| 维度 | Python | TypeScript | Go | Rust |
|---|---|---|---|---|
| LLM SDK 成熟度 | 顶级 | 良好 | 良好 | 起步 |
| 数据处理 | 极强 | 中 | 强 | 强 |
| 异步并发 | asyncio (中等) | 原生强 | goroutine 强 | tokio 强 |
| 部署体积 | 大 | 中 | 极小 (单二进制) | 极小 |
| 团队招聘 | 极易 | 易 | 中 | 难 |
| FDE 推荐场景 | 数据 / Eval / PoC | 前端 / Lambda | API / 高并发 | 关键路径 / 嵌入 |

**FDE 默认**: Python + TypeScript 双栈，绝大部分场景够用。

---

## B.8 决策综合表

```
        客户场景 → 推荐技术栈
        ─────────────────────────────────────────────────

  AWS 中等保险公司 + 文档 RAG
    模型:   Bedrock Claude 3.5 Sonnet
    框架:   Bedrock Knowledge Bases + 自建 Lambda
    向量:   OpenSearch Serverless
    Eval:   LangFuse Cloud + Promptfoo CI
    部署:   Lambda + API Gateway
    IaC:    AWS CDK
    监控:   CloudWatch + X-Ray
    安全:   IAM Identity Center + Bedrock Guardrails

  ─────────────────────────────────────────────────

  本地数据库已 PG + 中文金融 + 内网
    模型:   DeepSeek V3 / Qwen 2.5 72B 自部署 (vLLM)
    框架:   原生 SDK + 状态机
    向量:   pgvector
    Eval:   Phoenix (自部署) + 自定 judge
    部署:   K8s
    IaC:    Terraform
    监控:   Prometheus + Grafana
    安全:   内部 LDAP + 自定 audit

  ─────────────────────────────────────────────────

  跨国零售 + 多 SaaS 集成 + Agent
    模型:   Claude 3.5 Sonnet
    框架:   LangGraph + MCP servers
    向量:   Pinecone
    Eval:   LangFuse + DeepEval
    部署:   ECS Fargate
    IaC:    Pulumi (多云)
    监控:   Datadog
    安全:   Okta + per-call OAuth
```

---

[← 返回目录](../README.md) · [下一章: 评估集设计模板 →](appendix-c.md)
