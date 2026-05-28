---
title: "第 7 章 RAG / 微调 / Agent 决策树"
parent: "Part III — 技术选型"
nav_order: 2
---

# 第 7 章 RAG / 微调 / Agent 决策树

第 6 章把"用谁的模型"定下来了（合昇案例选了 Claude Haiku 4.5 + Opus 4.6 兜底）。但**模型只是引擎**——你还得决定怎么把客户的知识和工作流接上去。这就是这一章的事。

四种主流接法：

- **Prompting**——只改提示词，模型靠预训练里的知识回答
- **RAG**——把外部知识库索引起来，模型查了再答
- **Fine-tune**——把客户数据训进模型权重
- **Agent**——让模型自己规划、调用工具、做多步推理

新手 FDE 最常见的失败模式是听到客户说"做一个 AI 助手"就开始上四种里最复杂的——agent 加 RAG 加 fine-tune 全堆上。结果 6 周做完一个调不动的怪物，客户一个具体问题问下来发现答得不如 ChatGPT 直接调 prompt。

这一章给一个**判断顺序**：先想办法用 prompting 解决，不行加 RAG，再不行加 agent，最后才动 fine-tune。每一步都用客户实测验证，不达标才往下走。

---

## 7.1 四种接法的本质区别

| 接法 | 输入处理 | 知识来源 | 输出生成 | 一句话理解 |
|---|---|---|---|---|
| **Prompting** | 原始 query | 模型预训练权重 | 模型直接生成 | 改提示词，让模型自己懂 |
| **RAG** | query → 检索 | 外部知识库（可更新） | 检索 + 模型生成 | 把答案放进资料库，模型查了再答 |
| **Fine-tune** | 原始 query | 新权重（你训的） | 新模型生成 | 把答案教进模型脑子 |
| **Agent** | query → 规划 | 工具调用结果 + 模型权重 + 知识库 | 多步推理 + 综合 | 让模型自己用工具办事 |

读这张表注意一件事：**四种接法不是互斥的**。生产里大多数 LLM 应用都是 prompting + RAG，复杂的是 prompting + RAG + agent。Fine-tune 通常是和前三种之一配合用，单独用 fine-tune 上线的项目很少。

---

## 7.2 决断顺序：从便宜的试起

我给客户做选型时的标准顺序：

```
默认顺序:
  1. 先 Prompting (最便宜、最快)
  2. 不够 → 加 RAG (加外部知识)
  3. 还不够 → 加 Agent (让模型主动办事)
  4. 实在不行 → Fine-tune (最贵、最难维护)
```

**90% 的 LLM 应用，Prompting + RAG 已经够了**。Fine-tune 是最后的最后才考虑的方案。

为什么这个顺序？因为四种接法的成本结构差很大：

| 接法 | 启动成本 | 边际成本 | 维护成本 |
|---|---|---|---|
| Prompting | 几小时调 | 一次调用的 token 费 | 改 prompt（半小时） |
| RAG | 几天到一周 | 检索 + 调用 | 索引重建（几小时到一天） |
| Agent | 几周 | 多步调用 + 工具调用 | 工具协议升级 + 监控 |
| Fine-tune | 几周到几个月 | 推理（自己跑或托管） | 模型重训（每次几天） |

**最重要的判断不是"哪个最强大"，是"客户的痛点能不能用更便宜的接法解决"**。先 prompting，prompting 上限到了再升级。这是 outcome-driven 思维的具体落实——你对结果负责，不对"用了多复杂的技术"负责。

---

## 7.3 怎么判断当前痛点用哪种接法

四种接法对应四种典型痛点。下面是判断逻辑：

**问题 1：客户痛点是"模型不知道答案"还是"知道但答得不对"？**

如果是"不知道"——模型预训练里没有的领域知识、最新数据、客户内部信息——那默认走 RAG。RAG 的本质是"让模型查资料再答"。

