---
title: "第 3 章 FDE 不是什么"
parent: "Part I — 角色与心智"
nav_order: 3
---

# Chapter 3: 两种 FDE 形态 — 数据驱动型 vs LLM 驱动型

## 开场

```
两个 FDE 在同一家咖啡店。

A 在 Palantir，10 年。今天他在改一段 PySpark，把客户某 ERP 表
增量同步到 Foundry 的 Ontology，建一个"客户-订单-发货"的图谱。
他读 Avro schema 的速度比读小说快。

B 在 OpenAI，1 年。今天他在调一个 prompt template，让 Agent
能在客户的 Jira 里自动创建子任务。他熟悉 5 种 LLM 的 system prompt
风格差异。

两个人 title 都是 Forward Deployed Engineer。
两个人做的事看起来完全不一样。

但你跟他们聊一小时会发现 —— 思维方式 80% 重合，
工具栈 80% 不重合。

这一章讲：这两种 FDE 的边界在哪、什么时候切换、
你接到一个项目时怎么判断自己应该用哪种模式。
```

---

## 3.1 两种形态的本质区别

```
                  数据驱动型 FDE              LLM 驱动型 FDE
                  ─────────────────           ─────────────────
代表公司          Palantir, AWS GenAIIC      OpenAI, Anthropic
                  Snowflake PS, Databricks   Cohere, Cresta
                  传统 ToB 咨询              下游 AI 创业公司

核心问题          客户的"数据"怎么用上       客户的"工作流"怎么自动化

主要交付物        Ontology + Pipeline        Agent + Prompt + Toolset
                  + Dashboard + Report       + Eval Set

用的硬技能        SQL, Spark, ETL, dbt       LLM API, Prompt
                  数仓建模, schema 演化      RAG, Agent 框架
                  Avro/Parquet/Iceberg       MCP, Function Calling

用的软技能        和数据团队 / DBA 协作      和业务 PM / 一线员工协作
                  懂数据治理 / 隐私合规      懂业务流程 / 用户画像

时间分布          50% 数据探索               40% Discovery / 业务理解
                  30% Pipeline 工程          30% Prompt + Eval 工程
                  20% 业务对接               30% 集成 + 部署

成功的样子        客户做决策时能直接          客户工作流里某个动作的
                 用数据回答问题              中位时间显著下降

最致命的失败       数据正确但没人用           Demo 惊艳但用不起来
```

---

## 3.2 决定形态的不是公司，是项目

很多人以为"我在 X 公司就是 X 形态"。错。

**真正决定的是项目所处的阶段和客户的瓶颈**：

```
            判断你当前在哪种形态
            ─────────────────────────────────

  问 1：客户的瓶颈是"数据用不上" 还是 "工作流没自动化"？
        ↓                              ↓
        数据用不上                    工作流没自动化
        → 数据驱动型                   → 看问 2
                                      ↓
  问 2：现有的工作流是基于结构化数据还是基于自然语言？
        ↓
        基于结构化数据                基于自然语言/文档/对话
        → 偏数据驱动型                → LLM 驱动型
        （比如自动报表）              （比如客服 / 合同 / 知识问答）
```

### 几个真实例子

**例 1**：金融客户要"理赔自动化"

- 第 1-4 周：读他们的理赔流，发现关键卡点在"医生病历 → 理赔金额"的非结构化转结构化 → **LLM 驱动型**（OCR + LLM 提取）
- 第 5-8 周：发现提取出来的字段需要和保单条款 join，做规则引擎 → **数据驱动型**
- 第 9-12 周：把规则化的判断重新封装成可解释 Agent → **LLM 驱动型**

**同一个项目，三个阶段三种形态**。

**例 2**：制造业客户要"设备预测性维护"

- 整个项目核心是时序数据 + 模型 → **数据驱动型主线**
- 但报告生成 / 工单语言 / 操作员问答这块用 LLM → **LLM 驱动型支线**

