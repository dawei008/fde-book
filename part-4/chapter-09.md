# Chapter 9: 客户数据栈 — Ontology / ETL / 实时管道

## 开场

```
某金融客户。FDE 的 LLM Agent demo 跑得很好，但要接生产。

第一周接数据接到崩溃：
  - 客户数据库 5 个：PostgreSQL（主库）+ Oracle（合约）+
    SQL Server（财务）+ MongoDB（日志）+ 共享盘 Excel（30%）
  - 主键不统一：CRM 用 customer_id，ERP 用 cust_no，
    财务用 client_code，没有 mapping 表
  - 时区不统一：UTC + Asia/Shanghai + 客户当地时区混用
  - 一份关键报表的数据从 4 个系统拉出来，
    每个系统有不同的"客户" 定义

FDE 学到了一句话：
  "Agent 上线前 80% 的工程在数据治理上。
   不做数据治理直接上 Agent，
   Agent 越聪明越容易把不一致的数据
   错误地组合成自信的答案。"

这一章讲：怎么把一个客户的数据栈
从"五湖四海"治理到"Agent 能放心调用"。
```

---

## 9.1 客户数据栈的典型形状

```
        客户企业的"数据 5 层"
        ─────────────────────────────────────

  L1 操作型数据库 (OLTP)
     - PostgreSQL / MySQL / Oracle / SQL Server
     - 业务系统主存储

  L2 数据仓库 / 数据湖 (OLAP)
     - Snowflake / Redshift / BigQuery / Databricks / Iceberg
     - 跑分析的地方

  L3 中间层 (Data Mart / Cube)
     - dbt 模型 / 公司自建 view
     - 业务指标的"标准定义"

  L4 BI / Dashboard
     - Tableau / Power BI / Quicksight / Looker

  L5 业务应用 / Agent / API
     - 应用层使用数据的地方（FDE 的工作多在这一层）
```

**FDE 第一周要画一张这种"5 层数据图"**，把客户的现状画清楚。

---

## 9.2 Ontology — 把"五湖四海"统一

Ontology 是 Palantir 引入并推广的概念，本质上是**业务对象 + 关系 + 属性**的统一定义。

```
              Ontology 的 3 个组成
              ─────────────────────

  Object (对象):
    Customer / Order / Product / Contract / Employee
    每个对象有"金本位定义"

  Property (属性):
    Customer.id, Customer.name, Customer.tier
    每个属性有 source-of-truth

  Relationship (关系):
    Customer 1:N Order
    Order 1:N OrderItem
    Order N:1 Salesperson
```

### Ontology 的 4 个核心问题

```
1. 谁是"客户"？
   - CRM 表？还是付款主体？还是合同方？
   - 不同部门定义不一样 → 必须统一

2. ID 用什么？
   - CRM 的 customer_id?
   - 合同方的 unified_party_id?
   - 必须有"金 ID"

3. Mapping 怎么建？
   - 大部分情况是手工建表
   - 没有银弹

4. 谁有权改 Ontology？
   - 有 owner 才能避免"今天 A 改一个字段，明天 B 改回来"
```

### AWS 实操：用 Lake Formation + Glue Data Catalog 做轻量 Ontology

AWS 没有 Palantir 那种"完整 Ontology 框架"，但可以用 Glue + Lake Formation 实现轻量版：

```
        Glue Data Catalog 作为 Ontology 注册中心
        ─────────────────────────────────────────

  Database: customer_360_ontology

  Table: customer  (← 业务对象定义)
    Columns:
      - customer_id    (string, 金 ID)
      - source_systems (struct: crm_id, erp_no, finance_code)
      - tier           (string)
      - tags           (LF tags: PII, region=APAC)

  Table: order
    ...

  ↓
  Lake Formation Tags (LF-Tags):
    - PII: yes / no
    - sensitivity: public / internal / restricted
    - region: APAC / EMEA / NA

  ↓
  IAM 角色 + LF-Tags 控制谁能查哪个对象的哪个字段
```

**好处**：

- Ontology 的元数据由 Glue 维护
- 权限由 LF-Tags + IAM 维护
- Athena / Redshift / EMR 都能查
- Bedrock Knowledge Bases 直接读 Glue 元数据

> **AWS 知识参考**：搜 "AWS Lake Formation tags" 与 "Glue Data Catalog cross-account"。

---

