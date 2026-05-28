---
title: "第 6 章 第一周的技术选型"
parent: "Part III — 技术选型"
nav_order: 1
---

# 第 6 章 第一周的技术选型

苏州合昇精密重工，海外业务部，会议室。项目第八天。

合昇的整机出口主要走东南亚——新加坡总仓、吉隆坡、曼谷、雅加达、胡志明市，五个站点共 48 名驻外服务工程师。三年前他们把 MES、CRM、工单系统迁到了 AWS 新加坡区。董事会十一月底要看工单 Agent 上线效果。

CTO 周明远把投影仪打开，手里捏着三家 ISV 的标书。"他们都说自己用 RAG + Agent。你们准备怎么做？我下周一要给董事会拍板。"

陈雪是售后系统的业务方，她不抬头："我只关心 95% 的派工准确率。架构图我看不懂。"

顾建国是 IT 主管，他更直接："我只关心这个东西能不能跑在我们现有 AWS 账号里、不要再开第二条供应商关系。审计去年才搞定一遍。"

会议预计三十分钟。我得在一张纸上回答五个问题：模型放哪、用谁、怎么调用、谁来编排、怎么验证。三个人的问题都得给出答案。

---

## 把"技术选型"拆成可独立决策的维度

很多 FDE 第一周翻车，是因为把"技术栈"当成一个整体来讨论。会议室里讨论"我们用 LangChain 还是 LangGraph"——讨论不出结果，因为这个问题本身没意义。在你确定模型在哪、用谁之前，编排框架是不能选的。

我习惯把它拆成五个维度，从下到上：

```
        ┌────────────────────────────────────────────────┐
        │ D5  评估 / 可观测                              │  ← 第 8 章
        │     怎么知道它在变好还是变坏                   │
        └────────────────────┬───────────────────────────┘
                             │
        ┌────────────────────┴───────────────────────────┐
        │ D4  编排                                       │  ← 本章 6.4 节
        │     谁把 prompt、tool、retry、log 串起来       │
        └────────────────────┬───────────────────────────┘
                             │
        ┌────────────────────┴───────────────────────────┐
        │ D3  调用模式                                   │  ← 第 7 章
        │     RAG / Tool use / Agent / 微调              │
        └────────────────────┬───────────────────────────┘
                             │
        ┌────────────────────┴───────────────────────────┐
        │ D2  模型选型                                   │  ← 本章 6.2、6.3
        │     哪一个 / 哪几个                            │
        └────────────────────┬───────────────────────────┘
                             │
        ┌────────────────────┴───────────────────────────┐
        │ D1  托管面                                     │  ← 本章 6.1
        │     模型部署在哪、数据走哪条链路               │
        └────────────────────────────────────────────────┘
```

D1 决定 D2 的可选范围（区域里有什么模型）。D2 决定 D4 的复杂度（如果一个 Haiku 就能解决 95% 的工单，你不需要多 agent 编排）。所以这五维不是平行关系，是有先后的。

会议三十分钟，我会把 D1、D2、D4 锁定，D3 和 D5 留给后续两章。

---

## 6.1  D1：在客户现有的 AWS 账号里把第一条调用链跑通

我让顾建国把现行的 AWS 账号架构图拿出来。一张可读性很差的 draw.io 图，但够用：

- 主 region：ap-southeast-1（新加坡）
- VPC：双 AZ，私有子网跑 ECS（CRM、MES）和 RDS
- 出网走 NAT；只有 SaaS 集成走外部白名单
- IAM 用 Identity Center 接 Okta SSO
- 没用 Bedrock，也没开过模型访问

第一周的 D1 不是"挑 Bedrock 还是 SageMaker"——是把客户现有的账号配置打通到能跑第一条 Converse 调用。这步常常被低估。

具体做了三件事：

**第一件，开通 Bedrock 模型访问。**Bedrock 默认对每个账号是关的，每个模型要单独申请。新加坡区 Anthropic 的 Claude 4.5 系列一申请就过，4.6/4.7 系列要走 cross-region inference profile（跨区到 us-west-2 或 us-east-1），需要客户审批"流量是否允许跨 region"。顾建国走了一次 30 分钟的内部流程批了。

