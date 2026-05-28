---
title: "附录 B 比较矩阵"
parent: "附录"
nav_order: 2
---

# 附录 B: 模型 / 框架 / 平台对比矩阵

> 附录 A 是"广度速查"，本附录是"深度对比"。当你在某一类工具里要做严肃决策时，看这里。
>
> 立场说明：本书以 AWS 为演示平台。下文涉及非 AWS 工具仅作"客户已有栈对接"参考，不做横向友商商业评比。

---

## B.1 主流大模型 — 9 维对比（2026-05）

| 维度 | Claude Opus 4.5 | Claude Sonnet 4.5 | Claude Haiku 4.5 | Nova 2 Lite | Nova 2 Pro | Qwen3-Next | DeepSeek V3.2 | gpt-oss-20B |
|---|---|---|---|---|---|---|---|---|
| 上下文 | 200K | 200K+ | 200K | 1M | 长 | 长 | 长 | 中 |
| 中文 | 极强 | 强 | 强 | 中 | 中 | 极强 | 极强 | 一般 |
| 推理 | 顶级 | 极强 | 良好 | 良好 | 强 | 强 | 极强 | 良好 |
| 工具调用 | 极强（含 tool-search、effort 参数） | 极强 | 良好 | 内置 code interpreter / web grounding | 强 | 良好 | 良好 | 良好 |
| 多模态 | 视觉 | 视觉 | 视觉 | 文本+视觉 | 文本+视觉 | 视觉（VL 版） | 文本 | 文本 |
| Bedrock 可用 | ✅ | ✅ | ✅ | ✅（GA） | 预览 | ✅（Project Mantle） | ✅（Mantle, OpenAI 兼容） | ✅（Mantle） |
| Reserved 等级 | ✅ | ✅ | ✅ | — | — | — | — | — |
| Prompt cache TTL | 5 min / 1 hour | 5 min / 1 hour | 5 min / 1 hour | — | — | — | — | — |
| 价格档 | 高 | 中 | 低 | 低 | 中 | 中-低 | 低 | 低 |

**FDE 决策模式**：

```
  企业默认（AWS）：     Bedrock Claude Sonnet 4.5 — 平衡 + AWS 原生
  高 QPS / 分类路由：   Claude Haiku 4.5
  最高质量 / Judge：    Claude Opus 4.5（用 effort 参数控制成本）
  长文档 / 1M 上下文：  Nova 2 Lite
  中文 + 私有：         Qwen3-Next / DeepSeek V3.2（Mantle 端点 + PrivateLink）
  已有 OpenAI SDK 代码：Mantle 上的 gpt-oss / DeepSeek（drop-in 兼容）
  欧洲多语：            Mistral Large 3 / Magistral
```

**Inference 服务等级**（2025-11 起）：

| 等级 | 适合 | 备注 |
|---|---|---|
| Standard | 常规生产 | 默认 |
| Priority | 实时关键路径 | 价格更高，配额更稳 |
| Flex | 批量 / 离线 eval / 摘要 | 折扣，容忍延迟 |
| Reserved | 可预测产能 | 1 或 3 个月承诺，溢出回 Standard |

---

## B.2 RAG 框架对比

| 维度 | LangChain RAG | LlamaIndex | Haystack | Bedrock KB | 自建 |
|---|---|---|---|---|---|
| 上手速度 | 中 | 快 | 中 | 极快 | 慢 |
| 文档解析 | 中等 | 强 (LlamaParse) | 强 | 中等 + Bedrock Data Automation | 自定 |
| Chunking 策略 | 多 | 多 | 多 | 默认 + 自定 | 自定 |
| 检索策略 | 多 | 极多 | 多 | hybrid (OS) | 自定 |
| 多模态 | 自接 | 自接 | 自接 | ✅（2025-11 GA：文/图/音/视频） | 自定 |
| Rerank | 接 Cohere/外部 | 内置 + 外部 | 内置 | 接 Cohere | 自定 |
| 增量更新 | 自己写 | 自己写 | 自己写 | 自动 (S3) | 自定 |
| 多源融合 | 强 | 极强 | 中 | 中 | 自定 |
| 生产成熟度 | 中 | 中 | 高 | 高 | 取决于团队 |
| 锁定风险 | 低 | 低 | 低 | 高 (AWS) | 无 |

**经验**：
- PoC：LlamaIndex 最快出 demo
- 生产 + AWS：Bedrock KB（4 周省下一半工程；多模态走原生）
- 长期复杂 RAG：自建（用 Bedrock 做检索层 + 自己控编排）

