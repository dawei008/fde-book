---
title: "术语表"
nav_order: 90
---

# 术语表

> 按字母 / 拼音排序。引用页见 [bibliography](../bibliography/)。⭐ 标记表示全书高频核心术语。

---

## A

**AgentCore** ⭐ — Amazon Bedrock 旗下的 agent 托管平台（2024 年底推出，2025 年快速迭代）。本书使用其中 Runtime / Gateway / Memory / Identity / Observability / Evaluations / Policy 等能力，覆盖 agent 的 serverless 部署、MCP 工具网关、跨 session 上下文、Cedar policy 守门、OTel trace 评估等。Ch 6 / 8 / 14 / 15 主线。

**A. Lawrence** — 《Forward Deployed Engineer Rule Book》(2025-10) 作者，目前唯一以 ISBN 出版的英文 FDE 专著（其他 FDE 文献以 playbook / blog 形式发表）。

**Agent (AI Agent)** — 能自主规划、调用工具、迭代执行的 LLM 应用。本书 Part VI 重点。

**Agent Toolset** — 给 Agent 暴露的工具集合（read/write/exec/network/...）。Ch 14 主题。

**Anthropic** — Claude 模型的制造商。

**AWS GenAI Innovation Center** — Amazon 的 FDE 等价部门，官方使用 "Forward deployment engineering" 术语，公开 45 天 / 73% 数字。

## B

**Bob McGrew** — 前 OpenAI Chief Research Officer。"Sell the outcome, not the product" 提出者。

## C

**Cedar** — AWS 开源的 policy 描述语言（自然语言式 ABAC）。AgentCore Policy 用 Cedar 定义"哪个 agent / 哪个 session / 哪个工具"在什么条件下能调。区别于 Bedrock Guardrails 的"内容守门"，Cedar 是"动作守门"。Ch 14 / 15 出现。

**Conikeec** — Substack 作者，发表 *The Forward Deployed Engineer Playbook: A Practitioner's Field Manual (Early Draft)*。

**Confluence** — Atlassian 的企业 wiki。客户文档库的常见落地形态，FDE Discovery 阶段绕不开。

## D

**Discovery** — FDE 第一阶段：观察客户工作流、读现有系统、找真问题。Part II 主题。

**Dual-Credential Training** — Lawrence 概念：FDE 必须同时拥有"工程信誉 + 行业信誉"。

## E

**ETL (Extract-Transform-Load)** — 经典数据管道动作。Ch 9 主题。

**Eval / Eval Set / Eval-driven** — 评估集；先写评估集再写功能代码的开发流。Ch 8 主线。

**Embedded Problem Solver** — Lawrence 概念：FDE 是被嵌入到客户问题里的解题人。

## F

**FDE (Forward Deployed Engineer)** — 直接驻扎在客户现场、把 AI / 软件落到生产的工程师角色。本书主角。

**Fine-tuning** — 用客户私有数据继续训练 LLM。Ch 7 选型决策点之一。

**Fix Forward** — Lawrence 工法：在客户现场就地修问题，不带回总部。

**Foundry** — Palantir 的旗舰平台，Ontology + 数据集成 + 应用层。Ch 9 参照。

**Forward Deployment Engineering** — AWS 官方术语，对应其他公司的 "FDE"。

## G

**GTM (Go-To-Market)** — 把产品送到客户手上的方式。

**Guardrails (Bedrock Guardrails)** — Bedrock 的内容安全护栏。守 input / output 内容（PII 脱敏、敏感词、prompt injection、幻觉/grounding 检测、denied topic 拒答）。和 AgentCore Policy 是不同维度——Guardrails 守"模型说了什么"，Policy 守"agent 做了什么动作"。Ch 13 主题。

## H

**Handoff** — FDE 离场时把项目交回客户内部团队的动作。Ch 17 主题。

## I

**Immersion Before Judgment** — Lawrence 工法：动手前先沉浸到客户工作流。

**Inference Profile** — Bedrock 的跨区推理配置，model ID 形如 `us.anthropic.claude-…`、`apac.anthropic.…`、`global.anthropic.…`。Claude 4.6 系列在 Bedrock 上必须走 inference profile，不能用 on-demand model ID 直接调。Ch 6 实操坑点之一。

## J

**JD (Job Description)** — 招聘描述。

## L

**LLM (Large Language Model)** — 大语言模型。本书假设你已会调用 API。

## M

**MCP (Model Context Protocol)** ⭐ — Anthropic 牵头的开放协议，标准化 Agent 与外部工具的连接方式。Ch 15 主题。

**Morgan Stanley (MS)** — OpenAI 公开案例中的合作方，6-8+4 周期来自此案例。

## N

**Nabeel Qureshi** — Palantir 早期员工，FDE 模式最有影响力的英文阐释者。

## O

**Ontology** ⭐ — 客户业务概念的形式化建模（实体、属性、关系、动作）。Palantir 核心抽象，FDE 数据线主战场。Ch 9 重点。

**Outcome (in "Sell the outcome")** — 客户业务结果（收入、成本、风险），区别于功能 / 工具 / 演示。

## P

**Palantir** — FDE 模式的发明公司。

**PoC (Proof of Concept)** — 概念验证。本书 Ch 12 重点是 "PoC → 生产" 的过线条件。

**Private Deployment / VPC Deployment** — 客户私有部署 / VPC 部署。Ch 10 主题。

## R

**RAG (Retrieval-Augmented Generation)** — 检索增强生成。Ch 7 选型决策点之一。

**Rule Book** — 简称指 A. Lawrence 的《Forward Deployed Engineer Rule Book》。

## S

**SCIM (System for Cross-domain Identity Management)** — 企业身份同步标准。Ch 11 主题。

**Sell the outcome, not the product** — Bob McGrew 第一定律。Ch 2 主题。

**SOW (Statement of Work)** — 工作说明书 / 项目范围书。Ch 5 主题。

**SSO (Single Sign-On)** — 单点登录。客户合规几乎必查。Ch 11 主题。

**Skill** ⭐ — Anthropic 的 agent 扩展形态：一个目录加 `SKILL.md`（含 `name` / `description` frontmatter）+ body + 同目录脚本/模板。Claude Code / Agent SDK / Claude API 三处通用，按 description 命中按需加载，body 不命中不消耗 token。和 Tool（能力）/ MCP（互操作）并列为 agent 三种扩展形态。Ch 16 主题。

**Strands** — AWS 推出的轻量 agent SDK，与 AgentCore 配合使用。本书 Ch 14 demo 的 agent 编排层用 Strands；Strands 在两百行内能写完一个生产级 multi-tool agent，复杂度介于裸 boto3 与 LangGraph 之间。Ch 6 编排 Level 1 / Ch 14 主线。

## T

**T 字成长 (T-shaped Growth)** — 工程深度 + 行业纵深。Ch 18 主题。

**Trace / Tracing** — 分布式追踪。Ch 13 主题。

## V

**VPC (Virtual Private Cloud)** — 虚拟私有云。客户私有部署的常见承载形式。

## 其他

**反模式 (Anti-pattern)** — 常见但有害的做法。本书每章末尾给反模式清单。

**动手清单 (Action Checklist)** — 这一章读完可以立刻照做的工程动作。本书每章末尾固定栏目。

---

[← 返回目录](../)