**第二件，配 Bedrock VPC endpoint。**ECS 跑在私有子网，要么走 NAT 调 Bedrock 公网端点，要么开 VPC endpoint。顾建国坚持走 endpoint，理由是流量不出 VPC、可以接 endpoint policy 限制 modelId。我支持这个，因为它顺带把第一道安全护栏立了。

**第三件，跑通一次 hello world 调用。**真的就是 `boto3.client('bedrock-runtime').converse(...)` 调一次 haiku，看返回。这步看着没必要，但它能在第二天 demo 之前把所有"凭证 / endpoint / 模型 ID / IAM policy"的坑一次性踩干净。第一次跑我就撞到了两个坑（见 6.3）。

D1 锁定的不是"哪条供应商路线"，是"客户账号里下游所有 D2-D5 工作的网络/IAM/quota 已经准备好"。这一步做完，工单 Agent 才有地基。

> 后面的章节会用到的两个 Bedrock 能力，提前在这里说一句，避免到时候临时学。一个是 2025 年 11 月引入的 Reserved/Priority/Flex 三档服务等级——生产实时调用走 Priority，批量评估走 Flex（半价）。一个是 2026 年 1 月把 prompt cache 从 5 分钟扩到 1 小时——对工单这种"系统 prompt 长、用户输入短"的场景帮助很大。这两个都是上线后慢慢用的，第一周不用现在配。

---

## 6.2  D2：用谁的模型

我从来不在选型会议上回答"哪个模型最好"。这个问题没有答案——它取决于你的数据。

但合昇会议室里，周明远问的就是这个问题。我手里有什么？十条客户工单。

第六天我拉了陈雪和王师傅（资深维修工程师），让他们各自从历史工单里挑十条"最有代表性"的。两个人挑出来的有重合也有差异，我把并集二十条做了去重，最后留下十条：

- 五条机械组、五条电气组（覆盖两大派工去向）
- 至少一条是新人会派错的（陈雪指认 T-2018）
- 至少一条是带方言/口语化描述（"老师傅说那个不行了"——王师傅给的）
- 至少一条是带报警代码（`ALM 4501`、`报警 1042`）

每条由陈雪和王师傅双盲打标，两人意见不一致的，陈雪决断。十条标完，三十分钟。

这十条就是 eval-v0。它太小，跑不了任何科学结论，但它够用——够用来在会议室拍板"我们 primary 用谁"。

样本两条：

```json
{"id": "T-2025-Q4-0142",
 "ticket": "客户报修：JG-A6 五轴加工中心，X 轴定位异常，加工件公差超差 0.08mm，已发现 X 轴伺服电机过热报警 1042。请求工程师上门。",
 "expected_team": "电气组",
 "expected_fault_type": "伺服系统"}

{"id": "T-2025-Q4-2018",
 "ticket": "新来的徒弟操作：他说屏幕上显示 ALM 4501 报警动不了。我看了一下是冷却液液位低。我让他加了冷却液还是报警。是不是传感器坏了？",
 "expected_team": "电气组",
 "expected_fault_type": "传感器"}
```

完整十条在仓库 `demos/ch6-stack/data/eval-v0.jsonl`。

---

## 6.3  在客户的数据上跑一遍

第七天，我跑了一次基准。Bedrock 上四个候选：claude-haiku-4-5、claude-sonnet-4-6、claude-opus-4-7、amazon nova-pro。每个模型对每条工单调用三次。

跑这一次踩了两个坑，值得记下来。

**第一个坑**：Anthropic 的模型在 Bedrock 上不能直接用 on-demand 模型 ID。第一次跑，所有 Claude 都返回：

```
ValidationException: Invocation of model ID anthropic.claude-opus-4-7
with on-demand throughput isn't supported. Retry your request with the
ID or ARN of an inference profile that contains this model.
```

这是 Bedrock 推 cross-region inference 之后的硬要求。Claude 模型必须走 `us.anthropic.claude-opus-4-7` 这种带 region 前缀的 inference profile id。Nova 两条路都行，但为了一致我也走 profile。

```python
MODELS = {
    "claude-haiku-4-5":  "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "claude-sonnet-4-6": "us.anthropic.claude-sonnet-4-6",
    "claude-opus-4-7":   "us.anthropic.claude-opus-4-7",
    "nova-pro":          "us.amazon.nova-pro-v1:0",
}
```

