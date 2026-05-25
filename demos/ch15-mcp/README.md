# Ch15 — Stateful MCP: cross-session 状态持久化

合昇案例：海外服务部 + 工单分诊 agent。客户在 Session A 给工单
`T-2025-Q4-0142` 上传了 `manual-v2.pdf`；6 小时后客户在 Session B
（新的 Mcp-Session-Id，可能落在不同 microVM）回来继续问问题，agent
还能看到那份附件 —— 这就是 **stateful MCP 的核心价值**。

## 论点

- **MCP 协议层**：`Mcp-Session-Id` HTTP header 标识一次连续会话；同一
  session 内 server 可以维护内存状态（elicitation、sampling、progress
  事件等）。本 demo 的 server 用 `FastMCP(stateless_http=False)` 显式开启。
- **跨 session 持久化**：内存状态会随 session 关闭而丢失；要让"6 小时后
  回来还能看到"成立，必须把状态外推到 **持久层**——本 demo 用 DynamoDB
  表 `fde-book-ch15-ticket-context`，key 是 `ticket_no`。
- 两个层次合在一起：per-session 用 MCP 协议自带，cross-session 用 DynamoDB。
  这正是 Ch15 要演示的模式。

## 部署路径选择

3 条路径，按"首选 → 降级"排序：

| 路径 | 何时选 | 本 demo 选了吗 |
|---|---|---|
| AgentCore Runtime（stateful MCP 模式，2026-03 GA） | 生产环境，需要托管 microVM 隔离 | 否（部署链路较重，超 30min 预算） |
| Lambda + API Gateway（标准 HTTP MCP server） | 需要 AWS 托管 + 弹性，又不想等 Runtime | 否 |
| **本地 Python 进程 + DynamoDB**（本 demo） | 把"跨 session 状态"的协议层 + 持久层证给读者看 | **是** |

> 选本地路径的原因：核心论点（不同 Mcp-Session-Id 看到同一条 doc）
> 在哪条路径上都成立，本地路径最快、最可复现。生产场景写到书里时
> 会标注用 AgentCore Runtime 更优。

## Agent Registry

Registry 是 preview API，CreateRegistry 在很多账号被 SCP 拦，本 demo
不展开。Ch15 正文会一段话提及 Registry 是后续话题（agent / MCP server
的发现与版本管理）。

## 运行

依赖 `demos/hesheng-core/` 已 up（仅用于解析 region/account）。

```bash
make up      # 创建 DynamoDB 表 fde-book-ch15-ticket-context
make run     # 启动本地 MCP server，跑 Session A→sleep→Session B
make down    # 删表 + kill 残留 server 进程
make verify-down
```

`make run` 输出（节选实际执行的）：

```
[Session A] open client
  Session A sid = 3c374289e6c3469d8cd1218949b35946
  attach_doc -> {'ok': True, 'data': {... 'doc_id': 'd4fbb551b', 'doc_count': 1}}
  list_attached_docs -> doc_count=1

... sleeping 5.0s (stand-in for hours-later) ...

[Session B] open client (NEW Mcp-Session-Id)
  Session B sid = 3e74d5933bed4272bf7fae18d6431763
  list_attached_docs -> doc_count=1
  summarize_ticket_context -> Ticket T-2025-Q4-0142: 1 attached doc(s) ...

PASS: stateful MCP + DynamoDB delivers cross-session state.
```

两个 session id 不同；两次 list 看到同一条 `doc_id=d4fbb551b`；这就是
跨 session 持久化的真实证据。完整 JSON 在 `results/run-summary.json`。

## 工程

- `src/ch15_mcp/mcp_server.py` — FastMCP server，3 个 tool 共享 DynamoDB
- `src/ch15_mcp/state.py` — 持久化资源 ARN 到 `data/ch15-state.json`
- `scripts/up.py` — 建表（PAY_PER_REQUEST，免费档基本 0 成本）
- `scripts/run.py` — 启 server 子进程 → 两个 MCP client session → 验证
- `scripts/down.py` — 删表 + 清进程
- `scripts/verify_down.py` — 确认无残留

## 成本

DynamoDB PAY_PER_REQUEST，整次 demo ~3 W + ~3 R = 不到 1 cent。
本地进程不收 AWS 费。