## 9.3 ETL — 让数据流起来

ETL（Extract / Transform / Load）是把 L1 → L2 → L3 的工程。

### ETL 的 3 个工程信号

```
  数据"够新吗"？ → 看 SLA
    - T+1: 隔天看（90% 项目够用）
    - T+1h: 小时级（实时性要求高）
    - 实时: 秒级（CDC 才能做）

  数据"够准吗"？ → 看 quality 测试
    - 主键唯一
    - 不能有空值
    - 数值在合理范围
    - 业务规则（订单金额 > 0）

  数据"够稳吗"？ → 看依赖图 + 监控
    - 上游挂了，下游应该 graceful 失败
    - 失败应该有 alert
    - 重跑应该幂等
```

### ETL 工具速决

```
                    场景 → 推荐工具
                    ─────────────────────────

  云上 + Spark 系     Databricks / EMR + Delta
                      AWS Glue（serverless 友好）

  云上 + 数仓内       dbt + Snowflake / BigQuery / Redshift

  云上 + Streaming    Kafka + Kinesis Data Streams + Flink

  自建 / 离线         Airflow + Spark + Iceberg

  小规模 / 简单       AWS Step Functions + Lambda + S3
```

### dbt 是 FDE 的"瑞士军刀"

如果客户用云数仓，**80% 的 ETL 用 dbt 写**：

```
        dbt 项目的标准结构
        ──────────────────────────────────

  models/
    staging/
      stg_crm_customers.sql        (清洗 raw)
      stg_erp_customers.sql
    intermediate/
      int_customer_unified.sql     (做 join / mapping)
    marts/
      dim_customer.sql             (业务对象层)
      fct_orders.sql

  tests/
    not_null_customer_id.yml       (数据质量)
    unique_customer_id.yml

  macros/
    pii_mask.sql                   (复用逻辑)
```

dbt 的好处：

- SQL-only（FDE 不用学新语言）
- 自带 lineage（数据血缘可视化）
- 自带 testing（uniqueness / not-null / accepted-values）
- Git 管理 + 代码 review（数据工程也工程化）

---

## 9.4 数据血缘 / Lineage — 失败定位的命脉

```
        没有 Lineage 的数据栈：
        "下游报表错了" → 一个人翻 5 个系统找 3 天

        有 Lineage 的数据栈：
        "下游报表错了" → 5 分钟看清是哪个上游 ETL 改了 schema
```

### 工具

```
  开源:
    - OpenLineage（dbt / Airflow / Spark 都支持）
    - Marquez（OpenLineage 的 backend）

  商业 / 云:
    - DataHub
    - Atlan
    - AWS Glue (有 lineage 视图)
    - Unity Catalog (Databricks)
    - Foundry (Palantir)
```

### FDE 的最低要求

不要求"全公司血缘"，但**自己做的每个 dbt 模型 / Glue Job 必须接 lineage**：

```
1. dbt: 自动生成 lineage（dbt docs serve）
2. Airflow / Glue: 装 OpenLineage hook
3. 出问题第一步: 查 lineage，找根因
```

---

## 9.5 实时数据管道 — 慎用

### 什么时候真的要实时

```
  ✓ 业务流程必须秒级反馈（风控 / 推荐 / 广告竞价）
  ✓ 决策窗口短（库存 / 价格）
  ✓ 用户体验感知（在线状态 / 实时通知）

  → 满足 1 条考虑实时
  → 都不满足 → 用 T+1，省 70% 工程量
```

### 实时管道的工程坑

```
  ❌ 一开始就实时 → 调试地狱
  ❌ 没有 idempotency → 重放数据出错
  ❌ Schema 演化没考虑 → 一升级就坏
  ❌ 没有 dead letter queue → 单条坏数据卡所有
  ❌ 监控不到 lag → 用户投诉了你才知道
```

### AWS 实操：MSK + Kinesis + Firehose 三件套

```
        AWS 实时管道典型组合
        ─────────────────────────────────

  生产端 (Producer)
    ↓
  MSK (Managed Kafka) or Kinesis Data Streams
    ↓
  消费端选择:
    A. Lambda 直接处理（小流量）
    B. Flink on EMR / KDA (大流量 + 复杂逻辑)
    C. Kinesis Firehose 直接落 S3 / Redshift
    ↓
  下游: S3 (Iceberg) / Redshift / OpenSearch
```