合昇主 region 是新加坡，但这次基准我跑在 us-east-1，因为四个候选模型在 us-east-1 都直接可用。新加坡区当时还没全部开放，要走跨区 inference profile。这一步的目的是先确认"哪个模型够用"——区域可用性是落地时再做的二次 fit check。客户那边我也是这么解释的。

**第二个坑**：Claude 4.6 和 4.7 在 Converse API 上不再接受 `temperature`：

```
ValidationException: `temperature` is deprecated for this model.
```

老的脚本写 `inferenceConfig={"temperature": 0.0}` 就直接挂掉。改成按模型分支：

```python
def inference_config(model_id):
    cfg = {"maxTokens": 200}
    if "claude-opus-4-7" not in model_id and "claude-sonnet-4-6" not in model_id:
        cfg["temperature"] = 0.0
    return cfg
```

这两个坑我都不是查文档发现的，是上手跑才撞到的。这就是为什么在客户那边的网络上，第一周必须把 hello world 端到端跑一遍。

调用主体很简单：

```python
client = boto3.client("bedrock-runtime", region_name="us-east-1")

def call(model_id, ticket):
    t0 = time.perf_counter()
    resp = client.converse(
        modelId=model_id,
        messages=[{"role": "user",
                   "content": [{"text": PROMPT.format(ticket=ticket)}]}],
        inferenceConfig=inference_config(model_id),
    )
    return {
        "text": resp["output"]["message"]["content"][0]["text"],
        "in_tokens": resp["usage"]["inputTokens"],
        "out_tokens": resp["usage"]["outputTokens"],
        "elapsed_ms": (time.perf_counter() - t0) * 1000,
    }
```

完整代码：仓库 `demos/ch6-stack/scripts/bench.py`。

跑出来的数字（每模型 30 次调用）：

| 模型              | 派工准确率 | 故障类型准确率 | P50 延迟 | P90 延迟 | $/1k 工单 |
| ----------------- | ---------- | -------------- | -------- | -------- | --------- |
| claude-haiku-4-5  | 100%       | 40%            | 784ms    | 918ms    | $0.37     |
| claude-sonnet-4-6 | 93%        | 40%            | 1340ms   | 1997ms   | $1.10     |
| claude-opus-4-7   | 100%       | 40%            | 966ms    | 2383ms   | $5.63     |
| nova-pro          | 90%        | 40%            | 498ms    | 536ms    | $0.27     |

我把这张表打印出来带进会议室。陈雪扫了一眼："为什么故障类型全是 40%？四个模型一样？"

这是个好问题。四个候选在故障类型上全部 40%——这种"齐刷刷卡同一个数"的情况几乎肯定是 eval 设计问题，不是模型能力问题。我后来回去看：陈雪打标用的是"伺服系统"，模型经常输出"伺服电机"。语义相同，字符串不同。这个问题第 8 章会展开，它不是这次选型会议要解决的，但要承认它存在。

派工准确率上 haiku 100% 看起来最好，但十条样本的 ±10% 误差范围里，四个候选其实都接近达标。十条数据告诉我的是"四个候选都进入候选池"，不是"haiku 比 opus 强"。要分高下需要二百条以上。

真正能让我做决策的是延迟和成本：

- nova-pro 的 P90 是 0.5 秒，opus-4-7 是 2.4 秒。差五倍。调度员从"瞬时反应"变成"等一下"，体感差异很大。
- 单价 nova-pro $0.27 vs opus-4-7 $5.63（每千单）。日均 230 单 × 365 天 ≈ 8.4 万单/年，年化分别是 $23 和 $473。

合昇的工单 95% 是简单分诊。我没必要为每一条都用 opus。最终方案我推荐 primary + fallback：

```
primary:   claude-haiku-4-5  (95% 简单工单)
fallback:  claude-opus-4-7   (5% 复杂工单)

升级条件: 工单字数 > 200 OR 包含报警代码 OR 客户等级 = A

混合成本: 0.95 × $0.37 + 0.05 × $5.63 = $0.63 / 1k 工单
混合延迟: 0.95 × 0.92s + 0.05 × 2.4s   = 0.99s
```

这个方案比 all-in opus 便宜 9 倍，比 all-in haiku 贵 70%，但准确率上限拿到了 opus 的水平。

