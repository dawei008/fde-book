---
title: "第 9 章 数据工程"
parent: "Part IV — 工程化落地"
nav_order: 1
---

# 第 9 章 客户数据栈：Ontology、ETL 与实时管道的取舍

合昇精密重工那个工单 Agent，第 6 章我们在会议室签下了选型纸，第 7 章定了 RAG + tool use，第 8 章把评估集接进了 CI。现在 Scaffolding 进入了第三周，要把"模型能跑"变成"数据能进"。

董事会那张表里有一行我当时没敢轻易答："Agent 要不要拉客户当地经销商的实时备件库存？"——这一行后面藏着东南亚 5 个站点 + 总部 1 套 ERP + 各地经销商 8 个外部系统的数据接入工程量。我那天和顾建国说了一句："这个我得画一张数据图回来再答。"那张图，就是这一章。

这一章不教你"什么是数据仓库"——你已经做过五年后端，这些你都知道。这一章讲的是**从客户视角看数据栈、决定什么先接什么后接、什么用 Ontology 收拢什么用裸 SQL 凑合**——这些判断是 FDE 在客户现场的核心动作，和教科书里的"数据架构"不是一回事。

---

## 9.1 第一周必画的"5 层数据图"

我自己经历过的几个项目里，数据接入翻车永远不是因为某个工具不会用，是因为 FDE 进场前两周没花一上午把客户的数据栈画清楚。第三周开始接数据，发现"客户" 这个词在 4 个系统里有 4 种 ID，连"昨天的订单"是哪个时区的"昨天"都对不齐。

我习惯第一周内画一张这种图，5 层从下往上：

```
  L5  应用 / Agent / API           ← FDE 的工作多在这一层
        Bedrock Agent / Lambda / 内部应用
        
  L4  BI / Dashboard               ← 业务方每天看的
        QuickSight / Tableau / Power BI / 自研
        
  L3  指标层 / Data Mart           ← "客户" 在这里被定义
        dbt 模型 / 业务 view / 公司自建口径
        
  L2  数仓 / 数据湖                ← 跑分析的地方
        Redshift / Snowflake / S3 + Iceberg / Databricks
        
  L1  操作型数据库 (OLTP)          ← 业务系统主存储
        PostgreSQL / Oracle / SQL Server / MongoDB
```

合昇这边画完是这样的：L1 有 5 个——总部 PostgreSQL（CRM 工单）、Oracle（合约/财务）、新加坡 RDS（MES）、各站点本地 MongoDB（现场作业日志），还有 30% 的关键数据躺在共享盘的 Excel 里（备件库存就是这个）。L2 是新加坡区一个跑了两年的 Redshift。L3 是数据团队两个人维护的一堆 view，没用 dbt。L4 是 QuickSight 和给董事会看的几张静态周报。L5 现在是空的——他们之前没做过 Agent。

画这张图的目的不是好看，是回答三个问题：

- **数据现在在哪一层、要去哪一层？** 我们的 Agent 在 L5，要查的数据要么在 L1（实时工单状态）要么在 L2/L3（历史派工记录）。Excel 备件库存在哪一层？严格说在 L1 的"非结构化"角落——这就是一类典型的接入难题。
- **跨多少层？** 跨的层越多，工程量越大。Agent 直接读 L1 的 PostgreSQL，是最快但耦合最重的方案；走 L2 → L3 慢一天但稳定。这个选择第 9.3 节展开。
- **L3 这一层有没有"统一口径"？** 大多数 B 端客户在这一层是混乱的——同一个"客户"在 CRM 是 customer_id，在 ERP 是 cust_no，在财务系统是 client_code。没有 mapping 表，业务方靠经验拼接。这就是 9.2 节讲的 Ontology 问题。

> Lawrence 在 *Forward Deployed Engineer Rule Book* 里写过一句让我印象很深的话：*Most LLM hallucinations are actually data quality problems wearing a costume.* 我做了几个项目之后越来越同意——Agent 越聪明，越容易把不一致的数据自信地组合成错误的答案。第一周画清楚这张图，是给后面所有"为什么 Agent 答错了"的事故省时间。

