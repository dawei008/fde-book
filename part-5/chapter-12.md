---
title: "第 12 章 PoC 到生产"
parent: "Part V — 上线与运营"
nav_order: 1
---

# Chapter 12: PoC 过线条件 — 哪些能过，哪些卡死

## 开场

```
某 SaaS 公司。FDE 第 6 周交付 PoC，效果惊艳：
  - Demo 现场客户 CEO 鼓掌
  - Eval 总分 0.91
  - 媒体报道也写了

第 7 周客户 IT 总监问："上生产怎么走？"
FDE 回："照这个 demo 部署就行。"

第 14 周还没上线。
卡在哪里？

  - 没有 staging 环境（demo 就是 dev 改的）
  - 没有部署脚本（demo 是手动起的）
  - 没有压测（每秒 1 个请求是上限）
  - 没接客户监控（运维不知道怎么 oncall）
  - 成本预算没批（一个月 $20K，老板没准备）
  - 灰度方案没有（只能"all or nothing"）

复盘：PoC 阶段 没把"生产化的 6 件事" 同步做。
PoC 越炫，生产化越难。

这一章给：PoC 阶段就要做的 6 件事，
以及"4 个一定卡死"的信号。
```

---

## 12.1 PoC vs 生产 — 工程指标差 100 倍

```
                    PoC 标准              生产标准
                    ─────────             ─────────

  并发                单用户 / 几个         100-10K QPS

  可用性              "能演示就行"          99.5% / 99.9%

  延迟                P50 5 秒可接受        P95 < 3 秒

  容错                "出错重启"            自动重试 + 隔离

  可观测              控制台 print          全链路 trace

  权限                FDE 手里的 admin     RBAC + 审计

  数据                "你给我 50 条"        全量 + 实时

  成本                老板没说              月度预算控制

  发版                "我手改 prompt"       CI/CD + 灰度

  客户                FDE 一直在            客户运维独立维护
```

**90% 的 PoC 失败不是技术问题，是"工程标准"和生产差太远**。

---

## 12.2 PoC 阶段就要做的 6 件事

### 事 1：环境分层（dev / staging / prod）

```
        从第 1 天就分:
        ──────────────────────────────────────

  dev:        FDE 工作台，可随便改
  staging:    和生产同等配置，跑回归
  prod:       客户运维管理，最严

  即使 PoC 阶段，至少 staging 必须有
  否则: "demo 改的 prompt 没人记得" → 上线找不到
```

### 事 2：CI/CD 第一周就接

```
        最小 CI/CD pipeline:
        ──────────────────────────────────────

  on push to feature branch:
    - lint
    - unit test
    - eval (50 条 seed)

  on PR to main:
    - eval (200 条 golden)
    - integration test
    - cost estimate

  on merge to main:
    - 自动部署 dev
    - 触发 staging deploy

  on tag release:
    - 部署 staging
    - 等人 sign-off
    - canary deploy prod (10% → 50% → 100%)
```

**没有 CI/CD 的 PoC 不要进 PoC**。

### 事 3：监控 / Trace 第一周就接

```
  必有 trace 4 维:
    1. Latency (per step)
    2. Cost (input/output tokens, model)
    3. Quality (eval / 用户反馈)
    4. Error (stack trace + correlation_id)

  工具选型 (复习 Ch 6):
    - 云上: LangFuse Cloud / LangSmith / Bedrock built-in
    - 私有: LangFuse self-host / Phoenix
```

### 事 4：成本透明（PoC 阶段就开始报）

```
        每周报表必有:
        ──────────────────────────────

  - 本周 token 消耗 (input + output)
  - 按模型分布
  - 按场景分布 (RAG / Agent / Eval)
  - 单次请求平均成本
  - 月度推算

  PoC 阶段就开始 → 不会出现 "上线一周烧 $50k 老板震惊"
```

### 事 5：客户运维"挂上来"

```
        从第 4 周开始:
        ────────────────────────────────────

  - 客户至少 1 个运维加入项目 Slack
  - 一起 on-call (虽然 PoC 阶段不真值班)
  - 一起看 dashboard
  - 一起处理告警

  不挂上来: 上线后客户运维"接手" =
            从零开始学，3 个月才能独立
  挂上来:    上线时客户运维已经熟悉，
            1 周交接完
```

### 事 6：可降级方案（fallback）

```
        关键路径必须有 fallback:
        ────────────────────────────────────

  Bedrock 模型挂 → 切到备用模型 (跨 region)
  Knowledge Base 挂 → 切到 cached embeddings
  Agent 工具挂 → 拒绝服务 + 友好错误信息
  全挂 → 静态回复 + 工单创建

  PoC 阶段至少:
    ✓ 写一个"全挂时"的兜底
    ✓ 演练一次"全挂"
```

---

## 12.3 4 个"一定卡死"的信号

### 信号 1：客户没人愿意做 owner

```
        "这个项目谁负责"答不上来的项目:

  ✗ 业务方说"这是 IT 的事"
  ✗ IT 方说"这是业务的事"
  ✗ 老板说"两边一起负责"

  → 上线后没人 oncall, 没人审 prompt 变更, 没人改 KB
  → 6 个月内"自然死亡"
```

**FDE 的应对**：在 SOW 里硬性写"客户方 owner"，没有 owner 不开工。

### 信号 2：Eval 集是 FDE 自己写的

```
  FDE 一个人写 200 条 Eval →
  上线后客户业务专家说"这些题不是我们要的"
  → Eval 全部重做
  → 上线推迟 2-4 周

  应对: 第 3 周开始就拉客户业务专家共标
       FDE 写初版 → 业务专家审 → 再标
```

