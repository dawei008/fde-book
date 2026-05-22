# 附录 A: FDE 工具栈速查表 (2026 版)

每类 3-5 个候选 + 选型维度。供 PoC 选型时 30 分钟决策用。

---

## A.1 模型 API

| 模型 | 强项 | 适合场景 | 价格档 |
|---|---|---|---|
| Claude 3.5 Sonnet | 平衡 + 长上下文 | 通用 RAG / Agent | 中 |
| Claude 3 Opus | 推理强 | 复杂任务 / Judge | 高 |
| Claude 3 Haiku | 快 + 便宜 | 高 QPS / 简单任务 | 低 |
| GPT-4o | 强 + 多模态 | 通用 + 视觉 | 中高 |
| GPT-4o-mini | 性价比 | 高 QPS 通用 | 低 |
| Llama 3.1 70B | 开源旗舰 | 私有部署 | 自部署 |
| Qwen2.5 72B | 中文强 | 中文场景 | 自部署 |
| DeepSeek V3 | 推理 + 中文 | 中文 + 推理 | 自部署 |
| Bedrock Titan | AWS 原生 | AWS 一站式 | 中低 |
| Mistral Large | 欧洲 | 多语言 | 中 |

**选型维度**: 部署形态 (云/私有) / 上下文长度 / 中英文 / 推理需求 / 月度预算

---

## A.2 编排 / 框架

| 框架 | 强项 | 适合阶段 | 风险 |
|---|---|---|---|
| LangChain | 生态最大 | PoC 快出 demo | 抽象漏 |
| LlamaIndex | RAG 专精 | RAG 项目 | Agent 弱 |
| LangGraph | 状态图 + Agent | 生产 Agent | 学习曲线 |
| Bedrock Agents | AWS 一站式 | AWS 项目 | 锁定 AWS |
| AutoGen | 多 agent | 研究 / 复杂多 agent | 不太稳 |
| CrewAI | 角色扮演 | 内容 / 研究 | 不太稳 |
| 原生 SDK | 最稳 | 生产关键路径 | 开发慢 |

**经验**: PoC 用 LangChain, 生产换原生 SDK + 状态机。

---

## A.3 向量库 / Knowledge Base

| 工具 | 形态 | 适合规模 | 备注 |
|---|---|---|---|
| Bedrock Knowledge Bases | AWS 托管 | 中 | OpenSearch 后端默认 |
| OpenSearch (Serverless / 自部署) | AWS / 开源 | 中-大 | hybrid search 强 |
| Pinecone | SaaS | 中-大 | 最省心，但成本高 |
| Weaviate | 开源 + SaaS | 中 | 多 modal |
| pgvector | PostgreSQL 插件 | 小-中 | 客户已有 PG 时优先 |
| Milvus | 开源 | 大 | K8s 部署 |
| Chroma | 开源 | 小 / PoC | 内存型 |
| Aurora pgvector | AWS Aurora | 小-中 | VPC 内首选 |

**选型维度**: 规模 / 部署 / 元数据过滤 / 客户已有什么

---

## A.4 Eval / Trace

| 工具 | 类型 | 强项 |
|---|---|---|
| Bedrock Evaluations | AWS 托管 | Model / KB / Agent 三类 eval |
| LangFuse | OSS + Cloud | LLM trace + eval 一站 |
| LangSmith | LangChain 官方 | LangChain 项目 |
| Phoenix (Arize) | 开源 | 私有部署友好 |
| DeepEval | Python 库 | 写在 pytest 里 |
| Promptfoo | YAML 驱动 | CI 友好 |
| Ragas | 开源 | RAG 专评 |
| Helicone | 代理 trace | OpenAI 兼容代理 |

**经验**: PoC 用 LangFuse Cloud，企业用 LangFuse 自部署 / Phoenix。

---

## A.5 数据工程

| 工具 | 类型 | 适合 |
|---|---|---|
| dbt | SQL 转换 | 数仓内的 ETL |
| Airflow | 编排 | 复杂工作流 |
| AWS Glue | Serverless ETL | AWS 一站式 |
| Spark / EMR | 大数据 | TB+ 规模 |
| Iceberg / Delta | 表格式 | 数据湖 |
| Snowflake / BigQuery / Redshift | 数仓 | 分析 |
| Lake Formation | AWS | 权限治理 |
| OpenLineage | 血缘 | 数据血缘 |

---

## A.6 部署 / 运行时

| 工具 | 类型 | 适合 |
|---|---|---|
| AWS Lambda | Serverless | 单步 LLM / 简单 Agent |
| ECS Fargate | 容器 | MCP server / 中等服务 |
| EKS | K8s | 复杂 / 大规模 |
| SageMaker | 训练 + 部署 | 自训模型 |
| SageMaker JumpStart | 一键部署 | LLM 自部署 |
| Step Functions | 编排 | 长流程 / HITL |
| API Gateway | API 网关 | 鉴权 + 限流 |
| AppConfig | 配置中心 | prompt / model 热切 |

---

## A.7 安全 / 合规

| 工具 | 用途 |
|---|---|
| IAM Identity Center | SSO + SCIM |
| KMS | 密钥管理 |
| Secrets Manager | API key / OAuth |
| CloudTrail | API 审计 |
| Config | 配置合规 |
| Security Hub | 综合安全 |
| Macie | PII 自动发现 |
| Bedrock Guardrails | LLM 内容过滤 |
| WAF | 应用防火墙 |

---

## A.8 IaC

| 工具 | 类型 | 适合 |
|---|---|---|
| Terraform | 多云 | 通用 |
| AWS CDK | 编程式 IaC | AWS 项目 + 复杂逻辑 |
| AWS SAM | Serverless 专用 | Lambda / API GW |
| Pulumi | 编程式多云 | 同 CDK 思路但多云 |
| CloudFormation | AWS 原生 | 简单堆栈 |
| Bicep | Azure | Azure 项目 |

---

## A.9 监控 / 告警

| 工具 | 用途 |
|---|---|
| CloudWatch | AWS 原生 metrics + logs |
| X-Ray | AWS 分布式 trace |
| Datadog | 综合 observability |
| Grafana / Prometheus | 开源 + 私有部署 |
| OpenTelemetry | 协议 + SDK |
| Sentry | 错误追踪 |
| PagerDuty | on-call |
| Slack alerts | 协作通知 |

---

## A.10 客户协作

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

[← 返回目录](../README.md)
