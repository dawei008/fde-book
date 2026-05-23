---
title: "第 14 章 Agent Toolset 设计"
parent: "Part VI — Agent 与 MCP"
nav_order: 1
---

# Chapter 14: 在客户环境部署 Agent — 工具集 / 沙箱 / 失败恢复

## 开场

```
某 FDE 给客户做了一个"销售助理 Agent"，工具列表 47 个：
  - 查 CRM
  - 改 CRM
  - 查 ERP
  - 改 ERP
  - 发邮件
  - 改日历
  - 创建工单
  - 关单
  - 调价
  - 发优惠券
  - ... 一直到第 47 个

第 1 周演示完美。
第 3 周客户业务方私下找 FDE：
  "这周 Agent 连续给 3 个客户发了 100% 折扣优惠券，
   损失约 ¥20 万。"

复盘：模型在某些 prompt 下"自作主张"调用 send_coupon(100)。
没有 sandbox。没有金额上限。没有 dry-run。

FDE 当夜重写：
  - 47 个工具砍到 18 个（合并 + 砍掉危险）
  - 写、改类工具加了"二次确认 + 金额上限 + dry-run"
  - 加了 audit trail 和 alert

第 5 周再上线，0 事故。

这一章给：Agent 在客户环境部署的 4 件事 ——
工具集设计 / 沙箱 / 失败恢复 / 评估。
```

---

## 14.1 工具集设计 — 少即是多

### 工具数量的"魔法数字"

```
        Agent 工具数对应准确率（经验）
        ──────────────────────────────────────

  ≤ 5     95%+ 准确率，简单
  6-10    90% 准确率，工程友好
  11-20   80% 准确率，需要精心设计 prompt
  21-30   70% 准确率，建议拆分
  31-50   60% 准确率，不可控
  > 50    "工具地狱"，准确率玄学
```

**第一性原理**：模型选错工具的概率随工具数量指数级上升。

### 工具集设计的 4 条原则

```
  1. 一个动词 + 一个对象
     ✓ create_ticket(title, body)
     ✗ smart_helper(action, params)  (太宽)

  2. 描述要"对模型友好"
     ✓ "Returns customer order history. Use when user asks about
        past purchases."
     ✗ "Get orders" (模型不知道何时调用)

  3. 参数要严格
     ✓ JSON Schema 强校验
     ✓ Required vs Optional 明确
     ✓ Enum 限定取值

  4. 危险操作分级
     - read 类: 直接执行
     - write 类: 二次确认 / dry-run
     - 大金额 / 不可逆: 多人审批
```

### 工具描述模板

```python
# 一个好的工具定义示例
{
    "name": "send_email",
    "description": (
        "Send an email to specified recipients. "
        "Use this tool when user explicitly asks to send/notify someone. "
        "Do NOT use for internal logging or status updates. "
        "Maximum 5 recipients per call."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "to": {
                "type": "array",
                "items": {"type": "string", "format": "email"},
                "maxItems": 5,
                "description": "Recipient email addresses"
            },
            "subject": {"type": "string", "maxLength": 200},
            "body": {"type": "string", "maxLength": 5000},
            "dry_run": {
                "type": "boolean",
                "description": "If true, validate but do not actually send",
                "default": false
            }
        },
        "required": ["to", "subject", "body"]
    }
}
```

---

## 14.2 沙箱 — Agent 的"权限边界"

### 三层防线

```
        Agent 的执行沙箱三层
        ───────────────────────────────────

  Layer 1: 模型层
    - System prompt 严格限定行为
    - Guardrails 拦危险输出
    - Few-shot 示例引导

  Layer 2: 工具层
    - 危险工具二次确认
    - dry-run 模式默认开
    - 金额 / 数量 / 频率上限

  Layer 3: 执行层
    - IAM / 数据库权限隔离
    - VPC 网络隔离
    - 速率限流 + 熔断
```

### 关键技术：dry-run 模式

```python
# 默认 dry_run=True 的设计模式
def send_coupon(customer_id, amount, dry_run=True):
    if dry_run:
        return {
            "status": "dry_run",
            "would_send_to": customer_id,
            "amount": amount,
            "note": "Set dry_run=false to actually send"
        }
    # 实际发送逻辑...
```

**Agent 调用任何 write 类工具，第一次必须 dry_run**。模型自己决定第二次设 dry_run=false（带二次确认机制）。

### 关键技术：金额 / 频率限制

```python
# 工具内部硬限制
MAX_COUPON_AMOUNT = 50  # 元
MAX_COUPON_PER_HOUR = 10  # 次

def send_coupon(customer_id, amount):
    if amount > MAX_COUPON_AMOUNT:
        return {"error": f"Amount exceeds limit ({MAX_COUPON_AMOUNT})"}
    if rate_limit_exceeded("coupon", "1h", MAX_COUPON_PER_HOUR):
        return {"error": "Rate limit exceeded"}
    # 实际发送
```

**这些限制不能在 prompt 里写**（prompt injection 可绕过），必须在工具实现层硬编码。

### 权限隔离 — 工具用 user context, 不用 service account

