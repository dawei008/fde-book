---
title: "第 10 章 Scaffolding 与开发循环"
parent: "Part IV — 工程化落地"
nav_order: 2
---

# Chapter 10: 在客户 VPC / 私有部署 / 离线机房工作

## 开场

```
某国央企。FDE 第一天到客户机房：

  客户安全主管："我们规定如下 ——
    1. 所有代码必须在内网 GitLab 上
    2. 不能用 ChatGPT，不能 google
    3. 没有外网，pip install 走我们的私有 PyPI mirror
    4. 服务器只能 SSH 跳板机进，不能直接互联网
    5. 数据不能出我们机房
    6. 你们的 Mac 不能接我们网
       —— 用我们这台 Windows 工作站
    7. 工作站不能装非白名单软件
       (白名单不包括 VSCode 的 GitHub Copilot 插件)"

FDE 心想："那我还能干啥？"

她干了一个月之后总结："其实啥都能干，
只是节奏完全不一样 —— 不是 SaaS 工作流的节奏。
关键是想清楚什么能做、什么必须 Air-gap 做。"

这一章讲：客户 VPC / 私有部署 / 离线机房，
FDE 的具体工程动作是什么。
```

---

## 10.1 三种"非云原生"客户场景

```
        客户的"非 SaaS" 部署形态
        ─────────────────────────────────────────

  场景 A: 客户 VPC（云上但隔离）
    - 客户在 AWS / Azure / Aliyun 上有自己的 VPC
    - 互联网通过 NAT 受控出口
    - 安全组 + NACL 严格
    - 你的代码部署在客户账号里

  场景 B: 客户私有云 / 自建机房
    - 客户有自己的 K8s 集群 / VMware
    - 部分有外网，部分纯内网
    - 你的代码部署到客户机器上

  场景 C: Air-gap（完全离线）
    - 没有互联网
    - 模型 / 镜像 / 依赖必须 USB / 跳板机搬进来
    - 国防 / 军工 / 部分金融
```

**90% 的 ToB 客户在 A 或 B**，A 最常见。

---

## 10.2 场景 A：客户 VPC 工作流

### 关键工程动作

```
  1. 拿到 IAM 角色（不是 root，是 scoped role）
  2. 用 AWS Identity Center / 客户 SSO 登入
  3. 部署目标在客户账号 + VPC
  4. 你的开发本地机器 ↔ 客户 VPC 之间走
     - VPN（Site-to-Site / Client VPN）
     - 跳板机（Bastion / Session Manager）
     - 不能直连
```

### AWS 实操：客户 VPC 内部署 Bedrock 应用

最关键的是"**Bedrock 流量不出客户 VPC**"。配置：

```
        客户 VPC + Bedrock 私有路径
        ───────────────────────────────────────────

  客户 VPC
    ├── Subnet A (private, 应用层)
    │     ├── Lambda / ECS / EC2 (你的应用)
    │     │
    │     ↓ (VPC Endpoint)
    │
    ├── VPC Endpoint: bedrock-runtime
    │   (com.amazonaws.region.bedrock-runtime)
    │
    └── 流量: 应用 → VPCe → AWS Bedrock
              (不出 VPC，不上互联网)
```

为什么需要 VPC Endpoint：

- 客户安全主管: "所有调用必须可审计、可阻断"
- 走 VPC Endpoint = AWS 私有网络 = 不暴露公网
- CloudTrail + VPC Flow Logs 全程可审计

最小配置：

```bash
# 1. 创建 VPC Endpoint
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-xxx \
  --service-name com.amazonaws.us-east-1.bedrock-runtime \
  --vpc-endpoint-type Interface \
  --subnet-ids subnet-aaa subnet-bbb \
  --security-group-ids sg-yyy

# 2. 应用 SDK 调用 Bedrock
import boto3
client = boto3.client('bedrock-runtime')
# SDK 自动走 VPCe（DNS 解析到 VPCe 的私有 IP）
```

> **AWS 知识参考**：搜 "Bedrock VPC endpoints" 与 "AWS PrivateLink for Bedrock"。

### Knowledge Bases / Agents 也要走私网

```
  Bedrock Knowledge Bases
    - VPC Endpoint: bedrock-agent
    - 数据源 S3: VPC Endpoint: s3 (Gateway 类型)
    - OpenSearch Serverless: 在客户 VPC 内的 collection

  Bedrock Agents
    - VPC Endpoint: bedrock-agent + bedrock-agent-runtime
    - Lambda 工具: 在客户 VPC 内
    - 客户内部 API 调用: 直接 VPC 内调用
```

