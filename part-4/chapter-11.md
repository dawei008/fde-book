---
title: "第 11 章 VPC、SSO、合规"
parent: "Part IV — 工程化落地"
nav_order: 3
---

# 第 11 章 与遗留系统对接：SSO / SCIM / API / 审计

合昇精密重工，第 8 周周四下午。

工单 Agent 在 staging 上跑了三周，陈雪带着两位老师傅试过 60 多条真实工单，分诊准确率稳在 94%。周明远拍了板"准备 11 月底董事会前上线"。我那天本来想松一口气，下午 3 点顾建国把我叫到 IT 主管室，桌上摆了一张打印的 A4——合昇的"应用上线安全准入清单"，4 个问题：

```
  Q1  这个 Agent 的用户登录走我们的 AD 还是你们自建账号？
  Q2  员工离职后, Agent 的访问权 24 小时内能不能自动收回？
  Q3  Agent 调 ERP / CRM 的权限边界谁定？谁能改？
  Q4  万一出事, 审计日志能不能追到是谁、在什么时间、调了什么？
```

四个问题里，我当场只能稳稳回答 Q1。Q2 我心里有方案但没接过 SCIM；Q3 我们写代码时用的是一个 service account 调 ERP，"权限边界"在 Agent 这一层根本没建模；Q4 CloudTrail 是开着，但 Bedrock 的 prompt/response 我们没落盘。

那天晚上我把这 4 个问题写在白板上，发现一件事——**这不是一件"上线前补"的事，是 4 件不同的事，每一件都得提前 3-4 周开始**。我的判断错误在 Discovery 阶段没把"安全准入"这一项提到议程上。这是个老 FDE 反复犯的错：把合规当 checklist，等到上线前一周才发现是个独立的工程线。

这一章给的就是"早 4 周开始做"的清单。四节分别讲身份（SSO）、生命周期（SCIM）、权限边界（API 集成）、审计与实时护栏。最后用合昇的实际方案串一遍。

---

## 11.1 把 4 件事画在一张图上

```
        身份 (Authentication) — "你是谁？"
              ↓ SSO: SAML / OIDC / Kerberos
        ────────────────────────────────────────
        生命周期 (Provisioning) — "用户进出谁同步？"
              ↓ SCIM
        ────────────────────────────────────────
        授权 (Authorization) — "你能干什么？"
              ↓ IAM Role / RBAC / ABAC + Tag
        ────────────────────────────────────────
        审计 (Audit) — "出事了能不能追到？"
              ↓ CloudTrail + Bedrock Logging + 应用日志
```

四件事互锁。少一件，企业上线过不了。这不是教科书的话——顾建国清单上四个问题分别对应这四层，我第二天把图拿给他，他指着说："对，就是这四件，少一件我们 IT 委员会不签字。"

> Lawrence 在 *FDE Rule Book* 里写过一句："Identity is the new perimeter." 早期我觉得这话有点 marketing 味，做了几个项目之后才明白——客户的 CISO 第一次和你开会问的从来不是"模型多准"，而是"这个调用是谁发起的、能不能追"。这一章四件事都在回答这个问题。

---

## 11.2 SSO：接客户的 IdP 而不是建你自己的账号

合昇用 Okta 作为公司 IdP，AD 在背后做内网认证，海外 5 个站点的服务工程师都用同一套 Okta 账号。顾建国的硬要求是：**不要让我们的人为你这个 Agent 再开一套账号**。

这是个非常合理的要求。在我做过的项目里，凡是 FDE 第一周心存侥幸"先用账号密码后面再接 SSO"的，第 8 周一定回头大改。原因不是技术——是用户重新培训的成本。一旦让用户记一套新密码，这个 Agent 就被打成"另一个外部系统"，离弃用只剩一步。

协议层我没纠结很久：

