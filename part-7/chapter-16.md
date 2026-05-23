---
title: "第 16 章 项目交接"
parent: "Part VII — 交接与持续"
nav_order: 1
---

# Chapter 16: Handoff + 模式提取 — 把方案抽象成可复用资产

## 开场

```
某 FDE 完成了一个 12 周的 Agent 项目，技术上很成功。

3 个月后，客户运维找她："那个 prompt 我们想改，怎么改？"
她飞过去，2 小时改完。

6 个月后，客户："Agent 答错率上升了，您看看"
她飞过去，1 天 debug。

9 个月后，客户："我们想再加一个 use case"
她飞过去，打开自己的旧代码，发现自己也有点忘了。

FDE 的同事接到一个新客户的相似项目，跑过来问她：
  "这个怎么做来着？"
她回答："你看我之前的代码 ...
        但每个客户都不一样，重新做一遍吧。"

她公司的 CEO 看到第三个客户的报价，
问她："为什么我们 3 个相似项目都报 12 周？应该 4 周才对。"

她答不上来。

这一章讲两件事：
  1. Handoff — 让客户真正接走（你不再被电话叫飞过去）
  2. 模式提取 — 让下一个相似项目 4 周做完
```

---

## 16.1 Handoff 的工程定义

```
        Handoff = "客户能在没你的情况下独立运营这个系统"

        判断标准 (4 个能力):
        ──────────────────────────────────────

  1. 客户能独立 deploy 一次 hot fix
     (改 prompt / 改 KB / 改 model id)

  2. 客户能独立读 dashboard 找根因
     (没有 trace 你帮他看)

  3. 客户能独立跑一次 Eval
     (升级模型前不再依赖你)

  4. 客户能独立处理 Top 5 故障类型
     (而不是 P1 就打电话给你)
```

**4 个全部达到 → 真 handoff。少 1 个 = 项目还没交付完**。

---

## 16.2 Handoff 的"3 周倒计时"

不是上线那一刻才开始 handoff，是上线前 3 周开始：

```
        T-3 周 ───── T-2 周 ───── T-1 周 ───── T 上线 ───── T+4 周
        ──────       ──────       ──────       ───────     ──────

        计划         培训         影子         独立         FDE 退出
        启动         + 文档       运营         运营

  T-3   ✓ 找客户运维 owner (人 + 邮箱 + 排班)
        ✓ 写 Runbook 大纲
        ✓ Dashboard 给客户访问

  T-2   ✓ 4 小时培训 (Runbook + dashboard + Eval)
        ✓ 让客户 owner 操作一次每个动作
        ✓ Q&A

  T-1   ✓ 客户 owner 跟着 FDE 一起处理所有事情
        ✓ FDE 不主动操作，只 review 客户操作
        ✓ 一周末客户 owner 写一份 "我学到的"

  T     上线 + 灰度
        ✓ 客户 owner 主导, FDE 后排

  T+4   FDE 完全撤离
        ✓ 仍 on-call 但不主动看
        ✓ 客户每周报告自己的运营状态
```

---

## 16.3 Runbook — 给客户的"操作手册"

Runbook 不是文档，是**可操作的指令清单**。

```
        Runbook 必备的 7 个 section
        ─────────────────────────────────────

  1. 系统架构图 (一页 A4)
  2. 部署 / 回滚步骤 (命令 / 截图)
  3. Top 10 故障类型 + 处理 SOP
  4. Eval 怎么跑 + 阈值含义
  5. 关键配置在哪 + 怎么改
  6. 数据 / KB 更新 SOP
  7. Escalation 路径 (什么情况打谁电话)
```

### Runbook 的 SOP 范例