```
  错误做法:
    Agent → 工具 (用 admin role) → DB
    → 任何用户都能读 / 改任何数据

  正确做法:
    用户登录 → 拿到 user_token
    Agent (带 user_token) → 工具 → 用 user_token 调 DB
    → 用户只能看 / 改自己的数据
```

### AWS 实操：Bedrock Agents 的权限模型

```
        Bedrock Agent 权限三层
        ──────────────────────────────────

  1. Agent execution role
     - Agent 本身的 IAM role
     - 通常仅能调 Bedrock + 自己的 KB

  2. Action group Lambda
     - 每个 action group 可以单独的 Lambda
     - Lambda 用自己的 role 调下游服务

  3. User context (passed via session attributes)
     - 用户登录信息 (cognito / IAM identity)
     - Lambda 用这个 context 做 ABAC 决策

  → 不是给 Agent 一个万能 role
  → 是给 Agent 调用 Lambda 的权限，
    Lambda 内部根据 user 做权限决策
```

> **AWS 知识参考**：搜 "Bedrock Agent session attributes"、"Bedrock Agent execution role"。

---

## 14.3 失败恢复 — 多步任务中断怎么办

### Agent 任务的"断点"

```
        典型 Agent 任务路径
        ──────────────────────────────────────

  用户: "帮我把上周所有 P1 工单转给小张并通知他"

  Agent:
    Step 1: list_tickets(status="P1", week="last") → 5 条
    Step 2: assign_ticket(id=#101, to="zhang") ✓
    Step 3: assign_ticket(id=#102, to="zhang") ✓
    Step 4: assign_ticket(id=#103, to="zhang") ✗ (网络抖动)
    Step 5: ...

  问题:
    - 现在 #101 #102 已转，#103 失败
    - 重跑会重复转 #101 #102 吗？
    - 模型可能放弃这个任务
```

### 解决：Idempotency + State 持久化

```python
# 工具调用必须 idempotent
def assign_ticket(ticket_id, assignee, idempotency_key=None):
    if not idempotency_key:
        idempotency_key = f"assign-{ticket_id}-{assignee}"

    # 重复调用同一 key 返回上次结果
    if cache.exists(idempotency_key):
        return cache.get(idempotency_key)

    result = actually_assign(ticket_id, assignee)
    cache.set(idempotency_key, result, ttl=86400)
    return result
```

```python
# Agent 执行状态持久化
class AgentSession:
    def __init__(self, session_id):
        self.session_id = session_id
        self.state = load_from_dynamodb(session_id) or {
            "task": None,
            "completed_steps": [],
            "pending_steps": []
        }

    def execute(self, task):
        for step in self.state["pending_steps"]:
            try:
                result = run_step(step)
                self.state["completed_steps"].append(step)
                save_to_dynamodb(self.session_id, self.state)
            except RetryableError:
                # 留在 pending，下次会续
                save_to_dynamodb(self.session_id, self.state)
                raise
```

### AWS 实操：Step Functions 给 Agent 兜底

```
        Step Functions 包 Agent
        ────────────────────────────────────

  适合场景:
    - 单次 Agent 任务执行 > 5 分钟
    - 多个 Agent 协作
    - 需要持久化中间状态
    - 需要 human-in-the-loop

  优势:
    - 可视化执行历史
    - 自动重试 + 指数退避
    - 失败可断点恢复
    - 可暂停 + 等审批 + 续

  反模式:
    - 简单单步 Agent → Step Functions 过度
    - 高频低延迟 → 不适合
```

> **AWS 知识参考**：搜 "Step Functions express workflows for AI"、"Step Functions human approval"。

---

## 14.4 Agent Eval — 不一样的 Eval

普通 LLM 应用 Eval 看"答案对不对"。Agent Eval 还要看：

```
        Agent 评估的 5 维度
        ────────────────────────────────────

  1. 任务完成率
     用户的目标是否最终达成？
     binary: 是 / 否

  2. 路径正确性
     执行步骤是否合理？是否冗余？
     metric: 步骤数 / "标准路径"步骤数

  3. 工具使用准确性
     选对工具了吗？参数对吗？
     metric: tool_call_accuracy

  4. 副作用控制
     有没有"做了不该做的事"？
     metric: side_effect_count

  5. 体验成本
     总耗时 / token 成本 / 重试次数
     metric: latency, cost, retries
```

### Agent Eval 的样本设计

```jsonl
{
  "id": "agent-eval-007",
  "task": "把上周所有 P1 工单转给小张",
  "context": {"current_user": "manager-001"},
  "expected_outcome": {
    "tickets_assigned": ["#101", "#102", "#103", "#104", "#105"],
    "all_to": "zhang",
    "side_effects_allowed": ["notify_zhang"],
    "side_effects_forbidden": ["close_ticket", "notify_customer"]
  },
  "expected_path": {
    "min_steps": 6,
    "max_steps": 12,
    "must_use_tools": ["list_tickets", "assign_ticket"],
    "must_not_use_tools": ["delete_ticket", "send_coupon"]
  }
}
```

### AWS 实操：Bedrock Agent Evaluations