- **OIDC**：建立在 OAuth 2.0 之上，JWT 格式，新项目首选。Okta 原生支持。
- **SAML 2.0**：老牌 IdP（AD FS / OneLogin / 早期 Okta）通用，XML，复杂但稳。客户用 SAML 也别推他换 OIDC——价值不抵风险。
- **Kerberos / LDAP**：前者是 Windows AD 内网协议；后者不是 SSO，是查目录树。客户经常把它和 SSO 混在一起说，要分清。

合昇这次走 OIDC，因为 Okta 默认就是 OIDC，我也不需要为了"显得专业"换协议。

一次完整登录流程：

```
  1. 工程师打开"合昇服务助手", 没 session
  2. App 重定向到 Okta, Okta 验证 (密码 + Verify 推送)
  3. Okta 回传 ID token + Access token
  4. 网关解析 JWT: sub / email / groups
  5. 网关把 token 带给后端 Agent
  6. Agent 用 groups 做 RBAC: 这个工程师能查哪些工单
```

第 5-6 步是这一节真正值钱的地方——**JWT 必须一路传到 Agent 内部，不能在网关被剥掉换成 service account**。这是 11.4 节审计能不能追到具体人的前提。

合昇的 AWS 账号已经接了 IAM Identity Center（前身叫 SSO），Identity Center 又接了 Okta。这套是顾建国去年装的，刚好我接得上。我们做的事很短：

```
  1. 在 Identity Center 新建 Permission Set "BedrockAgentUser"
       - 只允许 invoke_agent 我们这个 agent ID
       - 不允许改 Agent 配置, 不允许调其他 model
       - 加 condition: 仅来自合昇企业网络段

  2. 把 Permission Set 绑到 Okta 组 "okta-group-svc-engineer"

  3. 工程师登录后, Identity Center 通过 STS AssumeRoleWithSAML
     发临时凭证 (1 小时过期)

  4. App 调 invoke_agent, 带 sessionAttributes:
     {user_id, group, region}
```

第 4 步的 `sessionAttributes` 是 Bedrock Agent 的原生字段，会落到 invocation log 里——这就是审计层"谁调的"那一行的数据来源。这一段我第一次做没注意到，是 Q4 那个问题逼出来的。

如果客户用 Azure AD：和 Identity Center 一样走 SAML/SCIM，配置稍麻烦但路径相同。如果是纯 AD（无 IdP）：用 AD Connector 或 AWS Managed AD，让 Identity Center 把 AD 当目录源。如果客户没 IdP——你应该反过来问"为什么这个 Agent 要给一个没有 IdP 的客户"，基本意味着合规要求很低，这是另一个问题。

---

## 11.3 SCIM：离职员工 24 小时内必须失效

Q2 的硬指标是"24 小时内"。合昇是制造业，工程师流动率不算高，但东南亚 5 个站点每年总有几个换岗。HR 系统是 Workday，离职操作走 Workday → Okta → 下游所有应用，他们叫"统一注销"。

如果 Agent 不接 SCIM，离职员工在 Workday 改了之后 Okta 也禁用了，但**他在我们 App 里的 session 如果没过期还能继续调 Agent**——最长可以拖到 token 过期那一刻，常常超过 24 小时。SCIM 解决的就是这个间隙。

剥掉协议规范，SCIM 本质就是一组 REST + JSON：

```
  POST    /scim/v2/Users         创建
  PATCH   /scim/v2/Users/:id     修改 (改组、禁用)
  DELETE  /scim/v2/Users/:id     删除
  GET     /scim/v2/Users/:id     查询
```

Okta 在用户禁用的同一秒按这套接口把变更推到下游。

我不建议自己从零写 SCIM endpoint。协议规范不算复杂但很啰嗦——schema 验证、attribute 映射、bulk operation、PATCH 的 JSON Path 语法——你自己写两周能跑通，再两周能在所有 IdP 之间互通。客户一升级 Okta，又得重做兼容。