```
═══════════════════════════════════════════════════════════════════
  SOP-001: Agent 错误率突然上升
═══════════════════════════════════════════════════════════════════

  现象: dashboard 显示错误率 > 1% (基线 0.3%)

  Step 1: 检查 Bedrock 服务状态
    - 打开 https://health.aws.amazon.com
    - 看 us-east-1 Bedrock service health
    - 如果 AWS 故障 → 等 + 通知用户

  Step 2: 检查最近 commit
    - GitLab → main 分支 last 5 commits
    - 是否有 prompt / KB / model 变更
    - 如有 → 走 Step 3 (rollback)

  Step 3: Rollback
    - 命令: ./scripts/rollback.sh prod --target-version=$LAST_GOOD
    - 等 5 分钟看 dashboard
    - 错误率回到基线 → 完成
    - 没回到 → 走 Step 4

  Step 4: 联系 FDE on-call
    - Slack: @fde-oncall
    - 电话: +XX-XXX-XXXX (24h)

  Step 5: 写故障报告
    - 模板: docs/incident-template.md
    - 24 小时内提交
═══════════════════════════════════════════════════════════════════
```

**好的 Runbook 让客户 P1 故障 5 分钟止血**。

---

## 16.4 培训 — 4 小时课程

```
        Handoff 培训 4 小时议程
        ─────────────────────────────────────

  Hour 1: 系统架构 + 业务流
    ├── 数据从哪来到哪去 (15 min)
    ├── Agent 的工具集和能力边界 (15 min)
    ├── Eval 是干嘛的 (15 min)
    └── 监控仪表盘逐项讲 (15 min)

  Hour 2: 日常运营
    ├── 怎么看 dashboard (实操) (20 min)
    ├── 怎么跑 Eval (实操) (20 min)
    └── 怎么改 prompt + 灰度 (实操) (20 min)

  Hour 3: 故障处理
    ├── Top 10 故障演练 (动手) (40 min)
    └── Rollback 演练 (实操) (20 min)

  Hour 4: 数据 / KB 维护 + Q&A
    ├── KB 更新 SOP (实操) (30 min)
    └── Q&A (30 min)
```

**关键**：每个环节都要客户**亲手操作**，不是看 FDE 演示。

---

## 16.5 模式提取 — 让下一个项目快 5 倍

### 什么是"模式提取"

每个项目结束时，问 4 个问题：

```
  Q1: 这个项目里哪些工作"换个客户也基本一样"？
       → 这是可复用资产

  Q2: 哪些工作"花了大量时间但下次能避免"？
       → 这是工程模板的来源

  Q3: 哪些"客户特有的"实际上很多客户都有？
       → 这是行业模板的来源

  Q4: 哪些"我以为简单实际很难"？
       → 这是预警卡片的来源
```

### 模式提取产出 — 4 类资产

```
        FDE 的"项目后资产库"
        ───────────────────────────────────

  1. 代码模板
     - LLM RAG 起手包
     - Bedrock Agent 起手包
     - Eval CI 起手包
     - Lambda MCP server 起手包

  2. 文档模板
     - Discovery 报告模板（Ch 4）
     - SOW 模板（Ch 5）
     - Runbook 模板（本章）
     - 验收标准模板

  3. 决策卡片
     - "客户问这个 → 答这个" 速记
     - "出现这个信号 → 切到这种解法"
     - "这种问题先做这 3 件事"

  4. 反模式案例集
     - 真实故障复盘
     - 错误代价 + 教训
```

### 模板"颗粒度" 经验

```
  ❌ 太粗: "Bedrock 起手模板"
     → 一上来还是要大改

  ✓ 适中: "Bedrock + Knowledge Bases + Aurora pgvector
           VPC 部署 + IAM Identity Center 起手模板"
     → 客户 80% 用例直接用

  ❌ 太细: "招商银行私有云 RAG 起手模板"
     → 颗粒度过细只能用一次
```

---

## 16.6 模式提取的工程动作

每个项目结束 1 周内做 5 件事：

```
  1. 写 1 页 "项目复盘"
     - 我们做了什么
     - 哪些做对了 / 做错了
     - 数字 (outcome / Eval / 成本 / 时间)

  2. Code review 自己整个项目
     - 哪些代码块"显然能复用"
     - 抽出来放公司 internal repo

  3. 抽 3 个"决策瞬间"
     - 那个时刻你判断了什么 → 写成卡片

  4. 抽 1-2 个"如果重来要怎么做"
     - 写成"项目模板 v X+1"

  5. 跟同事开 1 小时 brown-bag
     - 不是炫耀成功，是讲"你不知道的坑"
```

