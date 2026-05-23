---
title: "第 11 章 VPC、SSO、合规"
parent: "Part IV — 工程化落地"
nav_order: 3
---

# Chapter 11: 与遗留系统对接 — SSO / SCIM / API / 审计

## 开场

```
某保险客户。FDE 第 8 周演示成功，第 10 周准备上线。
客户 IT 总监问 4 个问题，FDE 当场答不出 3 个：

  Q1: 用户登录走我们的 AD 还是你们自己的账号？
  Q2: 离职员工怎么自动注销 Agent 的访问权？
  Q3: Agent 调用 ERP API，权限边界谁定？
  Q4: 出了事，审计日志能追到具体调用吗？

FDE 回去把这四个问题写在白板，发现 ——
SSO / SCIM / 权限 / 审计是 4 件不同的事，
没一件是"上线前补"能补完的。

她重新规划：
  Week 11: SSO + SCIM
  Week 12: 权限边界 + 审计
  → 上线推迟 2 周

她老板说："早 4 周做这个就好了。"
她说："下次知道了。"

这一章给的就是"早 4 周做"的清单。
```

---

## 11.1 四件事的关系

```
        身份 (Authentication)
           "你是谁？"
              ↓
        SSO (Single Sign-On)
        OAuth / SAML / OIDC
              ↓
        ──────────────────
              ↓
        授权 (Authorization)
           "你能干什么？"
              ↓
        RBAC / ABAC / Policy
              ↓
        ──────────────────
              ↓
        生命周期 (Provisioning)
        "用户增删改谁同步？"
              ↓
        SCIM
              ↓
        ──────────────────
              ↓
        审计 (Audit)
        "出事谁干的？"
              ↓
        Audit log + 不可篡改 + 可查询
```

四件事互锁。少一件，企业上线过不了。

---

## 11.2 SSO — 接客户 AD / Okta / Identity Center

### 协议速记

```
  SAML 2.0
    - 老牌企业 IdP 通用（AD FS / Okta / OneLogin）
    - 基于 XML，复杂但稳

  OIDC (OpenID Connect)
    - OAuth 2.0 之上的身份层
    - JSON / JWT，现代友好
    - 推荐新项目用 OIDC

  Kerberos
    - Windows AD 内部协议
    - 国内大型企业内网常用

  LDAP
    - 不是 SSO，是查目录
    - 但很多客户混着用
```

### 工作流（OIDC 例）

```
        典型 OIDC 登录流程
        ────────────────────────────────────

  1. 用户访问你的 Agent
  2. 你的 App 重定向到客户 IdP（AD / Okta）
  3. 客户 IdP 验证用户（密码 / 短信 / Yubikey）
  4. IdP 返回 ID token + Access token
  5. 你的 App 解析 token：
     - sub: 用户 ID
     - email: 邮箱
     - groups: 部门 / 角色
  6. 用 token 调你的后端 / Agent
  7. 后端用 group / role 做授权判断
```

### AWS 实操：用 IAM Identity Center + Bedrock Agent

```
        IAM Identity Center 三种集成
        ─────────────────────────────────

  方式 1: 客户自带 IdP (Okta / Azure AD)
    - SAML / SCIM 同步用户进 Identity Center
    - Identity Center 给用户分配 IAM Role

  方式 2: 客户用 AD（Active Directory）
    - AD Connector 或 AWS Managed AD
    - 用户用 AD 账号登 AWS

  方式 3: 客户没 IdP（小型）
    - Identity Center 自带用户管理（不推荐）
```

最小配置：

```
1. Identity Center 启用 (Organization 级)

2. 接客户 IdP:
   - SAML metadata 互换
   - Attribute mapping (email, groups)

3. SCIM 自动同步:
   - 客户 IdP 增删改用户 → 自动同步到 Identity Center

4. Permission Sets:
   - "BedrockAgentUser" → 仅能调 specific Agent ID
   - "BedrockAgentAdmin" → 能改 Agent 配置

5. Agent 调用:
   - 用户 → 你的 App → STS AssumeRoleWithSAML
     → 临时凭证 → invoke_agent (with session_attributes)
```

> **AWS 知识参考**：搜 "AWS IAM Identity Center external IdP" 与 "Bedrock Agent identity context"。

---

## 11.3 SCIM — 用户生命周期同步

### 为什么需要 SCIM

```
  没有 SCIM:
    客户 HR 系统员工离职
       → 手动通知 IT
       → IT 手动在 5 个系统里删账号
       → 你的 Agent 是第 6 个系统，常常被忘
       → 离职员工还能用 Agent 调 ERP

  有 SCIM:
    HR 系统离职 (Workday / SAP HCM)
       → IdP 自动同步 (Okta / Azure AD)
       → SCIM 协议 → 你的系统
       → 你的系统秒级禁用账号
```

