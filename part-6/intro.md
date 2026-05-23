---
title: "Part VI — Agent 与 MCP"
nav_order: 16
has_children: true
---

# Part VI: Agent 时代 — FDE 的新工程任务

> 适用范围：**LLM 应用主线**（数据驱动主线选读）

---

## 这个 Part 要解决什么问题

2025-2026 是 Agent 真正进入企业的一年。

不是"客服回答问题"那种 RAG，而是：
- 自动写 / 改 / 提交 PR
- 自动跨系统办事（CRM + ERP + 邮件 + 日历）
- 自动用浏览器 / 终端 / API 完成任务

Agent 给 FDE 带来的新工程问题：

1. **工具集设计** — 不是"能多就多"，是"够用 + 不出错"
2. **沙箱与权限边界** — Agent 越权后果不可控
3. **失败恢复** — 多步任务中断怎么续
4. **企业集成** — MCP（Model Context Protocol）怎么把 Agent 接到客户工具上

这个 Part 给两章实操：

- **Chapter 14**：在客户环境部署 Agent — 工具集 / 沙箱 / 失败恢复
- **Chapter 15**：MCP 与企业集成 — 把 Agent 接到客户工具上

## 包含章节

详见 [SUMMARY.md](../SUMMARY.md)。

## 与其他 Part 的关系

- **前置**：Part III (Eval) + Part IV (数据 / 集成) + Part V (生产化) 全部是 Agent 的基础
- **后续**：Part VII 完成交付与精进

---

[← 返回目录](../README.md)
