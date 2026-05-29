---
title: "第 16 章 Skill — 把客户专长打包给 agent"
parent: "Part VI — Agent 与 MCP"
nav_order: 3
---

# 第 16 章 Skill — 把客户专长打包给 agent

合昇苏州工厂车间，二期 GA 后第 5 周。王师傅站在工单调度台旁边，对着我说："你这个 agent 派工挺快，但有一类工单它学不会——海外站点带方言描述的那种。我看了今天 12 单，agent 派错 3 个，全是越南那边师傅写的，他们说'机器不动了'其实是'伺服报警'。我退休前能不能把这事教给它？"

王师傅是合昇做了 28 年的资深维修工程师，年底退休。这件事他已经提过两次。我第一次回答："我把这些案例加进 KB"——做了，agent 略有改善但不稳定。第二次："我把这些写进 system prompt"——prompt 涨到 6000 tokens，命中和漏召回都更不规律。

第三次他问的时候我已经在想另一种形态。Anthropic 在 2026 年初把 **Skill** 推成 Claude Code、Claude Agent SDK、Claude API 三处都通的一等公民。这一章讲的就是它怎么用——不是 prompt，不是 tool，不是 MCP，是另一种把"专长"装到 agent 里的形态。

---

## 16.1 三种形态的真实区别

第 14 章讲了 Tool，第 15 章讲了 MCP。这一章加 Skill，三个并列。新人 FDE 第一次接触很容易混。下面这张表是我每次给客户工程师讲的开场图：

| 形态 | 是什么 | 谁写 | 加载时机 | 一句话 |
|---|---|---|---|---|
| **Tool** | 一个原子能力（API call、SQL、读文件） | 你写 | 每次推理都暴露给模型 | 模型一次推理调一个 |
| **MCP server** | 一组 tool 的标准互操作封装 | 别人写 + 你接 | 通过 MCP 协议接进来 | 让别人写的能力也能用 |
| **Skill** | 一段"专长"——prompt + 流程 + 模板 + 脚本，按需加载 | 你或客户业务专家写 | 模型按 description 决定要不要加载 | 像给 agent 装一份岗位 SOP |

三者在工程上的关键差别：

**Tool 是无状态的能力**。`query_tickets()` 调一次返回一行 SQL 结果。模型可以用 tool 组合出复杂动作，但每个 tool 自己只做一件小事。

**MCP server 是 tool 的远端发布形态**。底层还是 tool，只是协议化了——你不需要在自己代码里实现 Salesforce client，连上别人写的 Salesforce MCP server 就有了一组 Salesforce tool。

**Skill 不是能力，是知识**。它告诉 agent "遇到 X 类问题时，按 Y 方式思考、用 Z 模板写、走 W 流程"。Skill 自己不执行任何动作，它指挥模型怎么用现有的 tool / 知识。

最直观的判断：你要让 agent **多做一件事** → Tool。你要让 agent **接一个外部系统** → MCP。你要让 agent **学一种做事的章法** → Skill。

---

## 16.2 Skill 的形状

一个 Skill 是一个目录，目录里有一个 `SKILL.md`，可能还有同目录的脚本、模板、参考资料。`SKILL.md` 长这样：

```markdown
---
name: hesheng-overseas-triage
description: Use this when triaging tickets from Hesheng's overseas service
  stations (Singapore / KL / Bangkok / Jakarta / HCMC). Covers local-language
  patterns, regional fault codes, and dispatch rules that differ from
  domestic triage. Activate when a ticket's `site_id` is overseas.
---

# Hesheng Overseas Triage

When a ticket comes from an overseas station, three things differ from domestic
triage:

## 1. Phrasing patterns

Vietnamese / Indonesian engineers often describe symptoms in non-technical
phrases. Translate before classifying:

- "机器不动了" / "máy không chạy" → check for servo alarm first, not "stuck"
- "屏幕黑了" / "màn hình tắt" → power supply OR display board
- "声音不对" → bearing OR spindle (need site to confirm)

(Full mapping in `glossary-overseas.md`)

## 2. Regional fault codes

JG-A6 in HCMC ships with firmware variant v3.2.1, which adds alarm codes
ALM 7100-7199 not in the domestic table. When you see ALM 71xx, route to
HCMC-local电气组, not Suzhou.

## 3. Dispatch rules

Overseas dispatch is constrained by visa + parts inventory:
- Tickets needing parts not in regional warehouse → escalate to Suzhou
  before dispatching local engineer
- Tickets needing engineers from another country → check
  `regional-visa-table.csv` (this directory) for current visa policy
```

