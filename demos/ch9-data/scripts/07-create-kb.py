"""Create a small Bedrock Knowledge Base over Hesheng maintenance manuals.

We synthesize 5 short manual pages (one per equipment model) covering
the most common faults referenced in tickets — alarm codes 1042, 4501,
2103 etc. The agent will use this KB to look up "what does this alarm
mean and which team handles it".

Uses the OpenSearch Serverless backend (the default for KB).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

OUT = Path(__file__).resolve().parent.parent / "data" / "stack-outputs.json"
cfg = json.loads(OUT.read_text())

REGION = cfg["region"]
ACCOUNT = cfg["account"]
KB_BUCKET = f"fde-book-ch9-{ACCOUNT}-kb"

s3 = boto3.client("s3", region_name=REGION)


MANUALS = {
    "JG-A6-faults.md": """
# JG-A6 五轴加工中心常见故障与处理

## ALM 1042 — X 轴伺服电机过热
- 故障类别: 伺服系统
- 处理团队: 电气组
- 症状: 加工过程中突然停机, 屏幕显示 ALM 1042
- 排查步骤: 检查电机散热风扇 → 测量电机温度 → 检查驱动器是否过流
- 平均处理时间: 4 小时

## ALM 4501 — 冷却液液位低
- 故障类别: 传感器
- 处理团队: 电气组 (传感器问题), 机械组 (液位真低)
- 症状: 屏幕报警, 但目视液位可能正常
- 排查步骤: 加冷却液 → 看是否复位 → 不复位则检查传感器线路
- 注意: 加液后报警未消失通常是传感器或线路故障

## #2103 — Z 轴回零参考点丢失
- 故障类别: 编码器
- 处理团队: 电气组
- 排查步骤: 手动模式可走但回零异常 → 检查 Z 轴限位开关 → 检查编码器电缆
""",
    "JG-A8-faults.md": """
# JG-A8 加工中心常见故障与处理

## 主轴异响 (无报警)
- 故障类别: 主轴/传动
- 处理团队: 机械组
- 症状: 低速运行明显, 转速超 6000rpm 后消失
- 处理: 通常为主轴轴承问题, 平均更换工时 6-8 小时
""",
    "general-alarm-codes.md": """
# JG 系列报警代码索引

| 代码 | 含义 | 团队 |
|---|---|---|
| 1042 | X 轴伺服电机过热 | 电气组 |
| 1043 | Y 轴伺服电机过热 | 电气组 |
| ALM 4501 | 冷却液液位低 (传感器) | 电气组 |
| ALM 4502 | 冷却液液位低 (实际) | 机械组 |
| #2103 | Z 轴回零参考点丢失 | 电气组 |
| #2104 | X 轴回零参考点丢失 | 电气组 |
| E-301 | 主轴启动失败 | 电气组 |
""",
    "team-routing-policy.md": """
# 工单派工策略 (合昇海外服务部)

## 派工原则
1. 含数字报警代码 (1042, 1043, 4501-4599) → 电气组
2. 含 # 开头报警 (#2103, #2104) → 电气组
3. 无报警代码 + 描述包含"异响"/"卡顿"/"渗油"/"磨损" → 机械组
4. 无报警代码 + 描述包含"通信"/"电源"/"PLC" → 电气组
5. 描述模糊或包含方言 → 升级 P1, 转资深工程师

## 站点工程师覆盖
- Singapore: 电气 4 / 机械 3 (覆盖 Singapore + KL)
- Bangkok: 电气 2 / 机械 2
- Jakarta: 电气 2 / 机械 1 (机械组工时不足, 复杂机械故障转 KL)
- Ho Chi Minh: 电气 1 / 机械 1
""",
    "service-level-agreement.md": """
# 合昇海外服务部 SLA

| 优先级 | 首响时间 | 上门时间 (Singapore) | 上门时间 (其他站点) |
|---|---|---|---|
| P1 | 30 min | 4 hours | 24 hours |
| P2 | 2 hours | 24 hours | 48 hours |
| P3 | 24 hours | 72 hours | 5 days |

P1 优先级触发条件:
- 整线停产 (含 1042/1043 等导致设备不可用的报警)
- 客户等级 A 客户的任何故障
- 客户主动升级
""",
}


def upload_manuals() -> None:
    try:
        s3.head_bucket(Bucket=KB_BUCKET)
        print(f"  KB bucket {KB_BUCKET} exists")
    except ClientError:
        s3.create_bucket(Bucket=KB_BUCKET)
        print(f"  Created KB bucket {KB_BUCKET}")

    manuals_dir = Path(__file__).resolve().parent.parent / "data" / "manuals"
    manuals_dir.mkdir(parents=True, exist_ok=True)
    for fname, body in MANUALS.items():
        p = manuals_dir / fname
        p.write_text(body)
        s3.upload_file(str(p), KB_BUCKET, f"manuals/{fname}")
        print(f"  Uploaded {fname}")

    cfg["kb_bucket"] = KB_BUCKET
    OUT.write_text(json.dumps(cfg, indent=2))


def main() -> None:
    upload_manuals()
    print()
    print("KB documents uploaded. Knowledge Base creation requires:")
    print("  1. OpenSearch Serverless collection (creation takes ~5 min)")
    print("  2. KB resource pointing to the S3 prefix")
    print("  3. Initial sync (Ingestion job)")
    print()
    print("For this demo I keep the KB step manual — we'll skip OpenSearch")
    print("and use the simpler approach: include manuals as plain text in")
    print("the agent's system prompt. 5 short manuals = ~3000 tokens, fits")
    print("comfortably in Claude's context window with prompt cache.")
    print()
    print("This is a real FDE judgment call — for small, stable knowledge")
    print("(< 30 short docs), prompt-stuffing is cheaper and faster than KB.")
    print("KB shines when you have 100+ docs or docs change weekly.")


if __name__ == "__main__":
    main()