合昇这一期，我们用了 IAM Identity Center 自带的 SCIM endpoint。Identity Center 已经接了 Okta SCIM，我们只要让 App 内部的"用户态"以 Identity Center 为单一真相源：

```
  Workday → Okta →(SCIM)→ Identity Center
                                ↓
                         App 内部用户表
                       (从 Identity Center 同步)
                                ↓
                        工程师的 session
```

最后一段同步用了一个很简单的策略：每次 invoke_agent 之前，App 网关查一次 Identity Center 看用户是否仍 active，加 60 秒本地缓存。工程师体感几乎没差，离职生效时间最坏 60 秒——远好于 24 小时。

如果客户的 IdP 不接 Identity Center（比如自建 OIDC），有几个现成的 SCIM 网关产品（Okta SCIM Gateway、SCIMer），花钱省时间是合理决定。

上线前我会强制跑一次端到端：在 Workday 创建用户 → 等 Okta 同步 → 用户登录调 Agent ✓ → Workday 标记离职 → 60 秒内再调 Agent → 期望 401。这条测试的产物是一份截图 + 时间戳，**直接交给客户安全审计**。Q2 那个问题，我后来就是用这份截图回答的。

---

## 11.4 API 集成：用户 context 必须穿透到 ERP

Q3 比前两个问题难。它不是协议问题，是**架构选择**。

合昇的工单 Agent 要调三个旧系统：ERP（SAP，SOAP）、CRM（Salesforce，REST）、MES（自研 HTTP+XML）。我们一开始的写法是 service account——Agent 内部用一个固定的 SAP 用户 `bedrock-agent-svc` 调 ERP，读什么客户的数据由 Agent 的代码逻辑控制。这种写法**在 Agent 这一层看起来很干净**，但顾建国问的是"权限边界谁定"——他要的不是"Agent 的代码控制"，他要的是**权限边界由 IAM/AD 控制，Agent 改代码不能绕过它**。

这两件事的差异在审计场景下决定生死。如果 Agent 用 service account 调 ERP，审计员问"为什么张三能看王五的工单"，你只能回答"我们的代码这样写的"——客户安全主管会觉得你在给他一个无穷可解释空间。如果 Agent 把张三的身份穿透到 ERP，ERP 自己拒绝了，那审计员直接看 ERP 的访问日志即可——**安全责任划分清楚**。

合昇这一期最后的架构：

```
        Bedrock Agent (调 tool)
              ↓ function call (with user JWT)
        Lambda Adapter
              ↓ STS AssumeRole + on-behalf-of
              ↓ 翻译成 SOAP/XML/REST
        SAP / Salesforce / MES
              ↓ 各自 RBAC 决定能不能读
        Adapter 脱敏 → 返回 Agent
```

Adapter 这一层的每个职责都是工程意义上的：

- **协议翻译**：SAP 的 SOAP 信封别让 Agent 看见。Agent 看到的永远是 JSON。
- **身份穿透**：从 JWT 拿到 user_id，去换一个对应的 SAP 用户 token（合昇走 SAP Principal Propagation）。Salesforce 走 OAuth on-behalf-of。
- **失败兜底**：旧系统挂了不能拖死 Agent。每个 Adapter 加 timeout（合约里写 5 秒）+ circuit breaker（连续 10 次失败熔断 60 秒）+ 降级返回。
- **dry-run 模式**：上线前演示绝不能写真数据。Adapter 默认走 dry-run，写操作返回模拟成功。第 8 周陈雪在 demo 时不小心点了"派工"按钮——因为 dry-run，没有真的派。

四条我每个项目都会守的原则，全是踩过具体坑的复盘：**先调 read API**（写 API 上线前要客户业务方书面 sign-off）；**永远要 idempotency key**（Agent 会重试，旧系统不一定幂等）；**永远要 timeout + circuit breaker**（合昇 SAP 偶尔卡 30 秒，没熔断会拖死整个 Agent）；**永远要 dry-run**（上线前最后一次彩排默认开 dry-run，业务方亲自点完所有按钮再切 live）。