---

## B.3 Agent 框架对比

| 维度 | Strands Agents | AgentCore | LangGraph | AutoGen | CrewAI | 原生 SDK 状态机 |
|---|---|---|---|---|---|---|
| 编程模型 | 轻量 SDK（Py / TS 1.0） | 托管 Runtime + Gateway | 状态图 (DAG) | 多 agent 对话 | 角色扮演 | 完全自定 |
| 工具集成 | 自由 + MCP | MCP / Action / Gateway | 自由 | 自由 | 自由 | 自由 |
| 长任务 | 自管 | 内置 8h 执行窗口 | LangGraph Cloud | 弱 | 弱 | 自定 |
| HITL | 自接 | 有状态 MCP（2026-03）+ Cedar 策略 | 内置 interrupt | 中 | 弱 | 自定 |
| 可观测 | OTEL → CloudWatch | CloudWatch GenAI Observability + Evaluations | LangSmith | 自定 | 自定 | 自定 |
| 评估 | 接 Bedrock Eval | 内置 13 evaluator + Performance Loop（2026-05） | LangSmith | 自定 | 自定 | 自定 |
| 锁定风险 | 低（开源） | 高 (AWS) | 中 | 低 | 低 | 无 |
| 适合规模 | 小到大 | 中-大 + AWS 客户 | 小到大 | 研究 / 实验 | 内容生成 | 高复杂度 |

**经验**：
- 客户在 AWS + 想要"开箱即用"产线 → AgentCore（Runtime + Gateway + Identity + Observability + Evaluations）
- 客户想要轻量 SDK 但保留 AWS 集成 → Strands（含 TS 1.0，前端团队可拥抱）
- 多云 + 业务流复杂 → LangGraph
- 关键路径 + 严谨 → 原生 SDK + 状态机

---

## B.4 向量库对比 — 6 个生产维度

| 维度 | OpenSearch (AWS) | Aurora pgvector | Pinecone | Weaviate | Milvus | Chroma |
|---|---|---|---|---|---|---|
| 部署 | AWS 托管 / Serverless | AWS Aurora / RDS | SaaS | SaaS + OSS | OSS (K8s) | OSS / 本地 |
| 单库规模 | 10亿+ | 1亿 | 10亿+ | 10亿+ | 100亿+ | 千万 |
| Hybrid 检索 | 极强 | 弱 (需扩展) | 支持 | 支持 | 支持 | 弱 |
| 元数据过滤 | 极强 | 极强 (SQL) | 强 | 强 | 强 | 中 |
| 多 modal | 中 | 弱 | 中 | 强 | 中 | 弱 |
| 增量 / 更新 | 容易 | 极容易 (UPDATE) | 容易 | 容易 | 容易 | 容易 |
| VPC 内部署 | Serverless / 自托管 | RDS / Aurora | Private 版 | 自托管 | 自托管 | 自托管 |
| 客户已有 | 部分 AWS 客户 | **大量客户已有 PG** | 通常没有 | 通常没有 | 通常没有 | 通常没有 |

**FDE 经验决策**：

```
  客户已有 PG / Aurora     → pgvector (零额外工具)
  客户在 AWS + 中等规模    → OpenSearch Serverless
  规模 > 5 亿               → Milvus 或 Pinecone
  PoC / 小项目              → Chroma
```

---

## B.5 Eval 工具对比

| 维度 | Bedrock Evaluations | AgentCore Evaluations | LangFuse | Phoenix | DeepEval | Promptfoo | Ragas |
|---|---|---|---|---|---|---|---|
| 形态 | AWS 托管 | AWS 托管 | OSS + Cloud | OSS | Python lib | YAML CLI | OSS |
| Eval 范围 | 单次调用 (Model / KB / Agent job) | 基于 trace 的 agent 行为；built-in / LLM-judge / 代码 (Lambda) 三种 evaluator | LLM 全栈 | LLM 全栈 | 单测嵌入 | 提示对比 | RAG 专项 |
| LLM-as-judge | 内置 | 内置 + 自定 | 支持 | 支持 | 支持 | 支持 | 支持 |
| 在线 trace | 静态为主 | online / on-demand / batch / dataset / simulation 五种模式；OpenTelemetry 入口 | 强 | 强 | 否 | 否 | 否 |
| CI 友好 | 中 | 中 | 中 | 中 | 强 | 极强 | 中 |
| 成本 | 按 token + judge | 按 invocation | OSS / Cloud | OSS | OSS | OSS | OSS |

**典型组合（AWS 客户）**：