### SCIM 协议

```
  本质: REST API + JSON Schema

  端点 (你需要实现):
    POST /scim/v2/Users         (创建用户)
    PATCH /scim/v2/Users/:id    (更新用户)
    DELETE /scim/v2/Users/:id   (删除用户)
    GET /scim/v2/Users/:id      (查询用户)

  双向同步:
    Push: IdP → 你的系统 (新增 / 修改 / 删除)
    Pull (可选): 你的系统 → IdP (反向同步)
```

### FDE 实操要点

```
  ✓ 优先用现成方案
    - AWS IAM Identity Center 自带 SCIM endpoint
    - Auth0 / Okta SCIM 模板
    - 不要自己从零写

  ✓ 测试用例必须有
    - 创建 → 登录 → 修改组 → 验证权限变 → 删除 → 验证不能登

  ✓ 日志记录每次 SCIM 调用
    - 客户审计要查"该员工是何时被禁用的"
```

---

## 11.4 API 集成 — 调客户的旧系统

```
        客户旧系统的 4 种"接口形态"
        ─────────────────────────────────────

  形态 1: REST / OpenAPI (现代)
    - 直接调
    - 通常带 OAuth 2.0 / API Key

  形态 2: SOAP / WSDL (传统企业)
    - XML 信封
    - 大量 enterprise 中间件
    - Python 用 zeep 库

  形态 3: 数据库直连 (反模式但常见)
    - 客户给你只读账号查 Oracle / SQL Server
    - 风险高，能避就避

  形态 4: 文件落地 (最古老)
    - SFTP 共享文件夹
    - CSV / XML 定时投递
    - 业务关键时间窗口
```

### Agent 调旧系统的设计模式

```
        Agent → Tool → Adapter → 旧系统
        ──────────────────────────────────

  Agent (Bedrock / LangGraph)
       ↓ (function call)
  Tool (Lambda / 你的代码)
       ↓ (实现 SDK 或客户提供的 client)
  Adapter (一层薄翻译)
       ↓
  旧系统 (SAP / Oracle / SOAP)

  Adapter 的好处:
    - 旧系统协议不漂到 Agent 里
    - Agent 升级 / 旧系统升级互不影响
    - 单点 fallback / retry / circuit breaker
```

### 4 个工程信号

```
  ✓ 永远先调 read API
    - 写 API 上线前要客户 sign-off

  ✓ 永远要 idempotency key
    - 同一个操作重试不能重复发生

  ✓ 永远要 timeout + circuit breaker
    - 旧系统挂了不能拖死你

  ✓ 永远要 dry-run 模式
    - 演示 / 测试时不真的写
```

---

## 11.5 审计日志 — "你能证明吗？"

```
        合规审计的 5 个问题
        ──────────────────────────────────

  Q1: 谁做了什么？
      → user_id + action + resource

  Q2: 什么时候做的？
      → timestamp (UTC, microsec)

  Q3: 从哪做的？
      → IP + User-Agent + session_id

  Q4: 结果是什么？
      → success / failure + 返回内容摘要

  Q5: 谁有权限做这件事？
      → 当时的 role / policy snapshot
```

### 审计日志的 4 个工程要求

```
  1. 不可删除
     - WORM (Write Once Read Many) 存储
     - S3 Object Lock / CloudTrail

  2. 可关联
     - trace_id 串联所有相关日志
     - 从用户行为 → API 调用 → DB 查询 → 模型调用

  3. 可查询
     - 不是只是"存着"，要能"查出来"
     - 推荐: CloudWatch Logs + Athena 查询

  4. 保留期
     - 合规一般 90 天 / 1 年 / 7 年（看行业）
     - 别忘归档（S3 Glacier）
```

### AWS 实操：CloudTrail + CloudWatch + Athena 三件套

```
        FDE 项目典型审计架构
        ─────────────────────────────────────

  应用层 → 应用日志 (含 trace_id)
              ↓
  CloudWatch Logs (1 周 → S3 归档)
              ↓
  Athena (按 trace_id 查询)

  AWS API → CloudTrail (所有 AWS API 调用)
              ↓
  S3 (Object Lock + KMS 加密)
              ↓
  Athena 查询 / Security Hub 告警

  Bedrock 调用 → Bedrock Model Invocation Logging
              ↓
  CloudWatch / S3
              ↓
  审计: "用户 X 在 T 调用了 Agent 问了什么 / 答了什么"
```

最小开关：

```
1. CloudTrail Multi-Region Trail (强制开)
   - All management events
   - Data events for S3 / Lambda (按需)
   - Insight events (异常检测)
   - 加 Object Lock 防删

2. Bedrock Model Invocation Logging
   - Bedrock console → Settings → Enable
   - Destination: CloudWatch + S3
   - 含 prompt + response 全文

3. 应用日志规范:
   - 每条日志带 trace_id (X-Ray / OpenTelemetry)
   - user_id (从 IAM context 拿)
   - action + resource_arn
```

