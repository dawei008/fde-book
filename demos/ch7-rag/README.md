# ch7-rag — prompting vs RAG vs RAG+rerank

Ch7 论点："先 prompting，不行加 RAG，再不行加 agent，最后才考虑 fine-tune"。
本 demo 用合昇海外业务工单场景的 15 道题，把同一组问题分别走 3 种接法，
把"加 RAG 到底值不值"变成可量化的延迟 / 准确率 / 成本三角对比。

## 三种接法

| | A. Prompting | B. RAG (RetrieveAndGenerate) | C. RAG + Rerank |
|---|---|---|---|
| 检索 | 无 | KB Retrieve top-5 | KB Retrieve top-10 → Cohere Rerank → top-3 |
| 生成 | Claude Haiku 4.5 直接答 | KB 一次调用搞定 (custom prompt template) | Converse with reranked chunks |
| 实现 | `Converse` API | `RetrieveAndGenerate` API | `Retrieve` + `cohere.rerank-v3-5` + `Converse` |

## 依赖

需要先把 `demos/hesheng-core` `make up`，本 demo 通过 `hesheng_core.config.load()`
读 manuals bucket 名字 (`fde-book-hesheng-{account}-manuals`)，KB 数据源指向那里。

```bash
cd demos/hesheng-core && make up      # 上传手册到 S3
cd ../ch7-rag
pip install -r requirements.txt
```

## 跑法

```bash
make up      # ~7 min: IAM + OpenSearch policies + collection (~5 min) + index + KB + ingestion
make run     # ~2 min: 15 questions x 3 approaches = 45 calls
make down    # ~1 min: tear everything down (IMPORTANT — OpenSearch is hourly billed)
make verify-down   # confirm KB / collection / role 全部消失
```

## 预期成本

OpenSearch Serverless 起来后即使空闲也按 OCU-hour 收费 (~$0.24/hour)，所以
"up → run → down" 必须是一次连贯流程。完整流程的实测花费：

| 项目 | 花费 |
|---|---|
| OpenSearch Serverless (collection 在线 ~12 min, 1 indexing OCU + 1 search OCU) | ~$0.10 |
| Bedrock 嵌入 (4 docs × ~300 tokens, Titan v2) | <$0.01 |
| Bedrock 生成 (45 calls × ~500 tokens avg, Claude Haiku 4.5) | ~$0.05 |
| Cohere Rerank (15 calls × $0.001) | $0.015 |
| **合计** | **<$0.20** |

> OpenSearch Serverless 最低收费 ~2 OCU 运行不到 1 小时，按小时取整后实际账单
> 可能落在 $0.50–$1.00 之间。第一次执行务必跑完立刻 `make down`。

## 实测结果（一次真实跑过的输出，见 `results/`）

```
A_prompting:  acc=32.22%  p50=2013ms  $0.93/1k calls
B_rag:        acc=87.78%  p50=2215ms  $0.33/1k calls
C_rag_rerank: acc=86.67%  p50=2331ms  $2.75/1k calls
```

按问题类别拆开：

| approach | simple | rag-specific | multi-doc | refusal |
|---|---|---|---|---|
| A | 0.83 | 0.07 | 0.54 | 0.25 |
| B | 1.00 | 0.95 | 1.00 | 0.25 |
| C | 1.00 | 0.95 | 1.00 | 0.17 |

读出来的工程结论：

1. **prompting only 在专有事实题（rag-specific）几乎全错**——它不知道
   ALM 4501 归哪个组、P1 SLA 多少分钟。这就是"加 RAG"的证据。
2. **RAG 加上去之后 rag-specific 直接打到 0.95**——加得对。
3. **rerank 在这个 4-文档的小 KB 上没带来准确率收益**，但延迟和成本都增加。
   这是真实工程信号：reranker 是为大型 KB（top-50 candidates）准备的，
   小 KB 直接用 top-5 就够了。
4. **B_rag 反而比 prompting 便宜**：custom prompt template 让 KB 输出极简短
   答案（avg 50 tokens vs prompting 的 200+ tokens），output token 少导致
   总成本反而下降。

## 这组数字不能直接外推（很重要）

这个 demo 跑的是一个 **4 文档的小 KB 场景**，prompt-only 装不下手册全文，
所以 prompting 看起来很差。但 Ch7 第 4 节合昇第一期里讲过另一个场景——
"200 条报警代码 prompt 塞得下，根本不上 RAG"——同一个论点的另一面。

**RAG 该不该上，先看 prompt 塞不塞得下，不看 RAG 这个 demo 能不能拿高分。**
如果你的语料 prompting 能装下（几十到几百 KB 量级、低频更新），先 prompting；
装不下、要时效更新、要引用透明，再考虑 RAG。这个 demo 是后一种情况下"加 RAG
值不值"的量化对比，不是"是否要加 RAG"的决策依据。

## 重要的真实坑（一次跑出来发现的）

1. **opensearch-py 3.x 是 keyword-only 参数**: `client.indices.exists(INDEX_NAME)`
   报 `TypeError`。必须写成 `client.indices.exists(index=INDEX_NAME)`。
2. **OpenSearch Serverless 数据访问策略 update 没有变化时会被拒绝**：
   `ValidationException: No changes detected in policy`。需要先 diff principals
   再决定要不要 update，否则二次 `make up` 直接挂掉。
3. **Bedrock RetrieveAndGenerate 的默认 prompt 太防御**：当 retrieval score
   ~0.4（其实是 hit）时，默认模板会输出 "Sorry, I am unable to assist..."。
   必须传 `generationConfiguration.promptTemplate` 自定义 prompt 才能用。
   这是第一次跑 B_rag 准确率只有 52% 的根因，加了 custom template 后
   立刻跳到 88%。
4. **Cohere Rerank v3.5 在 Bedrock 是 `cohere.rerank-v3-5:0`**，body schema 是
   `{api_version:2, query, documents, top_n}`，跟 Cohere 直家 API 略有不同。
5. **OpenSearch collection 删除是异步的**——`delete_collection` 返回后
   collection 还在。如果不等它真的消失就尝试删除 access policy，会报
   `OcuLimitExceededException` 或类似的错。teardown 必须 poll 到 collection
   gone 才往下走。

## 文件结构

```
ch7-rag/
├── Makefile                       up / run / down / verify-down
├── README.md                      this
├── requirements.txt               boto3 + opensearch-py
├── data/
│   ├── eval-v0.jsonl             15 道题 (simple/rag/multi-doc/refusal 4 类)
│   └── ch7-state.json            up 期间生成, 记录 KB / collection / role IDs
├── results/
│   ├── rows.jsonl                每问每接法一行原始记录
│   ├── summary.json              结构化汇总
│   └── summary.md                人读的对比表
├── scripts/
│   ├── up.py                     创建所有 AWS 资源
│   ├── run.py                    跑 eval
│   ├── down.py                   拆除（顺序: data source → KB → collection → policies → role）
│   └── verify_down.py            确认无残留
└── src/ch7_rag/
    ├── __init__.py
    └── state.py                  状态文件 dataclass
```

## 不要做的事

- 不要跨账号跨人共享 `ch7-state.json`（KB ID / Collection ID 都是账号专有的）
- 不要在 `make up` 跑到一半 Ctrl-C 后忘了 `make down`——OpenSearch 按小时收费
- 不要把 reranker 当万能补丁——它只在大型 KB（>50 候选）才显著有效