---

## 9.2 Ontology：把"五湖四海"统一到一张身份证

Ontology 这个词最早是 Palantir 推出来的，他们把它做成了产品的核心抽象。剥掉营销层，本质上是三件事：

```
  Object       业务对象的"金本位定义"
               Customer / Order / Product / Contract / Asset
               
  Property     每个对象的属性 + source-of-truth
               Customer.id = ?, Customer.tier = ?
               
  Relationship 对象之间的关系
               Customer 1:N Order, Order 1:N Item
```

这听起来像数据建模 101，但 Ontology 和传统数据建模有一个关键区别——**它不是数据团队关起门来定义的，是业务方、数据团队、应用团队三方共同 sign-off 的合同**。"客户" 是谁？这件事不能让数据工程师拍——必须业务方说话。

合昇这边我第二周和陈雪、顾建国坐下来过了一遍。我问的不是技术问题，是四个业务问题：

**第一，谁是"客户"？** 合昇的 CRM 里"客户"是采购方，ERP 里"客户"是付款主体，售后系统里"客户"是设备使用方。一台五轴加工中心，采购方可能是新加坡某代理商，付款主体是马来西亚一家工厂，使用方是越南胡志明的车间。三个"客户" ID 都不一样。我们 Agent 接的工单来自使用方——所以**售后系统的 customer_id 是金 ID**。

**第二，主键用什么？** 售后系统的 customer_id 长这样：`SVC-VN-HCM-001423`。带地区编码、带顺序号，看着规整，但有 200 多条历史数据是手填的，前缀不统一（`VN-HCM` vs `VHCM` vs `HCM-VN`）。我们没法直接用——必须先建一张"金 ID → 实际系统 ID" 的 mapping 表，把脏数据归位。这张表第三周陈雪带着两个客服花了两天手工修完。**没有银弹，就是手工**。

**第三，谁有权改？** Ontology 一旦定下来，下游所有 dbt 模型、所有 Agent prompt 都基于它。任何一个字段改名都是大事。我们约定 Ontology owner 是陈雪（业务方），任何改动需要她邮件确认。这条写进了 SOW 附录。

**第四，第一版要覆盖几个对象？** 合昇这一期 Agent 只做工单分诊——只需要 Customer、Asset（设备）、Ticket（工单）、Engineer（工程师）4 个对象。Order/Contract 不上 Ontology 第一版。**业务范围不到的对象不做**——Ontology 不是"先建好备用"，是"用到哪个建到哪个"。

到这里 Ontology 的设计完成了。落地用什么工具？合昇是 AWS 客户，主区在 ap-southeast-1，我们没必要去引入 Palantir Foundry——杀鸡用牛刀，而且过不了顾建国那一关（"不要再开第二条供应商关系"）。AWS 这个客户场景下，我们用 Glue Data Catalog + Lake Formation 做了一个轻量版：

```
  Glue Data Catalog 作为 Ontology 注册中心
  
    database: chsj_ontology_v1
    
    table: customer
      customer_id        string  PK    -- 金 ID
      legal_name         string
      country            string
      tier               string
      crm_id             string        -- mapping 到 CRM
      erp_no             string        -- mapping 到 ERP
      finance_code       string        -- mapping 到财务
      lf_tags:           PII=yes, region=APAC
      owner:             chen.xue@chsj.com
    
    table: asset
      asset_id           string  PK
      customer_id        string  FK -> customer
      model              string
      install_date       date
      ...
```

权限走 Lake Formation 的 LF-Tags：PII 字段在 dev 环境一律 mask，prod 环境按 IAM 角色分。这套不是"完整 Ontology 框架"——它没有 Foundry 那种带 UI 的对象浏览器、没有自动血缘——但它够用，而且不引入新供应商。这是 FDE 在客户现场最常见的取舍：**用客户已有平台的能力，做出 Palantir 那套抽象的 70%，剩下 30% 用 SOP 和 dbt 模型补上**。

如果你的客户用 Snowflake 或 Databricks，对应的工具是 Snowflake 的 Tags + Polaris、Databricks 的 Unity Catalog。换一个云，思路一样。

