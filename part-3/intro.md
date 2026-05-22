# Part III: 脚手架 — 6 周让 LLM 工作流跑起来

> 适用范围：**LLM 应用主线**（数据驱动主线读 Part IV）

---

## 这个 Part 要解决什么问题

Discovery 跑完，FDE 拿到 outcome、Eval 集 v0.1、SOW。

接下来 6 周做什么？

90% 的新手 FDE 在这一步陷入两个反模式：

1. **过度选型**：花 2 周比较 5 个向量库 / 3 个 Agent 框架 / 4 个 LLM —— 一行业务代码没写
2. **零选型**：抓起最熟的模型 + 最熟的框架就开干 —— 6 周后才发现选错

这个 Part 给一条第三路线：**用"速决矩阵 + 决策树 + Eval 先行"三件套，把 6 周脚手架阶段做成可控的工程任务**。

## 包含章节

- **Chapter 6: 技术栈速决矩阵** — 一张表帮你 30 分钟选定模型 / 框架 / 数据库 / 编排
- **Chapter 7: 决策树** — RAG / Fine-tune / Prompting / Agent 该用哪个？什么信号触发切换？
- **Chapter 8: 先 Eval 再开发** — 实操：怎么把 Eval 集变成 CI 守门员

## 与其他 Part 的关系

- **前置**：Part II 的 outcome + Eval v0.1 + SOW 是这一 Part 的全部输入
- **后续**：Part V 把 Scaffolding 阶段的产物推到生产；Part VI 在已有脚手架上加 Agent

---

[← 返回目录](../README.md)