下面这两条是 Skill 工程上最容易被忽略的事实：

**第一，Skill 的入口是 description 字段**。模型决定加载哪些 Skill 时，看的是每个 Skill 的 description。description 写得好不好直接决定 Skill 的命中率。description 不是给人看的，是给模型读的——它必须把"什么时候触发"说清楚到模型能根据 user input 判断。

**第二，Skill 只在被加载时才被消耗 token**。Claude API / Agent SDK / Claude Code 的 Skill 系统会先扫一遍每个 Skill 的 description（短的），决定加载哪一个，加载后才把 body + 同目录文件读进 context。这意味着你可以注册几十个 Skill 而不付几十个 Skill 的 prompt 成本——只有命中的几个进 prompt。

这是 Skill 和"塞进 system prompt"的根本区别。塞 system prompt 是每次调用都付全量 token；Skill 是按需付。合昇这个例子：原来塞 6000 tokens 进**每次**工单分诊（4500 是海外特化的内容、1500 是国内通用），现在国内工单只付那 1500 通用 + 100 token 的 description 预扫，海外工单（占总量约 30%）才加载这条 1500-token 的 Skill body。把"按调用量加权"算下来，平均每条工单的输入 token 从 6000 降到约 1900——降幅约 70%。具体数字随调用分布而变，关键是**结构上从全量变成按需**。

---

## 16.3 决策树：Tool / MCP / Skill 怎么选

我给客户工程师的判断框架就是下面这棵决策树。每次他们想"让 agent 学会做 X"时，照着走：

```
agent 应该多会一件什么事?
    │
    ├─ 是要"调一个外部 API / 数据库" 吗?
    │      是 → 写 Tool
    │      └ 是别人已经写好的服务?
    │            是 → 接 MCP server
    │            否 → 自己写 Tool (Lambda / 函数)
    │
    ├─ 是要"按某种章法做事 / 用某种模板写"吗?
    │      是 → 写 Skill
    │
    └─ 是要"学一份知识 / 一张对照表"吗?
           是 → 看体量
                小 (< 4000 tokens) → 写进 system prompt 或 Skill body
                大 → 上 RAG / KB
```

具体到合昇这个海外分诊问题：

- "了解越南方言对照"——是知识，但带着"何时翻译、何时不翻译"的章法判断 → **Skill**
- "查 ALM 71xx 是哪个故障"——是查一张表 → 用现有 KB tool（已存在）
- "决定某条工单要不要派给本地"——是按章法决策 → **Skill 里的章法** + 现有 dispatch tool

王师傅退休前那份"专长"其实是混合体：一部分是知识（方言对照表），可以查；一部分是判断章法（什么时候按 visa 升级到苏州），只有人懂。Skill 把后者形式化下来，让 agent 按章法走。

---

## 16.4 Description 是 Skill 的触发面

Skill 写得好不好，先看 description 写得准不准。这个字段我见过新人 FDE 反复写错。

写得太宽：

```yaml
description: A skill for handling tickets.
```

模型看到这条几乎所有工单都会触发——你写了 12 个 Skill，每条 description 都长这样，每次都全部加载，token 成本爆炸而且互相冲突。

写得太窄：

```yaml
description: Use when ticket text contains "máy không chạy".
```

只有一个 exact phrase 触发——任何变体（同义词、拼写差异、其他语言）都不命中。模型看到这条 description 的判断面太小，正常工单它根本不会想到要加载这个 Skill。

**写得对的样子**：

```yaml
description: Use this when triaging tickets from Hesheng's overseas service
  stations (Singapore / KL / Bangkok / Jakarta / HCMC). Covers local-language
  patterns, regional fault codes, and dispatch rules that differ from
  domestic triage. Activate when a ticket's `site_id` is overseas.
```

