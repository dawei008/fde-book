# Ch8 demo: strict vs semantic evaluator

Same predictions. Two evaluator implementations. Look at the gap.


| evaluator | team accuracy | fault accuracy | mode |
|---|---|---|---|
| Strict string match | 100% | 40% | local Python |
| Semantic equivalence | 100% | 100% | agentcore |

## Per-item disagreement (where the two evaluators differ on fault_type)

| id | predicted | expected | strict | semantic |
|---|---|---|---|---|
| T-2025-Q4-0817 | 主轴 | 主轴/传动 | FAIL | PASS |
| T-2025-Q4-1503 | Z轴 | Z 轴/丝杠 | FAIL | PASS |
| T-2025-Q4-2455 | 通信 | PLC/通信 | FAIL | PASS |
| T-2025-Q4-3621 | 回零 | 回零/编码器 | FAIL | PASS |
| T-2025-Q4-4044 | 冷却 | 液压/冷却 | FAIL | PASS |
| T-2025-Q4-5123 | 润滑 | 导轨/润滑 | FAIL | PASS |

**Mode**: agentcore  
**Evaluator ARN**: `arn:aws:bedrock-agentcore:us-east-1:118176377046:evaluator/hesheng_fault_type_v1-IQLIBlGxXV`

## 读出来的工程意义

Ch6 6.3 节里 4 个候选模型在 fault accuracy 上**齐刷刷**拿了一个数字 （demo 里我们再现的就是这个现象）。先怀疑评估，不怀疑模型。把 evaluator 从 `predicted == expected` 换成"在不在同一个等价类里"——靠的是**业务知识**（伺服系统 ≡ 伺服电机），不是模型能力——分立刻往上跳。
