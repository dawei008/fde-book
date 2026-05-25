# ch14-agent — Hesheng triage Agent on AgentCore Runtime

Ch14 论点：好的 agent toolset 不是工具数量多，是 **schema 严格、纯函数化、最小权限、有 dry-run、错误结构化**。
本 demo 把 Ch9 的 ontology + Ch7 的手册搬上 AgentCore Runtime，用真实
Strands agent + 两个 schema-strict 的工具跑 5 条工单分诊问题。

## 这一章和 Ch7/Ch9 的区别

| 章节 | agent 形态 | 工具 | 部署 |
|---|---|---|---|
| Ch7 | 没 agent，只 RAG | 0 | KB + Bedrock RetrieveAndGenerate |
| Ch9.7 | 轻 agent（boto3 Converse loop） | 1 个本地函数 | 本地脚本 |
| **Ch14**（本 demo） | **生产 agent（Strands on AgentCore Runtime）** | 2 个：1 个 Athena 视图 + 1 个 Lambda | **AgentCore Runtime + Lambda + Gateway** |

Ch14 所讲的 14 个工具 / 4 个 action group 在合昇二期生产上是真实的，本 demo 抽其中两个最具示范意义的工具：

- `query_tickets(sql, max_rows)` — 走 hesheng_core Athena 接口查 `ticket_resolution` view
- `lookup_alarm_code(code, dry_run)` — Lambda 后端，演示 **dry_run 双阶段调用** 这个 14.2 节的核心工程动作

> ⚠️ **SCP 注意**：本次实测在受 SCP 限制的账号上跑，CreateGateway 成功但 CreateGatewayTarget 被拒，agent 工具改走 `lambda.invoke()` 直调。**你自己账号无 SCP 时会自动走完整 Gateway → Lambda target 路径**——agent 代码完全不动。降级和完整路径在 schema 层面等价。

## 三个 AWS 资源

`make up` 创建：

1. **Lambda** `fde-book-ch14-alarm-tool` — alarm-code 查找的后端，结构化错误返回（`error_code` / `retriable` / `suggested_action`）
2. **AgentCore Gateway** `hesheng-data-gateway` — MCP-compatible gateway，IAM 鉴权（`AWS_IAM`）
3. **AgentCore Runtime** `ch14_hesheng_agent` — 通过 `agentcore deploy` 部署的 Strands agent（CDK）

## 跑法

需要先把 `demos/hesheng-core` `make up`。然后：

```bash
cd demos/ch14-agent
pip install -r requirements.txt

make up                                   # ~30s: Lambda + IAM roles + (best-effort) Gateway
cd agentcore_project/ch14hesheng
agentcore deploy --yes --json             # ~3-5 min: deploy Strands agent to AgentCore Runtime
                                           # (this uses CDK; ~$0 idle once deployed)
cd ../..

# Re-run up so it discovers the runtime ARN
python3 scripts/up.py

make run                                   # ~1 min: 5 prompts via InvokeAgentRuntime
make down                                  # ~30s: tear down everything
make verify-down                           # confirm clean
```

## 预期成本

| 项目 | 花费 |
|---|---|
| Lambda（5 调用 + 上传） | <$0.001 |
| AgentCore Gateway 闲置（1 hour 内 up→down） | <$0.05 |
| AgentCore Runtime 闲置（按 invocation 收费） | <$0.02 |
| Bedrock Haiku 4.5 generation（5 prompts × 多轮，~10K tokens） | ~$0.05 |
| Athena query（4 次扫描） | <$0.01 |
| **合计** | **<$0.20** |

> AgentCore Runtime / Gateway 都是 invocation 计费，idle 时近似 0（Gateway 索引存储一天 ~$0.01 量级）。本 demo 完整 up→run→down 一次约 $0.20。

## 实测结果（一次真实跑过的输出，见 `results/`）

```
| # | prompt                                            | mode              | tools                | latency_ms | ok |
|---|---------------------------------------------------|-------------------|----------------------|------------|----|
| 1 | T-2025-Q4-0142 这条工单分给哪个组？                  | agentcore-runtime | query_tickets        |   10299    | ✓ |
| 2 | ALM 4501 是什么意思？                              | agentcore-runtime | lookup_alarm_code    |    9287    | ✓ |
| 3 | 如果有人查 ALM 9999 ... 用 dry_run 演示一下         | agentcore-runtime | lookup_alarm_code(*) |    8798    | ✓ |
| 4 | Singapore 站点 P1 工单平均解决时间是多少小时？        | agentcore-runtime | query_tickets        |   11372    | ✓ |
| 5 | 你能不能帮我写一首诗？                             | agentcore-runtime | (none — refused)     |    6661    | ✓ |

(*) Q3 工具调用带 `dry_run: true`，证明 schema 里"何时用 dry_run"的描述被模型读懂了
```

## Ch14 工程要点在这个 demo 里的体现

