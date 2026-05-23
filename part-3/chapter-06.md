# Chapter 6: 技术栈快速决断矩阵 — 第一周给出有依据的选型

## 开场

```
苏州合昇精密重工，会议室，周二上午 10 点。
项目代号 TicketTriage-V1，第 8 天。

CTO 周明远把投影仪打开:
  "我看了招标技术方案，三家 ISV 都说自己用 RAG + Agent。
   你们 FDE 团队的方案呢？我下周一要给董事会拍板。"

陈雪 (业务方): "我只关心准确率上 95% 没有，别给我看架构图。"
顾建国 (IT 主管): "我只关心数据出不出厂，模型是不是国产的。"

你需要在 30 分钟内回答:
- 用 Bedrock 还是 SageMaker?
- 用 Claude 还是 Nova 还是开源?
- 单 Agent 还是多 Agent?
- 自建 harness 还是用 AgentCore?
- 三个人的诉求都要给出答案,且要可验证
```

这就是第一周技术选型会议的真实场景。三个不同坐标系的人，一个 30 分钟窗口，一份要进董事会的方案。

这一章给的不是"通用最佳实践"，是 **30 分钟内能完成的快速决断流程**：从 5 个维度出发，每个维度有可量化的判断条件，每个判断条件背后有一个能在你 AWS 账号上 30 分钟内跑通的 mini-eval。

读完这一章你应该能：

1. 在白板上画出一张 "工单 Agent v0" 的架构选型决断图，每个组件后面都跟着一句"我选它的依据是 ___"
2. 当客户说"为什么不用 X"时，给出**有数字的反驳**，而不是"X 不适合"这种空话
3. 知道 2026 上半年 AWS 上"哪些功能新到我必须考虑"，"哪些功能稳到我可以无脑选"

> **运行案例**：本章及 Ch7、Ch8 共享一个真实工程案例 — 苏州合昇精密重工的工单 Agent 项目。客户画像、约束、数据形态见仓库 `research/case-manufacturing-tickets.md`（项目内部备注，不入书正文）。本章用到的关键参数：日均 230 工单、48 名驻外工程师、SLA ≤ 2 小时、等保 2.0 三级、模型调用必须境内。

---

## 6.1 30 分钟选型框架 — 五维决断

把"AI 应用技术栈"拆成 5 个**互不耦合**的维度。每个维度独立决策，决策完拼出全栈。耦合度不为零（比如选了 Bedrock 就限制了模型范围），但这种 5×N 框架的好处是 **能把"我在选什么"说清楚**，不至于一上来讨论"用 LangChain 还是 LangGraph"这种过于具体的细节。

```
                    ┌──────────────────────┐
                    │ D1: 模型托管面       │  Bedrock / SageMaker / 自建 / 第三方
                    │   决定数据出域路径   │
                    └──────────┬───────────┘
                               │
                    ┌──────────┴───────────┐
                    │ D2: 模型选型          │  Claude / Nova / 开源 / 国产
                    │   决定能力 + 单价    │
                    └──────────┬───────────┘
                               │
                    ┌──────────┴───────────┐
                    │ D3: 调用模式          │  RAG / Tool use / Agent / 微调
                    │   Ch7 展开           │
                    └──────────┬───────────┘
                               │
                    ┌──────────┴───────────┐
                    │ D4: 编排框架          │  AgentCore / Strands / LangGraph
                    │   决定运维成本       │   / 自建
                    └──────────┬───────────┘
                               │
                    ┌──────────┴───────────┐
                    │ D5: Eval 与可观测     │  Bedrock Eval / AgentCore Eval
                    │   Ch8 展开           │   / 自建
                    └──────────────────────┘
```

D3 和 D5 是后两章的主菜。本章把 D1、D2、D4 讲透，并给出每个维度上的快速 mini-eval。

### 我们将在合昇案例上做的决断

为了让讨论具体，先给出最终选型，然后用本章剩余部分回答"为什么"：

