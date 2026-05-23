---
title: "Part IV — 工程化落地"
nav_order: 14
has_children: true
---

# Part IV: 数据与集成 — 面对客户真实环境

> 适用范围：**现场交付主线**（数据 / 集成 / VPC / 合规）；LLM 应用主线在涉及客户真实数据时也需要全部读

---

## 这个 Part 要解决什么问题

LLM 应用做出 demo 后，最容易死在两件事上：

1. **数据接不上** —— 客户数据在 SAP / Oracle / 私有云 / 离线 / 混合云
2. **接上了但合规过不了** —— PII / 跨境 / 等保 / 审计

Palantir 风格的 FDE 50% 时间在这一 Part 的话题上。LLM 风格的 FDE 走到生产前一定会撞上。

这个 Part 给三章实操：

- **Chapter 9**：数据栈本身（Ontology / ETL / 实时管道）
- **Chapter 10**：客户 VPC / 私有部署 / 离线机房怎么做工程
- **Chapter 11**：和遗留系统对接（SSO / SCIM / API / 审计）

## 包含章节

详见 [SUMMARY.md](../SUMMARY.md)。

## 与其他 Part 的关系

- **前置**：Part II 的 Discovery 必须把数据现状摸清楚（Ch 4.5 数据准入）
- **并行**：Part III 的 Scaffolding 阶段，数据接入工作并行进行
- **后续**：Part V 的生产化、Part VI 的 Agent 工具调用都依赖这一 Part 的基础

---

[← 返回目录](../README.md)
