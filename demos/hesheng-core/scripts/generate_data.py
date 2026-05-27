"""Synthesize Hesheng raw CSVs with realistic dirt.

Same design as the original Ch9 generator. 200 equipment / 500 tickets /
300 work_orders, with surface and semantic dirty-data seeded. Reproducible
(seed=42).
"""

from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

random.seed(42)

OUT = Path(__file__).resolve().parent.parent / "data" / "raw"
OUT.mkdir(parents=True, exist_ok=True)

EQUIPMENT_MODELS = ["JG-A6", "JG-A8", "JG-B12", "JG-C5", "TF-X2"]
SITES = ["singapore", "kuala_lumpur", "bangkok", "jakarta", "ho_chi_minh"]


def gen_equipment(n: int = 200) -> list[dict]:
    rows: list[dict] = []
    for i in range(n):
        model = random.choice(EQUIPMENT_MODELS)
        site = random.choice(SITES)
        rating = random.randint(15, 80)
        rating_field = f"{rating}kw" if i % 4 == 0 else str(rating)
        row = {
            "equipment_id": f"EQ-{i:05d}",
            "model": "JGA6" if (i == 7 or i == 42) else model,
            "site": site,
            "service_year": str(random.randint(2018, 2024)) if i % 3 == 0 else random.randint(2018, 2024),
            "power_rating": rating_field,
            "last_maintained": (datetime(2026, 1, 1) - timedelta(days=random.randint(1, 720))).strftime("%Y-%m-%d"),
            "customer_id": f"NUM-{random.randint(1000, 9999)}" if i < 100 else f"C-{random.randint(100, 999)}",
        }
        rows.append(row)
    if len(rows) > 50:
        rows[3]["model"] = "JG-A6​"
        rows[51]["model"] = "JG A8"
        rows[99]["model"] = "JG-B12 "
    return rows


FAULT_DESCRIPTIONS_CN = [
    "X 轴定位异常,加工件公差超差",
    "主轴异响,低速运行明显,转速超 6000rpm 后消失",
    "切削液不足,无报警但液位明显偏低",
    "PLC 与上位机通信中断,重启短暂恢复",
    "ALM 4501 报警,加冷却液后未复位",
    "Z 轴回零失败,错误代码 #2103",
    "新来的徒弟说屏幕显示报警,我看是冷却液低",
    "运行 8 小时后突然停机,无报警",
    "工件表面出现规律性纹路,每隔 30s 出现一次",
    "电机过热保护触发,1042 报警",
]
ALARM_CODES = ["ALM 4501", "ALM 4502", "1042", "1043", "#2103", "#2104", "E-301", ""]
PRIORITIES = ["P1", "P2", "P3", "high", "medium", "low", "1", "2", "3"]


def gen_tickets(n: int, equipment_ids: list[str]) -> list[dict]:
    rows: list[dict] = []
    for i in range(n):
        ts_choice = random.random()
        ts_dt = datetime(2026, 5, 1) - timedelta(hours=random.randint(0, 24 * 90))
        if ts_choice < 0.67:
            ts_str = ts_dt.replace(tzinfo=timezone.utc).isoformat()
        elif ts_choice < 0.90:
            ts_str = ts_dt.strftime("%Y年%m月%d日 %H:%M")
        else:
            ts_str = str(int(ts_dt.timestamp()))
        eq_id = random.choice(equipment_ids)
        if i % 14 == 0:
            eq_id = f"EQ-{99000 + i}"
        rows.append({
            "ticket_no": f"T-2026-Q2-{i:05d}",
            "ts": ts_str,
            "equipment_id": eq_id,
            "fault_desc": random.choice(FAULT_DESCRIPTIONS_CN),
            "alarm_code": random.choice(ALARM_CODES),
            "priority": random.choice(PRIORITIES),
            "reporter_phone": f"+65-{random.randint(80000000, 99999999)}" if random.random() < 0.6 else f"+86-138{random.randint(10000000, 99999999)}",
            "team": random.choice(["机械组", "电气组", "Mech", "Elec", "M-team", "E-team"]),
        })
    return rows


ENGINEERS = [f"ENG-{i:03d}" for i in range(1, 49)]
PARTS = ["P-101", "P-102", "P-203", "P-204", "P-301", "P-401", "P-402"]


def gen_work_orders(n: int, ticket_nos: list[str]) -> list[dict]:
    rows: list[dict] = []
    for i in range(n):
        part = random.choice(PARTS)
        if random.random() < 0.15:
            part = part.replace("P-", "PART-")
        h = round(random.uniform(0.5, 8.0), 1)
        h_choice = random.random()
        if h_choice < 0.7:
            hours_field = str(h)
        elif h_choice < 0.9:
            hh = int(h)
            mm = int((h - hh) * 60)
            hours_field = f"{hh}h{mm}m"
        else:
            hours_field = str(int(h * 60))
        rows.append({
            "wo_id": f"WO-{i:05d}",
            "ticket_no": random.choice(ticket_nos),
            "engineer_id": random.choice(ENGINEERS),
            "part_id": part,
            "hours_spent": hours_field,
            "status": random.choice(["closed", "Closed", "已完成", "DONE", "complete"]),
            "completed_at": (datetime(2026, 5, 1) - timedelta(days=random.randint(0, 90))).strftime("%Y-%m-%d %H:%M:%S"),
        })
    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)