> **AWS 知识参考**：搜 "CloudTrail data events"、"Bedrock model invocation logging"、"S3 Object Lock"。

---

## 11.6 Guardrails — Agent 的行为审计

不仅人在审计 Agent，Agent 也要被实时检查：

```
        Bedrock Guardrails 5 类拦截
        ────────────────────────────────

  1. Content filter (有害 / 暴力 / 仇恨 / 性内容)
  2. Topic filter (禁止讨论的话题)
  3. PII filter (身份证 / 电话 / 邮箱 自动脱敏)
  4. Word filter (公司禁词 / 竞品名 / 内部代号)
  5. Contextual grounding (回答必须基于知识库)
```

### 配置思路

```
  PoC 阶段:
    ✓ 开 PII filter
    ✓ 开 Content filter (中等强度)

  生产前:
    ✓ 加 Topic filter (业务相关红线)
    ✓ 加 Word filter (公司机密词)
    ✓ 加 Grounding (RAG 应用必加)

  上线后:
    ✓ 监控 Guardrails 拦截次数
    ✓ 拦得太多 → 调阈值或调 prompt
    ✓ 漏得太多 → 加规则
```

> **AWS 知识参考**：搜 "Bedrock Guardrails"。可以独立于模型使用，也可以绑到 Agent。

---

## 11.7 一个完整的整合例子

```
  客户场景: 保险公司销售助手 Agent

  身份层:
    - 销售员用 AD 账号 SSO 登入
    - Identity Center + SAML 接客户 AD

  生命周期:
    - HR 离职 → AD 禁用 → SCIM 同步 → Agent 立即不可用

  权限层:
    - "销售员" 角色: 只能查自己客户的保单
    - "经理" 角色: 能查团队所有保单
    - 用 ABAC: tag-based access control

  Agent 调用旧系统:
    - 调 ERP (SOAP) → Lambda Adapter → SAP RFC
    - 调 CRM (REST) → Lambda → Salesforce API
    - 所有调用带 user context（不是 service account）

  审计:
    - CloudTrail: AWS API
    - Bedrock Logging: prompt + response
    - 应用日志: trace_id 串联
    - 审计窗口: 7 年（保险行业）
    - 存储: S3 Object Lock + KMS

  Guardrails:
    - PII filter: 客户身份证 / 银行卡自动脱敏
    - Topic filter: 不讨论投资建议（合规要求）
    - Grounding: 答案必须基于产品文档
```

---

## 关键引用

> "*Identity is the new perimeter — and it's the first thing the customer's CISO will ask about.*"
> — A. Lawrence, *FDE Rule Book*, 2025

> "*Audit is not a feature — it's the only proof you have when something goes wrong.*"
> — AWS Well-Architected, 2025

> "*If your Agent can't tell who's asking, it shouldn't answer.*"
> — Anthropic enterprise best practices, 2025

---

## 动手清单

接到企业项目第 1-2 周必做：

1. **画一张"四件事图"**：SSO / SCIM / 权限 / 审计 各自现状
2. **跟客户安全主管开 30 分钟会**：他们用什么 IdP / 等保级别 / 审计要求
3. **拿到 SSO 测试账号**（SAML metadata 或 OIDC client）
4. **接 Identity Center + SCIM**（不要自己从零写身份系统）
5. **CloudTrail + Bedrock Invocation Logging 第一周打开**
6. **每个 Agent 调用旧系统的 Tool 都过 Adapter**（不要直连）
7. **Bedrock Guardrails 至少配 PII + Content filter**
8. **写一份"审计日志查询 SOP"** 客户审计来时直接交付

---

## 反模式清单

- ❌ **用 service account 跑所有调用**（审计追不到具体用户）
- ❌ **离职员工不在你这边自动禁用**（合规事故）
- ❌ **Agent 直连旧系统 SOAP 协议**（耦合 + 没法 fallback）
- ❌ **审计日志可被运营人员删除**（合规审计直接 fail）
- ❌ **PII 没脱敏就进了 Bedrock 调用日志**（GDPR / 等保事故）
- ❌ **没有 dry-run 模式调写 API**（demo 时把生产数据搞坏）
- ❌ **Guardrails 一拖再拖**（出事一次代价远高于配置成本）

---

## 与下一 Part 的关系

到这里，"FDE 在客户真实环境工作"的全部基础打好了：数据栈、网络隔离、身份审计。下一 Part 进入 **PoC → 生产** 这个最难的鸿沟 —— 在 demo 之后，怎么真正稳定上线、控制成本、灰度回滚。

[← 上一章: 在客户 VPC 工作](chapter-10.md) · [下一 Part: PoC → 生产 →](../part-5/intro.md)
