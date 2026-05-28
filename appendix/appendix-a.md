---
title: "附录 A 工具栈速查"
parent: "附录"
nav_order: 1
---

# 附录 A: FDE 工具栈速查表 (2026 版)

每类 3-5 个候选 + 选型维度。供 PoC 选型时 30 分钟决策用。

> 立场说明：本书以 AWS 为演示平台。下文清单包含 AWS 之外的开源/第三方工具，仅作为客户已有栈对接时的参考，不作横向对比。

---

## A.1 模型 API（Bedrock 上 2026-05 可用）

| 模型 | 强项 | 适合场景 | 价格档 |
|---|---|---|---|
| Claude Opus 4.5 / 4.6 | 顶级推理 + tool-search + effort 参数 | 复杂 Agent / Judge / 关键路径 | 高 |
| Claude Sonnet 4.5 / 4.6 | 平衡 + 长上下文 + 工具调用 | 通用 RAG / Agent 默认 | 中 |
| Claude Haiku 4.5 | 快 + 便宜 | 高 QPS / 简单分类 | 低 |
| Nova 2 Lite | 1M token + code interpreter + web grounding | 长文档 / 成本敏感 | 低 |
| Nova 2 Pro | AWS 一方旗舰 | AWS 一站式重场景 | 中 |
| Qwen3-Next / Qwen3 Coder Next | 中文 + 代码 | 中文场景 / 代码任务 | 中-低 |
| DeepSeek V3.2 | 推理 + 中文 | 中文 + 推理 | 低 |
| Mistral Large 3 / Magistral | 多语言 / 推理 | 欧洲 / 多语 | 中 |
| GLM-4 / Kimi K2 / MiniMax | 中文开源 | 中文场景备选 | 低 |
| gpt-oss / gpt-oss-safeguard | OpenAI API 兼容 | 已有 OpenAI SDK 代码迁移 | 低 |

**说明**：2025-12 与 2026-02 的两批扩展（共 24 个开源权重模型）让 Bedrock 不再等于 Claude；其中 Project Mantle 提供 OpenAI 兼容端点 + PrivateLink，可在 14 个区域跑。

**选型维度**：部署形态（云/VPC/私有）/ 上下文长度 / 中英文 / 推理需求 / 月度预算 / 是否需要 OpenAI SDK 兼容。

**Inference 服务等级**（2025-11 起）：Standard / Priority（实时优先）/ Flex（折扣，容忍延迟）/ Reserved（1 或 3 个月承诺，溢出回 Standard）。Claude 4.5 全家族（Sonnet/Opus/Haiku）已支持 Reserved。

---

## A.2 自部署 / 私有化模型

| 模型 | 形态 | 适合 |
|---|---|---|
| Llama 3.2 / 3.3 | 开源旗舰 | 通用私有部署 |
| Qwen3 系列（含 32B） | 中文/多语 | 中文私有部署 / RFT 基座 |
| DeepSeek V3.2 | 推理 + 中文 | 中文 + 强推理 |
| gpt-oss-20B | OpenAI 兼容 | RFT 蒸馏目标 |
| Gemma 4（E4B / 26B-A4B / 31B） | 多模态 + 函数调用 | 多语 / 非 Anthropic 备选 |
| Mistral Large 3 / Ministral 3 | 多语 | 欧洲合规 |

**部署平台**：SageMaker JumpStart（2026-04 起 30+ 模型有官方 cost/throughput/latency 优化部署）/ SageMaker HyperPod（含 G7e RTX PRO 6000 实例）/ EKS + vLLM。

---

## A.3 编排 / 框架

| 框架 | 强项 | 适合阶段 | 风险 |
|---|---|---|---|
| Strands Agents (Python / TS 1.0) | 轻量 + AWS 一方 SDK | 生产 Agent | 生态较新 |
| Bedrock AgentCore（2025-10 GA） | Runtime / Gateway / Memory / Browser / Code Interpreter / Identity / Observability / Evaluations / Policy / Registry (preview) / Payments (preview) — 11 项可独立选用 | 生产 Agent + VPC + 8h 长任务 + 多 BU 治理 | 锁定 AWS |
| LangGraph | 状态图 + Agent | 生产 Agent | 学习曲线 |
| LangChain | 生态最大 | PoC 快出 demo | 抽象漏 |
| LlamaIndex | RAG 专精 | RAG 项目 | Agent 弱 |
| AutoGen / CrewAI | 多 agent / 角色扮演 | 研究 / 内容 | 不太稳 |
| 原生 SDK + 状态机 | 最稳 | 生产关键路径 | 开发慢 |

**经验**：PoC 用 LangChain / LlamaIndex；生产 Agent 默认 Strands + AgentCore，或原生 SDK + Step Functions。AgentCore Runtime 自 2025-11 支持直接代码部署（不强制 Dockerfile），自 2026-03 支持有状态 MCP server，自 2026-04 增加 managed harness（preview）和 CLI。

---

## A.4 向量库 / Knowledge Base

| 工具 | 形态 | 适合规模 | 备注 |
|---|---|---|---|
| Bedrock Knowledge Bases | AWS 托管 | 中 | 2025-11 多模态 GA（文本/图/音/视频） |
| OpenSearch (Serverless / 自部署) | AWS / 开源 | 中-大 | hybrid search 强 |
| Aurora pgvector / RDS PG | AWS Aurora / RDS | 小-中 | VPC 内首选；客户已有 PG 时优先 |
| Pinecone | SaaS | 中-大 | 最省心 |
| Weaviate | 开源 + SaaS | 中 | 多 modal |
| Milvus | 开源 | 大 | K8s 部署 |
| Chroma | 开源 | 小 / PoC | 内存型 |