如果是"知道但答得不对"——回答机械、风格不对、行业术语用错——先试 prompting + few-shot。给模型 3-5 个示范例子，告诉它"这种问题应该这样答"，绝大多数风格问题这样能解。

回到合昇的工单分诊例子（第 6 章）：客户的痛点是"模型应该把工单派给机械组还是电气组"。这是"知道但答得不对"——模型完全理解工单的中文，但派工逻辑是客户公司内部约定的（哪些故障归机械组、哪些归电气组）。这种用 prompting + few-shot 试一下，给模型 5-10 个真实派工示范，再让它判新工单。

**问题 2：用 prompting 试过了，准确率上不去——加什么？**

看上不去的原因。

如果是因为 **prompt 太长 / few-shot 塞不下**——比如客户有几百种故障代码、每种代码对应不同的处理流程，prompt 里塞不下全部——升级到 RAG。把故障代码库作为外部知识库索引起来，按 query 检索相关的几条进 prompt。

如果是因为 **prompt 写得对，但模型输出还是不一致**——比如同一个工单两次问得到两个不同的派工结果——这是模型的"模式覆盖度"问题。先试 prompt 里加更明确的判断逻辑（"如果工单包含报警代码 4501-4999，归电气组"），如果还不行考虑 fine-tune。

**问题 3：客户需要的不是"回答问题"，是"自动办事"——怎么办？**

走 agent。"自动办事"的特征：模型需要**调用外部工具**（查 API、写数据库、发邮件），而且**步骤是动态的**（不是固定流水线，是模型根据上一步的结果决定下一步做什么）。

但要警惕——很多客户嘴里说"我要 agent"，实际需求是"我要一个固定流程的自动化"。这种用 prompting + 工作流编排（Step Functions、Airflow）就够了，不需要让 LLM 来规划。**判断标准**：如果你能用流程图把所有可能的执行路径画完，那不需要 agent；如果路径分支太多画不完，agent 才有价值。

合昇的工单分诊：纯分类问题，不需要 agent。如果二期扩成"分诊 + 自动调用 ERP 查备件库存 + 自动给客户发回执邮件"——那是 agent。

**问题 4：什么时候真的需要 fine-tune？**

三个场景：

- **风格 / 行话怎么都对不上**：prompting 加再多 few-shot 都达不到目标风格。常见于法律、医疗等强专业领域。
- **延迟 / 成本对不上**：你的 prompt 太长（几千 tokens），调用频率又高，每次调用都付一次 prompt 成本不可接受。Fine-tune 把知识压进权重里，prompt 可以缩到几百 tokens。
- **私有部署 + 强数据敏感**：客户不允许把数据送到任何外部 API（即使是 Bedrock 这种"私有云内"的也不行），必须在自己机房跑模型——这种通常配合 fine-tune。

90% 的 LLM 项目不属于以上三种。Fine-tune 是终极方案，不是默认方案。

---

## 7.4 在合昇案例上展开决断

回到第 6 章的合昇工单分诊。第 6 章定了模型选型，这一章决定怎么接客户的工单数据：

**第一步**：试 prompting + few-shot

模型直接看工单文字判机械组还是电气组。Prompt 里塞 10 个真实派工示范（5 个机械组 + 5 个电气组）。第 6 章的 bench 跑出来了——haiku 派工准确率 100%（10 条样本 × 3 runs = 30 次调用）。说明派工逻辑可以靠 prompting 解决。

**问题来了**：第 6 章的 bench 在 10 条样本上准确率 100%，扩到 200 条还能保持吗？

实测要在 Scaffolding 阶段做。这是评估集 v0 → v1 扩充的事，第 8 章展开。这一步最重要的判断是：**至少在 10 条上能做到 100%，说明这条路径成立**——不需要急着上 RAG 或 agent。先把 prompting 做到 v1.0 通过线，达不到再往下加。

**第二步**：判断要不要加 RAG

