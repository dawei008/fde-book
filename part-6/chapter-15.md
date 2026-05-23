---
title: "第 15 章 MCP 集成"
parent: "Part VI — Agent 与 MCP"
nav_order: 2
---

# Chapter 15: MCP 与企业集成 — 把 Agent 接到客户工具上

## 开场

```
2024 年 11 月 Anthropic 发布 MCP (Model Context Protocol)。

2025-2026 年，企业 ToB 项目几乎全部要求 MCP 适配。

某 FDE 第一次接 MCP：
  - 客户已有: Confluence + Jira + Salesforce + 内部 Wiki
  - 客户要的: "Claude / Bedrock Agent 能用上面所有工具"
  - 之前的做法: 一个个写 LangChain Tool → 6 周
  - 用 MCP 的做法:
      → Confluence MCP server (社区已有)
      → Jira MCP server (社区已有)
      → Salesforce MCP server (FDE 写一个)
      → 内部 Wiki MCP server (FDE 写一个)
      → 配置 Claude Desktop / Bedrock Agent 接入
      → 1 周

  10 倍开发效率。

但 MCP 的"威力" 同时是"风险":
  - 一个 MCP server 暴露了客户内部 API
  - Agent 可以一次性访问 50+ 工具
  - 安全 / 审计 / 权限边界 100% 由 FDE 设计

这一章讲：在客户企业里部署 MCP 的工程实操。
```

---

## 15.1 MCP 是什么

```
        没有 MCP 的世界                MCP 之后的世界
        ────────────────────           ────────────────────

  Agent 1 集成 Tool A             所有 Agent 共用 MCP 协议
  Agent 1 集成 Tool B
  Agent 2 集成 Tool A             Tool A 实现一次 MCP server
  Agent 2 集成 Tool B             Tool B 实现一次 MCP server

  N × M 的集成噩梦                 N + M 的标准接口
```

MCP 本质是**LLM 与工具之间的 USB-C 接口**：

```
        MCP 协议三层
        ──────────────────────────────────

  Client (LLM 应用)
    Claude Desktop / Cursor / Bedrock Agent / 自建 Agent
       ↕ JSON-RPC over stdio / SSE / HTTP
  Server (工具实现)
    File / Slack / Jira / Salesforce / 内部 API ...
       ↕
  Resource (工具暴露的能力)
    - tools (函数调用)
    - resources (文件 / 数据)
    - prompts (预定义 prompt 模板)
```

### 一个 MCP server 暴露 3 类能力

```
  Tools — 让 LLM 调用的函数
    例: list_jira_issues(status, project)

  Resources — 让 LLM 读的资源
    例: file:///docs/policy.md
        confluence://wiki/space/PROD/pages/123

  Prompts — 预定义的 prompt 模板
    例: "summarize_pr" 模板
        "review_security" 模板
```

---

## 15.2 企业部署 MCP 的 3 种形态

```
  形态 1: 本地 MCP server (开发者机器)
    场景: Cursor / Claude Desktop 用
    部署: 进程启动，stdio 通信
    适合: 个人 / 小团队

  形态 2: 远程 MCP server (HTTP/SSE)
    场景: 企业内部 + 多人共享
    部署: K8s / ECS / Lambda + API Gateway
    适合: 企业级

  形态 3: 集中式 MCP gateway
    场景: 有 50+ MCP servers 要管理
    部署: 一个网关聚合所有 server
    适合: 大型企业 + 多租户
```

**企业 ToB 项目 90% 是形态 2，部分大客户是形态 3**。

---

## 15.3 写一个企业 MCP server — 实操

以"Salesforce CRM MCP server"为例：

### Step 1: 设计 tools

```python
# 把客户业务关键操作列出来
tools = [
    "list_accounts",
    "get_account_details",
    "search_opportunities",
    "create_task",  # write 类
    "log_activity",  # write 类
    "update_stage",  # write 类，需 confirm
]
```

### Step 2: 实现 MCP server (Python SDK)

```python
from mcp import Server, Tool
from mcp.types import TextContent
import simple_salesforce as sf

server = Server("salesforce-mcp")

@server.tool()
async def list_accounts(name_contains: str = None, limit: int = 10):
    """List Salesforce accounts. Use when user asks about customers/accounts."""
    sf_client = get_sf_client()  # uses user-scoped OAuth token
    query = "SELECT Id, Name, Industry FROM Account"
    if name_contains:
        query += f" WHERE Name LIKE '%{name_contains}%'"
    query += f" LIMIT {limit}"
    results = sf_client.query(query)
    return TextContent(text=json.dumps(results['records']))

@server.tool()
async def update_stage(opp_id: str, stage: str, dry_run: bool = True):
    """Update opportunity stage. Use only when user explicitly asks to change stage."""
    if dry_run:
        return {"status": "dry_run", "would_set": stage}
    sf_client = get_sf_client()
    sf_client.Opportunity.update(opp_id, {'StageName': stage})
    return {"status": "updated"}

if __name__ == "__main__":
    server.run()
```

