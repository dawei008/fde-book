<p align="center">
  <img src="cover.png" alt="OpenBook · Forward Deployed Engineer" width="480" />
</p>

<h1 align="center">OpenBook · Forward Deployed Engineer</h1>
<h3 align="center">AI 应用的落地工程学</h3>

<p align="center">
  <strong>📖 <a href="https://dawei008.github.io/fde-book/">在 GitHub Pages 上阅读 →</a></strong>
</p>

<p align="center">
  <em>17 章 · 7 Part · 4 附录 · 中英双语 · 配套可执行 demo</em>
</p>

---

写给在客户现场把 AI 跑起来的工程师。

公式：

```
Outcome = Harness × Customer
```

Harness 提供能力，Customer 提供约束。这本书写的是怎么把 Harness 装到客户身上。

---

## 在线阅读 vs 仓库

**[👉 dawei008.github.io/fde-book](https://dawei008.github.io/fde-book/)** 是阅读体验最好的入口——左侧有完整目录、有搜索、移动端友好、夜间模式。

**这个仓库**是源文件 + 配套代码 + 翻译工程。clone 下来你能：

- 直接读 markdown（每章一个 `.md`，结构和书一致）
- 跑配套 demo（`demos/` 目录，每章独立、用完即拆，详见各章末尾）
- 提 PR / 开 Issue 反馈错处或补充案例

如果你觉得这本书有用，欢迎 ⭐ Star 这个仓库——这是判断我应不应该继续往下写的最直接信号。

---

## 目录

| Part | 讲什么 |
|---|---|
| **I — 角色与心智** | FDE 是什么、心智模型、不是什么 |
| **II — 客户发现** | 第一周怎么做、需求 → 评估集 → SOW |
| **III — 技术选型** | 第一周决断、RAG / 微调 / Agent 选型、评估先于代码 |
| **IV — 工程化落地** | 数据工程、scaffolding、VPC/SSO/合规 |
| **V — 上线与运营** | PoC 到生产、监控与 Guardrails |
| **VI — Agent 与 MCP** | Agent toolset 设计、MCP 集成 |
| **VII — 交接与持续** | 项目交接、FDE 的下一步 |
| **附录 A-D** | 工具栈速查、比较矩阵、评估集模板、客户启动包 |

英文版在 [`en/`](en/) 目录，结构镜像中文。

---

## 配套代码

`demos/` 下每章一个独立子目录。约定：

- 每个 demo 都能在你自己的 AWS 账号里复现
- 用完即拆，每个 demo README 给出 teardown 步骤
- 所有数字（延迟、准确率、$）都来自实跑，不是抄 benchmark

例如 [`demos/ch6-stack/`](demos/ch6-stack/) 是第 6 章的模型选型 bench：4 个 Bedrock 模型 × 10 条工单 × 3 轮，总成本约 $0.50。

---

## 致谢

这本书大量参考了：

- *Forward Deployed Engineer Rule Book* — A. Lawrence (2025)
- *The FDE Playbook: A Practitioner's Field Manual* — Conikeec (2025)
- *Reflections on Palantir* — Nabeel Qureshi
- AWS GenAI Innovation Center 公开案例
- Bob McGrew @ Y Combinator (2025) — "Sell the outcome, not the product"

完整书目在 [`bibliography.md`](bibliography.md)。

---

## License

CC-BY-SA 4.0（文本），MIT（代码）。

转载、引用、重组都欢迎，请保留来源链接。
