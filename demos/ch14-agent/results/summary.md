# ch14-agent run summary

deploy_mode: `agentcore-runtime`
lambda_arn: `arn:aws:lambda:us-east-1:118176377046:function:fde-book-ch14-alarm-tool`
gateway_arn: `arn:aws:bedrock-agentcore:us-east-1:118176377046:gateway/hesheng-data-gateway-unzkzlgp40`
runtime_arn: `arn:aws:bedrock-agentcore:us-east-1:118176377046:runtime/ch14hesheng_ch14_hesheng_agent-N9W2N7FqQ3`

| # | prompt | mode | tools | latency_ms | ok |
|---|---|---|---|---|---|
| 1 | T-2025-Q4-0142 这条工单分给哪个组？ | agentcore-runtime | query_tickets✓ | 10282 | ✓ |
| 2 | ALM 4501 是什么意思？ | agentcore-runtime | lookup_alarm_code✓ | 8379 | ✓ |
| 3 | 如果有人查 ALM 9999 你会怎么做？请用 dry_run 演示一下 | agentcore-runtime | lookup_alarm_code✓ | 9825 | ✓ |
| 4 | Singapore 站点 P1 工单平均解决时间是多少小时？ | agentcore-runtime | query_tickets✓ | 13021 | ✓ |
| 5 | 你能不能帮我写一首诗？ | agentcore-runtime | (opaque) | 6675 | ✓ |

## Per-row detail

### 1. T-2025-Q4-0142 这条工单分给哪个组？

**answer:** 我来查一下这条工单的信息。工单 T-2025-Q4-0142 在系统中找不到。请核对工单号是否正确，或者告诉我故障描述和报警代码，我可以帮你判断应该派给哪个组。

| tool | input | ms | ok | error |
|---|---|---|---|---|
| query_tickets | `{"sql":"SELECT ticket_no, team, fault_desc, alarm_code FROM ticket_resolution WHERE ticket_no = 'T-2025-Q4-0142'"}` | 0 | ✓ | - |

### 2. ALM 4501 是什么意思？

**answer:** ALM 4501 = **冷却液液位低（传感器）**，归**电气组**处理。

| tool | input | ms | ok | error |
|---|---|---|---|---|
| lookup_alarm_code | `{"code":"ALM 4501"}` | 0 | ✓ | - |

### 3. 如果有人查 ALM 9999 你会怎么做？请用 dry_run 演示一下你会怎么调工具，不要实际查。

**answer:** 我用 dry_run=true 演示一下：演示完成。我的做法是：

1. **调用 lookup_alarm_code**，传入用户提供的 **完整代码** `ALM 9999`（保留用户说的前缀和格式）
2. **dry_run=true** 仅做预览，不实际调 Lambda 后端
3. 返回显示：这个代码在系统中 **未知** (`preview_known: false`)

如果改成 `dry_run=false` 实际查，系统可能返回"未找到"或报错。那时我会告诉用户这个代码在库里没有定义，建议直接问工程师。

| tool | input | ms | ok | error |
|---|---|---|---|---|
| lookup_alarm_code | `{"dry_run":true,"code":"ALM 9999"}` | 0 | ✓ | - |

### 4. Singapore 站点 P1 工单平均解决时间是多少小时？

**answer:** Singapore 站点 P1 工单平均解决时间是 **4.57 小时**。

| tool | input | ms | ok | error |
|---|---|---|---|---|
| query_tickets | `{"sql":"SELECT AVG(total_hours) as avg_resolution_hours FROM ticket_resolution WHERE site = 'singapore' AND priority = '` | 0 | ✓ | - |

### 5. 你能不能帮我写一首诗？

**answer:** 抱歉，我只回答与工单分诊、报警代码、站点 SLA、备件相关的问题。

建议直接问工程师。😊

有工单问题我可以帮你！