### Step 3: 鉴权 — 关键

```
        企业 MCP server 鉴权 3 模式
        ─────────────────────────────────

  Mode A: 用户 OAuth (推荐)
    客户登入 → 拿到 token → 启动 MCP server
    → MCP server 用 token 调下游
    → 下游决定权限

  Mode B: Service Account
    MCP server 用 service account 调下游
    问题: 任何人都能用 MCP 越权
    只在内部 admin 工具用

  Mode C: Per-call Token Forwarding
    每次 MCP 调用带用户 token
    MCP server 透传 token 给下游
    最严谨，但实现复杂
```

**企业生产**：Mode A 或 Mode C。Mode B 仅限受控的内部工具。

### Step 4: 部署到客户 VPC

```
        企业部署架构
        ─────────────────────────────────────

  客户 VPC
    ├── ECS Service: salesforce-mcp-server
    │     ├── ALB (HTTPS, 客户证书)
    │     ├── 容器 (Python, MCP SDK)
    │     └── Secrets Manager: SF OAuth 配置
    │
    ├── ECS Service: jira-mcp-server
    │     └── ...
    │
    ├── ECS Service: confluence-mcp-server
    │     └── ...
    │
    └── Bedrock Agent
          └── Action Group: 调上面三个 MCP server 的 HTTP endpoint
```

---

## 15.4 MCP 的 4 个工程坑

### 坑 1：MCP server 暴露过多

新人写 MCP server 倾向"把所有 API 都暴露"。结果：

```
  ✗ Salesforce MCP 暴露 80 个 tools
    → Agent 选错率 60%
    → 维护成本爆炸

  ✓ Salesforce MCP 暴露 8 个高频 tools
    → 90% 业务场景覆盖
    → 准确率 90%+
```

**经验**：每个 MCP server 的 tools 控制在 5-15 个。多了拆 server。

### 坑 2：参数 schema 不严格

```python
# 反例
@server.tool()
async def query(text: str):  # text 是啥？
    ...

# 正例
@server.tool()
async def search_opportunities(
    name_contains: str = None,
    stage: Literal["Prospecting", "Qualification", "Negotiation"] = None,
    amount_min: int = None,
    limit: int = 10
):
    """Search Salesforce opportunities..."""
```

**严格 schema = 模型选错率大幅下降**。

### 坑 3：错误处理不规范

```python
# 反例
try:
    result = sf_client.query(...)
    return result
except Exception:
    return None  # 模型不知道发生了什么

# 正例
try:
    result = sf_client.query(...)
    return {"status": "ok", "data": result}
except sf.SalesforceMalformedRequest as e:
    return {"status": "error", "type": "bad_query", "message": str(e), "hint": "check field names"}
except sf.SalesforceAuthenticationFailed:
    return {"status": "error", "type": "auth_failed", "message": "OAuth token expired", "hint": "re-authenticate"}
except Exception as e:
    return {"status": "error", "type": "unknown", "message": str(e)}
```

**让模型能"读懂"错误并自己恢复**。

### 坑 4：缺审计

```python
# 每个 MCP 调用都要写审计
@server.tool()
async def update_stage(opp_id, stage):
    audit_log({
        "user_id": current_user_id(),
        "tool": "update_stage",
        "params": {"opp_id": opp_id, "stage": stage},
        "timestamp": now(),
        "trace_id": get_trace_id()
    })
    # 实际执行
```

**没有审计的 MCP server 不可上生产**。

---

## 15.5 AWS 实操：Bedrock Agent + MCP 集成

```
        AWS 上的 MCP 部署架构
        ───────────────────────────────────────

  客户 Bedrock Agent
       ↓ (Action Group)
  Lambda: mcp-bridge
       ↓ (HTTP/SSE)
  ALB / API Gateway
       ↓
  ECS Fargate: MCP servers
    ├── salesforce-mcp
    ├── jira-mcp
    ├── confluence-mcp
    └── internal-wiki-mcp
       ↓
  下游系统 (各自 SaaS / 内部 API)
```

最小 Lambda 桥接代码：