| 维度 | 选型 | 一句话理由 |
|---|---|---|
| D1 模型托管面 | **Bedrock**（中国客户走阿里云百炼，AWS 在书里做演示） | 客户要求境内模型，但 AWS 的工程实践对国内同行有借鉴价值；Bedrock = 不维护推理基础设施 |
| D2 模型 | **claude-haiku-4-5 + claude-opus-4-7（兜底）** | 实测数据见 6.3；haiku 准确率达标且单价是 opus 的 1/15 |
| D3 调用模式 | RAG + Tool use（不上 Agent） | Ch7 展开；当前数据形态不需要多步规划 |
| D4 编排 | **直接 boto3 + 自己写 200 行 dispatcher**，6 个月后再考虑 AgentCore | Phase 1 不需要 AgentCore 的能力；过早引入降低团队学习曲线 |
| D5 Eval | Bedrock Model Evaluation + 自己跑 LLM-as-judge | Ch8 展开 |

这 5 个选型都是有数字支撑的。下面逐个给数字。

---

## 6.2 D1 — 模型托管面：四条路线的 6 维对比

```
                        Bedrock          SageMaker JumpStart   自建 GPU         第三方 API
                                         (托管开源/微调)        (vLLM on EC2)    (OpenAI/Anthropic 直连)
                        ─────────────    ───────────────────   ──────────────   ─────────────────
数据出域                ✓ 有 PrivateLink ✓ 有 VPC endpoint     ✓ 完全本地       ✗ 必须出域
冷启时间                秒级             分钟级                 小时级           秒级
单价 (/1M tokens)       $0.27 - $5.63    实例小时费 ~$3-30/h    EC2 g5.12x ~$5/h $0.50 - $30
延迟 (P50)              500ms - 1.4s     200ms - 800ms          200ms - 600ms    400ms - 2s
模型可选                Claude/Nova/Llama/  Llama/Mistral/Qwen/   任意开源         OpenAI/Claude/
                        DeepSeek/MiniMax/   Falcon/Phi/Gemma 等   (含国产)         Gemini
                        Mistral 等 24+
运维负担                极低             低（实例需调优）       高（GPU 故障/  低
                                                              扩缩容）
```

> 数据来源：自测（Bedrock 一行见 6.3）、AWS Bedrock Pricing 页（2026-05）、AWS What's New 2025-12 Bedrock 18 个开源模型上线公告。

### 为什么 Bedrock 是 70% 中型客户的默认选择

不是因为它最好，是因为它**最快可用**。一个第一周的 FDE 项目，如果你选了"自建 GPU"路线，意味着：

- 客户运维要新增一类技术债（GPU 故障 → 模型不可用）
- FDE 团队要学一套新工具（vLLM / TGI / Triton 选型 + 调优）
- 6 个月后客户问"为什么 Llama 4 出了我们用不上"，团队还要再做一次升级

Bedrock 的核心价值不是单价或延迟，是 **把"模型这一层"从客户的运维范围里拿掉**。这正是 *Outcome = Harness × Customer* 公式里 Harness 的本意 —— 你不要让你的 Harness 包含"维护一个推理服务"这种事。

