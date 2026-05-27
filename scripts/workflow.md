# OpenBook 工程书 Multi-agent 工作流

这份文档是 OpenBook Vol II（FDE 中文书）的实操工作流总结。
后续 OpenBook Vol III+ 直接复用，不要重新设计。

**配套文件**：[`iteration-prompts.md`](iteration-prompts.md)（5 个角色的完整 prompt 模板）。

---

## 一句话定义

5 个角色（Orchestrator / Writer / Reader / Builder / Single-demo Reviewer / Cross-demo Reviewer）协作产出一本带可执行 demo 的工程书。Orchestrator 是 main agent，其他 4 个是 sub-agent。

---

## 第一步：开书前的对齐（一次性）

Orchestrator 用 AskUserQuestion 和用户对齐这 6 件事，**不要猜**：

1. **目标读者画像**：年限、技术栈、是否做过客户项目、中英文偏好
2. **平台立场**：哪家云 / SDK 是 demo 平台？是否允许客户在叙事里"最终选竞品"？（OpenBook 系列默认：不允许）
3. **客户案例边界**：用 Vol II 已有的合昇宇宙延续，还是新建虚构客户？
4. **Demo 预算**：单章预算 / 总预算 / 是否真部署 AWS 资源
5. **写作 voice**：第一人称 / 中英术语混用规则 / 是否保留四件套结尾
6. **资料窗口**：引用的"新功能"截止哪个日期之前

把对齐结果写进 `scripts/iteration-prompts.md` 顶部"通用写作约束"——所有 sub-agent 启动时继承这套。

---

## 第二步：章节分类与角色调度

```
新章节决定要做什么
   │
   ├─ 概念章（角色 / 心智模型 / 反思）
   │     → Writer + Reader 三轮即 ship
   │
   ├─ 工程章 无 demo（过程类，如交付流程）
   │     → Writer + Reader 1-2 轮即 ship
   │
   └─ 工程章 有 demo（API / 平台动手）
         → Writer + Reader 写章节
         → Builder + Single-demo Reviewer 配对建 demo
         → Reviewer APPROVED 后 Orchestrator commit
```

**关键纪律**：

- 不要把"写章节正文"交给 Builder，他写不出符合 voice 的叙事
- 不要把"评 demo 代码"交给 Reader，她审的是文本不是代码
- Orchestrator 自己决定哪些章节有 demo——见下表

| 适合做 demo | 不适合做 demo |
|---|---|
| 模型选型 / 评估 / RAG / Agent / MCP / VPC / Guardrails | 心智模型 / 角色 / 三条铁律 / Discovery 流程 / 交接 |
| 数据工程（合成数据可控） | 监控仪表盘（需要长时间真实流量） |
| 工具设计（一次调用就能展示纪律） | PoC → 生产（需要灰度真实用户） |

---

## 第三步：单 demo 的 builder/reviewer 循环

```
Orchestrator
   │
   │ spawn Builder（独立 sub-agent，每次新建）
   │   ├─ 30 分钟内完成
   │   ├─ 真起 AWS / 真跑 / 真 teardown
   │   ├─ 单文件 < 200 行
   │   ├─ Makefile + verify_down.py 是硬要求
   │   └─ 报告：实测数字 + 部署路径 + 成本 + teardown 确认 + 真实坑
   │
   │ Builder 完成
   │
   │ spawn Single-demo Reviewer（独立 sub-agent，code-reviewer 类型）
   │   ├─ 5 维独立判断（API、章节相关性、证据、teardown、读者价值）
   │   ├─ 必须查 boto3 service model 验证 preview API 真实
   │   ├─ 必须自己跑 verify_down.py 不信 builder 自报
   │   └─ 决断：APPROVED / NEEDS FIX（带具体文件 + 行号）/ REJECT
   │
   │ Reviewer 决断
   │
   ├─ APPROVED → Orchestrator commit + push
   ├─ NEEDS FIX
   │     ├─ < 30 行 diff → Orchestrator 自己快修
   │     └─ 多文件或 API 调整 → 重新 spawn 同一 Builder 修一轮
   │   （最多两轮，第三轮还修不下来就拉回 Orchestrator 决断）
   └─ REJECT → 拉回 Orchestrator + 用户对齐重新设计
```

**Spawn 多个 sub-agent 时的规则**：

- 不要让两个 builder 同时改同一个文件——在 prompt 里明确目录范围
- Reader / Builder / Reviewer 之间不互相通信——所有交接通过 Orchestrator
- 每个 sub-agent 启动时 **自带完整 context**——不要假设它知道前面发生了什么

---

## 第四步：一组 demo 的整体复核

一组章节 demo 全部 single-demo reviewer ship 之后，**必须**跑一次
Cross-demo Holistic Reviewer。**单 demo reviewer 抓不到的故事连贯性
问题只有 holistic 能抓**。

实测案例（Vol II）：

