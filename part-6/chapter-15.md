---
title: "第 15 章 MCP 集成"
parent: "Part VI — Agent 与 MCP"
nav_order: 2
---

# 第 15 章 MCP 集成 — 把 Agent 接到客户既有工具栈上

合昇精密重工，海外业务部，二期 GA 后第二个月。

二期那 14 个工具是我们自己写的——直接 Lambda 包 ERP / CRM / 工单 / 邮件 / 日历五个系统。跑了一个月，周明远找过来：销售总监想让 agent 也读他们的 Salesforce，IT 主管顾建国想让 agent 查内部 Confluence，售后的陈雪希望 agent 能直接看 Jira 工单。三个新接口，三套不同的 SaaS。

如果按二期的写法，我得再写六个 Lambda、六套 schema、六个 dry_run。算了下，三周。

陈雪问："这些工具其它公司应该早就接过了吧？为什么我们要从头写？"

她说得对。MCP（Model Context Protocol）就是这个问题的回答。

---

## 15.1 MCP 在解什么问题

Anthropic 在 2024 年 11 月开源了 MCP 协议，后来托管在 [modelcontextprotocol.io](https://modelcontextprotocol.io) 这个独立的工作组。它的工程动机一句话讲完：让 LLM 应用和工具之间存在一个标准接口，就像 LSP 之于编辑器和语言、USB-C 之于设备和外设。

没有 MCP 之前我做合昇二期那种集成，每接一个 SaaS 写一遍 Lambda、一套 schema、一段错误处理。N 个 agent 接 M 个工具就是 N×M 的工作量。MCP 把这件事改成 N+M：每个工具实现一次 MCP server，每个 agent 实现一次 MCP client，中间走标准 JSON-RPC。

协议本身定义了三类资源：

```
tools       LLM 可以调用的函数
            14 章那 14 个工具就是这一类
resources   LLM 可以读的"数据"
            confluence://wiki/pages/123 这种 URI
prompts     工具方预定义的 prompt 模板
            "总结这份 PR" / "review 这段 SQL" 这种
```

合昇二期 14 个工具全是 tools 那一类。新接的 Confluence / Salesforce / Jira 三个，工具能力本身和合昇业务关系不大——它们是被多家公司用过、社区已经写好 MCP server 的"通用 SaaS"。这就是 MCP 真正能省工的地方：通用能力复用社区，业务专属还是自己写。

---

## 15.2 什么时候用 MCP，什么时候直接写 function

我的判断标准是两条信号，满足任一条就走 MCP，否则继续用二期那种自己写 Lambda 的做法：

```
信号 1: 工具是"通用 SaaS / 通用基础设施"
        Confluence, Jira, Salesforce, GitHub, Slack,
        Postgres, S3, 文件系统 ...
        社区大概率已经有 MCP server, 不写就拿来用

信号 2: 同一组工具会被多个 agent / 多个 IDE 复用
        Claude Desktop 的开发者用一次, Cursor 里
        开发者用一次, 生产 agent 用一次 — 工具实现
        一遍, 三处都能用
```

合昇二期 14 个里有 12 个是合昇专属——`create_part_order` 这种工具的 schema 写死了"金额上限 ¥50000、必须传 destination_site"，不会被任何其他公司复用。这种工具 MCP 没好处，反而多一层 JSON-RPC 序列化。

但 Confluence / Jira / Salesforce 三个，社区现成的 MCP server 在 [modelcontextprotocol.io/servers](https://modelcontextprotocol.io/servers) 上有维护清单。我花了半天 review 三个 server 的实现质量、更新频率、issue 响应——结论是 Confluence 和 Jira 的官方/社区 server 可用，Salesforce 那个 issue 太多，自己写。三周的活，最后是五天。

反过来说一遍我没做的事：我没把合昇二期那 14 个工具改成 MCP server。它们已经在 Bedrock Agent action group 里跑稳了，业务专属、不会被复用、自己人维护——改成 MCP 是给自己加层。**MCP 不是越多越好，是接口标准化的成本应该低于自己写**。

---

## 15.3 MCP 的两种通信形态

MCP 协议本身定义了两种 transport：

```
stdio       本地进程, 通过标准输入输出通信
            场景: 开发者机器上 Claude Desktop / Cursor 起一个
                  本地 server, 进程间 pipe
            优点: 零网络配置, 启动快
            缺点: 每台机器一份, 没法多人共享, 不能跨网络

streamable HTTP   走 HTTP 长连接, 服务端推送结果
            场景: 企业部署, 一个 server 多人用
            优点: 一处部署多处调用, 鉴权跟随 HTTP 标准
            缺点: 需要部署、TLS、鉴权一整套
```

合昇这种企业场景，stdio 直接出局——总不能让陈雪每天在自己电脑上启动一个 Confluence MCP 进程。**企业部署只走 streamable HTTP**。这是接下来 15.4 节那一套部署架构的前提。

---

## 15.4 把 MCP server 部署到 AgentCore 上

二期我们没用 AgentCore——6.4 节那张 A4 写得清楚，单 agent 单一团队，Level 0 直写。但 MCP server 要让 Bedrock Agent 调用，又要保持 session 状态、要有标准的鉴权 + observability，这些事自己搭一套不划算。

AWS 在 2026 年 3 月把 AgentCore Runtime 的 stateful MCP server 能力 GA 了（[AgentCore Runtime supports stateful MCP server features (2026-03)](https://aws.amazon.com/about-aws/whats-new/2026/03/amazon-bedrock-agentcore-runtime-stateful-mcp/)；公开资料清单在章末）。简单说，AgentCore Runtime 现在能直接 host MCP server，给你三件事免费：

第一，**session 持久化**。MCP 协议本身有 session 概念（client 连上后维护一个上下文），stateful MCP 把 session 状态存在 AgentCore 托管的存储里，server pod 重启不丢、横向扩展不串。我们二期自己写 Lambda 时为了无状态绕了不少弯路，这一层省了。

第二，**鉴权直接接 Identity Center / Cognito**。HTTP 层走 IAM SigV4 或 OAuth bearer token，AgentCore 验完才把请求转到 server 的 handler。我不用在 server 代码里再写一遍 token 验证。

第三，**observability 直接进 CloudWatch**。每次 tool call 落 trace、错误进 metric——和二期 14.6 那一套 trace 维度数据同源，CloudWatch Logs Insights 一条 query 跨 agent 和 MCP server 联查。

合昇这次的部署架构落到 AgentCore 上是这样：

```
        合昇 Bedrock Agent (二期已有)
              │
              ├─ action group: 自有 14 个工具 (Lambda)
              │
              └─ action group: MCP servers
                    │
                    │  HTTPS + SigV4
                    ▼
              AgentCore Runtime (stateful MCP)
                    │
                    ├─ confluence-mcp  (社区 server, 包了一层)
                    ├─ jira-mcp        (社区 server, 包了一层)
                    └─ salesforce-mcp  (FDE 自己写)
                          │
                          ▼
                    各自 SaaS API
```

合昇自有 14 个工具继续走 Lambda action group——它们和 MCP 没关系。新加的三个 SaaS 走 MCP server，部署在 AgentCore 上。两条路并存。

stateful MCP 的"跨 session 状态持久化"在仓库 `demos/ch15-mcp/` 可复现——一个最小 MCP server（FastMCP + DynamoDB 共享后端），先在 Session A attach 一份文档到工单 `T-2025-Q4-0142`，然后**用一个完全不同的 Mcp-Session-Id**（Session B）调 list_attached_docs——能看到 Session A 那条 doc。两个不同 sid 看到同一个 doc_id 是 stateful MCP 的硬证据。整次跑约 2 分钟、<$0.01（DynamoDB 按需计费）。Demo 选了"本地 Python + 真 DynamoDB"路径而非 AgentCore Runtime，因为协议层结论一样、可复现性更高；生产部署到 Runtime 工程逻辑不变。

---

## 15.5 写一个企业 MCP server — Salesforce 那个例子

社区 Salesforce server 不可用，自己写。Python SDK 大概两天能跑通，关键是几个工程决定。

**第一，工具集合控制在 5–15 个**。Salesforce REST API 暴露三百多个对象、上千个端点。我让陈雪和销售总监列了下"这个 agent 在合昇真正需要的销售场景"，列出来六个：查客户、看商机、找最近联系记录、查产品、登活动、改阶段。六个工具，每个动词清楚，不写 `salesforce_query(action, params)` 那种万能分发器——这是 14.1 那一节的教训，MCP server 同样适用。

**第二，写类工具同样 dry_run + idempotency**。MCP 协议本身不强制这两个字段——它只规定了 tool 的 schema 怎么序列化。但我把它写进每个 write 工具：

```python
from mcp.server.fastmcp import FastMCP
from typing import Literal

mcp = FastMCP("salesforce-mcp")

@mcp.tool()
async def update_opportunity_stage(
    opportunity_id: str,
    new_stage: Literal["Prospecting", "Qualification",
                       "Negotiation", "Closed Won", "Closed Lost"],
    idempotency_key: str,
    dry_run: bool = True,
) -> dict:
    """Update the Stage field of a Salesforce opportunity.

    Use ONLY when the user has explicitly asked to change an
    opportunity's stage. The first call MUST be dry_run=true so
    the agent can confirm with the user before committing.
    """
    cached = await idem_lookup(idempotency_key)
    if cached:
        return cached

    if dry_run:
        return {"status": "dry_run",
                "would_set_stage": new_stage,
                "opportunity_id": opportunity_id}

    # 调下游用的是 user 透传过来的 OAuth token, 见 15.6
    sf = get_salesforce_client_from_session()
    sf.Opportunity.update(opportunity_id, {"StageName": new_stage})
    result = {"status": "updated", "opportunity_id": opportunity_id}
    await idem_save(idempotency_key, result)
    return result
```

二期 14.1 那一节的 schema 设计原则在这里一行不改地继续用。MCP server 是 tool 实现的另一种打包方式，**底下的工程纪律不变**。

**第三，错误结构化返回**。MCP 协议允许 tool 返回 error，但 error 的字段是开放的。我让所有 error 都返回 `error_code`（enum）+ `error_message` + `suggested_action`——和二期 14.5 那一节的格式一致，agent 看到的"错误形状"在自有工具和 MCP 工具之间一样，reasoning 不需要专门学两套。

---

## 15.6 鉴权：用户身份必须透传到下游

二期 14.3 节那个判断——"工具调下游必须用 user context，不能用 service account"——在 MCP 这里只会更严格。MCP server 通常一处部署多 agent 共用，如果它用一个 service account 调 Salesforce，那任何能连上 MCP server 的 client 都能读全公司销售数据。

合昇的做法是用 OAuth on-behalf-of（AgentCore Identity 把这个流程托管掉）：

```
工程师 Web 端登录 ─── 客户 IdP (Okta / Cognito)
                       │
                       ▼
              AgentCore Identity workload identity:
              用工程师的 IdP 身份, 通过 Salesforce
              OAuth (authorization_code grant or
              token-exchange) 换取 user-scoped token,
              token 由 AgentCore Identity 托管缓存
                       │
                       ▼
              Bedrock Agent 调 MCP server, HTTP header
              带 user-scoped Salesforce token
                       │
                       ▼
              MCP server 用这个 token 调 Salesforce
                       │
                       ▼
              Salesforce 看到的是工程师本人, 权限按
              Salesforce 自己的 profile / sharing rule 决定
```

这套模式 AWS 文档里叫 **inbound auth + outbound auth** 的组合（AgentCore Identity 把它做成了平台原语，参见 [AgentCore Identity 文档](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity.html)）——inbound 是 client 怎么证明自己是哪个用户（IdP token 验证），outbound 是 server 怎么用这个用户身份调下游（OAuth on-behalf-of 换 user-scoped token）。两端都不能用 service account 一刀切。

我见过的事故 #1 就是 MCP server 图省事用 service account——演示阶段没事，上生产某个用户问 agent "帮我看一下王总最近的商机"，service account 是销售总监级别的，agent 把全公司销售数据都读出来了。客户那次没出公关事故纯属运气。**MCP server 在企业上生产前，鉴权链路必须走过一次完整的 pen test**。

---

## 15.7 多 server 同台时的工具数量

合昇这次接进来的是三个 MCP server——Confluence、Jira、Salesforce，每个 server 的工具数我都控制在 6 个以下：

```
合昇 MCP servers (3 个 server, 共 18 个工具)
─────────────────────────────────────────────

[confluence-mcp · 4 个]
  search_pages(query, space_key=None, top_k=5)
  get_page(page_id)
  list_recent_pages_by_user(user_email, days=7)
  get_page_attachments(page_id)

[jira-mcp · 5 个]
  search_issues(jql, top_k=10)
  get_issue(issue_key)
  list_my_open_issues(user_email)
  add_comment(issue_key, body)              write
  transition_issue(issue_key, transition)   write

[salesforce-mcp · 6 个]
  search_accounts(name_contains, top_k=10)
  get_account(account_id)
  search_opportunities(filters, top_k=10)
  get_recent_activities(account_id, days=30)
  log_activity(account_id, type, body)      write
  update_opportunity_stage(...)             write
```

加上二期自有 14 个，合昇 agent 现在的总工具数是 32 个。但 14.4 那个 action group 路由继续生效——任何一次 invocation 模型看到的还是 3-6 个工具。**MCP 把工具来源拓宽了，但 14.4 那条"模型每一步只看一组"的纪律必须守住**。Anthropic 在 [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) 里那条"工具数量影响选择准确率"的论述，在 MCP 接入之后只会更重要。

---

## 15.7b 工具规模化的下一步——AWS Agent Registry（preview）

合昇二期 32 个工具我能管，三期如果合昇集团其他 BU（销售线、财务线、IT 运维线）也要做 agent，工具会很快涨到几百个。每个 BU 的 FDE 各自重复造轮子——销售 BU 自己写一个 Salesforce MCP、IT BU 自己写一个 Jira MCP——浪费工作量、也没法做集团级的统一治理（哪些 server 安全可信、哪个版本是当前推荐、谁在维护）。

AWS 在 2026 年把 **AWS Agent Registry** 推成 preview，正是为这个场景。它是一个中心目录，发布、审批、发现 agent / tool / skill / MCP server / 自定义资源。两层资源模型：

- **Registry**——容器，可按 BU、按环境（prod/QA/dev）、按资源类型分多个
- **Record**——单个资源条目，按协议 schema 校验（MCP server 按 MCP schema、agent 按 A2A schema）

四个角色 / 工作流：

- **Admin** 在集团 AWS 账号建 Registry，配 IAM 或 JWT 授权（接 Cognito / Okta / Entra ID）
- **Publisher** 提交 record——比如 IT 团队把 jira-mcp v1.2 提交到注册表
- **Curator** 审批通过或拒绝——一般是企业级安全或平台团队角色
- **Consumer** 搜索发现——FDE 或 agent 都能搜（Registry 自己就提供 MCP endpoint，agent 能直接查它来发现工具）

合昇的二期还没用上 Registry——32 个工具自己一个 FDE 团队就管得住。我把它放在这里讲，是因为 FDE 在三期或者集团多 BU 项目时一定会撞上"agent / tool 怎么治理"这个问题——届时 Registry 会从"知道有这个东西"变成"必须用上"。

**和 Gateway 的区别要分清**：Gateway 是"把现有 API/Lambda 转成 MCP 工具"，Registry 是"发现已经存在的 agent/tool 资源"。两者互补——你用 Gateway 做的工具，可以发布到 Registry 让别的团队搜到。

Preview 注意事项和 Optimization 一样：FDE 项目默认不进生产关键路径，可以做 PoC 探索，正式生产前等 GA。

文档：https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/registry.html
公告：https://aws.amazon.com/blogs/machine-learning/the-future-of-managing-agents-at-scale-aws-agent-registry-now-in-preview/

---

## 15.8 MCP 上线前的安全检查

合昇 MCP 上生产前我让顾建国和我一起跑过一遍下面这张清单。它不是教科书清单，是二期那次差点出事的 service account 教训之后我自己整理的：

```
□ 每个 MCP server 部署在 VPC 内, 公网不可达
□ 走 streamable HTTP + TLS, 不是裸 HTTP
□ inbound 鉴权: SigV4 或 OAuth bearer, 拒绝匿名
□ outbound 鉴权: 工具调下游用 user OAuth token, 不用 service
   account; 真要用 service account 必须明确写在 server README
   并通过审批
□ 每个 write 工具默认 dry_run=true, idempotency_key 必填
□ 工具描述里写清楚 "use only when..." / "do not use for..."
□ 工具的 input schema 用 enum / pattern / min / max 限制取值
□ 错误结构化返回 (error_code + alternatives + suggested_action)
□ 每次 tool call 落 audit log: who / what / when / result / trace_id
□ rate limit per user, 不只是 per IP
□ 工具开关通过配置中心管理 (Feature flag), 不是改代码重发
□ MCP server 单独跑一遍漏洞扫描, 上线后季度复扫
```

这张表打印出来贴在合昇 IT 那边的墙上。每接一个新 MCP server 走一遍。

---

## 收尾

这一章和 14 章是一对：14 章讲 agent 自己工具栈怎么从 47 砍到 14、写出 schema、加 dry_run；本章讲什么时候不要自己写、复用社区 MCP server、部署到 AgentCore stateful MCP runtime、用户身份怎么透传。两章共享同一套工程纪律——schema 严格、写类工具 dry_run、错误结构化、用户 context 不能丢、工具数量分桶——只是包装方式从 Lambda action group 换成了 MCP server。合昇的 32 个工具最终是这两种打包方式的并存：业务专属继续 Lambda、通用 SaaS 走 MCP。下一 Part 进入交付与精进——把这套东西交给客户工程师能独立维护、把项目里抽象出可复用的模式资产、FDE 自己的 T 字成长路径。

---

## 本章引用的公开资料

- Anthropic, [Model Context Protocol 官网](https://modelcontextprotocol.io) — 协议规范、SDK、社区 server 清单
- Anthropic, [MCP 发布博客 (2024-11)](https://www.anthropic.com/news/model-context-protocol) — MCP 的设计动机和 N×M → N+M 论述
- Anthropic, [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) — 工具描述质量、tool partitioning
- AWS, [Bedrock AgentCore Runtime supports stateful MCP server features (2026-03)](https://aws.amazon.com/about-aws/whats-new/2026/03/amazon-bedrock-agentcore-runtime-stateful-mcp/) — AgentCore 托管 MCP server 的能力清单
- AWS, [Bedrock Agents — Session attributes 文档](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-session-state.html) — inbound / outbound auth 透传机制
- modelcontextprotocol.io, [Servers 目录](https://modelcontextprotocol.io/servers) — 社区维护的 MCP server 清单, 接入前先 review 这一页

[← 上一章：Agent Toolset 设计](../chapter-14/) · [下一章：Skill — 把客户专长打包给 agent →](../chapter-16/)
