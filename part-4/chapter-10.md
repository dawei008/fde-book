---
title: "第 10 章 Scaffolding 与开发循环"
parent: "Part IV — 工程化落地"
nav_order: 2
---

# 第 10 章 Scaffolding 与开发循环

苏州合昇精密重工，海外业务部。第 4 周周一上午。

第 6 章那张选型纸三人都签了字，第 9 章那张数据图我也画完了。Bedrock 通了、eval 跑得动、KB 灌了第一批 1500 份 PDF。按理说这一周该是"动手干活"的开始。

我打开 IDE 准备改 dispatcher 那 200 行代码，发现保存不了——客户工作站的 VS Code 没有写入 `~/.vscode-server` 的权限。我换 SSH 模式连客户跳板机，跳板机的 Python 是 3.8.10，我本地一直用 3.11，pydantic v2 装不上。我尝试 pip install，提示 "PyPI mirror 内部地址无效，请联系 IT"。

到中午为止我没改成一行代码。

这一章讲的是这件事：**当客户的环境把你"几分钟一次保存看效果"的开发节奏拆成了"两小时一次审批"，你怎么把项目继续往前推**。

它分三段：第一段讲 scaffolding 真正在做的是什么——不是"搭代码骨架"，是把 Discovery 的结论变成一个能持续迭代的最小闭环。第二段讲在客户环境里 inner loop 会被打成什么样，以及一组让自己能继续干活的工程动作。第三段讲 staging 和 hot fix——上线之后才真正开始的那部分工作。

---

## 10.1 Scaffolding 不是搭骨架，是搭迭代闭环

很多人第一次做 FDE 项目，"scaffolding 阶段"做出来的是一份 README、一个 Hello World 的接口、一个能在本地跑通的 demo 脚本。给老板看一眼，老板说"看起来挺好"，然后就进入下一阶段。

这种 scaffolding 是教程腔的 scaffolding。真正的 scaffolding 阶段，**产物不是代码，是一条能从"代码改了一行"走到"客户业务方在真实环境里看到效果"的最短路径**。这条路径上的每一段，都得能在工作日内跑完。

合昇这个项目，我第二周末画过一张工作流图，列出从"我改一行 prompt"到"陈雪在她工位上点开工单看到结果"中间所有的步骤：

```
  我改一行 prompt
    ↓
  本地跑 eval-v0 (10 条)            ← 30 秒
    ↓
  push 到客户 GitLab
    ↓
  客户内部 GitLab CI 跑 eval-v1     ← 4 分钟
    ↓
  构建镜像推 Harbor                 ← 6 分钟
    ↓
  ArgoCD 部署到 staging             ← 3 分钟
    ↓
  陈雪在 staging 上点开工单看到结果 ← 30 秒
```

整条路径理论上 15 分钟可以走完。这 15 分钟就是这个项目的 inner loop。

scaffolding 阶段我大头时间不在写业务代码，在让这 15 分钟真的能跑下来。具体的事项很琐碎：

- 客户 GitLab 上的项目权限谁批，CI runner 谁加，凭证怎么注入
- Harbor 上的命名空间申请下来要 1-3 天，得提前申
- staging 集群 ArgoCD 的 application 模板谁有权限改
- eval-v0 那 10 条数据放仓库里行不行，还是必须放客户的对象存储
- 我的 IDE 通过跳板机 SSH 进客户开发机，Remote Container 能不能用

这些事情每一件都不复杂，但是每一件都需要找客户某个具体的人盖章。第 1 周如果不开始触发这些流程，第 4 周就会像我那个周一上午那样——所有东西都还差一步。

我习惯第二周开一张表，左列是"inner loop 的步骤"，右列是"卡在谁手里、需要什么动作"，每周和顾建国过一次。这张表上"所有项都绿了"的那一天，就是 scaffolding 真的开始的那一天。在那之前所有的代码都是预备性的——你以为在做开发，其实在做基础设施搬运。