---

## 9.3 ETL：怎么决定"够新"和"够准"

Ontology 定义了"对象长什么样"，ETL 解决"对象怎么从 5 个系统里被组装出来"。

我从来不在客户现场讨论"用哪个 ETL 工具最好"。这件事的判断顺序是反过来的——**先回答 SLA、再回答工具**。

SLA 我用三档说话：

```
  T+1 (隔天可见)   ──→ 90% 的项目这一档够用
                       适合: 周报 / 月报 / 历史分析 / 客服 RAG
                       工程量基准: 1x

  T+1h (小时级)    ──→ 大约 8% 的项目需要
                       适合: 业务方上午调整下午想看效果
                       工程量基准: 2-3x (要做增量同步)

  实时 (秒级)      ──→ 不到 2% 的项目真正需要
                       适合: 风控 / 推荐 / 在线状态 / 库存竞争
                       工程量基准: 5-10x (要 CDC + 流式处理)
```

合昇那个备件库存——我和陈雪谈了一次，问她："如果系统给工程师推荐的备件，库存其实已经被另一个站点订走了，你能接受多久才发现这个事？"她想了一下："几个小时内吧。如果是早上派工的，下午能改就行。"

那就是 T+1h。不是实时。我们省掉了一整套 CDC 流水线。

工程现实里，**一上来就上实时管道是 FDE 最常踩的坑之一**。我自己在第二个 FDE 项目踩过——客户随口一句"最好实时"，我没回头确认，搭了 Kinesis + Flink 一整套，三周后发现业务真实需要的是"早上能改晚上能改"。三周白搭。从那之后我养成习惯：**任何"实时"的需求，我会反问一句"半小时延迟你能接受吗？"，能接受就降一档**。

SLA 定下来后，工具按场景选。我画过一张速决表，合昇这次走的是第一行：

| 客户场景 | 推荐组合 | 备注 |
|---|---|---|
| AWS + 数仓内变换 | dbt + Redshift / Athena | 80% 项目首选，SQL-only |
| AWS + Spark 友好 | Glue / EMR + Iceberg | Glue 适合 serverless 偏好的客户 |
| AWS + 简单调度 | Step Functions + Lambda | 数据量小、逻辑简单时最省 |
| AWS + 实时 | MSK / Kinesis + Flink/Firehose | 真要实时再上 |
| 客户用 Snowflake | dbt + Snowflake | 同左，换数仓 |
| 客户用 Databricks | dbt + Databricks 或纯 PySpark | 看团队风格 |

我们最后用的是 dbt + Redshift。合昇 Redshift 已经跑了两年，dbt 是数据团队上个季度引入的（之前是堆 view），现在正好用 Agent 项目做一次系统化的 customer_360 迁移。dbt 项目结构合昇那边变成这样：

```
  models/
    staging/
      stg_crm__customers.sql      -- 清洗 CRM 原始表
      stg_erp__customers.sql      -- 清洗 ERP
      stg_svc__tickets.sql        -- 清洗售后工单
      stg_finance__clients.sql    -- 清洗财务
    intermediate/
      int_customer__id_mapping.sql   -- 4 个系统的 customer_id 拼接
      int_ticket__enriched.sql       -- 工单接上设备 + 客户
    marts/
      dim_customer.sql            -- Ontology 里的 customer 对象
      dim_asset.sql
      fct_ticket.sql

  tests/
    not_null_customer_id.yml
    unique_customer_id.yml
    referential_asset_to_customer.yml
```

dbt 在这个层面有三个好处直接对应 FDE 的痛点：**SQL-only**（团队不用学新语言）、**自带血缘**（dbt docs serve 能可视化）、**自带测试**（uniqueness / not-null / 引用完整性 / 接受值）。第三个尤其关键——Agent 项目最怕的不是"今天数据错了"，是"今天数据错了但没人知道"。每张主表 3 个 dbt test 起步，是我现在每个项目的默认动作。

---

## 9.4 数据血缘：失败发生时的 5 分钟 vs 5 天