数据驱动主线 70%，LLM 支线 30%。**不是非此即彼**。

---

## 3.3 不同形态下的"三条铁律"具体落法

铁律没变，但落法不一样：

### Sell the outcome

| | 数据驱动型 | LLM 驱动型 |
|---|---|---|
| Outcome 例子 | 月度报表准点率 60%→95% | 客服首响中位时间 4h→30min |
| 数字来源 | 数据系统本身能算 | 需要新加埋点 / trace |
| 沟通对象 | 数据团队 + BI 部门 + 业务 | 业务团队 + 一线员工 |

### Eval-driven

| | 数据驱动型 | LLM 驱动型 |
|---|---|---|
| Eval 标的 | 数据正确性、口径、SLA | 答案质量、相关性、安全性 |
| Eval 工具 | dbt tests, Great Expectations, 自写 SQL | DeepEval, Promptfoo, Bedrock Evaluations |
| 跑分频率 | 每个 ETL run | 每个 PR + 每天回归 |

### Fix Forward

| | 数据驱动型 | LLM 驱动型 |
|---|---|---|
| 现场修什么 | 一段 SQL / 一个 dbt 模型 / 一个调度 | 一段 prompt / 一个 retriever 配置 / 一个 tool 定义 |
| Hot fix 通道 | Airflow / dbt cloud 直接发 | 配置中心 / Lambda / 边车 prompt 仓 |
| 部署权限 | 数据库写权限（受限） | 应用配置写权限（多用） |

---

## 3.4 工具栈的两套肌肉

下面两个清单，你可以判断自己当前缺哪一块：

### 数据驱动型 FDE 必备

```
入门              中级                  高级
────              ────                  ────
SQL（必备）       dbt                   数据建模 (Kimball / Inmon)
Python pandas    Airflow / Prefect      Apache Iceberg / Delta
JSON / Avro      Spark / PySpark        ontology 设计 (Palantir 风格)
PostgreSQL       Snowflake / BigQuery   schema 演化
                 Redshift               实时管道 (Kafka, Kinesis)
                 Kerberos / IAM         数据血缘 (OpenLineage)
                 ETL 调试               隐私合规 (GDPR, PII)
```

### LLM 驱动型 FDE 必备

```
入门               中级                  高级
────               ────                  ────
LLM API 调用       LangChain / LlamaIndex Agent 框架 (LangGraph,
                                          AutoGen, Bedrock Agents)
Prompt 工程        RAG (向量库)           MCP 协议
Function Calling   Eval 框架              Agent 工具沙箱 / 权限
JSON Schema        Trace 工具             Function Calling 复合
                   (LangFuse, Phoenix,    流式 / 结构化输出
                    LangSmith, Bedrock)
                   Vector DB              微调 (LoRA)
                   (Pinecone, Weaviate,   推理优化 (vLLM, TGI)
                    OpenSearch, pgvector) 部署 (SageMaker, Bedrock)
```

**FDE 不需要两套全精通**，但**两边都要"懂到能问对问题"**。

---

## 3.5 同一个项目内的形态切换

实操中，最难的是切换的"判断时机"。给你三个信号：

### 信号 1：发现"数据本来就有，只是没人能查"

→ 这是 LLM 驱动型机会（自然语言查询、RAG）

例：客户说"我们的合同条款搜不到"。先别急着写 ETL，看看是数据格式问题还是检索问题，可能 RAG 一上来就解决。

### 信号 2：发现"LLM 输出基本对，但下游没法接进系统"

→ 切回数据驱动型（结构化输出、schema 校验）

例：Agent 抽取的字段进不了 ERP，因为编码不统一。这时候你需要数据治理思维 —— 建 mapping 表 / 校验规则 / 异常处理。

### 信号 3：发现"客户决策需要数字，但现有数据不够"

→ 数据驱动型主线（埋点、ETL、看板）