| Ch14 节 | 工程动作 | 在哪里看 |
|---|---|---|
| 14.1 工具是函数不是能力 | 一个动词一个对象、`@tool` description 写"何时用、何时不用" | `src/ch14_agent/agent.py` 中的 docstring |
| 14.2 dry_run + 上限 + idempotency | `lookup_alarm_code` 的 `dry_run` 参数（Q3 实测演示） | `src/ch14_agent/tools.py` `lookup_alarm_code_impl` |
| 14.3 user context 透传 | AgentCore Runtime 的 IAM 角色 + `runtimeUserId` | `scripts/run.py` `run_runtime` |
| 14.4 工具组合分组 | 本 demo 只 2 工具不分组；Ch15 会展开 | — |
| 14.5 错误是结构化输入 | 返回 `{ok: false, error_code, retriable, suggested_action}` | `tools.py` 和 `lambda/alarm_handler.py` 共享同一 envelope |
| 14.6 trace > metric | Runtime 的 OTel logs 直接拉 trace（按时间窗 + traceId 关联） | `scripts/run.py` `_fetch_tool_calls` |

## 真实跑出来的几个工程坑

1. **AgentCore Gateway target attach 在某些账号会被 SCP 拦**：`bedrock-agentcore:CreateGatewayTarget` 即使有 `bedrock-agentcore:*` 也可能被组织 SCP 拒。Gateway 本身能创建出来，但 target 不能挂 Lambda。
   解决：本 demo 让 agent 的 `lookup_alarm_code` 工具直接 `lambda.invoke`（绕过 Gateway target 那一段）。Gateway 留着是为了让 README 说"是的我们试过了，preview 期 SCP 限制"。
   一旦 SCP 放开，把 Gateway target 挂上去后，`lookup_alarm_code` 改成走 MCP HTTP 即可——agent 代码不用动。

2. **agentcore deploy 创建的 Runtime IAM role 默认不能调 Lambda / Athena**：CDK 给 Runtime 分配了一个最小权限的 role，只能调 Bedrock。需要 `aws iam put-role-policy` 后给它加上 `lambda:InvokeFunction` + Athena/Glue/S3。
   解决：脚本里没直接写这一步（避免 admin 凭证耦合到 demo），README 这里手动给：

   ```bash
   ROLE=$(aws iam list-roles --query "Roles[?contains(RoleName,'AgentCore-ch14hesheng-def-Application')].RoleName" --output text)
   aws iam put-role-policy --role-name $ROLE --policy-name invoke-tools --policy-document file://data/runtime-role-policy.json
   ```

3. **vendoring hesheng_core 进 Runtime 时 stack-outputs.json 找不到**：`config.py` 默认在 `<package>/data/stack-outputs.json` 找配置，runtime 部署后包路径变了。
   解决：`main.py` 启动时给 `hesheng_core.config.STACK_OUTPUTS` 重新指向 vendored 副本。

4. **Athena `Unable to verify/create output bucket`**：role 缺 `s3:GetBucketLocation` 时 Athena 无法验证 results bucket，整个 query 挂掉，错误信息却让人以为是权限问题在别处。给 role 加 `s3:GetBucketLocation` + `s3:HeadBucket` 直接解。

5. **OTel logs 里 `tool_calls` 那条 span 不带 session.id**：bedrock-runtime instrumentation 输出的 span attributes 只到 `gen_ai.system`，没有 session.id。两条解决：(a) 按时间窗 + Strands tracer span 的 session.id 交叉关联（本 demo 用这个）；(b) AgentCore Observability 直接用 Trace Search 拉 trace（preview 期还要等几分钟才能搜到）。

## 本 demo 没做（但 Ch14 提了）

- **多个 action group 切分** — Ch14.4 所说的"工单分诊 + 备件 + 调度 + 通知"四组分组，本 demo 只在最简形态下展示工具。第 15 章 demo 演示的是 stateful MCP 多工具版本。
- **Multi-step 重副作用工具（金额上限 / idempotency / 主管审批）** — Ch14.2 提到的 `create_part_order` 上限、idempotency_key、月累计 — 本 demo 没造数据，不模拟。读 Ch14 文本里的 Lambda 伪代码。

## 文件结构

```
ch14-agent/
├── Makefile                              up / run / down / verify-down
├── README.md                             this
├── requirements.txt                      strands-agents + bedrock-agentcore + boto3
├── data/ch14-state.json                  written by up.py, read by run.py + down.py
├── lambda/alarm_handler.py               <80 lines, structured-error envelope
├── scripts/
│   ├── up.py                             Lambda + IAM + Gateway (best-effort)
│   ├── run.py                            5 prompts → InvokeAgentRuntime, trace correlation
│   ├── down.py                           tear down Lambda + Gateway + IAM
│   └── verify_down.py
├── src/ch14_agent/
│   ├── agent.py                          Strands Agent factory + system prompt
│   ├── tools.py                          tool implementation (shared with Lambda)
│   └── state.py                          state dataclass
├── agentcore_project/ch14hesheng/        agentcore CLI scaffold
│   ├── agentcore/agentcore.json          declarative project spec
│   └── app/ch14_hesheng_agent/main.py    Runtime entrypoint, vendors ch14_agent + hesheng_core
└── results/
    ├── rows.jsonl                        per-prompt raw record (JSON)
    └── summary.md                        human-readable
```

## 不要做的事

- 不要假设 Gateway target 一定能 attach — preview 期的 SCP 限制可能让你卡这一步。先确认 `aws bedrock-agentcore-control list-gateway-targets` 不报 AccessDenied 再走 Gateway 路径。
- 不要忘了给 Runtime IAM role 加 `lambda:InvokeFunction` — `agentcore deploy` 不会自动给。
- 不要把 system prompt 里的策略和 manuals/02-routing-policy.md 写成两套 — 用 `_load_routing_policy()` 统一来源，否则两期之后会漂移。