---

## 16.7 行业模板 — 一个例子

```
  行业: 保险公司
  模板: "保险 RAG/Agent 起手包 v3.2"

  内容:
  ├── 行业知识
  │   ├── 保险公司组织架构常见样
  │   ├── 核保 / 理赔 / 销售 三条主流
  │   ├── 通用监管要求 (银保监 / 等保)
  │   └── 通用数据栈 (核心 + ECIF + 渠道 + 风控)
  │
  ├── 通用 Discovery 模板
  │   ├── 12 个保险特有的问题
  │   └── 5 类关键产出物清单
  │
  ├── 代码模板
  │   ├── 保单条款分片 (PDF + 表格)
  │   ├── 客户身份匹配 (ID 卡 / 客户号 / 保单号 mapping)
  │   ├── Bedrock + Aurora pgvector + KMS 部署 IaC
  │   └── 等保审计日志规范
  │
  ├── Eval 模板
  │   ├── 保险问答 200 条 golden
  │   ├── 安全性 50 条 (PII / 不当承诺)
  │   └── 业务专家校准流程
  │
  └── Handoff 模板
      ├── 保险公司运维交接 SOP
      └── 监管检查应答模板
```

**新 FDE 接保险客户**：用 v3.2 起步，第 4 周客户已经看到 demo。

---

## 16.8 公司层面的模式管理

模式提取不是个人行为，公司应该有结构化沉淀：

```
        FDE 团队的"知识中心" 结构
        ─────────────────────────────────

  公司 Wiki:
    /fde-knowledge/
      patterns/                (跨行业)
        rag-starter/
        agent-starter/
        eval-ci-starter/
      industries/              (行业)
        insurance/
        finance/
        retail/
        manufacturing/
      anti-patterns/           (反例)
        2025-Q3-incidents.md
        ...
      decision-cards/          (决策卡片)
      tools/                   (内部工具)

  Code Repo:
    fde-platform/
      starter-kits/
      common-lambdas/
      shared-prompts/
      eval-suites/
```

**FDE 老手 vs 新手的差距 80% 在这个知识中心的厚度**。

---

## 关键引用

> "*Handoff is not a milestone — it's a 4-week process you start 3 weeks before launch.*"
> — A. Lawrence, *FDE Rule Book*, 2025

> "*The second project on a customer should take 1/3 the time of the first.*"
> — Bob McGrew @ YC, 2025

> "*Pattern extraction is the difference between a consultant and an engineer.*"
> — AWS GenAI Innovation Center, 2025

---

## 动手清单

项目最后 4 周必做：

1. **T-3 周开始 Handoff 倒计时**（16.2 节）
2. **写 Runbook 7 sections**（16.3 节）
3. **客户运维 4 小时培训**（亲手操作）
4. **客户 owner 影子运营 1 周**
5. **项目结束 1 周内写复盘 + 抽 3 个决策卡片**
6. **抽公司内部能复用的代码 / 文档 / 配置**
7. **跟同事 brown-bag 1 小时**（讲坑而不是讲赢）

---

## 反模式清单

- ❌ **上线那一周才想起 Handoff**（来不及培训）
- ❌ **Runbook 写成"功能文档"**（不是可操作 SOP）
- ❌ **培训只有 PPT 没有动手**（客户记不住）
- ❌ **客户运维 P1 就打电话给 FDE**（4 个能力没培训到位）
- ❌ **项目结束就下一个，不复盘**（每个项目都从零）
- ❌ **模式只在自己脑袋里**（同事不知道，公司不知道）
- ❌ **复盘只讲赢**（最值钱的是讲坑）

---

## 与下一章的关系

到这里，从 Discovery → Scaffolding → 生产 → Handoff → 模式提取的全流程闭环。

最后一章讲：FDE 自身的能力如何长期成长 —— 不是技术追新，而是**T 字成长**：工程深度 + 行业纵深的双向加深。

[← Part VII 导读](intro.md) · [下一章: T 字成长 →](chapter-17.md)
