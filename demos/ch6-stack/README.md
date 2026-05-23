# Ch6 demo — 工单 Agent 技术栈快速决断矩阵

苏州合昇精密重工的工单 Agent 项目第一周：在 Bedrock 上对四个候选模型 + 两种调用模式跑同一个 Eval 集，得到真实的延迟/成本/准确率三角对比。

## 目标

让 FDE 第一周的"技术栈选型会议"不再依赖网络流传的 benchmark 截图，而是有客户实际数据做依据。

## 部署

```bash
cd demos/ch6-stack
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 跑评测（不部署 CDK，纯 boto3 调用）
python scripts/bench.py --eval data/eval-v0.jsonl --models all --runs 3

# 看结果
python scripts/report.py results/latest.json
```

## 销毁

```bash
# 本章 demo 不创建持久资源（Bedrock 是按调用计费的 managed service）
# 仅需删除本地结果即可
rm -rf results/
```

## 预期成本

100 条 Eval × 4 模型 × 3 次重复 = 1200 次调用，约 $0.50-2.00（取决于模型）。

## 真实测得（2026-05-23 跑的快照）

见章节正文里的对比表。