### 信号 3：成本到月底才算

```
  Demo 阶段每月 $500
  上线第一周 $5K
  客户老板看到账单："这不能用，砍掉"

  应对: PoC 第 2 周就给老板报第一份成本测算
       上线前给"3 种规模下的成本曲线"
       上线后每周成本仪表盘
```

### 信号 4：客户 IT 没参加任何 PoC 评审

```
  6 周 PoC 全是和业务对接，零 IT 参与
  上线时 IT 一票否决:
    "VPC Endpoint 没接"
    "审计日志不达标"
    "等保过不了"
  → 推倒重来

  应对: 第 1 周 Discovery 就拉 IT 进来
       每两周一次 IT-FDE 同步会
       第 4 周开始 IT 参加 demo
```

---

## 12.4 PoC 过线的 5 项硬指标

把这 5 项写进 SOW，达不到就不上生产：

```
┌─────────────────────────────────────────────────────────────────┐
│  指标                       过线条件                              │
├─────────────────────────────────────────────────────────────────┤
│  Eval 综合分                ≥ SOW 约定值 (典型 0.85)            │
│  生产场景压测               P95 < 3s,  100 QPS 稳定 30 分钟      │
│  成本                        单次请求成本 ≤ 预算 X 元            │
│  审计                        所有调用 100% 上 CloudTrail/日志    │
│  灰度方案                    能 1% / 10% / 50% / 100% 灰度切     │
└─────────────────────────────────────────────────────────────────┘
```

**5 项 5 全过 → 进灰度生产**。少 1 项 → 推迟。

---

## 12.5 一个真实的 PoC → 生产时间表

```
        12 周项目典型时间表
        ──────────────────────────────────────

  W1-2  Discovery (Part II)
        - 5 件物料: 报告 / Eval seed / SOW
        - 客户 owner / IT 接入 / 安全 review

  W3-6  Scaffolding (Part III)
        - 6.7 速决表 baseline
        - Eval CI 接好 (Ch 8)
        - 第一版 demo

  W6    PoC 中检
        - 12.4 五项硬指标第一次跑
        - 哪些不达标？

  W7-9  Productionize Phase 1
        - 数据接入 + VPC + SSO + 审计 (Part IV)
        - 监控 + 成本 + 灰度准备 (Ch 13)

  W10   PoC 终检
        - 12.4 五项硬指标全过
        - 客户 IT + 业务 + 老板三方签字

  W11   Canary 灰度 (10% → 50%)

  W12   100% 上线
        + Handoff (Ch 16) 启动
```

**节奏控制**比"功能完成度"更重要。

---

## 12.6 一个真实反例

> *某互联网公司 FDE 团队做了一个 8 周的 LLM 客服 PoC。
> 第 8 周客户 CEO 看 demo 满意，准备签 12 个月合同。*
>
> *PoC 期间这些没做：*
> *- 没接客户的 SSO（用了 service account）*
> *- 没接 CloudTrail（说"上线再加"）*
> *- 没做压测（demo 时一个 QPS）*
> *- 没和客户 IT 对过架构（IT 第一次见图是签合同前）*
>
> *合同签了之后，IT 部门花 3 周 review 架构，提了 47 条修改意见。
> 重做花了 5 周。*
>
> *客户业务方："你们承诺 8 周上线，怎么 16 周还在改？"*
>
> *FDE 团队失去了下一阶段续单。*

**复盘**：PoC 期间，**业务方满意 ≠ 项目能上**。**IT / 安全 / 合规 / 财务任何一方不满意，都能让项目推倒重来**。

---

## 关键引用

> "*The PoC is not the project — it's the trailer for the project.*"
> — A. Lawrence, *FDE Rule Book*, 2025

> "*A 73% PoC-to-production conversion rate doesn't come from better models. It comes from running PoC like it's already production.*"
> — AWS GenAI Innovation Center, 2025

> "*Every PoC has a critic — find them in week 1, not week 8.*"
> — Bob McGrew @ YC, 2025

---

## 动手清单

PoC 项目第 1 周必做：

1. **写 SOW 里的"PoC 过线 5 项硬指标"**（12.4 节）
2. **第 1 天分好 dev / staging / prod 三套环境**
3. **CI/CD 第一周接好**（Eval + lint + deploy）
4. **接 trace + cost dashboard**（CloudWatch 或 LangFuse）
5. **拉 IT / 安全 / 财务 / 业务方 owner 进项目群**
6. **第 4 周开始客户运维和 FDE 一起看 dashboard**
7. **第 6 周做一次"假装上线"演练**（包括成本测算 + 压测 + 演练故障）

---

## 反模式清单

- ❌ **把 PoC 当成"演示版"做**（一切都要重做才能上）
- ❌ **dev 直接 demo**（没 staging）
- ❌ **PoC 期间不接监控 / 审计 / SSO**（说"上线再加"）
- ❌ **客户 IT 不在项目群**（最后一刻被一票否决）
- ❌ **成本到上线后才算**（老板不批，项目暴毙）
- ❌ **没有灰度方案，只能 0% / 100%**（出问题不能优雅回退）

---

## 与下一章的关系

这一章给了"PoC 过线的 5 项硬指标"。下一章具体讲：监控 / 成本 / 灰度 / 回滚 — 生产化"四件套"的工程实操。

[← Part V 导读](intro.md) · [下一章: 可观测性 / 成本 / 灰度 / 回滚 →](chapter-13.md)
