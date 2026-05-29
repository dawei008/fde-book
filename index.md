---
title: 首页
nav_order: 0
description: "OpenBook · Forward Deployed Engineer — AI 应用的落地工程学"
permalink: /
---

# OpenBook · Forward Deployed Engineer
{: .fs-9 }

AI 应用的落地工程学 — 一本写给"在客户现场把 AI 跑起来"的工程师的书。
{: .fs-6 .fw-300 }

[开始阅读](preface){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }
[GitHub 仓库](https://github.com/dawei008/fde-book){: .btn .fs-5 .mb-4 .mb-md-0 }
[English version](en/README){: .btn .fs-5 .mb-4 .mb-md-0 }

---

## 这本书是什么

三章给角色定义和心智模型，十五章给可在 AWS 账号里跑通的工程实操（其中 Part VI 三章覆盖 agent 三种扩展形态：Tool / MCP / Skill），四份附录给可复用的客户启动模板。配套代码在仓库 `demos/`，每章用完即拆。

公式：

> **Outcome = Harness × Customer**
>
> Harness 提供能力，Customer 提供约束。FDE 的工作是把 Harness 装到 Customer 身上。

---

## 这本书写给谁

- 5+ 年工程经验，能独立 own 一个后端服务
- 至少跑过一次客户 PoC、至少在生产 handoff 阶段卡过一次
- 调过 LLM API、做过 demo，但还没在客户环境里跑过 agent
- 能直接读 OpenAPI、跑 SQL、看分布式 trace，不需要中间层

如果你完全没做过客户面、或者从未调用过 LLM API — 先做几个小项目再来。这本书不教这些。

---

## 怎么读

最有用的方式是 **跟着一个真实的 FDE 项目读**。每章末尾问自己：

1. 我现在的项目里有没有这一章讲的问题？
2. 如果有，我之前是怎么处理的？
3. 这一章的做法和我的差在哪里？哪种更好？

通读 6-7 小时；带着一个真实项目读，2-3 周可能更有用。

---

## 反馈

GitHub Issues 是最快的渠道。我最想要的：

- **反例**：这本书的方法在你那边失效的具体场景
- **真实数字**：你的 PoC 转化率、客户 NPS、第一周交付物
- **缺失章节**：你认为这本书漏掉的关键工程话题

下一版会吸收最强的信号。