> 6 个月前实现这个 primary+fallback 自己得写一段路由逻辑。Bedrock 在 2026 年 5 月推了 Advanced Prompt Optimization and Migration Tool，能自动跑跨模型 A/B 并出延迟成本对比。如果你做的是和 6.3 节一模一样的实验，可以省掉一些手工活。但教学上我还是建议自己写一遍 bench.py——你需要知道每一行在做什么，工具是后来的事。

回到会议室。我把这张表念给周明远，他点头："这种依据我能给董事会讲。"陈雪问："五个百分点的复杂工单走 opus，会不会加错条件，简单工单也走过去？"我说："Ch7 那个升级路由我写完了我们再过一遍。"顾建国问："这个 inference profile 跨区的事，新加坡能拉回来吗？"我说："能。Bedrock 现在新加坡区的 Claude 4.5 全系都开了，4.6/4.7 走 cross-region。我们落地前再跑一次区域 fit check，区别主要是延迟，不影响选型逻辑。"

D2 锁定。

---

## 6.4  D4：什么时候你不需要框架

第二天周明远找过来："我让团队先看了下 LangGraph，听说挺好的。我们要不要直接上？"

我说不要。原因不是 LangGraph 不好，而是合昇这一期不需要它。

我用过的 agent 项目，第一周引入框架的，六个月后客户工程师能独立维护的，比例不到一半。框架不是没价值，是它的价值要等到项目复杂度真的需要它了才显现。在那之前，引入框架等于给客户加了一层学习负担和一类排错盲区。

我把 agent 编排分成三层：

**Level 0：直接 boto3，自己写 dispatcher**
两百行 Python。状态都在请求级别，每次调用从头算。日志走 CloudWatch Logs，metric 自己埋。能做的事：分诊、路由、简单 RAG、tool use。

**Level 1：轻量 agent SDK（Strands、LangGraph、AutoGen）**
五百行。框架帮你管对话栈、tool 调用 trace、retry。能做的事：上面所有的，加多步规划、tool 链。

**Level 2：托管 agent 平台（AgentCore）**
一千多行加一堆配置。平台管 session、policy、observability。能做的事：长会话（小时-天级别）、跨团队协作、复杂审批流。

合昇的工单 30 分钟内闭环、单 agent 单 tool（调 KB 检索）、第一期只有一个团队改代码。这是教科书级别的 Level 0 场景。我让团队第一期写 200 行直写，6 个月后视情况再升级。

这个判断我用三个信号来核：

```
满足两条以上 → 才考虑 Level 2 (AgentCore):

  A. 单个用户的会话状态需要跨 8 小时以上
     例: agent 等客户上传一份文档, 6 小时后客户传了, agent 接着干

  B. agent 调用 5 个以上工具, 其中至少一个需要管理员审批
     例: 备件下单要主管批, agent 暂停在那里等

  C. 4 个以上团队同时在改同一个 agent
     例: 售后/销售/IT 各接了 tool, 互相之间需要 policy 隔离
```

合昇三条都不满足。这是我建议 Level 0 的工程依据，不是凭直觉。

如果有一天合昇满足了——比如二期接入了备件下单流程（出现 B 信号），又把销售也接进来（出现 C 信号）——那我会重新评估。AgentCore 这一年做了很多扎实的工作，截至 2026 年 5 月一共 11 个能力（FAQ 上的官方清单）：

- **Runtime**——serverless 部署 agent / MCP server，8 小时长任务、bi-directional streaming、session 隔离、VPC 接入
- **Gateway**——REST API / Lambda / 现有 MCP server 一键转成 MCP-compatible tool
- **Memory**——跨 session 上下文存储
- **Browser**——云端浏览器，agent 操作网站
- **Code Interpreter**——沙箱跑 Python/JS/TS
- **Identity**——接 Cognito / Okta / Entra ID，agent 凭证管理
- **Observability**——Trace、debug、CloudWatch GenAI dashboard 一体
- **Evaluations**——LLM-judge + 代码 evaluator、五种评估模式（online/on-demand/batch/dataset/simulation）。Ch8 展开。子能力 **Optimization (preview)** 从生产 trace 自动生成 prompt / tool description 改进建议 + A/B 验证，Ch13 展开
- **Policy**——Cedar 自然语言 policy authoring、tool 调用层守门（不同于 Bedrock Guardrails 的内容守门）
- **Agent Registry**（preview）——企业内部发布 / 审批 / 发现 agent / tool / MCP server 的中心目录。Ch15 展开
- **Payments**（preview）——x402 协议，agent 付费访问 SaaS / paid APIs / MCP。本书不展开