- ticket id schema 在 demo A 用 `T-2025-Q4-NNNN`、demo B 用 `T-2026-Q2-NNNNN`，导致 demo C 的 agent 查 demo A 的 ID 找不到——单 demo reviewer 不会发现
- region 在章节正文写 ap-southeast-1、所有 demo 跑 us-east-1 但只 Ch6 有解释
- 早期 demo 没复用后建的共享基础（Vol II 的 ch9-data 有自己的数据生成器）

Holistic reviewer 不能省。

---

## 第五步：每章 ship 时的 commit 卫生

Orchestrator 写 commit message 必须包含：

1. **章节 + demo 名称**：`Ch7 demo: prompting vs RAG vs RAG+Rerank on Hesheng manuals`
2. **真实数字**：accuracy / latency / cost
3. **Reviewer 几轮迭代 + 修了什么**
4. **真实坑（preview API 等）**
5. **Cost 实测**

不要写 marketing 风的 commit message。Vol II 的 commit log 是好范本——
直接 `git log --oneline` 看 7 个 demo commit 的格式。

---

## 第六步：AWS 账号卫生

**Budget 防御**：

```bash
# 月预算告警 5%/20%/80% 三档
aws budgets create-budget --account-id $ACCOUNT \
  --budget '{"BudgetName":"openbook-demo","BudgetLimit":{"Amount":"3000","Unit":"USD"},"TimeUnit":"MONTHLY","BudgetType":"COST"}'
```

**每章跑完一定查一次 cost**：

```bash
aws ce get-cost-and-usage --time-period Start=$YESTERDAY,End=$TODAY \
  --granularity DAILY --metrics UnblendedCost
```

**全套 demo ship 之后跑一次 audit**（cross-demo reviewer prompt 里有完整清单）：

```bash
aws s3 ls --region us-east-1 | grep openbook
aws iam list-roles --query 'Roles[?contains(RoleName, `openbook`)].RoleName'
aws bedrock list-guardrails --region us-east-1
aws bedrock-agent list-knowledge-bases --region us-east-1
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `openbook`)]'
aws dynamodb list-tables --region us-east-1
aws bedrock-agentcore-control list-evaluators --region us-east-1
aws bedrock-agentcore-control list-gateways --region us-east-1
aws bedrock-agentcore-control list-agent-runtimes --region us-east-1
aws ec2 describe-vpcs --filters Name=tag:Name,Values=openbook-* --region us-east-1
```

任何前缀匹配的资源都是遗留。

---

## 第七步：交付物 contract

每个 demo 必须交付：

```
demos/[chN-name]/
├── README.md                # 跑法 + 成本 + 真实坑
├── Makefile                 # up / run / down / verify-down
├── requirements.txt
├── data/                    # gitignored 的 raw + state
├── results/                 # 真实跑过的输出（json / md）
├── src/[ch_name]/           # Python package
│   ├── state.py             # 资源 ID 持久化
│   └── ...
└── scripts/
    ├── up.py
    ├── run.py
    ├── down.py
    └── verify_down.py
```

每章正文必须包含：

- 一段引用 demo 路径的实测段落
- 至少一张实测数字表
- 至少一处"真实跑出来撞到的工程坑"——不是抄文档来的

---

## 第八步：Vol II → Vol III+ 复用 checklist

新书开工前，Orchestrator 跑这一遍：

- [ ] 读 `iteration-prompts.md` 确认 5 角色 prompt 模板
- [ ] 读 `workflow.md`（本文件）确认决策表
- [ ] 用 AskUserQuestion 对齐 6 件事（见第一步）
- [ ] 在 `iteration-prompts.md` 顶部更新本书的写作约束（平台、客户、voice）
- [ ] 建 AWS Budget alert
- [ ] 决定共享基础（hesheng-core 类比物——是延续合昇宇宙还是新建？）
- [ ] 决定哪些章节做 demo（参考第二步章节类型表）
- [ ] 跑第一章试水：Writer 一稿 + Reader 一轮 + Orchestrator 评估 voice 是否落地

跑完上面 8 步，剩下的就是按章节循环。

---

## 实测产出参考（OpenBook Vol II）

| 维度 | 数字 |
|---|---|
| 总章节 | 17 章 + 4 附录 |
| 带 demo 章节 | 8 个（hesheng-core + Ch6/7/8/9/11/13/14/15）|
| Reader 迭代轮数 | Ch1-5 三轮、Ch6-17 单轮 ship |
| Single-demo reviewer | 7 轮（每个独立 demo 一轮）|
| Cross-demo holistic reviewer | 1 轮（最后一次） |
| 总 AWS 实际花费 | < $3（预算 $3K） |
| 抓到的 P0 数 | 2（race condition orphan KB；ticket id schema） |
| 抓到的 NEEDS FIX 数 | 5 |
| 最终 teardown | 100% 干净（s3/iam/guardrails/kb/lambda/ddb/agentcore-* 全 0 遗留）|

实操中工作量分布：

- 章节叙事写作：~40%（Orchestrator + Writer）
- demo builder：~30%（sub-agent，并行）
- demo reviewer：~10%（sub-agent）
- Orchestrator 决断 + commit：~20%