合昇的客户工单有几个特征：经常带报警代码（如 `ALM 4501`）、引用机床型号（如 `JG-A6`）、提到具体的故障类型。模型预训练里没有合昇的报警代码表，没有 JG 系列机床的故障对照表——这些是客户内部知识。

但 prompt 能不能塞下？合昇的报警代码表大约 200 个，全塞进 prompt 大概 3000-4000 tokens。Claude Haiku 4.5 的上下文窗口是 200K，完全塞得下。

**结论**：第一期不上 RAG。把报警代码表和机床型号-故障类型对照表全塞进 system prompt。第 6 章的 1 小时 prompt cache 正好让这种长 system prompt 不会每次都付费。

什么时候才需要切到 RAG？两种情况：

- 客户报警代码表扩到几千条 prompt 塞不下
- 客户加进新场景需要历史维修记录的检索（比如"过去半年类似故障怎么处理的"）——这是真正的 RAG 场景

**第三步**：判断要不要加 agent

合昇第一期 scope 只有"分诊"——给定工单输出一个结构化判断（派工组 + 故障类型 + 优先级）。没有"调用外部工具"的需求。

如果二期扩到"分诊后自动调 ERP 查备件库存"——那才需要 agent。但二期不在第一期 scope 里。

**结论**：第一期 prompting 单解决，不上 RAG，不上 agent。架构最简、成本最低、客户工程师最容易接手维护。

---

## 7.5 RAG 的关键工程决策（如果你要上）

如果你的项目确实需要 RAG（合昇第一期不需要，但很多 LLM 应用项目需要），下面是几个关键决策点。

### 切片策略

切片是 RAG 最容易做错的地方。两个常见错误：

- **切得太碎**：500 tokens 一片，召回时拿到的片段不完整，模型根据残缺信息瞎答
- **切得太大**：4000 tokens 一片，token 成本爆炸，且模型在长上下文里抓重点能力下降

实操经验：**先按文档结构切**（章节、段落），保持语义完整；**长段落再按 800-1500 tokens 二次切**，重叠 100-200 tokens 防止信息断开。Bedrock Knowledge Bases 默认提供这种 hierarchical chunking 策略，省去自己造轮子。

### 检索方式

三种主流：

- **稠密检索（向量相似度）**：把 query 和文档都转成 embedding，算余弦相似度。适合语义匹配（同义词、复述）。弱点是精确关键词匹配（人名、产品 ID、报错代码）经常召回不到。
- **稀疏检索（BM25）**：传统的关键词匹配。精确关键词强，语义弱。
- **混合检索**：稠密 + 稀疏并行，结果合并。这是大多数生产 RAG 系统的标配。

具体到合昇这种带报警代码的场景：纯向量检索会漏报警代码。一定要混合检索。Bedrock Knowledge Bases 现在原生支持 hybrid search，配置上一行的事。

### Reranking

检索回来 top 10 的文档，里面会有几条不相关的。直接全塞进 prompt 浪费 token 还干扰回答。

加一层 reranking——用一个小模型（Cohere Rerank、Bedrock 自带的 rerank）对 top 10 重新打分，选 top 3-5 进 prompt。这一步能显著提升答案质量，成本极低（rerank 调用比生成调用便宜一个数量级）。

### 评估

RAG 的评估比纯 prompting 复杂。两个独立维度：

- **Context Relevance**：检索回来的文档和 query 真的相关吗？这是检索系统的责任。
- **Answer Faithfulness**：模型生成的答案是基于检索的文档，还是自己幻觉？这是生成系统的责任。

两个分要分别测。Bedrock Knowledge Bases Evaluation 内置这两个维度。第 8 章展开评估方法。

---

## 7.6 Fine-tune 的常见误判

最后说几个 fine-tune 的常见误判，避免新手 FDE 走错路：

**误判一：客户问"能不能用我们的数据训一个专属模型"**

客户的本意通常是"让模型懂我们的业务"。这件事 RAG 能做、prompt with few-shot 能做、fine-tune 也能做。客户不在乎用哪种技术，只在乎效果。**先用前两种试，达不到再上 fine-tune**——同样的 outcome，前两种省 90% 的工作量。