# Signature tickets — these 10 are the Ch6 eval-v0 samples. They're
# injected as real rows so demos referencing T-2025-Q4-0142 etc. can
# actually find them in the ticket_resolution view.
SIGNATURE_TICKETS = [
    {"ticket_no": "T-2025-Q4-0142", "equipment_id": "EQ-00007",
     "fault_desc": "客户报修：JG-A6 五轴加工中心,X 轴定位异常,加工件公差超差 0.08mm,已发现 X 轴伺服电机过热报警 1042",
     "alarm_code": "1042", "team": "电气组"},
    {"ticket_no": "T-2025-Q4-0817", "equipment_id": "EQ-00012",
     "fault_desc": "用户反馈机床主轴启动后有规律的异响,低速运行时明显,转速超 6000 rpm 后消失。设备型号 JG-A8",
     "alarm_code": "", "team": "机械组"},
    {"ticket_no": "T-2025-Q4-1503", "equipment_id": "EQ-00031",
     "fault_desc": "客户:工件原点设置后,第一次自动加工正常,第二次开始 Z 轴下刀深度逐渐变浅,每次约 0.02mm",
     "alarm_code": "", "team": "机械组"},
    {"ticket_no": "T-2025-Q4-2018", "equipment_id": "EQ-00042",
     "fault_desc": "新来的徒弟操作:他说屏幕上显示 ALM 4501 报警动不了。我看了一下是冷却液液位低",
     "alarm_code": "ALM 4501", "team": "电气组"},
    {"ticket_no": "T-2025-Q4-2455", "equipment_id": "EQ-00067",
     "fault_desc": "数控机床 PLC 与上位机通信中断,工厂内网正常,机床端 ping 不通车间交换机",
     "alarm_code": "", "team": "电气组"},
    {"ticket_no": "T-2025-Q4-3187", "equipment_id": "EQ-00085",
     "fault_desc": "客户使用 5 年,从未保养换油。最近发现液压站噪音大",
     "alarm_code": "", "team": "机械组"},
    {"ticket_no": "T-2025-Q4-3621", "equipment_id": "EQ-00099",
     "fault_desc": "Z 轴急停后无法回零,屏幕显示 #2103 错误,手动模式可以走但回零异常",
     "alarm_code": "#2103", "team": "电气组"},
    {"ticket_no": "T-2025-Q4-4044", "equipment_id": "EQ-00121",
     "fault_desc": "客户反馈一台老机床(8 年机龄)切削液泵不出液,清理过滤器后还是没流量",
     "alarm_code": "", "team": "机械组"},
    {"ticket_no": "T-2025-Q4-4789", "equipment_id": "EQ-00148",
     "fault_desc": "三相电源切换后机床无法启动,主电柜内 24V 电源指示灯亮但 5V 电源无指示",
     "alarm_code": "", "team": "电气组"},
    {"ticket_no": "T-2025-Q4-5123", "equipment_id": "EQ-00177",
     "fault_desc": "Y 轴运行有规律性卡顿,2 秒卡一下,卡顿时无报警。X/Z 轴正常",
     "alarm_code": "", "team": "机械组"},
]


def inject_signatures(tickets: list[dict]) -> list[dict]:
    """Inject Ch6 eval-v0's 10 signature tickets at fixed positions.

    These have known ids that Ch14/Ch15 demos hardcode (e.g., T-2025-Q4-0142).
    By embedding them in the synthetic ticket table we make the
    "agent looks up the canonical demo ticket" path actually work.
    """
    base_ts = "2025-12-15T08:00:00+00:00"
    for sig in SIGNATURE_TICKETS:
        tickets.append({
            "ticket_no": sig["ticket_no"],
            "ts": base_ts,
            "equipment_id": sig["equipment_id"],
            "fault_desc": sig["fault_desc"],
            "alarm_code": sig["alarm_code"],
            "priority": "P1" if sig["alarm_code"] else "P2",
            "reporter_phone": "+65-87654321",
            "team": sig["team"],
        })
    return tickets


def main() -> None:
    eq = gen_equipment()
    write_csv(eq, OUT / "equipment.csv")
    print(f"  equipment.csv: {len(eq)} rows")
    tk = gen_tickets(500, [r["equipment_id"] for r in eq])
    tk = inject_signatures(tk)
    write_csv(tk, OUT / "tickets.csv")
    print(f"  tickets.csv: {len(tk)} rows ({len(SIGNATURE_TICKETS)} are Ch6 signature ids)")
    wo = gen_work_orders(300, [r["ticket_no"] for r in tk])
    write_csv(wo, OUT / "work_orders.csv")
    print(f"  work_orders.csv: {len(wo)} rows")


if __name__ == "__main__":
    main()