**选型维度**：规模 / 部署 / 元数据过滤 / 客户已有什么。

---

## A.5 Eval / Trace

| 工具 | 类型 | 强项 |
|---|---|---|
| Bedrock Evaluations | AWS 托管 | Model / KB / RAG / Agent |
| AgentCore Evaluations (preview, 2025-12+) | AWS 托管 | 基于 OpenTelemetry trace 评估 agent 行为；built-in / LLM-judge / 代码（Lambda）三种 evaluator；五种模式（online/on-demand/batch/dataset/simulation）；SESSION/TRACE/TOOL_CALL 三种粒度 |
| CloudWatch GenAI Observability | AWS 托管 | 模型调用 + AgentCore 一体面板，含 evaluations 集成 |
| AgentCore Optimization (preview) | AWS 托管 | 从生产 trace 自动生成 prompt / tool description 改进；batch eval + Gateway A/B 验证；统计显著性报告 |
| AWS Agent Registry (preview) | AWS 托管 | 企业级 agent / tool / MCP server 发现 + 审批 + 治理目录；hybrid 搜索；MCP-native 端点 |
| Bedrock Advanced Prompt Optimization | AWS 托管 | 跨模型迁移 + 多模态 + 内置 eval（2026-05） |
| LangFuse | OSS + Cloud | LLM trace + eval 一站 |
| LangSmith | LangChain 官方 | LangChain 项目 |
| Phoenix (Arize) | 开源 | 私有部署友好 |
| DeepEval | Python 库 | 写在 pytest 里 |
| Promptfoo | YAML 驱动 | CI 友好 |
| Ragas | 开源 | RAG 专评 |

**经验**：客户在 AWS → AgentCore Evaluations + CloudWatch GenAI Observability 一站到位；多云或要进 CI → Promptfoo + LangFuse。

---

## A.6 数据工程

| 工具 | 类型 | 适合 |
|---|---|---|
| Bedrock Data Automation | AWS 托管 | 文档/图像/音视频抽取（2025-12 起 blueprint 优化；2026-04 起自定语音词表） |
| dbt | SQL 转换 | 数仓内的 ETL |
| Airflow | 编排 | 复杂工作流 |
| AWS Glue | Serverless ETL | AWS 一站式 |
| Spark / EMR | 大数据 | TB+ 规模 |
| Iceberg / Delta | 表格式 | 数据湖 |
| Snowflake / BigQuery / Redshift | 数仓 | 分析 |
| Lake Formation | AWS | 权限治理 |

---

## A.7 部署 / 运行时

| 工具 | 类型 | 适合 |
|---|---|---|
| AWS Lambda | Serverless | 单步 LLM / 简单 Agent |
| ECS Fargate | 容器 | MCP server / 中等服务 |
| EKS | K8s | 复杂 / 大规模 |
| AgentCore Runtime | AWS 托管 Agent runtime | 8h 长任务 / VPC / MCP |
| SageMaker Endpoint / JumpStart | 训练 + 部署 | 自部署模型 |
| SageMaker HyperPod | 训练集群 | 自训 / 大规模 fine-tune |
| Step Functions | 编排 | 长流程 / HITL |
| API Gateway | API 网关 | 鉴权 + 限流 |
| AppConfig | 配置中心 | prompt / model 热切 |

---

## A.8 安全 / 合规

| 工具 | 用途 |
|---|---|
| IAM Identity Center | SSO + SCIM |
| KMS | 密钥管理 |
| Secrets Manager | API key / OAuth |
| CloudTrail | API 审计 |
| Config | 配置合规 |
| Security Hub | 综合安全 |
| Macie | PII 自动发现 |
| Bedrock Guardrails | LLM 内容过滤；2025-11 起支持代码用例（注释/标识符/字面量）；2026-04 cross-account safeguards GA |
| AgentCore Policy（Cedar） | Agent 工具调用层面的策略守门（2025-12 preview） |
| WAF | 应用防火墙 |

---

## A.9 IaC

| 工具 | 类型 | 适合 |
|---|---|---|
| Terraform | 多云 | 通用 |
| AWS CDK | 编程式 IaC | AWS 项目 + 复杂逻辑 |
| AWS SAM | Serverless 专用 | Lambda / API GW |
| Pulumi | 编程式多云 | 同 CDK 思路但多云 |
| CloudFormation | AWS 原生 | 简单堆栈 |

---

## A.10 监控 / 告警

| 工具 | 用途 |
|---|---|
| CloudWatch + GenAI Observability | AWS 原生 metrics + logs + LLM/Agent 仪表盘 |
| X-Ray | AWS 分布式 trace |
| OpenTelemetry | 协议 + SDK（Strands / LangChain / LangGraph 兼容） |
| Datadog | 综合 observability |
| Grafana / Prometheus | 开源 + 私有部署 |
| Sentry | 错误追踪 |
| PagerDuty | on-call |
| Slack / Teams alerts | 协作通知 |

---

## A.11 客户协作

| 工具 | 用途 |
|---|---|
| Confluence | 客户 wiki |
| Jira | 客户工单 |
| Notion | FDE 内部笔记 |
| Slack / Teams | 即时沟通 |
| Linear | 高效工单管理 |
| Loom | 屏幕录屏（解释问题） |
| Excalidraw | 架构图 |
| Miro | 协作白板 |

---

[← 返回目录](../../)