```
  Bedrock 内置 Agent Evaluation:
    - 自动评 trajectory（路径）
    - 评 tool selection accuracy
    - 评 task success rate
    - 支持自定义 metric
```

---

## 14.5 Human-in-the-loop — 高风险动作必有人审

```
        三种 HITL 模式
        ──────────────────────────────────

  1. Always-approve (高风险)
     - 删数据 / 大金额转账 / 发外部邮件
     - Agent 准备 → 推送审批 → 人点 → 执行

  2. Sample-approve (中风险)
     - 改 CRM / 创建工单
     - Agent 直接做
     - 但 5% / 10% 抽样推审批 (后审 + 校准)

  3. No-approve (低风险)
     - 查询 / 报表 / 内部备忘
     - Agent 全自主
```

### 实操架构

```
  Agent → 检测高风险动作 → 写到 SQS / DynamoDB
                            ↓
                       (通知人 via Slack / 邮件)
                            ↓
                       人在 Web UI 审批
                            ↓
                       Step Functions 续作
                            ↓
                       Agent 执行
```

---

## 14.6 部署清单

```
        Agent 上生产前 checklist
        ─────────────────────────────────────

  □ 工具数 ≤ 20（超过强行拆分）
  □ 每个工具有完整 description + JSON schema
  □ 写、改、删类工具默认 dry_run
  □ 金额 / 频率 / 数量上限硬编码
  □ 用户 context 透传到工具（不用 service account）
  □ Idempotency key 强制
  □ 状态持久化（DynamoDB / Step Functions）
  □ Bedrock Guardrails: PII + Topic + Content
  □ 高风险动作走 HITL
  □ Trace + Cost dashboard
  □ Eval 集涵盖 task / path / tool / side-effect 4 维
  □ 灰度 + Rollback 通道
  □ 故障演练（模型挂 / 工具挂）
```

---

## 14.7 一个端到端的 Agent 部署

```
  客户场景: 保险公司"理赔助理 Agent"

  工具集 (12 个):
    [read]
      - get_policy(policy_id)
      - get_claim_history(customer_id)
      - get_doctor_records(claim_id)
      - search_clauses(keyword)
    [write 简单]
      - create_followup_ticket(claim_id, note)
      - send_internal_msg(team, msg)
    [write 重要]
      - request_more_info(claim_id, items[]) → dry_run + 业务员审批
      - flag_for_review(claim_id, reason) → 主管审批
      - approve_claim(claim_id, amount) → 人审批 always
      - reject_claim(claim_id, reason) → 人审批 always
    [escalate]
      - escalate_to_human(claim_id, reason)
      - request_legal_review(claim_id)

  沙箱:
    - approve_claim 必须 amount <= 5000 元
    - approve_claim 必须 HITL
    - 所有 write 工具用 user_id (业务员的) 调用

  失败恢复:
    - 任务通过 Step Functions 编排
    - 每步状态写 DynamoDB
    - 重试 3 次，仍失败 → escalate

  Eval:
    - 100 条历史理赔做 golden
    - 评:
      - approval/rejection 决策 vs 人工实际决策一致率
      - 平均工具数（标准 5-8 步）
      - 错误工具调用率

  上线:
    - W11 灰度 1% (内部业务员)
    - W12 灰度 10% (低风险 case)
    - W14 50%
    - W16 100%
```

---

## 关键引用

> "*An agent without a sandbox is a liability.*"
> — A. Lawrence, *FDE Rule Book*, 2025

> "*The best agents have boring tools.*"
> — Anthropic Claude tool use guide, 2025

> "*Don't ship an agent until you've watched it fail safely 100 times.*"
> — AWS GenAI Innovation Center, 2025

---

## 动手清单

接到 Agent 项目，部署前必做：

1. **画工具列表 + 标 read/write/delete 类型**
2. **任何"write" 工具加 dry_run + 上限**
3. **用户 context 透传，不用 service account**
4. **接 Idempotency 缓存**（DynamoDB / Redis）
5. **Bedrock Guardrails 配 PII / 业务红线**
6. **Step Functions 包高风险任务**（断点恢复）
7. **Eval 集 4 维齐全**（task / path / tool / side-effect）
8. **HITL 配置**（金额 / 不可逆 / 外部影响）

---

## 反模式清单

- ❌ **工具数 > 30 直接上线**（准确率玄学）
- ❌ **不接 dry_run 直接 write**（事故 #1 来源）
- ❌ **Agent 用 admin / service account 调下游**（任何用户都越权）
- ❌ **Agent 失败靠"模型自己重试"**（没有 idempotency 重复操作）
- ❌ **Agent 高风险动作不走 HITL**（损失到客户面前才发现）
- ❌ **用普通 Eval 评 Agent**（漏掉 trajectory / side-effect）
- ❌ **没演练故障就 100% 上线**（凌晨 2 点见真章）

---

## 与下一章的关系

这一章解决了 Agent 在"自己环境"的工程问题。下一章解决：Agent 怎么"接到客户工具上" —— **MCP (Model Context Protocol)** 时代的企业集成。

[← Part VI 导读](intro.md) · [下一章: MCP 与企业集成 →](chapter-15.md)