> Lawrence 在 *FDE Rule Book* 里有一句话我一直记着："The first thing you build for a customer is not the product, it's the loop." 翻译过来不太顺，但意思是：在客户那边给客户做的第一件事，不是产品本身，是产品能改起来的循环。

### scaffolding 的"完成"标准

我经常被问"什么时候算 scaffolding 做完了？"这个问题没有银弹答案，但我用三个判断信号：

**第一，能不能在 30 分钟内把一个新功能从想法变成 staging 上的可点击页面。** 不是测试通过，不是部署成功，是业务方能在 staging 上点出来看效果。如果不能，inner loop 还没立起来。

**第二，eval 跑分能不能进 CI，每次 PR 自动跑。** 这是第 8 章的产物。如果还在"我手工本地跑一下 bench.py"的阶段，scaffolding 没完成——你做的优化没有"是变好还是变坏"的客观依据。

**第三，业务方能不能在 staging 上自己点。** 不是你打开屏幕给她看，是她有自己的账号、自己点开、自己反馈。陈雪那边的反馈占我后面三周修复方向 70% 的依据，如果她拿不到 staging 入口，我的开发是闭门造车。

合昇这个项目，三个信号齐绿是第 5 周周三。从第 1 周到第 5 周中间这四周多，我写的业务代码不到 800 行，但 inner loop 通了之后，第 6-8 周写的 2000 多行代码每一行都有评估和反馈兜底。后面这 2000 行的修改成本比前面 800 行低一个量级。

这一点新人很难接受。第 4 周末周明远问过我一次："你们这一个月主要在干什么？我看 PR 列表很短。"我打开当时那张"inner loop 阻塞表"——27 项，已绿 22 项，在转 5 项。我跟他说："这 22 项每一项过去都是潜在的延期一周。等下个礼拜全绿了，我们的速度会肉眼可见地变快。"第 5 周末他自己注意到了节奏的变化，没再问过这个问题。

### Dev velocity 不是 LOC，是循环数

衡量 scaffolding 完成度的另一个方法是数循环数。FDE 项目里"循环"指的是一次完整的"假设 → 评估 → 决策"——不是一次 commit，不是一次部署，是一次"我以为 X 是问题，跑 eval 看到 Y，决定改成 Z"。

合昇第 6-8 周我数过自己的循环数：第 6 周 14 个，第 7 周 19 个，第 8 周 22 个。单看 LOC 这三周代码量差不多，但循环数翻倍意味着 inner loop 的每一段都更顺。LOC 每周可能差不到 10%，但循环数能差 50% 以上——后者才是 dev velocity 的真实指标。

在自己公司里我大概能做到一天 5-8 个循环。在档位 A 的客户那边，第 1 周一天 1 个循环都难，scaffolding 完成之后能稳定到一天 3-5 个。从 1 个到 5 个，就是 scaffolding 这一阶段在做的事。

---

## 10.2 在被打断的环境里做 inner loop

FDE 干活的环境，inner loop 永远不会像在自己公司那样顺。本地开发机权限受限、VPN 抖、跳板机延迟、依赖装不上、GitHub 不让连——这些不是偶发故障，是日常。

我把客户环境分成三档，每档的 inner loop 长得不一样：

```
        档位 A: 客户云上 VPC（最常见）
          - 客户有 AWS / Aliyun 账号
          - 我用客户给的 IAM 角色登入
          - 出网受 NAT + 安全组管控
          - 我自己的 Mac 通过 VPN 进客户 VPC
          - inner loop: 本地 IDE → push 客户 GitLab → CI → staging
          - 实际节奏: 15-30 分钟

        档位 B: 客户私有云 / 自建机房
          - 客户有自己的 K8s / VMware
          - 我必须用客户配的 Windows 工作站
          - 跳板机 SSH 进客户内网
          - inner loop: 跳板机内 IDE → 内部 GitLab → 内部 Jenkins → staging
          - 实际节奏: 30-60 分钟，依赖装不上经常打断

        档位 C: Air-gap（完全离线）
          - 没互联网，所有东西 USB 进
          - inner loop 里没有"pip install"这一步
          - 实际节奏: 1-2 小时，且每周末批量回传公司 review
```