合昇上线前两周，我们遇到过一次小事故。一个 dbt 模型 `dim_customer` 突然多了一行——某个 customer_id 在 CRM 里被重命名了一次，又被改回来，触发了 stg 层一个 left join 的边界 bug。下游的 Agent prompt 拿到了一条"客户名 = NULL"的数据，给工程师推送了一条莫名其妙的派工建议。

陈雪在 Slack 群里 @ 我："这个工单为什么派给电气组？" 我从这条工单回查到 Agent 的 prompt，再回查到 prompt 引用的 customer 信息，再回查到 dim_customer 的那一行——这一路下来，因为 dbt 自带 lineage，我用了 4 分钟。

如果没有 lineage——我得分别打开 CRM、ERP、财务系统、Redshift 的 view 定义，一个一个对——保守估计半天。

这就是为什么"接 lineage" 不是 nice-to-have，是 FDE 第一周该做的动作之一。具体最低要求：

- **dbt 项目**：默认就有，跑 `dbt docs generate` + `dbt docs serve` 即可，把链接发给客户和团队
- **Glue / Airflow 调度的非 dbt 任务**：装 OpenLineage hook，把 lineage 发到 Marquez 或 DataHub
- **Bedrock Agent 调用 Athena 时**：把 query 和返回的 query_id 写进 CloudWatch Logs，这是 lineage 的最后一公里

商业产品（DataHub Cloud、Atlan、Foundry）在合规重的客户那边有意义——它们把 IAM、审计、跨云血缘都打包了。但合昇这种规模，dbt 自带的就够。**别在客户没需求的地方上重型工具**——这是 FDE 一条很无聊但很值钱的判断力。

---

## 9.5 PII 与"上线前最低 5 件事"

合昇做的是 B2B 工单，PII 看起来不重——但客户数据里仍然有联系人手机号、邮箱、签收人姓名。东南亚有几个国家有数据本地化要求（印尼 PP 71/2019、越南网络安全法），合规这一块我们和顾建国确认过：客户数据不出 ap-southeast-1。

PII 处理我们做了三件事：

```
  1. PII 字段在 Glue Data Catalog 打 LF-Tag: PII=yes
  2. dev 环境通过 Lake Formation 的 column-level 权限做哈希 mask
  3. prod 环境只对 Agent 调用的 IAM 角色开放, 走 VPC endpoint 不出网
```

写进 SOW 的是这三句话——非常具体，有 IAM 角色名、有 LF-Tag 名、有 VPC endpoint ID。**SOW 里写的 PII 控制必须是工程上可验证的**，写"严格保护客户隐私" 没用，写"客户数据通过 IAM 角色 `chsj-agent-runtime-role` + LF-Tag `PII=yes` 控制访问，dev 环境字段哈希 mask"才能在审计时拿出证据。

数据工程上线前，FDE 至少要做完这 5 件事——这不是"完整治理体系"，是合昇这种典型 B 端客户的最低门槛：

```
  1. 每张主表有一个 owner (人 + 邮箱)
  2. PII 字段全部打 LF-Tag, dev 环境 mask
  3. Schema 变更走 PR review, 通知下游
  4. 每张主表至少 3 个 dbt test
  5. Lineage 接通 (能 5 分钟内回答 "这个数从哪来")
```

5 件事都不到位 → Agent 上去就是雷区。这话不是吓唬人——我自己在前一个项目少做了第 4 项（dbt test），上线第三周客户那边一个上游库 schema 改了一个字段类型，下游 Agent 静默拿到了空值，三天后业务方看报表才发现。事故之后我把这 5 件事写成了我自己的 checklist，每个新项目用一次。

---

## 9.6 把 9.1-9.5 串起来：合昇这一期的实际工程动作

回到合昇的工单 Agent。第三周到第五周，数据工程的实际时间线长这样：

**Week 3（数据画像 + Ontology）**