合昇二期我用上了其中 5 项：Runtime、Gateway、Identity、Observability、Evaluations。Browser/Code Interpreter 用不上（没那种工作流），Policy 因为 14 个工具自己写规则就够了，Registry 和 Payments 是 preview 不进生产路径，Memory 因为我们的会话不需要跨 session 持久化。

判断逻辑很重要——AgentCore 11 项不是清单式"全部都要用"，而是"按需采用"。每一项的引入都对应一个具体的工程理由。三期合昇集团多 BU 协同时 Registry 才会变成必选项；金融客户做需要主管审批的工作流时 Policy 才会变成必选项。第一期 Level 0 的判断仍然是默认起点。

如果你想知道每一项的细节边界，仓库 `research/whats-new-2026.md` 整理了 2025-11 到 2026-05 的所有更新；`research/agentcore-2026-features.md` 是 11 项能力的逐项要点。

---

## 6.5  会议室里的产物

回到第一周那个三十分钟会议。最后我交给周明远的是一张 A4：

```
合昇精密重工 · 海外工单 Agent v1 选型决断
─────────────────────────────────────────

D1 托管:    AWS ap-southeast-1 (现有账号)
            Bedrock VPC endpoint + Identity Center 已就绪
            Claude 4.5 系列原生; 4.6/4.7 走 cross-region inference

D2 模型:    primary  claude-haiku-4-5
            fallback claude-opus-4-7  (字数>200 / 含报警码 / A 客户)
            预估     $0.63/1k 工单, P50 1 秒, 派工准确率 ≥ 95%

D3 模式:    Prompting + 长 system prompt（含报警代码全表），不上 agent (Ch 7)

D4 编排:    boto3 + 200 行 dispatcher                    (本章 6.4)
            6 个月后视 A/B/C 信号决定是否升级

D5 评估:    eval-v0 (10 条) → eval-v1 (200 条)            (Ch 8)
            上线前必须做的 4 件事见 Ch 8

锁定到:    2026-08-23 (三个月)                          周明远 ____
                                                        陈雪    ____
                                                        顾建国  ____
```

签字栏三个名字签了。这张纸接下来三个月是我的护身符——每次有人问"为什么不用 opus"、"为什么不上 agent"，我把这张纸拿出来。三个人都在上面签过字。

---

## 这一章踩过的坑

按时间顺序：

第三天，我在没看 IAM 架构图的情况下就开始写 bench 脚本，凭证用的是我自己的 AWS 账号。第五天顾建国把客户账号架构图推过来，我才发现 endpoint policy 限制只允许特定 modelId，我之前的脚本到客户账号上一行跑不了。**第一周第一天就要拿到客户账号架构图**。

第六天，我让陈雪一个人打 eval 标。她当时表示"差不多就行"。后来我才知道她对电气组报警代码不熟，T-2018 那条她标错过。**eval 标注必须双盲**，最好业务方 + 一线工程师。

第七天，我跑 bench 时直接抄了 6 个月前的脚本，撞进了 inference profile 和 temperature 两个坑，浪费 40 分钟。**第一周必须把每个候选模型在客户网络环境下端到端跑通一次**——不是看 README，是真跑。

第八天，会议室里我差点说"haiku 准确率 100% 比 opus 还高"。如果不是临进会议室前再看一眼数据想到 ±10% 误差，我就把这句话说出去了。**十条样本能告诉你 4 个候选都达标，不能告诉你谁更好**。

---

## 下一章

D3 还没解决：RAG、Tool use、Agent、微调，哪个？

合昇有 5000 份 PDF（产品手册 + 历史工单库 + 维修知识库），周明远的直觉是"先做个 RAG"。这是不是对的？这就是下一章。

[← Part III Intro](../intro/) · [下一章：RAG / Fine-tune / Agent 决策树 →](../chapter-07/)