合昇是档位 A，inner loop 还算完整。但即使是档位 A，第一个月里我也会反复撞到这些细节：

**Bedrock 的 VPC endpoint 必须先开。**ECS 跑在私有子网，调 Bedrock 默认走 NAT，到客户安全审计那里会被点名。第 1 周我就让顾建国把 `bedrock-runtime` 的 interface endpoint 建好，安全组放行 443，再加一条 endpoint policy 限制 `modelId` 只能是已审批的几个。这一步在第 6 章也提过，是 D1 锁定的一部分。它对 inner loop 的意义是：我所有调用从第一行起就符合上线时的安全模型，不会到第 8 周突然发现"本地能跑、staging 上 deny"。

**KB / Agents 也必须走私网。**第 9 章的 RAG，KB 调 OpenSearch Serverless 默认走公网，得在 collection 上开 VPC access policy，把 endpoint 关到 staging 子网。第一次我没配，eval 在本地能跑，部到 staging 直接 timeout。这种"环境差异"的 bug 是 inner loop 里最贵的一类——因为它在本地复现不了。

**SageMaker JumpStart 是兜底。**有的客户不让用 Bedrock，要求"模型必须自部署"。这种场景我会在 SageMaker JumpStart 上拉 Llama 3.1 / Qwen 镜像，部到客户 VPC 里的 SageMaker endpoint，调用方式还是 SDK，只是端点名换了。inner loop 没变，只是底层模型托管换了一层。合昇这个项目没走到这一步——周明远第 2 周就拍板可以用 Bedrock。但我知道下次遇到不让用的客户，这条路是通的。

**eval 跑得快是 inner loop 的隐藏前提。**eval-v0 才 10 条，每次跑 30 秒。但是 eval-v1 有 200 条，第一次跑下来 11 分钟。CI 一次 11 分钟，意味着我每次 push 之后要等 11 分钟才能知道有没有 regression——这会直接把 inner loop 从 15 分钟拉到 25 分钟以上。第 6 周末我做了两件事让它降到 4 分钟：评估调用走 Bedrock 的 Flex 服务等级（latency-tolerant 折扣档，CI 评估对延迟不敏感），且只对修改过的 prompt 路径跑全量、其他路径走采样。这种工程优化看起来不起眼，但它是 dev velocity 真实的瓶颈。

### inner loop 被打断时的工程动作

环境总会出问题。我整理了几条让自己能继续干活的动作，按出现频率排：

**第一，把"能离线跑"和"必须在线跑"的代码分开。** prompt 模板、工具函数、数据 schema、评估打分逻辑——这些都能在我本地 Mac 上跑，不需要客户网络。真正必须在客户环境里跑的，只有"调 Bedrock + 调 KB + 调客户 ERP"这三类。我把代码组织成两层，本地能 mock 的全部 mock，让自己每天有 70% 的时间能在不连客户 VPN 的情况下推进。这个比例最初我是 30%，第 3 周末优化到 70%。

**第二，所有 prompt 写在仓库里，不口头说。**这条是 air-gap 客户那边学到的，但所有档位都适用。客户的安全审计不接受"FDE 私下试一下"——所有提示词、所有改动都得在仓库里有记录。我自己 prompt 写一条就 commit 一条，哪怕只是"加了一句不要输出 markdown"。三个月后回头看 git blame，我能复盘出每一处 prompt 是因为什么 bug 改的。