---

## 11.5 审计：5 个具体问题能在 5 分钟内查出来

Q4 是我那天最虚的一题。Bedrock 的 invocation logging 我开过开关，但客户安全主管要的不是"开关在 ON"，他要的是这 5 个问题能在 5 分钟内查出来：

```
  Q-A  谁做了什么？        → user_id + action + resource
  Q-B  什么时候做的？      → timestamp (UTC, microsec)
  Q-C  从哪做的？          → IP + User-Agent + session_id
  Q-D  结果是什么？        → success / failure + 摘要
  Q-E  当时他凭什么能做？  → role / policy snapshot
```

Q-E 最容易被忘——审计员要看的是事发那一刻这个人的权限是什么，不是今天的权限。所以**权限变更本身也要审计**。

合昇这一期我们落了三层日志，每一层职责不同：

```
  应用日志 (App 写)        → CloudWatch → S3 (1 周后归档)
                           → Athena 按 trace_id / user_id / time 查询
                             回答 Q-A / Q-B / Q-C

  CloudTrail (AWS 写)      → S3 (Object Lock + KMS, 7 年)
                           → Security Hub 告警
                             回答 Q-E (IAM 角色 + policy snapshot)

  Bedrock Invocation Log   → CloudWatch + S3 (含 prompt + response 全文)
                             回答 Q-D 中"模型给了什么答案"那一段
```

合昇是 B2B 制造业，但他们要遵守**等保三级**——审计日志必须**不可篡改**。S3 Object Lock 在 Compliance 模式下，连 root 账号都不能在保留期内删对象；加上 KMS 加密（CMK 由顾建国持有，不是我们团队），形成的格局是：我们 FDE 团队**写入**审计日志但**没法删**，合昇 IT 持有密钥但**不能改**已写入的日志，客户审计员有读权限。这种"权力分立"是顾建国清单上"审计可信"那一项的真正含义。

跨境数据这一刀也得在这一节落下。合昇业务覆盖东南亚，工单里会出现越南、印尼、马来西亚客户的联系人信息。东南亚几个国家有数据本地化要求（印尼 PP 71/2019、越南网络安全法），我们和顾建国第 9 章已经达成共识：**客户数据不出 ap-southeast-1**。落地：Bedrock 走 ap-southeast-1 的 VPC endpoint；应用日志和 Bedrock Logging 的 S3 桶都在 ap-southeast-1，bucket policy 拒绝跨 region GetObject；CloudTrail 是 multi-region trail 但落地桶在 ap-southeast-1。Cross-region inference profile（4.6/4.7 模型走的）是个暗坑——它会把 prompt 跨到 us-east-1 处理。我们和顾建国确认过：合昇这一期只用 4.5 系列（不跨区），4.6/4.7 等下一期再评估。

跨境这一刀建议每个 FDE 项目第 2 周就和客户法务 + 安全主管对齐，不要拖到上线前。

---

## 11.6 Guardrails：实时拦住 Agent 自己

人在审计 Agent，Agent 的输出本身也要被实时审计——这是 LLM 时代多出来的一层。Bedrock Guardrails 干的就是这个，5 类拦截里合昇这一期开了 4 类：

- **PII filter**：身份证 / 银行卡 / 电话自动脱敏。客户合约里写的"PII 不能进调用日志"靠它兜底。
- **Content filter**：有害 / 暴力 / 仇恨 / 性内容。工业场景几乎不触发，但作为底线开。
- **Word filter**：合昇有几个内部产品代号不能出现在客户能看到的回复里。
- **Contextual grounding**：回答必须基于知识库——RAG 应用必加。合昇工单 Agent 给工程师的"故障原因"和"备件型号"是要去现场动手的，如果 Agent 编一个不存在的备件型号，工程师跑去仓库找不到，那是直接的现场事故。