例：客户问"这个 Agent 到底节省了多少时间"，你发现没埋点。先做埋点 → ETL → 看板，再继续 LLM 工作。

---

## 3.6 一个 AWS 视角的形态对照

AWS GenAI Innovation Center 的 FDE 是"两种形态都做"的典型代表。它的项目通常按以下 stack 配置：

```
        数据驱动型部分                  LLM 驱动型部分
        ────────────────              ────────────────
存储     S3, Lake Formation            S3 (KB 文档)
数据     Glue ETL, Glue Catalog        OpenSearch / Knowledge Bases
计算     EMR, Athena, Redshift         Bedrock (model invoke)
编排     Step Functions, MWAA          Bedrock Agents / Step Functions
治理     Lake Formation 权限           IAM + KMS
监控     CloudWatch + OpenLineage      CloudWatch + Bedrock guardrails
                                       + Bedrock Evaluations
```

一个客户的项目同一周可能既动 Glue ETL，又动 Bedrock Agent。**FDE 必须能"上下左右"切换**。

> **AWS 知识参考**：完整的两条线工具集见附录 A（FDE 工具栈速查表）和附录 B（对比矩阵）。

---

## 3.7 自检：你现在该侧重哪种形态

```
─────────────────────────────────────────────────────
 项目特征                          → 偏向哪种形态
─────────────────────────────────────────────────────
 客户最大痛点是"数据找不到"        → 数据驱动 60%
 客户最大痛点是"重复劳动太多"      → LLM 驱动 70%
 客户合规要求很严                  → 数据驱动 50%（先治理）
 客户业务高速增长，文档跟不上      → LLM 驱动 60%
 客户已经有数据团队                → 你做 LLM 驱动主线
 客户没有数据团队                  → 你做数据驱动主线
 客户希望"3 个月内见效"            → LLM 驱动（更快见效）
 客户希望"接下来 3 年的基础设施"    → 数据驱动（基础更扎实）
─────────────────────────────────────────────────────
```

---

## 关键引用

> "*The forward deployed engineer is data-driven by training and LLM-driven by opportunity.*"
> — A. Lawrence (paraphrased), *FDE Rule Book*, 2025

> "*The boundary between data work and AI work disappeared the moment LLMs became infrastructure.*"
> — AWS GenAI Innovation Center positioning, 2025-2026

---

## 动手清单

1. **判断你当前项目的形态**（用 3.2 / 3.7 的判断树）
2. **写一句话给老板**：本季度 70% 时间在 X 形态、30% 在 Y 形态
3. **检查自己的工具栈缺口**（3.4 节两个清单）选最缺的一项，本周补
4. **找你公司里另一种形态的资深 FDE 喝杯咖啡**，问他常见的失败模式
5. **画一张你当前项目的「两种形态分工图」**，对每个模块标注偏哪边
6. **下次客户对话**有意识感受："这个需求是数据型还是 LLM 型？"

---

## 反模式清单

- ❌ **强行用一种形态做所有事**（"我擅长 LLM 所以一切都用 LLM 解"）
- ❌ **数据治理还没做就堆 Agent**（地基不稳，越多 Agent 越糟）
- ❌ **数据已就绪还逼自己写 ETL**（错过 LLM 快速见效窗口）
- ❌ **跨形态切换时不知会客户和团队**（下游懵）
- ❌ **以为"切换形态 = 推翻重做"**（很多时候只是接一层适配）

---

## 与下一 Part 的关系

Part I 三章给了完整的 FDE 工程坐标系：时间形状（Ch 1）、判断形状（Ch 2）、能力形状（Ch 3）。

Part II 进入第一个具体动作 —— Discovery。从你接到一个新项目开始，**第一周到底问什么、看什么、写什么**。这是 FDE 工作中"最容易被忽视、收益却最高"的阶段。

[← 上一章: 三条铁律](chapter-02.md) · [下一 Part: 客户发现 →](../part-2/intro.md)