三个特征：

1. **明确触发条件**："overseas service stations" 加上 "site_id is overseas"——模型可以从工单 metadata 直接判断
2. **覆盖多个场景但内聚**：方言、代码、派工三件事都属于"海外分诊"这个 cluster
3. **互斥于其他 Skill**：不会和"国内分诊"或"备件下单"撞车

写完一份 description 我会做一个测试：把它和其他 Skill 的 description 一起放进一个 mock prompt 里，给模型 20 条 ticket，看它选谁。如果命中率低于 90%（应命中没命中、或不该命中却命中），改 description。

这一步比写 Skill body 更值得花时间。Body 错了改 body 就行；description 错了模型根本不会加载你的 Skill，body 写得再好都没用。

---

## 16.5 在客户环境里发布 Skill

合昇这个案例 Skill 在哪里发布？三种部署形态对应三个客户场景：

**场景 A：Claude Code 用户**（FDE 自己 + 客户工程师本地用）

Skill 放在 `~/.claude/skills/<name>/SKILL.md`。Claude Code 启动时自动扫描，符合 description 的会被加载。这种适合开发期间——FDE 在客户工位边写 Skill，立刻在自己的 Claude Code 里测试，调对了再迁出去。

**场景 B：Claude Agent SDK 部署的 agent**（生产 agent）

Skill 打包进 agent 的容器镜像，放在约定路径（如 `/app/skills/`）。agent 启动时加载。版本随镜像走，rollback 直接退到上一个镜像。合昇二期这条 Skill 就是这种部署。

**场景 C：Anthropic API 直调**（应用层调 Claude API）

应用层把 Skill body 拼进 system message 或通过 Files API 上传。这种相比前两种更原始，需要应用代码自己管理"什么时候加载哪条 Skill"——不如前两种自动化，但灵活性最高。

合昇是场景 B。我们的发布流程：

```
开发: FDE 在自己 Claude Code 里写 Skill, 测 description 命中
      ↓
入仓: PR 进 main, /skills/ 目录有 lint check (description 必须 ≥ 30 字)
      ↓
评估: CI 跑一次 eval-v3 + 海外子集 (10 条 overseas ticket),
      命中率必须 ≥ 90%, 准确率必须 ≥ baseline + 5pp
      ↓
镜像: 合并后 GitHub Action 打镜像, 推 ECR
      ↓
灰度: AgentCore Runtime 切 5% 流量到新镜像, 观察 24 小时
      ↓
全量: dashboard 各项指标无回归 → 切 100%
      ↓
旧版: 旧镜像保留 7 天, 期间可一键 rollback
```

这一套和第 13 章讲的 prompt 灰度发布几乎是同一条流水线——区别是 Skill 改动更"重"（有 body + 同目录文件），所以走容器镜像而不是 Parameter Store。

**如果客户是离线机房**（金融或医疗常见）：流水线照搬，只是 ECR 换成客户内部 registry，AgentCore Runtime 换成客户 K8s。Skill 这层抽象在离线环境完全成立——它只是文件，没有外部依赖。

---

## 16.6 Skill vs Bedrock Agent action group / Agent Toolset

AWS 这边有两个名字长得像 Skill 但不是 Skill 的概念，FDE 第一次接触会撞混：

**Bedrock Agent Action Group** 是 Bedrock Agents 的工具组——按 OpenAPI schema 把多个 Lambda 注册到同一个 agent，agent runtime 帮你做工具路由。Action group 是 **tool 的容器**，不是知识。它和 Ch14 那个 Strands agent 里的 action group（应用层的概念）思路一致，只是包装层不同。

**Agent Toolset** 是更宽泛的术语——指给 agent 暴露的工具集合本身，不指任何具体产品。Ch14 整章讲的就是这个。

**和 Skill 的区别**：Skill 装的是"按什么章法做事"，前两个装的是"能做什么事"。同一个 agent 上可以同时有 Action group（=tool）+ Skill（=章法）：

