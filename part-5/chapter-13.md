---
title: "第 13 章 监控与 Guardrails"
parent: "Part V — 上线与运营"
nav_order: 2
---

# Chapter 13: 可观测性 / 成本 / 灰度 / 回滚

## 开场

```
某零售客户的 Agent 上线第 3 天凌晨 2 点：

  P1 告警: Agent 错误率 18% (基线 < 0.5%)

  on-call 的客户运维打电话给 FDE：
    "你们的 Agent 出问题了，怎么办？"

  FDE 心想（应该）：
    1. 看 trace → 找根因 (5 分钟内定位)
    2. 1% 流量切回旧版 → 止血 (2 分钟内)
    3. 不行就 100% 切回 (1 分钟内)
    4. 修完后再灰度上 → 可控

  FDE 实际（坏情况）：
    1. trace 没接 → 不知道哪一步错
    2. 没有灰度通道 → 要么硬撑要么全部下线
    3. 没有 baseline → 不知道是不是真的"比平时差"
    4. 1 小时手忙脚乱 → 客户看在眼里

这一章给的"四件套" —— 观测 / 成本 / 灰度 / 回滚 ——
就是为了那个凌晨 2 点能 5 分钟止血。
```

---

## 13.1 可观测性 — 不只是"看日志"

```
        三大可观测性维度
        ───────────────────────────────

  Metrics (聚合数字)
    QPS, P50/P95 latency, error rate, token throughput
    → 看趋势, 设告警

  Logs (单条文本)
    具体错误堆栈, prompt + response 全文
    → 排查根因

  Traces (跨服务调用链)
    用户请求 → API → 检索 → 模型 → 工具 → 返回
    → 找瓶颈 / 串联问题
```

LLM 应用的可观测有 4 个**特殊维度**：

```
  1. Token 经济:
     - input/output tokens per request
     - cost per request (按模型计价)

  2. Eval 漂移:
     - 生产采样回来 → 跑 Eval → 看分数趋势

  3. Hallucination 监控:
     - 答案不被 grounding 文档支持的比例
     - 用 LLM-as-judge 实时打分（采样）

  4. Agent 路径:
     - 单次完成步数分布
     - 工具调用成功率
     - 重试次数
```

### AWS 实操：可观测三件套

```
        最小可观测栈 (AWS 上)
        ──────────────────────────────────────

  Metrics:
    - CloudWatch Metrics (自动: Bedrock invocations, latency, tokens)
    - CloudWatch Custom Metrics (你的: eval score, hallu rate)

  Logs:
    - CloudWatch Logs (应用日志, 必须含 trace_id)
    - Bedrock Model Invocation Logging (prompt + response)
    - 长期归档 → S3

  Traces:
    - X-Ray (跨 Lambda / API Gateway / ECS)
    - 可选: LangFuse / Phoenix (LLM 专用 trace)

  Dashboard:
    - CloudWatch Dashboard (运维)
    - 自建 BI (业务 KPI)
```

### 必看的 6 个 dashboard 卡片

```
  ┌─────────────────────────────────────────────┐
  │  1. QPS + Error rate (主健康度)              │
  │  2. P50 / P95 / P99 latency (体验)          │
  │  3. Token usage + Cost trend (钱)           │
  │  4. Eval score (实时采样) (质量)            │
  │  5. Top failure types (排错入口)            │
  │  6. Agent step distribution (Agent 健康)    │
  └─────────────────────────────────────────────┘
```

> **AWS 知识参考**：搜 "CloudWatch metrics for Bedrock"、"X-Ray for Bedrock Agents"、"Bedrock model invocation logging"。

---

## 13.2 成本控制 — Token 是新的"水电费"

LLM 应用最大的"非工程"风险是**钱**。

```
        典型成本结构 (按月)
        ────────────────────────────────────

  Bedrock 模型调用 (60-80%)
    - input tokens × 单价
    - output tokens × 单价 (通常贵 4-5 倍)

  Embedding (5-10%)
    - 索引时一次性 + 查询时每次

  Knowledge Base / Vector DB (5-15%)
    - OpenSearch Serverless OCU 或 pgvector 实例

  其他 (5-15%)
    - Lambda / ECS / 网络 / 监控
```

### 成本的 4 个工程动作