```python
# Lambda: mcp-bridge
import boto3
import requests

def lambda_handler(event, context):
    # Bedrock Agent 调来
    action_group = event['actionGroup']
    api_path = event['apiPath']
    parameters = event['parameters']

    # 转发到对应的 MCP server
    mcp_url = MCP_SERVER_MAP[action_group]
    user_token = event['sessionAttributes'].get('user_token')

    response = requests.post(
        f"{mcp_url}/tools/call",
        json={"name": api_path, "arguments": parameters},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    return {
        'response': {
            'actionGroup': action_group,
            'apiPath': api_path,
            'httpStatusCode': response.status_code,
            'responseBody': {
                'application/json': {'body': response.json()}
            }
        }
    }
```

> **AWS 知识参考**：搜 "Bedrock Agent action group OpenAPI"。MCP 与 Bedrock 的官方桥接方案在 2025-2026 仍在演进，关注 AWS 官方更新。

---

## 15.6 多 server 协作 — 一个客户场景

```
  场景: 销售助理 Agent

  Agent 接的 MCP servers:
    1. crm-mcp (Salesforce, 8 个 tools)
    2. email-mcp (Outlook / Gmail, 5 个 tools)
    3. calendar-mcp (Google Calendar, 4 个 tools)
    4. wiki-mcp (内部 Confluence, 3 个 tools)
    5. order-mcp (内部 ERP, 6 个 tools)

  总工具数 26 → 控制在 14.1 节"魔法数字 ≤ 30"内

  典型对话:
    用户: "客户 ABC Corp 上次反馈了什么？我下周要拜访他。"

    Agent 路径:
      Step 1: crm-mcp.search_accounts("ABC Corp")
      Step 2: crm-mcp.get_account_details(account_id="...")
      Step 3: crm-mcp.list_recent_activities(account_id="...")
      Step 4: email-mcp.search_emails(from="abc.com", days=30)
      Step 5: wiki-mcp.search("ABC Corp")
      Step 6: 综合回答
      Step 7 (用户确认后): calendar-mcp.create_event(...)
```

**26 个工具分布在 5 个 server，每个 server 内聚 + 单一职责**。

---

## 15.7 安全清单

```
        企业 MCP 部署安全清单
        ─────────────────────────────────────

  □ 用户 OAuth 而非 service account
  □ MCP server 在 VPC 内，HTTPS 强制
  □ 每个 tool 有详细 description + JSON schema
  □ Write 类 tool 默认 dry_run
  □ 危险操作 HITL
  □ 全链路 trace_id
  □ 审计日志（who / what / when / result）
  □ Bedrock Guardrails 双重保险
  □ Rate limit per user（不只是 per IP）
  □ 工具 enable/disable 通过配置中心（不是代码改）
  □ 最小工具集（每个 server ≤ 15）
  □ MCP server 单独漏洞扫描 + pen test
```

---

## 关键引用

> "*MCP turned tool integration from O(N×M) to O(N+M).*"
> — Anthropic MCP launch, 2024-11

> "*A poorly designed MCP server is a backdoor with documentation.*"
> — A. Lawrence, *FDE Rule Book*, 2025

> "*The future enterprise agent will use 50+ MCP servers — the FDE's job is to make all 50 boring.*"
> — AWS GenAI Innovation Center, 2025

---

## 动手清单

接到 MCP 集成项目第 1 周必做：

1. **盘点客户工具** — 哪些 SaaS / 哪些内部 API
2. **看社区有没有现成 MCP server**（Awesome MCP / Anthropic 官方仓库）
3. **没有的写 MCP server** — Python SDK 一两天能上
4. **用户 OAuth 接入**（不要 service account）
5. **每个 tool 写完整 description + schema**
6. **接 trace + 审计日志**
7. **写 Eval 集**（包括"误调"的反例）
8. **VPC 内部署 + HTTPS + 鉴权**

---

## 反模式清单

- ❌ **第一版就把 60 个 tool 全暴露**（准确率玄学）
- ❌ **MCP server 用 service account 跑**（鉴权事故 #1）
- ❌ **没 schema 让 LLM "猜参数"**（错误率飙升）
- ❌ **错误返回 None**（模型不知道发生了什么）
- ❌ **MCP server 部署在公网**（任何人扫到都能调）
- ❌ **tools 粒度过粗**（"smart_helper" 这种万能函数）
- ❌ **没审计就上**（合规直接 fail）

---

## 与下一 Part 的关系

到这里，FDE 在客户环境从"PoC → 生产 → Agent → 企业集成"的全流程已经走完。

最后一个 Part：**交付与精进** —— Handoff 让客户接走、模式提取沉淀成可复用资产、FDE 自身的 T 字成长。

[← 上一章: 在客户环境部署 Agent](chapter-14.md) · [下一 Part: 交付与精进 →](../part-7/intro.md)