```
合昇二期 agent
├─ Tools (14 个, 通过 action group 包装):
│   ├─ query_tickets, lookup_alarm_code, ...
│   └─ stateful MCP: confluence_search, jira_lookup, salesforce_query, ...
│
└─ Skills (5 个, Anthropic Skill 形态):
    ├─ hesheng-domestic-triage
    ├─ hesheng-overseas-triage  ← 王师傅那一份
    ├─ hesheng-parts-ordering-sop
    ├─ hesheng-customer-receipt
    └─ hesheng-incident-postmortem
```

这两套并存，没有冲突——tool 是手脚，Skill 是大脑里的 SOP 卡片。模型在每次 inference 时综合两套信息：tool descriptions 告诉它能做什么，加载的 Skill 告诉它该怎么做。

---

## 16.7 合昇二期最终落地的 5 个 Skill

合昇这一年最后稳定下来 5 条 Skill。每一条对应一个具体的"客户专长"——也就是一个原本住在某个老员工脑袋里的章法：

| Skill | 来源 | 解决的问题 |
|---|---|---|
| **hesheng-domestic-triage** | 陈雪 + 一线调度员 | 国内 5 个站点的派工口径、A/B/C 客户优先级判断 |
| **hesheng-overseas-triage** | 王师傅 | 海外方言、JG-A6 海外固件 ALM 71xx、跨境派工的 visa / 备件约束 |
| **hesheng-parts-ordering-sop** | 仓管主管 | 备件下单时仓库优先级（先调拨再采购）、紧急加价的边界 |
| **hesheng-customer-receipt** | 海外销售 | 给越南 / 印尼客户回执邮件的语气和模板（不是直译） |
| **hesheng-incident-postmortem** | 我自己 | Ch13 那个事故 timeline 卡片走通后整理出的复盘章法 |

写这 5 条 Skill 我用了大约两周，但**真正的工作量不在"写"，在"找"**——找到合昇内部 5 个真正"有这门专长"的人，跟他们各自坐 4-6 小时，把他们脑袋里的章法逐条问出来、逐条让他们 review。每条 Skill 第一稿是我写的，但 sign-off 必须是来源专家——Skill 里写的不是我的判断，是他们的判断。

王师傅那条最有意思。第一稿我把他口述的"先看是不是伺服报警"写成了一条规则。他看完说："不对，这条只对越南站点成立，胡志明市的师傅写'伺服'其实是'气动'——他们当地没分清。"我才意识到 Skill 必须按站点细化。最终 hesheng-overseas-triage 里有一节按 5 个站点拆开的方言对照表。

**这一节最值钱的判断**：Skill 是把"老员工脑袋里的章法"形式化下来的工程动作。它不是 FDE 自己编 prompt——FDE 编不出来这种章法，没在这个行业干 28 年。Skill 的本质是 FDE 当**章法的编辑**，不是章法的作者。

---

## 16.8 收尾

第 14 章给了 Tool，第 15 章给了 MCP，这一章给了 Skill。三种形态并列——把"agent 怎么扩展"这个抽象问题分解到了三个具体形态：能力、互操作、专长。

合昇二期这套 agent 最后稳定运行，靠的不是哪一种形态独大，是三种各管一摊：14 个 tool 是手脚、5 条 Skill 是大脑里的 SOP、stateful MCP 把 Confluence / Jira / Salesforce 三个外部 SaaS 挂进来。Ch14 / 15 / 16 三章合起来才是一个真实生产 agent 的完整画像。

下一 Part 进入 handoff——王师傅的 Skill 已经写下来了，agent 学会了，但他退休那天客户接手人能不能维护这套 Skill？这是 Ch17 的问题。

---

## 本章引用的公开资料

- Anthropic, [Claude Skills 文档](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) — Skill 的官方定义、frontmatter 规范、加载机制
- Anthropic, [Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) — Skill vs prompt 的工程论述
- Anthropic, [Claude Agent SDK 文档](https://docs.claude.com/en/api/agent-sdk/overview) — Skill 在 SDK 层的加载形态

---

[← Part VI 导读](../intro/) · [上一章：MCP 集成](../chapter-15/) · [下一 Part：交付与持续 →](../../part-7/intro/)
