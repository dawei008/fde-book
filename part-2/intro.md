---
title: "Part II — 客户发现"
nav_order: 12
has_children: true
---

# Part II 客户发现

FDE 项目里最贵的代码，是没人要的代码。

而"没人要的代码"几乎都来自同一个地方——Discovery 没做透。客户 PM 在 kick-off 上说"我们要做一个 agent 自动写邮件"，FDE 听了就开始搞工具集成、写编排——三周后做完才发现客户真正紧迫的是"销售月底搬数据进 ERP"，是个一上午就能写完的小自动化。

这种事在 FDE 圈子里反复发生。Part I 第 1 章的四个阶段里，Discovery 之所以排在最前，就是因为一旦走偏，后面 Scaffolding / Production / Handoff 全都白搭。

---

很多工程师听到 Discovery 第一反应是"那是 PM 的事"。这本书不接受这个分工。FDE 的 Discovery 不是开会听需求然后写 PRD，是带工程师视角下到客户现场，**观察、量化、原型化**他们的真实工作流，最终输出可以扔进 CI 跑分的评估集和能签字的 SOW。

第 4 章讲 Discovery 怎么做。重点是"观察 > 提问"——客户嘴里说的工作流和他们真实在做的工作流之间，几乎一定存在一段差距，而那段差距才是 FDE 该解决的问题。这一章给你具体的观察姿势、必问的几个问题、以及怎么把现场看到的东西沉淀成一份能拿回去复盘的 Discovery 笔记。

第 5 章讲怎么把 Discovery 的结论翻译成可工程化的合同物——评估集 v0.1、验收标准、SOW。这一章是 Part II 通向 Part III 的桥：评估集是 Part III 第 8 章 CI 守门员的输入，SOW 是 Part V 第 12 章 PoC 过线判定的依据。

---

Part II 的产物（评估集 + 验收标准 + SOW）是 Part III–VII 全部工程动作的输入。Discovery 不达标，后面所有代码都是浪费。所以这两章不能跳。
