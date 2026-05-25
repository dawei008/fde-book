---
title: "第 8 章 评估先于代码"
parent: "Part III — 技术选型"
nav_order: 3
---

# 第 8 章 评估先于代码

第 6 章定了模型，第 7 章定了接法，最后一个 D5 维度——评估和可观测——是这一章。

我先讲一个真实但概括过的场景。一个 FDE 在 PoC 第五周做客户演示，业务负责人当场说："上周演示挺好的，但今天这个 demo 怎么答得不一样？"FDE 翻 prompt commit 历史：周二改了 system prompt。看 trace：上周对的那条今天答错了。客户："你们平时不测试吗？"FDE 沉默。

第二天他做了一件正确的事：把 200 条评估集接进 CI，每个 PR 必须跑分，分数低于上周不能 merge。从那以后演示前一晚再也不慌——分数昨晚跑过了，今天客户问什么心里都有底。

这一章讲怎么把"评估驱动"这个铁律变成日常工程纪律，而不是开会时说说的口号。

---

## 8.1 第 6 章那个 40% 准确率的真相

回到第 6 章 6.3 节的实测——四个候选模型在合昇评估集上的"故障类型准确率"全部 40%。当时我说这是 eval 设计问题，不是模型问题，留到这一章展开。

什么意思？回看那 10 条评估样本中的一条：

```json
{"id": "T-2025-Q4-0142",
 "ticket": "X 轴伺服电机过热报警 1042",
 "expected_team": "电气组",
 "expected_fault_type": "伺服系统"}
```

模型实际输出："电气组 / 伺服电机"。我的评分逻辑是字符串完全相等：`predicted == expected`。"伺服电机" ≠ "伺服系统"，判错。

但**业务上这两个是一回事**——客户的派工流程里"伺服系统"和"伺服电机"是同一个分类。我的评估集错把字符串差异当成业务差异，所以四个模型都被卡在 40%。

这个错误暴露了**评估集设计的两个普遍问题**：

第一个，**评估指标和业务真实判断不对齐**。我用的是字符串完全匹配，业务上等价的不同表述都被判错。这种问题永远不会在"模型 a vs 模型 b"的对比里暴露——因为所有模型都同样被错判。要在 baseline 阶段就捕获，必须**让业务专家看几条评估结果**，不是只看分数。

第二个，**评估集没有给"等价表述"留空间**。这条样本如果我写 `expected_fault_type: ["伺服系统", "伺服电机", "伺服"]`——任何一个匹配都算对——四个模型立刻都到 100%。

这就是 8.2 接下来要讲的：评估集不是一份样本，是**样本 + 评分逻辑**两件事。两件事都要设计。

---

## 8.2 评估集是"样本 + 评分逻辑"

第 5 章已经讲了评估集的最小结构（200 条样本、三种打分函数）。这一章展开**评分逻辑**的设计。

评分函数要回答三个问题：

**第一，每条样本怎么算"对"？**

这是上一节说的。"伺服系统"等价于"伺服电机"——评分函数要知道。等价类怎么定？三种来源：

- **同义词字典**：客户业务领域内的同义词（行话、缩写、不同部门用法）。每个领域都不一样——保险业的同义词字典和制造业完全不同。这件事**业务专家比工程师靠谱**。
- **规则**：合规相关的某些字段必须精确（保单号、金额），不能放宽。
- **LLM judge**：复杂判断（"答案是否抓住了客户问题的核心"）。规则写不出来的部分用 LLM 判。

合昇案例下，"伺服系统 / 伺服电机 / 伺服" 算一类——这是同义词字典。报警代码必须精确——这是规则。"客户优先级是否合理"——这种用 LLM judge。

**第二，多个 metric 怎么合成一个分？**

第 5 章给过一个例子：0.3 × 关键词 + 0.3 × 相似度 + 0.4 × LLM judge。但这个权重怎么定？

判断标准：**让客户业务方看几个边界 case 投票**。把"关键词高但 LLM judge 低"和"关键词低但 LLM judge 高"两类样本各挑 5 条，让业务专家说哪一类更接近"业务上能接受"。客户的投票结果决定权重。