```
  1. Caching (缓存)
     - 相同 query 缓存 1 小时
     - prompt prefix 缓存（Anthropic / Bedrock 已支持）
     - 节省 30-70%

  2. Routing (路由)
     - 简单 query → mini / haiku
     - 复杂 query → sonnet / opus
     - 节省 50-80%

  3. Compression (压缩 context)
     - RAG 召回前 top_k 太多 → 限制
     - System prompt 优化（去重 + 精简）
     - 节省 10-30%

  4. Batching (批处理)
     - 异步任务用 Bedrock Batch (50% 折扣)
     - 适合 eval / 离线分析
```

### AWS 实操：Bedrock 成本监控

```
        Bedrock 成本监控三层
        ──────────────────────────────────

  Layer 1: AWS Cost Explorer
    - 按 service / region / tag 聚合
    - 月度趋势 + 异常告警

  Layer 2: Cost Allocation Tags
    - 给每个 Agent / KB 打 tag (project / team / customer)
    - 按 tag 分摊成本

  Layer 3: 应用层埋点
    - 每次 invoke 记 input/output tokens + model
    - 按业务场景 / 用户 / 部门聚合
    - CloudWatch Metrics 上报
```

### Budget Alarm 必配

```
  AWS Budgets:
    - 月度预算 X 美元
    - 80% / 100% / 120% 三级告警
    - 超 100% 邮件 + Slack 通知 owner
    - (生产环境慎用 auto-stop)
```

> **AWS 知识参考**：搜 "AWS Cost Explorer for Bedrock"、"Bedrock prompt caching"、"Bedrock batch inference"。

---

## 13.3 灰度发布 — 不是"all or nothing"

### 为什么必须灰度

```
  没灰度的部署:
    上线 → 发现问题 → 全量回退 → 用户全感知
    损失 = 全部 user × 故障时间

  有灰度的部署:
    1% → 监控 30 分钟 → 10% → ... → 100%
    损失 = 1% user × 短时间
    放大 100 倍止血空间
```

### 灰度策略

```
        三种灰度方式
        ──────────────────────────────

  By percentage (流量百分比)
    - 1% → 5% → 25% → 50% → 100%
    - 适合: 通用功能 / 大流量

  By user / segment (用户分组)
    - 内部员工先 → beta 用户 → 高级会员 → 全部
    - 适合: 风险大 / 商业关键功能

  By feature flag (开关位)
    - 同 binary, 配置中心控制开关
    - 适合: A/B / 功能可热切
```

### 灰度的"门"

每个灰度阶段都要有"过门"条件：

```
  从 1% 升 5%:
    ✓ 错误率 ≤ baseline + 0.5%
    ✓ P95 latency ≤ baseline + 200ms
    ✓ Eval 实时采样 ≥ baseline - 0.02
    ✓ 无 P1 告警

  从 5% 升 25%:
    ✓ 上面 + 至少 30 分钟稳定
    ✓ 客户业务方书面 sign-off
```

### AWS 实操：3 种灰度方案

```
方案 A: API Gateway Stage + Lambda Alias
  - 一键切流量百分比 (Lambda traffic shifting)
  - 简单 / Bedrock 应用最常用

方案 B: ECS / EKS 蓝绿 / Canary
  - CodeDeploy + ECS service
  - 支持全套灰度

方案 C: 应用层 feature flag
  - LaunchDarkly / AWS AppConfig
  - 不用部署即可切流量
  - 推荐: 配合 Lambda 用
```

---

## 13.4 回滚 — 5 分钟内必须能切

```
        Rollback 必须做到的 3 件事
        ─────────────────────────────────

  1. 触发简单
     一个命令 / 一个按钮 / 一个 PR revert
     不要"5 步配置 + 重新发版"

  2. 时间可控
     从决定到生效 < 5 分钟
     最好 < 1 分钟

  3. 数据兼容
     新版本写入的数据，旧版本能读
     (向前兼容设计)
```

### Rollback 检查清单

```
  ✓ 配置回滚 (config / prompt / model / KB version)
  ✓ 代码回滚 (Lambda alias / ECS service)
  ✓ 数据回滚 (DB schema / 嵌入数据)
  ✓ 前端回滚 (CDN cache 失效)
```

### Prompt / Model / KB 回滚的特殊处理

LLM 应用的"回滚"不只是代码：

```
  Prompt 回滚:
    - 把 prompt 存在配置中心 (AppConfig / SSM Parameter Store)
    - 不要写死在代码里
    - 切换 = 改一个参数

  Model 回滚:
    - 应用读 model_id from config
    - 切换 = 改 config 里的 modelArn

  Knowledge Base 回滚:
    - KB 版本化 (data source 变更前快照)
    - 应用读 KB id from config
    - 切换 = 改 config 里的 KB id
```