**第三，pip / npm 第一周就申白名单。**客户的私有 PyPI mirror 大概率不全。pydantic、boto3、langfuse、各种小工具，第一周列一份完整清单交给客户 IT，让他们一次审完。比第 4 周一个一个补麻烦小很多。这条听起来是常识，但每个新项目我都还会在某个奇怪的包上栽一次跟头。

**第四，反复出问题的功能简化方案。**air-gap 客户那边我学到一条规矩：依赖越少越安全。在客户环境里 debug 第三方库的成本是平时的 5-10 倍——你不能 stack overflow、不能 GitHub issue 翻一翻、不能拉它的 src 进 IDE 里 step through。一个第三方库出过两次问题，我就开始考虑能不能用 200 行自己写的代码替代。第 6 章那条"Level 0 优先"的判断，根上就是这个理由。

**第五，每周末把代码批量回传公司做 review 和备份。**客户网络隔离意味着代码只在客户那边有一份。如果客户那边硬盘坏了、权限被回收，三个月的活就没了。我的习惯是每周五下班前打一个 zip，按客户的"出网软件流程"传一份回公司私有仓库，作为冷备份。这条是 air-gap 客户那边一个老 FDE 教我的，他原话是"客户 IT 不是你的同事，他们有他们的 KPI，他们某天可以完全合理地把你的访问权回收"。

> Conikeec 在 *FDE Playbook* 里把这一类动作叫"defensive engineering"——不是为了写漂亮代码，是为了在客户环境的不可控里保住自己每天能继续推进的能力。

### 什么时候你已经在反模式里了

我反复见过几种 inner loop 的反模式，列出来：

- **本地用 SaaS API、上线换私有部署。**模型行为差异、上下文窗口差异、tool call 格式差异，每一项都能让 staging 上行为完全变样。第 6 章那张选型纸第一行就是"D1 锁定"，根上就是为了避免这件事。
- **没走 VPC endpoint、上 NAT 出去。**短期能跑，到客户安全审计那里直接红。我每个项目第 1 周必做的事就是把所有外调流量画在一张图上，每条流量配一个 endpoint 或 NAT，由顾建国签字。
- **不申请软件入网就装第三方依赖。**客户 IT 第一次会警告，第二次会回收你的开发机权限。
- **把客户数据下载到本地分析。**这条是合规事故第一名，我自己见过有人这么干被项目经理直接 escalate 到客户 CIO。客户数据永远在客户那边，分析也在客户那边，结果可以脱敏导出来——这是底线。

最难记住的是第一条。SaaS API 在本地起开发太顺手了，所有人都想这样开始。但它的代价是第 8 周一次性付清——而第 8 周通常就是客户高层第一次看演示的那一周。

我在合昇的做法是第 1 周就在我自己 Mac 上接客户的 Bedrock VPC endpoint（通过 VPN + STS assume role），让本地 dev 直接调客户账号的模型。这样我开发用的是和 staging 一模一样的链路。第一次配通花了大半天，但后面 12 周再没踩过"本地能跑、客户那边不能跑"的坑。前期一次性成本，换后期 zero 环境差异 bug，这笔账值。

---

## 10.3 Staging 部署与 hot fix 通道

scaffolding 完成、inner loop 跑起来之后，下一道关是 staging。staging 不是"上线前的最后检查"——staging 是 FDE 工作中最被低估的一环。它是业务方真实使用的地方，是"客户能不能维护"的第一次预演。

合昇这个项目 staging 是这样长的：

```
  staging 集群 (客户 ap-southeast-1 ECS)
    ↓
  域名: agent-staging.hesheng.internal
    ↓
  访问: 客户内网 VPN + Identity Center SSO
    ↓
  数据: 工单库镜像 + KB 全量 + ERP 只读
    ↓
  日志: CloudWatch Logs + Langfuse self-hosted
    ↓
  评估: eval-v1 每次部署自动跑，结果贴 Slack
```