### Sagemaker JumpStart — 自部署模型的兜底

如果客户连 Bedrock 都不让用（"必须自部署"），用 SageMaker JumpStart：

```
  SageMaker JumpStart 一键部署:
    - Llama 3.1 / Qwen / Mistral 镜像
    - 部署在客户 VPC 的 SageMaker endpoint
    - 私有 endpoint，不出公网
    - 完全在客户账号里
```

---

## 10.3 场景 B：客户私有云 / 自建机房

### 工作日常

```
        典型一天
        ────────────────────────────────────────

  7:30  到客户大楼，刷工卡 + 人脸 + 包过 X 光
  8:00  上机房二楼 FDE 工作区
  8:30  开机：客户配的 Windows 工作站
        - 没装 Outlook（用客户邮箱网页版）
        - 没装 Slack（用客户内部沟通工具）
        - VS Code 装了，但没 Copilot
  9:00  ssh 跳板机 → 客户 K8s
        - 先看夜里有没有报警
  10:00 跟客户运维拿当天的部署窗口
  ...
  17:00 提交今天的代码到客户 GitLab
        push 时跑 SAST / DAST 扫描
  18:00 写日报 + 回家
```

### 关键工程配置

```
  代码托管:
    - 客户内部 GitLab / Gitea / Gerrit
    - 不能 push 到 GitHub

  CI/CD:
    - 客户内部 Jenkins / GitLab CI / ArgoCD
    - 不能用 GitHub Actions / CircleCI

  镜像仓库:
    - 客户内部 Harbor / Quay
    - 基础镜像（Python / Java）必须从客户内部 mirror 拉

  依赖管理:
    - pip / npm / maven 走客户内部私有仓库
    - 一定要列清单，安全主管会扫

  模型存储:
    - 模型权重存客户对象存储（MinIO / Ceph / OSS）
    - 不能从 HuggingFace 直接拉

  监控:
    - 客户的 Prometheus + Grafana
    - 不能接 Datadog / NewRelic
```

### 模型如何"搬进来"

```
        模型权重的进入流程
        ──────────────────────────────────────

  Step 1: FDE 在公司侧从 HuggingFace 下载模型权重
          （Llama / Qwen / Mistral）

  Step 2: 病毒扫描 + license 检查 + 安全审计

  Step 3: 走客户的"软件入网流程"
          - 一份"模型入网申请"
          - 一份模型说明 + license + scan 报告
          - 等审批 (1-3 周不等)

  Step 4: 批准后客户允许 USB 或专网传入

  Step 5: 落到客户对象存储 + 注册到模型仓库
```

**FDE 第一周必须把这个流程触发起来**。否则到了第 6 周才发现模型还没进来 = 项目延期。

---

## 10.4 场景 C：Air-gap（完全离线）

### 真实故事

> *某 FDE 在一个完全离线的客户场景部署 LLM，第一天发现 ——*
>
> *公司给的笔记本上的 git 用了 GitHub 远端，他没改 origin 直接 git push，
> 客户安全主管秒回：" 你的笔记本被隔离 24 小时观察。"*

Air-gap 的核心特点：

```
  ✓ 完全没互联网
  ✓ 所有代码 / 工具 / 镜像必须 USB 或可信中转
  ✓ 你的本地机器和客户机器之间走"摆渡机"
  ✓ 进客户网络的所有动作都被审计
```

### 工作前 3 天清单

```
  Day 1: 准备 USB 包
    - Python / Node / Docker 镜像
    - 你的所有代码 + 依赖（pip download / docker save）
    - 模型权重
    - VS Code + 离线插件
    - 文档（带 RFC / 设计 / 数据字典）

  Day 2: USB 安检 + 入网
    - 客户安全审计你的 USB
    - 客户帮你装到内部摆渡机
    - 摆渡机扫描 + 隔离观察 + 投递到内网

  Day 3: 内网 PC 拿到资料，开始干活
```

### 工程纪律

```
  ✓ 所有 prompt 写在仓库里（不能"我等会想想再说"）
  ✓ 不能假设有 ChatGPT / Claude 帮你 debug
  ✓ 必须自带"离线参考"：
    - HuggingFace cache
    - PyPI mirror
    - 离线文档（pip download docs）
  ✓ 反复出问题的功能 → 简化方案，不要复杂依赖
  ✓ 每周末把最新代码批量回传公司（review + 备份）
```

---

## 10.5 私有化 LLM 部署的工程要点

不是云上 SaaS LLM，而是**自部署 Llama / Qwen / Mistral**：

### 选模型规模