---

## 13.5 故障演练 — Chaos Engineering for LLM

```
        必须演练的 5 种故障
        ─────────────────────────────────

  1. 模型完全不可用
     → 切备用模型 (跨 region 或 跨 provider)

  2. KB / 检索不可用
     → 应用降级到 "纯模型回答 + 风险提示"

  3. 工具调用失败
     → Agent 优雅返回 + 工单创建

  4. 单 Region 故障 (AWS)
     → DR 切换到备用 Region

  5. 上下游限流 / 过载
     → Circuit breaker + queue + retry
```

### 怎么演练

```
  季度: 一次完整 DR 演练 (跨 region)
  月度: 一次小演练 (杀掉 KB / 模型 / 工具)
  每周: trace 抽样回看 + 异常分析
```

---

## 13.6 一个生产化 dashboard 范例

```
══════════════════════════════════════════════════════════════════
  Customer Insurance Assistant — Production Dashboard
══════════════════════════════════════════════════════════════════

[Health]                                  [Cost]
  QPS: 23.4 (avg)                          Today: $89.2
  Error rate: 0.3% (baseline 0.4%) ✅      MTD:   $1,847
  P95 latency: 1.8s (target <3s)  ✅      Forecast: $5,420 / mo
  Active users: 312                         Budget: $6,000     ✅

[Quality]                                 [Eval Drift]
  Sampled accuracy: 87.2% ✅                7-day:  0.872 ↘ (-0.005)
  User thumbs-up: 89%                       30-day: 0.876
  User thumbs-down: 4%                      Threshold: 0.85 ✅
  Unrated: 7%

[Top Failures (last 24h)]
  - Tool 'get_policy_pdf' timeout: 12 cases
  - Hallucination flag: 3 cases (sampled)
  - Guardrail block (PII): 18 cases (intended)

[Canary]
  Current rollout: 100%
  Last change: 2026-05-19 14:00 (prompt v2.3.1)
  Auto-rollback armed: ✅
══════════════════════════════════════════════════════════════════
```

**这个 dashboard 在客户的 oncall 屏幕上，FDE 在自己屏幕上，两边看同一份**。

---

## 关键引用

> "*A system without observability is a system you don't own.*"
> — A. Lawrence, *FDE Rule Book*, 2025

> "*Every dollar saved by caching is a dollar of production runway.*"
> — Anthropic enterprise best practices, 2025

> "*If you can't roll back in 5 minutes, you can't deploy on Friday.*"
> — AWS GenAI Innovation Center, 2025

---

## 动手清单

PoC 第 4-6 周 + 上线前必做：

1. **接 CloudWatch + X-Ray + Bedrock Logging**（缺一不可）
2. **建 6 卡片 dashboard**（13.1 节）
3. **配 Cost Explorer Tag + AWS Budgets 月度告警**
4. **prompt / model / KB 全部走配置中心**（不要写死）
5. **CI/CD 加 canary deploy**（API Gateway / Lambda Alias）
6. **写"5 分钟 rollback SOP"**：从决定到生效流程
7. **第一次故障演练**（杀掉 KB 看 graceful degrade）

---

## 反模式清单

- ❌ **prompt / model 写死在代码里**（每次改要发版）
- ❌ **没接 cost 监控就上线**（账单到月底惊喜）
- ❌ **灰度只有 0% 和 100%**（出问题全量受灾）
- ❌ **rollback 靠"重新部署上一版"**（5 分钟变 50 分钟）
- ❌ **dashboard 客户看不到**（客户 oncall 不知道发生了什么）
- ❌ **不演练就相信"理论上能切"**（真出事都来不及）
- ❌ **告警太多 → 麻木**（只对真正可执行的告警告警）

---

## 与下一 Part 的关系

到这里，"PoC → 生产"的鸿沟跨过了：你的 LLM/Agent 已经在客户生产环境稳定运行。

下一 Part 进入 **Agent 时代** —— 不是"加个 RAG"那种 Agent，而是真正"自主决策 + 工具调用 + 跨系统办事"的 Agent。FDE 在这一阶段的工程任务是新的。

[← 上一章: PoC 过线条件](chapter-12.md) · [下一 Part: Agent 时代 →](../part-6/intro.md)