这套环境我从第 4 周开始搭，第 5 周陈雪能用，第 7 周王师傅和另外两位资深维修工程师加进来。到第 8 周演示之前，已经积累了 600 多条真实 staging 调用记录，每一条都有 trace、有 token 用量、有他们标的"对/错/凑合"三档反馈。

这 600 条数据是第 8 周演示能成的根本原因。**周明远问"为什么 95% 准确率"，我打开 Langfuse 让他看 600 条真实工单的 trace。这不是 demo，是已经在用的工具。**

### staging 上的几个要点

**第一，staging 用真实数据。**很多人 staging 用脱敏数据或人工造的数据，结果上线那天发现真实数据里有些边角情况之前没见过。我建议工单库做一份镜像，PII 字段（客户姓名、电话）做哈希处理，其他全保留。这样的 staging 才能反映上线行为。合规上要和客户法务确认 staging 集群的访问权限收紧到 FDE + 业务方核心几人。

**第二，staging 必须有"撤回"能力。**业务方在 staging 上点出某个错误结论后，能不能立刻把这条记录撤回不被记入 KB？能不能把某个错误的 prompt 版本一键回滚？这两件事我在第 4 周搭 staging 时就接进去了。撤回能力比不上 production 重要，但它决定了业务方愿不愿意在 staging 上"放手用"。陈雪第 6 周在 staging 上点错过两次，每次我都能在 30 秒内把对应记录撤回；第 7 周开始她自己点的越来越多，反馈量从一周 20 条涨到一周 90 条——这个数据曲线和"撤回能力是否到位"是直接挂钩的。

**第三，staging 是 hot fix 通道的演练场。**上线之后某天客户那边出问题，从你收到告警到你修完上线的这条路径——你必须在 staging 上演练过。

### Hot fix 通道

合昇上线后第三周一个周二下午，陈雪在 Slack 群里 @ 我："T-2026-0531 这条工单分错了，客户已经投诉到周总那里。"

从这条消息到修复推到 production，我走的路径：

```
  14:32  收到 @
  14:35  打开 Langfuse 看 trace, 定位到是 KB 检索召回错了
         （工单里"主轴抖动"被检索成"主轴更换"）
  14:48  在 staging 上重现, 确认是 chunking 把报警代码切到下一个
         chunk 导致的, prompt 拿到的上下文不全
  14:55  改 chunking 策略 (从 800 token 改成 1200 token + 500 重叠)
  15:02  push, CI 跑 eval-v1, 7 条历史相似工单全过
  15:08  staging 部署完成, 我让陈雪在 staging 上拿 T-2026-0531 重跑, OK
  15:14  ArgoCD 推 production, 5% 灰度
  15:30  灰度数据稳定, 推到 100%
  15:35  在 Slack 回陈雪: "已修, T-2026-0531 重跑确认对了, 流量已全切。"
```

整条 hot fix 通道 1 小时 3 分钟。这个时间不是因为我手快——是因为前 8 周搭的 inner loop + staging + eval-v1 这三件事每一件都在这条路径上发挥作用。如果其中任何一件没搭好，这条 hot fix 大概率要花一整天。

**Inner loop 把 staging 部署压到 8 分钟以内**——所以我在 15:08 能让陈雪重跑。**eval-v1 在 CI 里自动跑**——所以我 15:02 push 之后能在 6 分钟内确认 7 条相似工单都过了，不会因为这次修改 regression。**staging 用真实数据**——所以"在 staging 上重现"是个真问题，不是"造一个测试用例"。

> Bob McGrew 在 YC 那次 talk 里说过一句话："Most production bugs are not new failures, they're old failures that scaffolding didn't surface." 我那次 hot fix 撞上的"chunking 把报警代码切开"这个问题，复盘之后发现 eval-v1 里没有任何样本是"报警代码出现在 chunk 边界"。修完之后我做的第一件事是把 T-2026-0531 加进 eval-v1，标号 251。下一次同类问题不会再到客户那边才暴露。

### Hot fix 通道平时怎么演练