不要 FDE 单方拍权重——你拍的权重大概率反映工程审美，不反映业务审美。客户最终验收的是业务审美。

**第三，跑分采几次样？**

LLM 是概率性输出。同一个 input 跑两次可能得到不同 output。如果只采一次样，分数有 ±5-10 个点的噪声——你今天看到 0.85 明天看到 0.78，很可能没改任何东西，只是抽到了不同的样本。

实操：**每条样本跑 3 次取平均**。Bedrock 上有个简单的省钱办法——用 batch inference（Flex tier，半价），离线跑。如果项目不要求实时反馈，这是默认选择。

---

## 8.3 评估集的金字塔结构

200 条样本不是平均分布的。按层级组织：

```
                ┌──── Production ────┐
                │  线上抽样回流       │  持续增长
                └─────────┬───────────┘
                          ↑
                ┌─── Adversarial ────┐
                │  边角 / 攻击 / 越界  │  ~30-50 条
                └─────────┬───────────┘
                          ↑
                ┌──── Golden Set ────┐
                │  人工标准答案       │  100-300 条
                └─────────┬───────────┘
                          ↑
                ┌────── Seed ────────┐
                │  Discovery 收的     │  50 条
                └────────────────────┘
```

四层各有用途：

**Seed（种子）**——50 条，从 Discovery 阶段拿到。**用途**：快速 baseline，不用每次都跑全集。开发期间每改一次 prompt 跑一次 seed，30 秒出分数。如果 seed 都没过，没必要跑 golden set。

**Golden Set（金标准集）**——100-300 条，业务专家共同标注。**用途**：客户 sign-off 的"过线分数"在这一层算。这是合同的客观依据。

**Adversarial（对抗集）**——30-50 条边角情况。**用途**：找模型的失败模式。包括：

- 表述模糊（"那个东西不行了"）
- 长尾故障类型（极少出现的）
- 跨意图（一条工单包含多个不相关的需求）
- 攻击性输入（提示注入、越权请求）
- "应该拒答"的样本（涉及 PII、超出 scope）

新人 FDE 最容易省掉这一层。但**生产事故几乎全部来自对抗集类型的输入**。第 13 章会展开。

**Production（生产采样）**——上线后的真实输入持续回流。**用途**：评估集本身的"活水"。每周抽 10-20 条新的真实 case 标注后加进 golden set。模型上线半年后这一层会变成评估集的主体。

---

## 8.4 接进 CI：每个 PR 跑分

评估集建好了不能只手动跑。要接进开发流程。

最小可行的 CI 集成：

```yaml
# .github/workflows/eval.yml
on: pull_request
jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: python scripts/bench.py --eval data/seed.jsonl --runs 3
      - run: python scripts/check_threshold.py --min 0.85
```

跑哪些样本？两层策略：

- **PR 触发**：只跑 seed（50 条）。30 秒出分。**用途**：避免明显回归。
- **每天定时（如凌晨 2 点）**：跑 full set（golden + adversarial）。20 分钟出分。**用途**：定位 PR 跑不到的细节问题。

阈值怎么定？两个原则：

- **不能比上周差**——比上周分数低 2 个点以上的 PR，自动阻断 merge。强制开发者解释。
- **不能低于 sign-off 阈值**——客户合同里写的 0.85，任何 PR 都不能让分跌穿这条线。

这两个阈值合起来叫 **regression gate**。它把"评估"从"开发周末项"变成"每个 PR 都必须正面回答的工程问题"。

---

## 8.5 在 AWS 上跑评估：两套服务的分工

如果你的项目在 AWS 上，平台有**两套**官方评估服务——容易混淆，FDE 必须知道差别。

**Bedrock Evaluations** 评的是"一次调用"的质量。三种 job：

- **Model Evaluation**——纯模型输出（不带 RAG / Agent）
- **Knowledge Base Evaluation**——RAG 系统的 Context Relevance + Answer Faithfulness
- **Agent Evaluation**——agent 多步推理路径的对错

适用：选模型、对比 RAG 切片策略、PoC 阶段建 baseline。控制台 10 分钟跑通，不写代码。

