---
title: "阅读指南"
nav_order: 2
---

# 阅读指南

> 17 章，约 6-7 小时读完。两条主线并存，按你的 FDE 类型选路线。

---

## 按 FDE 类型选路线

### 路线 A：LLM 应用 FDE（推荐主路线）

**适合**：在 OpenAI / Anthropic / Cohere / 中国大模型公司或下游创业公司做 LLM 应用落地的 FDE。

**路线**：Part I → Part II → **Part III** → Part V → **Part VI** → Part VII。

**重点章**：Ch 6 技术栈速决矩阵、Ch 7 RAG/FT/Agent 决策树、Ch 8 Eval-driven、Ch 14 Agent 部署、Ch 15 MCP。

**用时**：约 5 小时。

---

### 路线 B：现场交付 FDE（Palantir 风格）

**适合**：在 Palantir、企业 AI 咨询公司、云厂商应用落地团队做客户现场数据 + 软件交付的 FDE。

**路线**：Part I → Part II → **Part IV** → Part V → Part VII。

**重点章**：Ch 9 Ontology / ETL、Ch 10 VPC 部署、Ch 11 SSO/SCIM/审计、Ch 12 PoC 过线、Ch 16 Handoff。

**用时**：约 4 小时。

---

### 路线 C：通读（FDE 团队 lead / 想拉通两条线）

**适合**：FDE 团队负责人、要为团队做内部培训的 staff/principal、跨两类项目的 FDE。

**路线**：从 Part I 一直读到 Part VII。

**用时**：6-7 小时。

---

### 路线 D：当工具书

**适合**：有一个具体问题，比如"客户要私有部署，我怎么估算硬件"、"PoC 验收标准怎么写"。

**用法**：直接查附录 A-D 和对应章节。

| 你的问题 | 直接查 |
|---|---|
| 选模型 / 框架 / 向量库 | 附录 A、附录 B |
| 写评估集 | Ch 8、附录 C |
| 写 SOW / 安全问卷 / 风险登记 | 附录 D |
| Agent 沙箱怎么搭 | Ch 14 |
| 客户 VPC 部署清单 | Ch 10 |

---

## 章节难度

```
🟢 直接照做 — 工程师拿来就能用
🟡 需要思考 — 需要结合自己项目判断
🔴 需要决策权 — 涉及组织 / 商务 / 合规判断
```

| Part | 难度 |
|---|---|
| I 起手 | 🟢 |
| II 客户发现 | 🟡 |
| III 脚手架 | 🟢 |
| IV 数据与集成 | 🟡 |
| V PoC→生产 | 🟡 |
| VI Agent 时代 | 🟢 |
| VII 交付与精进 | 🔴 |

---

## 每章结构

每章从一个具体场景开篇——一段会议、一次故障、一份评估集——再展开几节工程判断，中间穿插反思段落。反模式不放在结尾的清单里，而是和正文场景一起出现，让"这件事为什么是错的"和"它在什么处境下被犯下"始终绑在一起。

时间紧的话，直接看每节的小标题，挑当下项目对得上的那几节读。

---

## 出场的核心概念

完整术语见 [glossary.md](glossary.md)。最关键的：

| 概念 | 一句话 |
|---|---|
| **Sell the outcome** | 不卖工具，卖结果 — McGrew 第一定律 |
| **Fix Forward** | 在客户现场就地修，不带回总部 — Lawrence 工法 |
| **Eval-driven** | 先有评估集，再写代码 — 本书 Ch 8 主线 |
| **Ontology** | Palantir 的核心抽象，本书 Ch 9 给工程师视角 |
| **Agent Toolset** | 给 Agent 暴露的工具集合，本书 Ch 14 主题 |
| **MCP** | Model Context Protocol，把 Agent 接到企业工具的标准 |
| **PoC 过线** | 从概念验证到生产的鸿沟，本书 Ch 12 主题 |
| **Handoff** | FDE 离场时的交付动作，本书 Ch 16 主题 |

---

## 配套资源

- **research/** — 本书所有研究素材公开可查（07 篇）
- **附录 D** — 12 份第一周可用模板
- **GitHub Issues** — 提反例 / 真实数字 / 缺章建议

---

下一步：[前言](preface.md) → [Part I 导读](part-1/intro.md)