**误判二：fine-tune 解决"幻觉"问题**

不解决。Fine-tune 改变的是模型的输出风格和领域适应，不改变它编造事实的倾向。事实正确性靠 RAG（让模型基于真实文档回答）和 guardrails（让模型在不知道时承认）解决，不靠 fine-tune。

**误判三：fine-tune 一次就完事**

不对。Fine-tune 出来的模型有"维护周期"——客户业务变了、新数据来了、底层模型升级了，你都需要重新 fine-tune。每次 fine-tune 周期几天到几周，对客户来说是持续负担。这也是为什么尽量不上 fine-tune 的核心原因——它是**在客户那边创造了一类长期债务**。

**误判四：fine-tune 一定比 RAG 准**

不一定。在很多任务上 RAG + 强模型的准确率超过 fine-tune 后的小模型。Fine-tune 的优势是延迟和成本，不是准确率。如果你的客户对延迟不敏感，RAG 几乎一定是更好的选择。

---

## 7.7 在 AWS 上的实操对照

如果项目跑在 Bedrock 上，四种接法对应的服务：

| 接法 | 主要 AWS 服务 | 实操要点 |
|---|---|---|
| **Prompting** | Bedrock 模型 + 1h prompt cache | system prompt 长就开 cache，省钱 |
| **RAG** | Bedrock Knowledge Bases + OpenSearch / pgvector | 默认 hybrid search + reranking |
| **Agent** | Bedrock AgentCore（参考第 6 章 6.4 节是否升级到 Level 2 编排） | 第一期单 agent 单 tool 不需要 AgentCore |
| **Fine-tune** | Bedrock Custom Models / SageMaker JumpStart | 优先 Bedrock 上的 LoRA fine-tuning，不要自己起 SageMaker 训练 job |

每一条都需要单独的工程展开。Knowledge Bases 的实战在第 9 章（数据工程）展开，agent toolset 设计在第 14 章，fine-tune 数据集准备在第 9 章末尾。这一章只决定**用哪种接法**，不展开每种接法的实战。

---

## 7.8 实测：三种接法在合昇手册上的对比

理论判断"先 prompting，不行加 RAG"听起来对，但**不在客户数据上跑过的判断不算判断**。这一节给一个可在你 AWS 账号上复现的端到端 demo——同一组合昇风格的问题，分别走三种接法，看真实的延迟、成本、准确率三角对比。完整代码在仓库 `demos/ch7-rag/`，依赖 `demos/hesheng-core/`（共享基础已 up）。

**Eval 集 v0**：15 条合昇业务问题，分四类：
- simple（2 条）——基础事实，prompting 能直答
- rag-specific（7 条）——查具体报警代码、SLA 数字、特定故障，必须查手册
- multi-doc（4 条）——跨多文档综合，比如"Jakarta 机械故障工时不够该怎么办"
- refusal（2 条）——故意问手册没有的（如 JG-A8 详细故障表），测幻觉

**实测结果**（每条问题每种接法各 1 次，共 45 次调用）：

| 接法 | 准确率 | P50 延迟 | P95 延迟 | $/1k 调用 |
|---|---|---|---|---|
| **A: Prompting only** | 31.56% | 1808 ms | 3124 ms | $0.93 |
| **B: RAG (Bedrock KB)** | **87.11%** | 2098 ms | 3783 ms | **$0.33** |
| **C: RAG + Cohere Rerank** | 87.11% | 2537 ms | 3653 ms | $2.75 |

按类别看准确率：

| 接法 | simple | rag | multi-doc | refusal |
|---|---|---|---|---|
| A: Prompting only | 0.83 | 0.07 | 0.54 | 0.20 |
| B: RAG | 1.00 | 0.95 | 1.00 | 0.20 |
| C: RAG + Rerank | 1.00 | 0.95 | 1.00 | 0.20 |