- 周一上午：和陈雪、顾建国画完 5 层数据图
- 周一下午到周三：和陈雪过 Ontology 的 4 个业务问题，定下 Customer/Asset/Ticket/Engineer 4 个对象
- 周四到周五：陈雪带客服手工修 customer_id mapping 表（200 多条）；我在 Glue Data Catalog 注册了 Ontology v1 的 4 张表，打 LF-Tags

**Week 4（dbt 模型 + 测试）**

- 周一周二：写 stg 层（4 个系统的清洗）和 int 层（id mapping + ticket 富化）
- 周三：写 marts 层的 dim_customer / dim_asset / fct_ticket
- 周四：3 张主表各加 5-7 个 dbt test（uniqueness / not-null / referential / accepted-values）
- 周五：跑 dbt docs generate，把 lineage 链接发给客户

**Week 5（备件库存 T+1h + Agent 接入）**

- 周一周二：备件库存（Excel）走 Glue crawler + Athena，做了一个 4 小时跑一次的 Step Functions 流水线（不是实时）
- 周三：Bedrock Agent 接 Athena tool，能查 dim_customer + dim_asset + fct_ticket
- 周四：跑评估集 v1（200 条），发现 dim_customer 那个 left join 的 NULL 问题（9.4 节那次事故）
- 周五：修完，把对应的 dbt test 加上，重跑评估集到达上线阈值

整个数据工程占了三周。如果第一期备件库存做实时——按我经验至少加两周，而且业务方实际上不需要。

---

## 9.7 实测：从脏数据到 agent 端到端

上面 9.1-9.6 是叙述。这一节给一个**可在你 AWS 账号上复现**的端到端 demo——把整章的判断变成可跑的代码。完整代码在仓库 `demos/ch9-data/`，跑完即拆，单次成本 < $1。

合成数据按合昇风格生成：200 台设备、500 条工单、300 条派工记录，**故意带表面和语义两层脏**——时间戳格式三种混用（67% iso8601 / 22% 中文格式 / 11% Unix epoch）、priority 字段 9 种命名（P1/high/1 / P2/medium/2 / P3/low/3）、team 字段 6 种命名（机械组/Mech/M-team / 电气组/Elec/E-team）、part_id 两种前缀（P-101 / PART-101）、36 条工单引用了不存在的设备 ID（broken FK）。

跑完整流程：

```
01-generate-data.py    →  3 个 CSV 写到本地
02-setup-aws.py        →  S3 + Glue Crawler + Glue DB
                          (crawler 第一次跑识别 tickets/work_orders 失败,
                           因为 CSV 里中文 fault_desc 含逗号)
04-explicit-schema.py  →  显式注册 OpenCSVSerde schema 修复
                          (这是真实的 FDE 第一周坑)
05-explore-athena.py   →  6 个 Athena 查询暴露所有脏数据形态
06-build-ontology.py   →  4 个 SQL view 把脏数据归并成 ontology
                          (ticket_clean / equipment_clean /
                           work_order_clean / ticket_resolution)
07-create-kb.py        →  5 份维修手册上传 (但本期不上 KB,
                          换成 prompt-stuff: < 30 份小手册不值得 KB)
08-agent-with-athena-tool.py
                       →  Claude Haiku 4.5 + 一个 SQL 工具,
                          回答 4 个合昇风格的业务问题
09-teardown.py         →  全部拆掉
```

跑出来的真实数字：

**Athena 探索阶段**——6 个查询，scanned 数据量都在 < 0.1 MB（数据量小），平均 engine time 600ms。

**Ontology 视图构建**——4 个 view，最复杂的 `ticket_resolution` 含 LEFT JOIN + 子查询，建立 858ms。每次查询时按需重新执行，不预物化（适合 Hesheng 这种数据量级；上 TB 时考虑物化）。

**Agent 实测对话**（节选第一个问题）：