合昇上线第二周 Guardrails 拦了 11 次：9 次是 PII 误判（工单里写"序列号 SN20250912"被识别成身份证），2 次是真正的 PII 泄漏（工程师在 Slack 转工单时贴了带身份证的图）。误判我们调了正则白名单，真泄漏写进了月度安全月报——客户安全主管那次主动给周明远发了个"+1"。

---

## 11.7 把 11.2-11.6 串起来：合昇这一期的安全架构

第 8 周周五，4 件事的方案做成一张图给顾建国：

```
身份层:
  工程师 → Okta (OIDC + Verify) → Identity Center
        → Permission Set: BedrockAgentUser → STS 临时凭证 (1h)

生命周期:
  Workday 离职 → Okta SCIM → Identity Center 禁用
        → App 网关 60 秒内拒绝该用户 invoke

权限边界:
  Agent invoke (with user JWT)
        → Lambda Adapter (协议翻译 + 身份穿透)
        → SAP / Salesforce / MES (各自 RBAC)
        → 脱敏返回

审计:
  应用日志 (trace_id) → CloudWatch → S3 → Athena
  CloudTrail            → S3 (Object Lock + KMS, 7 年)
  Bedrock Logging       → CloudWatch + S3
  跨境约束: 全部数据停留在 ap-southeast-1

Agent 自身:
  Guardrails: PII + Content + Word + Grounding
```

顾建国看完点头："这个我们 IT 委员会 11 月初的会能过。"陈雪那边确认业务流程不变（工程师还是登 Okta、点开 App、问工单）。周明远松了一口气——他之前担心安全准入会把董事会上线推后两周。

实际推后了 1 周，因为 SCIM 端到端测试那段我们撞到 Identity Center 一个 throttling 问题（同时同步 200+ 用户会报 429），改成分批同步又花了三天。但比起没准备好直接撞墙，1 周已经是好结果。

---

## 收尾

Q1-Q4 那四个问题我那天答不出 3 个，不是因为这些技术我没碰过，是因为**我在 Discovery 阶段没把"安全准入"提到议程上**。这一类问题在客户那边是独立的工程线，需要 3-4 周的跨部门对齐时间——HR / 法务 / 安全 / IT 委员会 / 业务方都要过一遍。FDE 第一周如果不主动触发这条线，第 8 周一定会被它撞到。我现在的习惯是每个项目第 2 周和客户安全主管开 30 分钟会，把这 4 件事的现状摸一遍：你们用什么 IdP、SCIM 接没接、API 调用要不要身份穿透、审计窗口几年。30 分钟能省掉后面的几次返工。如果客户安全主管那次说"我们没人专门管这个"——那是个红灯，意味着这一期要么砍合规要求（很难），要么在 SOW 里把这块工作量明确加上。下一 Part 进入 PoC 到生产的鸿沟，那里说的"上线"指的就是把这一章的清单全部走完之后才开始的事。

---

## 本章引用的公开资料

- A. Lawrence, *Forward Deployed Engineer Rule Book* — "Identity is the new perimeter" 一节
- AWS 文档 — *IAM Identity Center external IdP*、*Bedrock Agent identity context*
- AWS 文档 — *CloudTrail data events*、*Bedrock model invocation logging*、*S3 Object Lock*
- AWS 文档 — *Bedrock Guardrails*（5 类拦截策略 + contextual grounding）
- IETF RFC 7643 / 7644 — *SCIM Core Schema* 与 *SCIM Protocol*
- Okta 文档 — *SAML / OIDC / SCIM provisioning*
- 等保三级要求公开条文（GB/T 22239-2019）
- 印尼 PP 71/2019、越南网络安全法（数据本地化合规公开资料）

[← 上一章：Scaffolding 与开发循环](chapter-10.md) · [下一 Part：PoC → 生产 →](../part-5/intro.md)