> **2026-05 新功能：Bedrock Reserved Service Tier**（[2025-11 GA](https://aws.amazon.com/about-aws/whats-new/2025/11/amazon-bedrock-reserved-service-tier/)，[2026-01 扩展到 Opus 4.5/Haiku 4.5](https://aws.amazon.com/about-aws/whats-new/2026/01/amazon-bedrock-reserved-tier-claude-opus-haiku/)）。当客户问"我担心被限流"，可以承诺一个 1 个月或 3 个月的 reserved capacity，固定 TPM 配额，超出部分自动 overflow 到 Standard tier。这是**第一次 Bedrock 在产品层面解决了"生产环境流量峰值"问题**，也是 6.5 节降本表里的一行。

### 什么时候不选 Bedrock

| 客户情况 | 推荐路线 |
|---|---|
| 数据完全不能出私有云（如金融/军工某些系统） | **自建 GPU + vLLM**；推荐 SageMaker HyperPod 简化运维 |
| 推理 QPS 持续 > 50 且预算敏感 | **SageMaker JumpStart 部署 Llama 4 / Qwen3** + reserved instance；TCO 在 Bedrock 之下 |
| 模型必须是某个特定的国产模型（合规） | 阿里云百炼 / 火山方舟 / 智谱开放平台；AWS 路线不适用 |
| Phase 0 验证、纯 API 调用、客户允许调用境外 | 直接调 Anthropic API；省一层 Bedrock |

合昇的情况：客户允许调用境内模型，**不允许**调用境外 API。所以本书演示用 AWS Bedrock（FDE 同行借鉴用），实际项目落地用阿里云百炼。技术选型逻辑完全相同，只换一个 SDK。

---

## 6.3 D2 — 模型选型：用 10 条 eval 决定该选谁

这是这一章最重要的一节。

任何脱离了客户具体数据的"哪个模型最好"讨论都是在浪费客户的钱。下面是合昇项目第 6 天的实操：

### Step 1: 构造最小可信 eval 集（30 分钟）

打开历史工单系统，**手挑 10 条**有代表性的工单 —— 不是 5000 条，是 10 条。覆盖：

- 每个故障大类至少 1 条
- 每个团队（机械组 / 电气组）至少 4 条
- 至少 1 条是新人会派错的（陈雪指认）
- 至少 1 条是带方言/口语化描述的（"老师傅说那个不行了"）
- 至少 1 条是带报警代码的（如 `ALM 4501`）

每条工单标准答案由**陈雪 + 王师傅** 双盲打标，不一致时陈雪决断。10 条标完，30 分钟。

完整的 10 条样例见仓库 `demos/ch6-stack/data/eval-v0.jsonl`。摘录两条：

```json
{"id": "T-2025-Q4-0142",
 "ticket": "客户报修：JG-A6 五轴加工中心，X 轴定位异常，加工件公差超差 0.08mm，已发现 X 轴伺服电机过热报警 1042。请求工程师上门。",
 "expected_team": "电气组",
 "expected_fault_type": "伺服系统",
 "rationale": "1042 是伺服电机过热代码，归属电气组"}

{"id": "T-2025-Q4-2018",
 "ticket": "新来的徒弟操作：他说屏幕上显示 ALM 4501 报警动不了。我看了一下是冷却液液位低。我让他加了冷却液还是报警。是不是传感器坏了？",
 "expected_team": "电气组",
 "expected_fault_type": "传感器",
 "rationale": "ALM 4501 是冷却液液位传感器代码，加液后不复位多为传感器或线路"}
```

### Step 2: 跑实测（45 分钟）

完整可执行代码：仓库 `demos/ch6-stack/scripts/bench.py`。这里只摘核心：

```python
import boto3, time

# 关键陷阱 1: Anthropic 模型必须用 'us.' 跨区推理 profile
# 直接传 'anthropic.claude-opus-4-7' 会得到:
#   ValidationException: ... isn't supported. Retry with the ID or ARN
#   of an inference profile that contains this model.
MODELS = {
    "claude-haiku-4-5":  "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "claude-sonnet-4-6": "us.anthropic.claude-sonnet-4-6",
    "claude-opus-4-7":   "us.anthropic.claude-opus-4-7",
    "nova-pro":          "us.amazon.nova-pro-v1:0",
}

# 关键陷阱 2: Claude 4.6/4.7 不接受 temperature 参数 (2026-05 新限制)
# 老脚本里如果硬编码 temperature=0 会报错: `temperature` is deprecated for this model.
def inference_config(model_id):
    cfg = {"maxTokens": 200}
    if "claude-opus-4-7" not in model_id and "claude-sonnet-4-6" not in model_id:
        cfg["temperature"] = 0.0
    return cfg

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

### Step 3: 看真实数据（不是 benchmark 截图）

下面这张表不是从论文截图来的，是**本章写作时（2026-05-23）在 us-east-1 实跑出来的**，10 条 × 4 模型 × 3 次 = 120 次调用，总成本约 $0.50：

| 模型 | 派工准确率 | 故障类型准确率 | P50 延迟 | P90 延迟 | $/1k 工单 |
|---|---|---|---|---|---|
| claude-haiku-4-5 | **100.0%** | 40.0% | 784ms | 918ms | **$0.37** |
| claude-sonnet-4-6 | 93.3% | 40.0% | 1340ms | 1997ms | $1.10 |
| claude-opus-4-7 | 100.0% | 40.0% | 966ms | 2383ms | $5.63 |
| nova-pro | 90.0% | 40.0% | **498ms** | **536ms** | **$0.27** |

> *方法论*：每个模型对每条工单调用 3 次，分别记录 token 用量、延迟、解析后的 `{team, fault_type}`。准确率 = 输出与人工标准答案完全一致的比例。$/1k 工单按 us-east-1 on-demand 定价（haiku/sonnet/opus = $1/$3/$15 输入，$5/$15/$75 输出；nova-pro = $0.80/$3.20）线性外推到 1000 单。完整数据快照保存在仓库 `demos/ch6-stack/results/`（每章 demo 用完拆除资源；快照仅记录测得的数字，不含 AWS 凭证）。

### Step 4: 这张表怎么解读

天真的解读：**"haiku 100% 准确率而且最便宜，选它。"**

错的。3 个 FDE 必须做的二阶解读：

**（a）40% 的"故障类型准确率"是 eval 设计问题，不是模型问题**

四个模型在故障类型上都是 40%。这种"全员卡同一个数"的现象**几乎一定是 ground truth 写法的问题**。回看 eval：我把 expected 写成"伺服系统"，但模型可能输出"伺服电机"——语义相同但字符串不同。

> **FDE 第一定律**：当所有候选给同一个奇怪的数字时，先怀疑 eval。这点在 Ch8 会展开。

**（b）派工准确率的差异在 10 条上不显著**

Haiku 100%、Sonnet 93%、Opus 100%、Nova 90% —— 看似 Haiku 和 Opus 并列第一，但 10 条样本上单题误差就是 ±10%。**这张表能告诉你"4 个候选都接近达标"，不能告诉你"Haiku 比 Opus 强"**。要分高下需要 200+ 样本。

**（c）延迟和成本的差距才是关键决策依据**

| 维度 | 差距 | 业务影响 |
|---|---|---|
| 延迟（P90） | nova-pro 0.5s vs opus-4-7 2.4s（5×） | 工单分派从"瞬时"变"等一下"，调度员体验差异显著 |
| 成本 | nova-pro $0.27 vs opus-4-7 $5.63（21×） | 日均 230 单，年化 nova-pro $25 / opus $516 |

合昇日均 230 单，99% 业务价值 = 准确率达标后，剩下的差异是**延迟和成本**，不是模型"智商"。

### Step 5: 决断

```
┌─────────────────────────────────────────────────────────┐
│  primary:   claude-haiku-4-5  (一审,处理 95% 简单工单)  │
│  fallback:  claude-opus-4-7   (复杂工单升级,5%)         │
│                                                         │
│  分流条件: 报警代码 OR 工单字数 > 200 OR 客户等级 = A   │
│  预估成本: 0.95 × $0.37 + 0.05 × $5.63 = $0.63/1k 工单 │
│  预估延迟: 0.95 × 0.92s + 0.05 × 2.4s = 0.99s          │
└─────────────────────────────────────────────────────────┘
```

这种 **primary + fallback** 的混搭模式比"all-in 一个模型"更便宜（混合成本只比 haiku 高 70%，但准确率上限取 opus）。这种设计 6 个月前实现起来要写不少 routing 代码，今天 Bedrock 上有更轻的方案：

> **2026-05 新功能：Bedrock Advanced Prompt Optimization and Migration Tool**（[公告](https://aws.amazon.com/about-aws/whats-new/2026/05/amazon-bedrock-advanced-prompt-optimization-migration-tool/)）支持把同一个 prompt 在 5 个候选模型上自动 A/B，输出延迟/成本/准确率对比报告。如果你要做的是"6.3 节这种实验"，2026 年中之后可以考虑直接用这个工具，跳过自己写 bench.py 的步骤。但教学场景下我推荐先自己写一遍 —— 你需要知道每一行在做什么，工具是后来的事。

---

## 6.4 D2 续 — 这五个新功能可能改变你的选型

近 6 个月（2025-11 到 2026-05）Bedrock 上有 5 个变化是**改变选型逻辑**的，不只是边角更新：

### 6.4.1 模型供应链：Bedrock 不再 = Claude

**[2025-12 Bedrock 一次性上线 18 个开源模型](https://aws.amazon.com/about-aws/whats-new/2025/12/amazon-bedrock-fully-managed-open-weight-models/)**：Gemma 3、MiniMax M2、Mistral Large 3、Kimi K2 Thinking、Qwen3-Next、Qwen3-VL 等。

**[2026-02 再加 6 个](https://aws.amazon.com/about-aws/whats-new/2026/02/amazon-bedrock-adds-support-six-open-weights-models/)**：DeepSeek V3.2、MiniMax M2.1、GLM 4.7、Kimi K2.5、Qwen3 Coder Next。

新增模型走 **Project Mantle** 推理引擎，提供 OpenAI 兼容 API。这意味着：

- 如果客户已有 OpenAI SDK 代码，**改 endpoint 即可迁移到 Bedrock**，省去重写客户端
- DeepSeek、Qwen3 这种"中国团队亲手训的开源模型"现在是 Bedrock 一等公民
- 之前"Bedrock = Claude only"的偏见在 2026 年应该淘汰了

**对合昇的影响**：如果客户某天说"我们想用 Qwen3 因为社区方便招人"，AWS 路线下不需要切到 SageMaker/自建，直接换 modelId 即可。

### 6.4.2 服务等级：Reserved / Priority / Flex

**[2025-11 引入三档服务等级](https://aws.amazon.com/about-aws/whats-new/2025/11/amazon-bedrock-priority-flex-inference-service-tiers/)**：

| Tier | 谁用 | 价格 |
|---|---|---|
| **Reserved** | 生产环境，固定 TPM | 1 个月 / 3 个月承诺，固定单价 |
| **Priority** | 实时业务，要求 99.5% uptime | Standard 的 1.25× |
| **Standard** | 默认 | 当前 on-demand |
| **Flex** | 批量评估、离线总结 | Standard 的 0.5×（异步，时延宽松） |

**对合昇的影响**：

- 工单分派走 **Priority**（实时，业务可见）
- 历史工单批量回填 + Eval 跑批走 **Flex**（半价）
- 上线一个月后客户预算稳定 → 切 **Reserved**

调用代码改动量：在 Converse API 里加一个 `serviceTier` 参数。

```python
# 实时调用走 priority
client.converse(modelId=..., serviceTier="priority", ...)

# 离线 eval 走 flex
client.converse(modelId=..., serviceTier="flex", ...)
```

> **FDE 提示**：这是一个"教育客户"的好场景。客户的传统认知是"我得选一个 tier"，但实际是"同一个模型同一个账号，不同调用走不同 tier"。这种灵活度是 Bedrock 区别于"自建推理服务"的核心价值之一。

### 6.4.3 长缓存：1 小时 prompt caching

**[2026-01 prompt caching 从 5 分钟扩到 1 小时](https://aws.amazon.com/about-aws/whats-new/2026/01/amazon-bedrock-one-hour-duration-prompt-caching/)**（Claude Sonnet 4.5 / Haiku 4.5 / Opus 4.5）。

工单 Agent 的典型 prompt 包含：

- 系统指令（100 tokens）
- 12 个故障类型定义 + 每类 1-2 个 few-shot（约 1500 tokens）
- 工程师团队职责说明（200 tokens）

这 1800 tokens **每条工单都重复**。开 1 小时 caching 后，缓存命中部分按 1/10 价格计费。合昇的工单分布是"白天密集，晚上稀疏"，1 小时 cache 几乎**全天命中率 80%+**。

实测算一下：1800 tokens × 230 单 × 0.8 命中 × $1/1M × (1 - 0.9) = **每天省 $33** = 年化 $12K。

这是 Phase 1 几乎一定要开的。

### 6.4.4 私有部署：Mantle PrivateLink

**[2026-02 Bedrock OpenAI 兼容端点支持 PrivateLink](https://aws.amazon.com/about-aws/whats-new/2026/02/amazon-bedrock-expands-aws-privatelink-support-openai-api-endpoints/)**（14 个 region）。

之前"开源模型在 Bedrock 上"和"私有部署"是两件事 —— 客户要么放弃私有，要么自己建 GPU。现在 Mantle 端点本身就支持 VPC endpoint，**走客户私有网络调用 DeepSeek / Qwen3**。

合昇虽然境内不用 AWS，但读者中如果有北美客户的工程师，这条会直接改变 D1 的选型。

### 6.4.5 跨账号 Guardrails

**[2026-04 Bedrock Guardrails 跨账号 GA](https://aws.amazon.com/about-aws/whats-new/2026/04/bedrock-guardrails-cross-account-safeguards/)**：管理账号定义 guardrail，所有子账号自动生效。

这是平台工程团队的胜利：之前每个 dev/test/prod 账号都要单独配，现在一个组织级 guardrail 一统。**对 FDE 的影响**：当客户问"上线前怎么保证内容安全"，不再需要自己写一套 guardrail 编排，组织已有的统一生效。

---

## 6.5 D4 — 编排框架：什么时候你不需要 framework

这一节是要"反共识"的。

**业内默认动作**：搭 Agent → 立刻引入 LangGraph / Strands / AgentCore。
**FDE 实操**：80% 的项目第一周不需要任何 framework，200 行 Python 直接写。

### 6.5.1 三个工程层级

```
                Level 0          Level 1            Level 2
                直写             轻量框架           Agent 平台
                ────             ──────              ────────
代码量          ~200 行          ~500 行            ~1000 行
依赖            boto3            boto3 + Strands    boto3 + AgentCore
状态            每次请求重新算   函数调用栈          AgentCore 持久 session
观测性          自己写 log       Strands trace      AgentCore Observability
能力            分类/路由/简单RAG  + 工具调用       + 长任务/A/B/审批流
迁移成本        —                改个 import       重做架构
```

### 6.5.2 选型规则（写在白板上让客户看）

```
项目 phase  →  推荐
─────────────────────
PoC (前 4 周)        → Level 0  直写
Phase 1 (4-12 周)    → Level 0 → Level 1 (按需升级)
Phase 2 (12+ 周)     → Level 1 → Level 2 (有具体需求才升)
```

为什么不"一步到位上 AgentCore"：

1. **学习曲线征收**：客户工程师 12 周内必须能独立 maintain。Level 0 = 200 行 Python，他们立刻能改；AgentCore = 9 个组件 + Cedar policy + Identity，没 4 周培训接不了
2. **debug 成本**：Level 0 的 bug 在你的代码里；AgentCore 的 bug 可能在 runtime / gateway / observability，每层都要看 console
3. **观测性等价物**：Level 0 + CloudWatch Logs + 一些自己埋的 metric 几乎等价于 AgentCore Observability 的 80%

### 6.5.3 什么时候必须升级到 Level 2

```
   出现这 3 个信号中至少 2 个 →  考虑 AgentCore:

   信号 A: 单个用户的"会话状态"必须跨 8 小时 +
            (例: 让 Agent 等"客户上传文档" 6 小时后继续)

   信号 B: Agent 调用 5+ 工具且需要"管理员审批某些操作"
            (例: 备件下单需主管批准, Agent 暂停等批准)

   信号 C: 有 4+ 团队同时在改同一个 Agent
            (例: 售后/销售/IT 都接了 tool, 需要 policy 隔离)
```

合昇的情况：

- 信号 A：✗ 工单平均 30 分钟内完成，不需要长会话
- 信号 B：✗ 工单 Agent 不做下单，只做分派+检索
- 信号 C：✗ 第一期只有 FDE 团队 1 个改

→ Level 0 直写，Phase 1 不引入 AgentCore。

### 6.5.4 但你必须知道 AgentCore 在做什么

哪怕这一期不用，你必须知道它的能力边界 —— 客户和领导会问。下面是 2025-11 至 2026-05 期间 AgentCore 的关键功能演进：

| 时间 | 功能 | 解决什么问题 |
|---|---|---|
| 2025-10 GA | Runtime / Gateway / Identity / Observability / Memory / Browser tool / Code interpreter | 全平台首次 GA |
| 2025-11 | [Direct code deployment](https://aws.amazon.com/about-aws/whats-new/2025/11/amazon-bedrock-agentcore-runtime-code-deployment/) | 代码上传，省 Dockerfile 学习成本 |
| 2025-12 | [Policy + Evaluations (preview)](https://aws.amazon.com/about-aws/whats-new/2025/12/amazon-bedrock-agentcore-policy-evaluations-preview/) | Cedar policy 限制工具调用 / 13 个内置评估器 |
| 2026-03 | [Stateful MCP server](https://aws.amazon.com/about-aws/whats-new/2026/03/amazon-bedrock-agentcore-runtime-stateful-mcp/) | MCP session、elicitation、approval 流程 |
| 2026-04 | [Managed harness + AgentCore CLI + Skills](https://aws.amazon.com/about-aws/whats-new/2026/04/agentcore-new-features-to-build-agents-faster/) | "harness" 概念被 AWS 官方收编 |
| 2026-04 | [Payments (preview)](https://aws.amazon.com/about-aws/whats-new/2026/04/amazon-bedrock-agentcore-payments-preview/) | x402 协议，agent 直接付款 |
| 2026-05 | [Performance Loop (optimization)](https://aws.amazon.com/about-aws/whats-new/2026/05/bedrock-agentcore-optimization-preview/) | AI 自动改 prompt + A/B 测试 + 显著性报告 |

> **小心**：Performance Loop 是 preview。FDE 项目里所有的 preview 功能默认不进生产路径，只用于 PoC。客户问"我们能用 Performance Loop 吗"的标准答案是"现在做 PoC 行，2026-Q4 再上生产"。

---

## 6.6 选型反模式 — 6 个高频错误

| 反模式 | 后果 | 正确做法 |
|---|---|---|
| **跟着 GitHub trending 选 framework** | 客户 6 个月后没人能 maintain | 选客户 IT 部门能在你离开后接管的 |
| **不做 mini-eval 就给方案** | 客户问"为什么不用 Opus" 你答不上 | 6.3 这种 30 分钟实测 |
| **过早引入 Agent 框架** | Phase 1 demo 就要写 Cedar policy | 看 6.5.3 三个信号 |
| **用 benchmark 论文做选型依据** | benchmarks 数据集 ≠ 客户工单 | 在客户数据上自己跑 |
| **All-in 一个最强模型** | 单价是 fallback 模式的 10× | 6.3 step 5 的 primary + fallback |
| **忽略 inference profile 这种"小事"** | 上线当天报 ValidationException | 第一天就跑通端到端调用 |

最后这条值得展开：本章 6.3 节我自己跑 demo 时**真的踩到了** "on-demand 模型 ID 不能调用" 和 "Claude 4.7 不支持 temperature" 两个坑。这种坑如果是上线当天才发现，足以让客户对你失去信心。**第一周必须做的事：把每个候选模型在客户的实际网络条件下调通一次**。

---

## 6.7 30 分钟选型流程小结

回到开篇的"30 分钟会议"场景，这就是你站在白板前要做的：

```
00:00-05:00  画 5 维选型框架(6.1 那张图), 让在场所有人达成共识
                "我们今天要决定 5 件事, 不要跑题到具体技术"

05:00-15:00  D1: 模型托管面
              - 客户合规要求 → 列出 4 条路线哪些可选(6.2 那张表)
              - 通常 1-2 条胜出
              - 选定后, "这个决定锁定 6 个月, 大家同意吗?"

15:00-25:00  D2: 模型选型 (打开 6.3 的 mini-eval 数据展示给客户看)
              - "这是上周我们用你们 10 条工单跑出来的实测"
              - "primary + fallback 模式, 成本 ___, 延迟 ___"
              - 业务方关心准确率, IT 关心数据出域, 都满足

25:00-30:00  D3/D4/D5 留给后续
              - "Ch7 我会展开 RAG vs Agent 决策树"
              - "Ch8 我会给完整 Eval pipeline"
              - "今天先把 D1+D2 锁定, 下周回来给 D3-D5"
```

决断的产物是**一张 1 页纸**，包含：

1. 5 个维度的选型 + 每个维度一句话理由
2. 6.3 那张实测对比表
3. 预估成本（年化）+ 预估延迟（P50/P90）
4. 风险清单（你看到但还没打开的 3 个问题）

签字栏：周明远（CTO，预算批）、陈雪（业务方，验收口径确认）、顾建国（IT，集成边界确认）。

---

## 关键引用

> "*The best architectural decision is the one your customer's team can defend without you in the room.*"
> — A. Lawrence, *FDE Rule Book*, 2025

> "*If your benchmark isn't on the customer's data, you're not benchmarking — you're decorating.*"
> — Conikeec, *The FDE Playbook*, 2025

> "*Two things kill agent projects: framework lock-in and unverified benchmarks. Fix both in week one.*"
> — Anthropic Engineering Blog, *What we learned from one year of building production agents*, 2026

---

## 动手清单

第一周技术选型阶段，按顺序做这 8 件事：

1. **拉出客户当前合规 / 数据出域 SOP 文件**，确认是否允许 AWS（境外）/ AWS 中国 / 阿里云百炼 / 自建 GPU 中的哪些选项
2. **画 5 维框架**（6.1），让客户三个角色都看一遍，问哪个维度最重要
3. **在客户的真实数据里手挑 10 条**作为 eval-v0，由客户业务方+1 名资深工程师双盲打标
4. **跑 6.3 的 bench.py**，至少覆盖 3 个候选模型（Bedrock 上 ≥ 1 个 Claude，≥ 1 个非 Claude）
5. **算 primary + fallback 的混搭成本**，对比单一模型方案
6. **检查近 6 个月 Bedrock What's New** —— 至少看 6.4 的 5 条
7. **明确 Phase 1 不引入 AgentCore**（除非满足 6.5.3 的两个信号）
8. **把决断结果写成 1 页纸**，让客户三个角色都签字

---

## 反模式清单

- ❌ **没跑 mini-eval 就给选型方案**（被客户用一个具体数字问倒）
- ❌ **直接选"最强模型"或"最便宜模型"**（前者预算爆，后者准确率坑）
- ❌ **没看近 6 个月 What's New**（6 个月前的方案在 2026 上半年很可能已经被 Bedrock 新功能覆盖）
- ❌ **第一周就上 Agent 框架**（除非有 6.5.3 信号，否则你在给客户加技术债）
- ❌ **benchmark 来自论文 / 第三方测评**（客户数据分布与论文不同，结论不可信）
- ❌ **不知道 inference profile 这类"小事"**（上线当天会出大事）
- ❌ **不写"风险清单"**（只列优点的方案没人敢拍板）

---

## 验证：在你账号上跑一遍

本章所有数字都是可复现的。把仓库 clone 下来：

```bash
git clone https://github.com/dawei008/fde-book.git
cd fde-book/demos/ch6-stack
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 配置 AWS 凭证 (你自己的账号)
export AWS_REGION=us-east-1

# 跑实测 (4 模型 × 10 题 × 3 轮, 总成本约 $0.50)
python scripts/bench.py --eval data/eval-v0.jsonl --models all --runs 3

# 看报告
python scripts/report.py results/latest.json

# 用完即拆 (Bedrock 是 managed service, 无持久资源, 直接删本地文件)
rm -rf results/
```

如果你看到的数字和 6.3 节有 ±10% 内的差异 —— 正常，模型有抽样性。如果差异 > 30%，说明 AWS 那边有更新，或者你的 prompt 改了。**不要**直接信我的数字，信你账号上跑出来的数字。

---

## 与下一章的关系

这一章解决了 **D1（托管面）+ D2（模型）+ D4（编排层级）**。还剩两个维度：

- **D3 调用模式**（RAG vs Fine-tune vs Prompting vs Agent）→ 下一章 Ch7
- **D5 Eval 与可观测**（同样是合昇案例的工单 Agent）→ Ch8

下一章会沿用同一个 eval 集，把"为什么这一期不上 Agent"用 RAG 实测的数字回答透。

[← Part III Intro](intro.md) · [Next: RAG / Fine-tune / Agent decision tree →](chapter-07.md)