**这张表能告诉你三件事**：

第一，**rag-specific 类别从 0.07 跳到 0.95**——查具体故障代码这种事，prompting 完全靠不住，加 RAG 之后准确率打到天花板。这是"先 prompting，不行加 RAG"判断的具体支撑。

第二，**B 比 A 还便宜**（$0.33 vs $0.93/1k）。这反直觉。原因是 RAG 把上下文从"手册全文塞进每个 prompt"变成"按需检索几段相关的"——输出 token 数也短了（agent 答得更聚焦），总成本反而下降。这是 Bedrock 内置 prompt template 的工程效益。

第三，**Reranker 没让 B 变好**——C 准确率和 B 完全一样（87.11%），但延迟多 20%、成本贵 8 倍。**4 文档的小 KB 上 reranker 是负 ROI**。Reranker 的价值在 KB 上百份文档时——前几十条召回里有多条不相关，reranker 才有过滤价值。合昇这种小 KB 场景一定不要默认上 reranker。

**真实工程坑**（demo 跑过程中撞到的，写到章节里供后人避免）：

- **Bedrock RetrieveAndGenerate 默认 prompt 太防御**：第一次 B 的准确率只有 52%。看 trace 发现模型经常答"对不起我无法回答"——根因是 RAG 召回分数 ~0.4 时（中文检索的真实命中分），默认模板会让模型谨慎到拒答。改用自定义 `generationConfiguration.promptTemplate` 后跳到 88%。**任何中文 RAG 项目都需要自定义生成模板**。
- **Knowledge Base 删除有 race**：默认 `dataDeletionPolicy=DELETE` 时，删 data source 会异步清理向量库；如果你紧接着删 OpenSearch collection，两个动作 race，KB 卡在 `DELETE_UNSUCCESSFUL`。修法是创建时显式 `dataDeletionPolicy="RETAIN"`，反正 collection 删了向量库自然没了。
- **Cohere Rerank v3.5 的 body schema** 是 `{api_version:2, query, documents, top_n}`，和 Cohere 直连 API 不一样。Bedrock 文档不显眼，第一次调容易踩。

**回到合昇第一期的判断**：上面这张表反而是反向证据——**一旦 prompt 塞得下，先用 prompting**。合昇第一期 200 条报警代码全塞进 system prompt 才 4000 tokens，远未到上限；用 Bedrock 1 小时 prompt cache（system prompt 前缀缓存命中），后续工单调用只为短的 user 输入付输入 token 费——平均每次调用的有效成本比这一节 demo 里的 RAG 路径还低。RAG 该不该上，**先看 prompt 塞不塞得下，不看 RAG 能不能拿高分**。这个 demo 的小 KB 场景下 RAG 必胜，但"必胜"不等于"必上"——合昇的判断是"用最便宜的够用方案"。

完整代码 + 实测产物：`demos/ch7-rag/`。OpenSearch Serverless 是按小时计费的（B / C 接法都依赖它），跑完务必立刻 `make down`，不要留着过夜。

---

## 收尾

这一章给的是判断顺序：先 prompting，不行加 RAG，再不行加 agent，最后才考虑 fine-tune。每一步都用客户的实测验证，不达标才往下走。

合昇案例第一期落地 prompting，不上 RAG，不上 agent，不 fine-tune。这是看起来"最不 AI"的方案，但它是最可能在 12 周内交付的方案。

下一章解决最后一个 D5 问题——评估和可观测。第 6 章定了模型，这一章定了接法，下一章定**怎么知道自己做得对**。这是 FDE 工作的最后一块拼图，也是最容易被新手低估的一块。

---

## 本章引用的公开资料

- Anthropic / OpenAI 工程博客 — 关于 prompting 优先、再 RAG、再 fine-tune 的方法论排序
- Lewis et al., *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks* (2020) — RAG 的原始定义
- AWS Bedrock 文档 — Knowledge Bases、AgentCore、Custom Models 的产品说明