简单场景用 Firehose（自动 buffer + 压缩 + S3 partition），复杂场景用 Flink。

> **AWS 知识参考**：搜 "Amazon MSK best practices"，"Kinesis Data Firehose"。

---

## 9.6 数据治理的"最低 5 件事"

不是"完整数据治理体系"，是 FDE 在客户现场至少要做的 5 件事：

```
1. 数据 owner 表
   每张表 / 每个 dbt 模型有一个 owner（人 + 邮箱）

2. PII 标记
   哪些字段是 PII，必须打 tag，必须 mask 在 dev

3. Schema 变更流程
   增字段：通知 + 文档
   改字段类型 / 删字段：必须 review + 通知下游

4. 测试覆盖
   每张主表至少 3 个 dbt test (uniqueness / not-null / referential)

5. Lineage 可视化
   能在 5 分钟内回答"这个数从哪来"
```

**5 件事都不到位 → Agent 上去就是雷区**。

---

## 9.7 一个真实端到端例子

```
  客户: 某保险公司
  Agent 任务: 自动核保（投保人风险评估）

  数据需求 (FDE 在 Discovery 摸出来的):
    - 投保人基础信息（CRM）
    - 历史理赔记录（理赔系统 Oracle）
    - 健康告知 PDF (扫描件 + OCR)
    - 黑名单 (合规系统 SQL Server)
    - 信用评分 (外部 API)

  → 5 个系统 4 个内部 + 1 个外部

  FDE 的工程方案:
    Week 1: Glue Data Catalog 注册 4 个内部系统的元数据
            建 customer Ontology（统一 customer_id mapping）
    Week 2: 写 dbt models 把 4 个系统的客户数据合并到 customer_360
            打 LF-Tags（PII 字段 mask）
    Week 3: Lambda + EventBridge 拉外部 API 信用评分
    Week 4: Bedrock Agent 调用 Athena 查 customer_360
            + 调 Lambda 拉信用 + 调 OCR
    Week 5-6: Eval + 灰度

  关键工程动作:
    - 没有写"实时" 管道（Discovery 时业务确认 T+4h 可接受）
    - 用 Glue Data Catalog 做 Ontology（轻量）
    - 所有 PII 字段在 dev 环境一律 mask
    - 每个 dbt 模型有 owner + tests
```

---

## 关键引用

> "*The Ontology is the contract between data engineering and the rest of the company.*"
> — Palantir Blog, *On Ontology*, 2024

> "*Most LLM hallucinations are actually data quality problems wearing a costume.*"
> — A. Lawrence, *FDE Rule Book*, 2025

> "*If you can't explain where the number came from, the customer can't trust the answer.*"
> — AWS GenAI Innovation Center, 2025

---

## 动手清单

接到一个数据密集型 FDE 项目，第 1-2 周必做：

1. **画客户的"5 层数据图"**（9.1 节）
2. **找出 3 个核心业务对象的 source-of-truth**（customer / order / product）
3. **建 Glue Data Catalog database**（即使是 PoC）
4. **每张表打 owner + LF-Tags（PII / region / sensitivity）**
5. **用 dbt 写 customer_360 之类的统一视图**
6. **接 OpenLineage**（dbt 自带）
7. **决定 SLA**：T+1 / T+1h / 实时（默认 T+1，能跑就先 T+1）

---

## 反模式清单

- ❌ **跳过 Ontology 直接接 Agent**（Agent 会基于不一致数据自信地说错话）
- ❌ **5 个系统直连不做统一**（任何上游小变动都崩）
- ❌ **数据没 owner**（schema 变了没人通知，下游一片崩）
- ❌ **第一版就上实时管道**（调试成本 10x，不一定值）
- ❌ **Dev 环境用真实 PII**（合规事故的高发区）
- ❌ **dbt 项目无 tests**（数据出错只能靠下游投诉知道）
- ❌ **Lineage 不接**（数据问题排查时间从 5 分钟变 5 天）

---

## 与下一章的关系

数据栈有了，但客户大多不让你用云上的"开箱即用"方案 —— 数据要待在客户 VPC / 私有部署 / 离线机房里。下一章讲：在客户网络隔离环境下，FDE 的工程动作怎么做。

[← Part IV 导读](intro.md) · [下一章: 在客户 VPC 工作 →](chapter-10.md)