**AgentCore Evaluations** 评的是"agent 行为"的质量。它的输入不是预先准备的 jsonl，而是 agent 跑产生的 **OpenTelemetry / OpenInference trace**。Bedrock Eval 是"考试卷打分"，AgentCore Eval 是"工作录像回放打分"。

AgentCore Evaluations 的几个关键事实，FDE 第一次接触时容易踩偏的地方：

**五种评估模式**——根据触发方式选：

- **Online**：线上实时打分，每条 trace 自动评，分数推到 CloudWatch
- **On-demand**：手动触发，跑历史 trace
- **Batch**：批量跑大量 trace
- **Dataset**：基于固定数据集跑（最接近 Bedrock Eval 的用法）
- **Simulation**：模拟用户对话（测 multi-turn）

**三种 evaluator 形态**——根据评什么选：

- **Built-in**：AWS 提供的通用评估器（如 Helpfulness），ARN 形如 `arn:aws:bedrock-agentcore:::evaluator/Builtin.Helpfulness`，公开可用
- **Custom LLM-as-Judge**：你写 prompt + rating scale，让模型判
- **Custom code-based**：Lambda 函数判（确定性逻辑——比如 schema 校验、PII 检查、数字精度——用代码比 LLM 准）

**三个评估粒度**——`SESSION`、`TRACE`、`TOOL_CALL`。一个会话整体评、一次请求-响应评、单次工具调用评，按需选。

回到合昇案例怎么选：

第一期单 agent + 单 tool（分诊），用 **Bedrock Agent Evaluation** 在 Scaffolding 阶段建 baseline 就够了，不需要 AgentCore Evaluations 的复杂度——这是第 6 章 6.4 的判断信号 A/B/C 还没满足时的默认选择。

二期升级到多工具 agent（备件下单 + 跨站点协调）后，开始用 **AgentCore Evaluations**：online 模式持续打分、code-based evaluator 校验工具调用的字段 schema、LLM-judge evaluator 评工作流是否合规。这一步对应第 6 章里"信号 B + 信号 C 都满足，可以升级到 Level 2 编排"的时机。

**一个常见误区**：很多 FDE 第一次看到 AgentCore Eval 就想全替换 Bedrock Eval。不要。两者并存——Bedrock Eval 跑在 CI（PR 必过），AgentCore Eval 跑在线上（实时持续打分）。前者是"开发约束"，后者是"生产观察"。

具体 API 和控制台入口随产品迭代，使用前以 docs.aws.amazon.com 为准。完整文档入口在 `docs.aws.amazon.com/bedrock-agentcore/latest/devguide/evaluations.html`。

---

## 8.6 上线后的评估

PoC 阶段评估关注的是"这个版本的代码改动有没有让分数掉"。生产阶段评估关注的是不同的事——**真实分布上发生了什么**。

三件事必须做：

**第一，CloudWatch 埋 metric**。每次模型调用记录：input、output、token 用量、延迟、是否 fallback、调用模型 ID。这些是后面所有事的基础数据。

**第二，每周抽样 LLM judge**。Production 流量里每周随机抽 100 条，让一个强模型 judge 它的回答质量。生成一个"本周 production quality score"。这个分如果掉了——意味着真实输入分布在变（客户业务变了、上游数据有问题、用户开始问新问题）——你需要第 4 章那种 shadowing 重新理解发生了什么。

**第三，监控告警的真值不是 production 分数本身，是分数的趋势**。比如本周 0.83 比上周 0.85 低——这是噪声还是信号？答案在标准差。如果你的 production 分历史标准差是 0.02，那 0.85 → 0.83 是 1 个标准差，正常波动；如果是 0.85 → 0.78，是 3.5 个标准差，必须 alert。第 13 章会展开监控仪表盘。

**第四，分掉了之后怎么改？** 这是上线后最难的事。传统做法是 FDE 翻 trace、猜原因、改 prompt、再观察一两周——一个迭代周期一个月起步。