```
USER: 过去 90 天里 Singapore 站点 P1 工单的平均解决时间是多少?

  TOOL CALL: query_tickets(
    SELECT AVG(total_hours), COUNT(*) ... INTERVAL '90' day ...)
  TOOL RESULT: ERROR — Trino doesn't support INTERVAL syntax this way
  TOOL CALL: query_tickets(
    SELECT ... ts_utc >= date_add('day', -90, current_date) ...)
  TOOL RESULT: avg_resolution_time_hours=5.26, p1_ticket_count=9

AGENT: 过去 90 天内 Singapore 站点共有 9 张 P1 工单, 平均解决时间为
       5.26 小时。在 SLA 规定的 4 小时上门时间基础上, 仅额外需 1.26
       小时现场处理, 说明现场工程师应急响应和故障排查效率较高。
```

注意第一次 SQL 失败、agent 自己 self-correct 重写。这是 agent 接 SQL 工具时**真实会发生**的容错过程——Trino 方言、字段类型、视图未刷新等问题都会在 tool call 失败里出现。生产里你会想给工具加更精确的 schema 描述帮模型一次写对，但这个能力本身（agent 接住错误自己修）是 LLM 应用的核心价值之一。

**完整 4 个问题的 agent 回答**（详见仓库 `demos/ch9-data/`）：

| 问题 | Agent 答案 |
|---|---|
| Singapore P1 平均解决时间 | 5.26 小时（9 张工单），加 SLA 解读 |
| ALM 4501 站点分布 | 胡志明 19 / Bangkok 14 / Jakarta 13 / Singapore 11 / KL 10 / 数据缺失 6，加业务推断 |
| 多少工单引用不存在的设备 | 36 条 = 7.2%，加治理建议 |
| Jakarta 本月超 SLA 工单 | 诚实说"本月暂无数据"，反问澄清时间窗口 |

**这一节最值钱的 takeaway**：从 200 行脏数据到 agent 能用业务语言回答业务问题，全栈用 AWS 数据服务串起来用了 8 个脚本，团队工程师 30 分钟内能从零跑完。**这就是数据工程"准备好让 LLM 用"的形态**——不是上 OpenSearch、不是 ETL 大改造，是 Athena view + 一个 SQL 工具。

什么时候要升级到 KB / AgentCore Runtime / Gateway？三个信号：

1. **手册超过 30 份或每周更新** → 上 Bedrock Knowledge Base（这一期 5 份 prompt-stuff 够用）
2. **Agent 需要跨 session 状态或长任务** → 上 AgentCore Runtime（这一期 30 秒一次问答，Lambda 够用）
3. **多个 BU 团队接入同一个 agent** → 上 AgentCore Gateway（这一期单团队，直接 Converse tool use 够用）

合昇一期三个信号都不满足。第 14、15 章会展开二期升级到 AgentCore 的判断和路径。

---

## 收尾

数据工程不是 FDE 项目里最炫的部分——会议室里讲 RAG、Agent、模型对比，业务方会眼睛发亮；讲 Ontology、dbt test、PII 标记，业务方会想刷手机。但**80% 的 Agent 上线事故根因在数据层**——你解决不了 Ontology 的不一致，再好的模型也只是把混乱的数据自信地说错。

我现在每次进客户现场，第一周必做的是画 5 层数据图、和业务方过一次 Ontology、看 PII 现状。这三件事每件 1-2 小时，当周内能做完。做完之后我对这个项目能不能上线、要花多久，心里就大致有数。如果你接手一个数据栈混乱的客户，又被催着第二周就上 Agent demo——那是个红灯，下一章会讲一个相关问题：客户的网络隔离环境下 FDE 的工程动作怎么做。

---

## 本章引用的公开资料

- A. Lawrence, *Forward Deployed Engineer Rule Book*（公开 GitHub 文档）
- Palantir 工程博客 — *Ontology* 系列文章
- AWS 文档 — *Lake Formation Tag-Based Access Control*、*Glue Data Catalog cross-account*
- AWS 文档 — *Amazon MSK best practices*、*Kinesis Data Firehose*
- dbt 官方文档 — *Tests*、*Documentation and Lineage*
- OpenLineage / Marquez 项目文档
- 印尼 PP 71/2019、越南网络安全法（数据本地化合规公开资料）

[← Part IV 导读](../intro/) · [上一章：评估先于代码](../../part-3/chapter-08/) · [下一章：Scaffolding 与开发循环 →](../chapter-10/)