合规要求严的客户，"周二下午直接推 production"是不能允许的。多数客户会要求 hot fix 走一个简化版的审批：值班 SRE 一人 + FDE 一人即可，不走完整 change request。这条简化通道必须在上线前和客户 IT 把流程谈下来，写进 runbook，并且至少演练一次。

合昇这个简化通道是顾建国第 9 周和我一起谈下来的。当时我们打了一个赌：第 11 周上线前必须做一次 fire drill——故意在 staging 上引入一个 P0 bug，从告警触发开始走完整的 hot fix 通道，目标是 1 小时内修完。第一次跑了 1 小时 47 分，主要卡在审批流程上（值班 SRE 是另一位同事，他不在工位）。我们改了流程，第二次跑 52 分钟。第三周真出 T-2026-0531 那条线上故障，1 小时 3 分钟修完——这个数字不是巧合，是演练出来的。

如果你这一章只能记住一件事：**Hot fix 通道不是上线之后才搭的，是 scaffolding 阶段就要立的、staging 上要反复演练的**。等到真正出故障再搭，已经晚了。

### Fire drill 的两条经验

合昇那两次 fire drill 我事后写过一份小复盘。两条对下一个项目最有用的经验：

**第一，演练前业务方不要知道。**第一次 fire drill 我提前告诉了陈雪"我们下午要演练一次故障"，结果她当时坐得离手机很近，看到 Slack 一响就秒回。真实故障里业务方是"刚开会回来才看到一堆消息堆在群里"。第二次我没告诉她，她过了 14 分钟才看到 @，这才是真实流程的起点。演练数据要尽量真。

**第二，演练完一定要回看 trace。**第一次 fire drill 我们改完上线就结束了，没回看。第二次我让所有人坐下来过一遍 Langfuse trace，发现 hot fix 那段时间内 KB 检索其实有 3 次空召回，被代码 fallback 兜住了没暴露——但这 3 次空召回是 KB 索引在部署窗口内不一致导致的。这个隐藏 bug 只有在事后回看 trace 才能看见。回看是演练的另一半。

---

## 收尾

合昇这个项目从第 1 周到第 8 周，我每天大头时间在做的不是"写 LLM 应用"——是把 inner loop 立起来、把 staging 搭出来、把 hot fix 通道演练通。这些活在简历上写出来不性感，没有"用了 RAG"那么显眼，但它们是这个项目从 demo 走到 production 没翻车的根本原因。

你下一份项目第 1 周开始时，可以问自己一个简单的问题：**从我改一行 prompt，到业务方在真实环境里看到效果，整条路径上有几道阻塞我没解开**。一道一道列出来，一道一道找客户的人去解开。把这件事干到第 5 周末三个信号齐绿，scaffolding 才算真的做完。在那之前，所有的代码都是预备性的。下一章讲的"和遗留系统对接"——SSO、SCIM、API、审计——很多内容也是同一个底层逻辑：你不解开这些阻塞，inner loop 在客户那边永远没法跑顺。

---

## 本章引用的公开资料

- A. Lawrence, *Forward Deployed Engineer Rule Book* (2025) — "The first thing you build for a customer is not the product, it's the loop."
- Conikeec, *The FDE Playbook: A Practitioner's Field Manual* (2025, Substack) — "defensive engineering" 一节
- Bob McGrew @ Y Combinator (2025) — staging 与生产 bug 的关系
- AWS 官方文档：Bedrock VPC endpoints / PrivateLink for Bedrock / SageMaker JumpStart 私有部署 — 本章 D1 段落的事实依据

- Nabeel Qureshi, *Reflections on Palantir* — 关于在客户环境里"defensive engineering"为什么是 FDE 的隐性核心能力

完整书目和链接见全书末尾的 *参考文献*。

[← 上一章：客户数据栈](../chapter-09/) · [下一章：与遗留系统对接 →](../chapter-11/)