```
                    GPU 配置 → 推荐模型
                    ──────────────────

  4× A100 80G        Llama 3.1 70B 半精度 / Qwen2 72B
  2× A100 80G        Llama 3.1 70B AWQ 4bit / 32B 模型
  1× A100 80G        Llama 3.1 8B / Qwen2 14B
  1× A100 40G        7B / 8B 模型
  无 GPU             不要硬上 LLM，建议用云上 API
```

### 推理引擎

```
  vLLM (推荐)
    - PagedAttention 内存高效
    - OpenAI 兼容 API
    - 高 QPS

  TGI (HuggingFace)
    - 易上手
    - 流式输出好

  TensorRT-LLM (NVIDIA)
    - 极致性能
    - 但 ramp-up 复杂

  llama.cpp
    - CPU / Mac 也能跑
    - 极小 footprint
```

### 部署架构

```
  K8s + vLLM 标准架构:
    ─────────────────────────────────

  Ingress (内网 LB) → API Gateway (鉴权 + 限流)
                          ↓
                     vLLM Pods (HPA)
                       (每 Pod 1 GPU)
                          ↓
                     模型权重 (PVC / S3 / OSS)

  监控: Prometheus + Grafana (token/sec, GPU util)
  日志: Loki / 客户 ELK
```

### Eval / Trace 的私有化

```
  云上 SaaS:           私有部署:
  ───────────          ─────────────
  LangFuse Cloud   →   LangFuse self-hosted
  LangSmith        →   Phoenix (Arize 开源)
  Bedrock Eval     →   自写 Python 脚本 + dbt
```

---

## 10.6 合规清单（私有部署 / 中国 ToB 常见）

```
        合规要点速查
        ─────────────────────────────────────

  数据出境:
    - 中国客户的数据不能出境
    - 模型权重一般可以入境（看具体 license）

  等保:
    - 等保 2.0 三级 / 四级 = 大量约束
    - 你的 FDE 工作受影响最大的是审计 + 部署流程

  GDPR / SOC 2:
    - 数据分类 + 访问审计
    - PII 保护

  PCI DSS (金融):
    - 支付数据加密 + 网络隔离

  HIPAA (医疗 / 美国):
    - PHI 数据 + audit trail

  CSA STAR (企业云):
    - 云服务商资质
```

**FDE 的策略**：合规不是 FDE 一个人能搞定的，但 **FDE 必须在 Discovery 阶段就摸清这些要求**，不然到了部署前发现"不能用 X" 整个方案推倒重来。

---

## 关键引用

> "*The customer's network is the customer's contract — disrespect it once, lose the project.*"
> — A. Lawrence, *FDE Rule Book*, 2025

> "*Architecture changes when the GPU lives in the customer's data center.*"
> — Palantir FDE training, 2024

> "*PrivateLink is the most underused service among new AWS users.*"
> — AWS Solutions Architects, 2025

---

## 动手清单

接到一个非云 SaaS 客户项目，第 1 周必做：

1. **画一张"网络拓扑图"**：客户 VPC / 私有云 / Air-gap，进出流量怎么走
2. **拿到 IAM / SSO 身份**（不要用别人的账号）
3. **建 VPC Endpoint**（Bedrock + S3 + CloudWatch 至少这三个）
4. **走"软件入网流程"**（模型 / 工具 / 依赖一并申请，越早越好）
5. **第一周末跑通"hello world"**（一个简单的应用从客户 VPC 内调通 Bedrock 或自部署模型）
6. **画一份"数据流图"**：哪些数据进哪些不能进，有 PII 标记
7. **找客户安全主管 30 分钟咖啡**（这个人决定你后面 12 周顺不顺）

---

## 反模式清单

- ❌ **本地起开发用 SaaS API，部署再换私有**（行为差异巨大，到时候才发现不能上）
- ❌ **没走 VPC Endpoint，上 NAT 出去**（合规审计点名 #1）
- ❌ **不申请软件入网就开始装**（"先装上再说"会被秒清）
- ❌ **把客户数据下载到本地分析**（合规事故 #1）
- ❌ **代码 push 到 GitHub** （客户禁止外部仓库）
- ❌ **Air-gap 客户开发还想 ChatGPT 帮忙写代码** （隔离 24 小时观察）

---

## 与下一章的关系

数据 + 网络都搞定，最后一道是和"客户已有系统"对接 —— SSO / SCIM / API / 审计。下一章讲：和遗留系统对接的工程模式。

[← 上一章: 客户数据栈](chapter-09.md) · [下一章: 与遗留系统对接 →](chapter-11.md)
