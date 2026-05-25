# ch8-eval — strict vs semantic evaluator (AgentCore Evaluations)

Ch8 论点之一：**4 个候选模型在某个 metric 上齐刷刷拿同一个奇怪的数字
（比如 40%），先怀疑评估逻辑，不要怀疑模型**——这是 Ch6 6.3 节那个伏笔。
此 demo 用 **AgentCore Evaluations** 把现象复现一遍，对比"严格字符串
匹配" vs "包含语义等价类的代码评估器"两种评分逻辑下的同一组预测。

## 实测结果（一次真实跑过的输出，见 `results/`）

```
strict   (string match):       team=100%  fault=40%
semantic (Lambda + AgentCore): team=100%  fault=100%
```

10 条工单，**模型不变、预测不变**——只换 evaluator，fault accuracy
从 40% 跳到 100%。差的 6 条都是同义异写：

| id | predicted | expected |
|---|---|---|
| T-2025-Q4-0817 | 主轴 | 主轴/传动 |
| T-2025-Q4-1503 | Z轴 | Z 轴/丝杠 |
| T-2025-Q4-2455 | 通信 | PLC/通信 |
| T-2025-Q4-3621 | 回零 | 回零/编码器 |
| T-2025-Q4-4044 | 冷却 | 液压/冷却 |
| T-2025-Q4-5123 | 润滑 | 导轨/润滑 |

模型说 "主轴"，标准答案写 "主轴/传动"——业务上就是同一类，但
`predicted == expected` 把它们判错。第二种 evaluator（Lambda 内
维护一个等价类字典 → 在 AgentCore Evaluations 注册成
**code-based evaluator**）正确判通过。

## 三种接法

| 元件 | 实现 |
|---|---|
| 预测 (predict.py) | Bedrock `Converse` + Claude Haiku 4.5（与 Ch6 prompt 完全一致） |
| 严格 evaluator (eval_strict.py) | 本地 Python，纯字符串相等 |
| 语义 evaluator (eval_semantic.py) | Lambda 函数，注册成 AgentCore code-based evaluator，调 `bedrock-agentcore:Evaluate` 拉分 |

## 依赖

需要先把 `demos/hesheng-core` `make up`（本 demo 通过
`hesheng_core.config.load()` 读 region / account）。

```bash
cd demos/hesheng-core && make up
cd ../ch8-eval
pip install -r requirements.txt
```

## 跑法

```bash
make up           # ~30 sec: IAM role + Lambda + AgentCore evaluator 注册
make run          # ~30 sec: 10 题 × Bedrock 预测 + 两种 evaluator 各跑一遍
make down         # ~10 sec: 删 evaluator + Lambda + IAM role
make verify-down  # 确认无残留
```

## 预期成本

| 项目 | 花费 |
|---|---|
| Bedrock 预测（10 调用 × Haiku 4.5，~ 600 tokens 各） | ~$0.005 |
| Lambda 调用（10 次 RequestResponse） | <$0.001（free-tier 内） |
| AgentCore Evaluations Evaluate 调用（10 次） | preview 期免费 |
| **合计** | **<$0.01** |

实测一次完整 up→run→down 总账单 < $0.01。

## 用 AgentCore 注册成功了吗？是的

`scripts/up.py` 调 `bedrock-agentcore-control:CreateEvaluator`，level=`TRACE`，
`evaluatorConfig.codeBased.lambdaConfig.lambdaArn` 指向上一步部署的 Lambda。
返回的 ARN 形如：

```
arn:aws:bedrock-agentcore:us-east-1:<account>:evaluator/hesheng_fault_type_v1-<id>
```

`scripts/eval_semantic.py` 然后调 `bedrock-agentcore:Evaluate(evaluatorId=...)`，
传入合成的 OTel 风格 trace（一个 span 装预测的 JSON 在 `gen_ai.completion`
attribute 里）+ ground-truth（`expectedResponse.text`）。AgentCore 自己
fan-out 到 Lambda、parse 返回、给 label/value/explanation。