```
  AgentCore Evaluations + CloudWatch GenAI Observability  → 在线 + 仪表盘
  Bedrock Evaluations                                     → CI 合规跑分 + 合规验收
  Promptfoo                                               → 跨模型提示对比
  AgentCore Optimization (preview)                        → 评估→改 prompt 闭环
  AWS Agent Registry (preview)                            → 多 BU 共享评估 / agent / tool
```

---

## B.6 部署平台对比 — LLM 应用维度

| 维度 | Lambda | ECS Fargate | EKS | AgentCore Runtime | SageMaker Endpoint | Step Functions |
|---|---|---|---|---|---|---|
| 启动延迟 | 冷启动 100ms-3s | 容器启动秒级 | Pod 秒级 | microVM 秒级 | 启动秒级 | 编排开销 |
| 单次最长 | 15min | 无 | 无 | 8h | 无 | 1年 |
| 并发模型 | 自动 | 自管 | 自管 | 托管 | 自管 | N/A |
| 适合 | 单次 LLM 调 / 简单 Agent | 长 server / MCP | 复杂集群 | Agent + MCP + VPC | 自部署模型 | 长流程 / HITL |
| 状态 | 无状态 | 无状态 / EFS | StatefulSet | session microVM（含有状态 MCP） | 无状态 | 状态在 SF |
| 私网 | VPC | VPC | VPC | VPC + PrivateLink | VPC | — |

**经验**：
- 简单 RAG / API → Lambda
- MCP server / Agent 服务 → ECS Fargate 或 AgentCore Runtime（推荐后者：免维护、内置 8h 长任务）
- 长流程 + HITL → AgentCore + 有状态 MCP，或 Step Functions + Lambda
- 自部署 70B+ 模型 → SageMaker JumpStart 优化部署 / HyperPod / EKS + GPU

---

## B.7 编程语言 / 运行时

| 维度 | Python | TypeScript | Go | Rust |
|---|---|---|---|---|
| LLM SDK 成熟度 | 顶级 | 良好（Strands TS 1.0 起 AWS Agent 也覆盖） | 良好 | 起步 |
| 数据处理 | 极强 | 中 | 强 | 强 |
| 异步并发 | asyncio (中等) | 原生强 | goroutine 强 | tokio 强 |
| 部署体积 | 大 | 中 | 极小 (单二进制) | 极小 |
| 团队招聘 | 极易 | 易 | 中 | 难 |
| FDE 推荐场景 | 数据 / Eval / PoC | 前端 / Lambda / Agent | API / 高并发 | 关键路径 / 嵌入 |

**FDE 默认**：Python + TypeScript 双栈，绝大部分场景够用。Strands TS 1.0 后，前端团队可独立拥有 Agent 代码。

---

## B.8 决策综合表

```
        客户场景 → 推荐技术栈
        ─────────────────────────────────────────────────

  AWS 中等保险公司 + 文档 RAG
    模型:   Bedrock Claude Sonnet 4.5（Reserved Tier）
    框架:   Bedrock Knowledge Bases + Lambda
    向量:   OpenSearch Serverless
    Eval:   Bedrock Evaluations + Promptfoo CI
    部署:   Lambda + API Gateway
    IaC:    AWS CDK
    监控:   CloudWatch GenAI Observability + X-Ray
    安全:   IAM Identity Center + Bedrock Guardrails（含跨账号）

  ─────────────────────────────────────────────────

  本地数据库已 PG + 中文金融 + 内网
    模型:   DeepSeek V3.2 / Qwen3-Next（Bedrock Mantle + PrivateLink），
            或自部署（vLLM）
    框架:   原生 SDK + 状态机，或 Strands
    向量:   pgvector
    Eval:   Phoenix（自部署）+ 自定 judge
    部署:   K8s / EKS
    IaC:    Terraform
    监控:   Prometheus + Grafana
    安全:   内部 LDAP + 自定 audit

  ─────────────────────────────────────────────────

  跨国零售 + 多 SaaS 集成 + Agent
    模型:   Claude Sonnet 4.5（主） + Haiku 4.5（路由 / 分类）
    框架:   Strands + AgentCore（Gateway + Identity）
    向量:   OpenSearch Serverless
    Eval:   AgentCore Evaluations + Performance Loop
    部署:   AgentCore Runtime
    IaC:    CDK
    监控:   CloudWatch GenAI Observability
    安全:   IAM Identity Center + AgentCore Policy（Cedar）+ Guardrails
```

---

[← 返回目录](../../) · [下一附录：评估集设计模板 →](../appendix-c/)