AWS 在 2026 年 5 月把 **AgentCore Optimization** 推成 preview，专门解决这件事。它的工作流是：从生产 trace 出发，**自动生成**"改 prompt"或"改 tool description"的候选建议；用 batch evaluation（基于你的评估集）验证候选；通过 Gateway 切线上流量做 A/B；出统计显著性报告告诉你哪个候选真的好。

简单说：把"FDE 凭直觉迭代 prompt"自动化掉。

但要警告两件事：第一，它现在是 **preview**，FDE 项目默认不进生产路径——可以用来探索改进方向，但合同 sign-off 的修改必须人工 review；第二，**它能自动改 prompt，但不能自动改业务定义**——如果你的分数低是因为 outcome 定义错了（第 1 章第 1 条铁律），Optimizer 救不了你。它解决"prompt 怎么写更好"，不解决"我们到底要做什么"。

公告：https://aws.amazon.com/blogs/machine-learning/introducing-the-agent-performance-loop-agentcore-optimization-now-in-preview/

---

## 8.7 评估集的运维节奏

评估集不是"建一次完事"。它有自己的运维节奏：

| 阶段 | 评估集规模 | 主要动作 |
|---|---|---|
| Discovery 末 | 50 条 (seed) | 业务专家共同标注 |
| Scaffolding 中（第 4-5 周） | 150-200 条 (seed + golden) | 业务专家批量标注 |
| Scaffolding 末（第 6-7 周） | 200-250 条（加 adversarial） | FDE 主导找边角 case |
| Production（第 8 周后） | 持续增长 | 每周抽样回流 |
| Handoff 末 | 通常 300-500 条 | 客户能自己跑 |

合昇案例第一期最终会有大约 250-300 条评估集。这个量级是**够用**的——更大不是更好，关键是覆盖度和评分逻辑的合理性。

最常见的运维错误是**评估集冻结**——上线后再没更新过。半年后客户业务变了、模型供应商升级了，评估集还停在最初版本。这时候分数依然好看（因为没变化），但生产质量真实下滑——你和客户都不知道。每周抽样回流是防止这种情况的唯一办法。

---

## 8.8 评估和验收的关系

第 5 章的验收标准 + 这一章的评估流程，串起来是这样的：

```
Discovery 报告 (Ch 4)
    ↓ 一句话问题 + outcome 数字
SOW + 验收标准 (Ch 5)
    ↓ "0.85 通过分" 写进合同
评估集 v0 → v1 (Ch 8 这一章)
    ↓ 跑分输出"0.87"
Production 监控 (Ch 8 这一章)
    ↓ 每周追踪
Handoff (Ch 16)
    ↓ 客户接管评估集
```

每一步的输出是下一步的输入。这条链断哪一步项目都会出问题：Discovery 没收 outcome 数字 → 验收标准写不出可验的话；验收标准没数字 → 评估集没目标可对；评估集不接 CI → 上线前发现性能掉了；上线没监控 → 客户半年后说"好像不太行"你不知道发生了什么。

**评估系统是 FDE 项目的命脉**。它把"我们做得对吗"这个抽象问题变成"今天 0.87，比昨天 0.85 高 2 个点"这种可对话的具体数字。客户、业务方、商务方、你的老板，全部用同一组数字说话。这是评估驱动这条铁律为什么排第二（只在 Sell the outcome 之下）。

---

## 收尾

Part III 三章给完了：第 6 章选模型，第 7 章选接法，第 8 章建评估。三个动作完成，FDE 项目就有了完整的"技术骨架"——Discovery 决定做什么，技术骨架决定怎么做、做到什么算 done。

Part IV 进入 Scaffolding 阶段的剩下 70%：数据工程（怎么把客户散乱的数据接进系统）、scaffolding 和开发循环（怎么搭一个能让客户用一周以上的最小系统）、VPC / SSO / 合规（FDE 在企业环境下绕不过去的三件事）。

---

## 本章引用的公开资料

- Anthropic 工程博客 — *Evaluating LLM-based Applications* 系列文章
- Bedrock 文档 — Model / Knowledge Base / Agent Evaluation 的产品说明
- DeepEval、Promptfoo 等开源评估框架的设计文档