state 文件 `data/ch8-state.json` 里的 `used_agentcore_register: true`
确认走的是这条路。如果 `CreateEvaluator` 在某个 region 暂时不开放、或
account 没有该 API 权限，up.py 会自动**降级到 direct-invoke 模式**
——只部署 Lambda + run.py 用 `lambda:Invoke` 直接调（同样的 evaluator
代码、同样的语义结果），并把降级原因记录在 state。

## 实测踩到的坑（这一次跑出来发现的）

1. **OTel trace_id 必须 32 位 lowercase hex，span_id 必须 16 位**——
   `traceId: "trace-T-2025-Q4-0142"` 直接被 ParamValidationError 拒掉。
   用 `hashlib.sha256(item_id).hexdigest()[:32]` 派生稳定 ID。
2. **`evaluationReferenceInputs[].context.spanContext` 是 required**——
   只填 `expectedResponse.text` 报 `Missing required parameter context`。
3. **span-level reference inputs are not currently supported**——
   `spanContext` 里如果带 `spanId`，preview 期 AgentCore 直接拒，
   要求 trace-level 或 session-level。把 `spanId` 从 spanContext 拿掉就过。
4. **session span 必须 OTel-shape**：`scope`、`start_time` (unix nano)、
   `end_time` (unix nano)、`status`、`kind` 都要有；缺哪个报哪个。
5. **`attributes` 字段是 dict 不是 OTel 协议的 list**：放
   `[{"key": ..., "value": {"string_value": ...}}]` 报
   `'list' object has no attribute 'get'`，必须 `{"key": "value"}` dict shape。
   这一条和 OTel proto 标准不同，preview 期专用。
6. **IAM role description 不接受 em-dash (—)**——
   ValidationError on `[	
 -~¡-ÿ]*`。
7. **CreateEvaluator 是幂等性意义上的"创建"——不是 upsert**——
   重跑 up.py 时先 `list_evaluators()` 查重，否则同名报错。

## 文件结构

```
ch8-eval/
├── Makefile
├── README.md                       this
├── requirements.txt                boto3
├── data/
│   ├── tickets.jsonl              10 道 Ch6 复用工单（expected_team + expected_fault_type）
│   ├── predictions.jsonl          run 期间生成（Haiku 4.5 的实际预测）
│   └── ch8-state.json             up 期间生成（Lambda ARN / evaluator ID）
├── results/
│   ├── strict.json                字符串相等评分
│   ├── semantic.json              AgentCore Evaluations 评分
│   └── comparison.md              人读对比
├── lambda/
│   └── handler.py                 code-based evaluator（被 AgentCore invoke）
├── scripts/
│   ├── up.py                      创建 IAM + Lambda + AgentCore evaluator
│   ├── predict.py                 调 Bedrock 生成 predictions.jsonl
│   ├── eval_strict.py             本地 Python，严格字符串
│   ├── eval_semantic.py           调 AgentCore Evaluate API
│   ├── run.py                     orchestrator: predict → strict → semantic → comparison.md
│   ├── down.py                    删 evaluator → Lambda → IAM role
│   └── verify_down.py             确认无残留
└── src/ch8_eval/
    ├── __init__.py
    ├── state.py                   state file dataclass
    └── equivalence.py             等价类清单（与 lambda/handler.py 同步维护）
```

## 不要做的事

- 不要把 `equivalence.py` 当成 "训练好的语义模型"——这是一份**业务知识**
  字典，靠合昇售后主管维护。这个 demo 的论点是：什么时候该用代码评估器
  （deterministic、业务规则可以列举）、什么时候该用 LLM judge（开放式
  生成、规则列举不全）。10 条工单 7 个等价类——这是代码评估器的甜区。
- 不要把 `equivalence.py` 和 `lambda/handler.py` 里的 EQUIVALENCE_CLASSES
  当成两份独立数据——它们必须一致。Lambda zip 是 self-contained，没共享
  layer，所以代码物理上重复。改一处务必同步另一处。
- 不要在 `make up` 跑完忘了 `make down`——AgentCore evaluator 本身免费、
  Lambda 也几乎免费，但 evaluator 占活跃配额（每 region 100 个），别堆。
