"""Synthesize Hesheng raw data with realistic dirt.

Produces 3 CSVs that mimic what an FDE actually finds when first
asking a customer DBA for an export. Surface dirt (encoding, units,
timestamp formats, naming) and semantic dirt (department-specific
field meanings, broken FK references) are both seeded.

Run from repo root:
    python demos/ch9-data/scripts/01-generate-data.py

Outputs to demos/ch9-data/data/raw/ (gitignored).
"""

from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

random.seed(42)  # reproducible

OUT = Path(__file__).resolve().parent.parent / "data" / "raw"
OUT.mkdir(parents=True, exist_ok=True)


# ---------- Equipment master ----------

EQUIPMENT_MODELS = ["JG-A6", "JG-A8", "JG-B12", "JG-C5", "TF-X2"]
SITES = ["singapore", "kuala_lumpur", "bangkok", "jakarta", "ho_chi_minh"]


def gen_equipment(n: int = 200) -> list[dict]:
    rows: list[dict] = []
    for i in range(n):
        model = random.choice(EQUIPMENT_MODELS)
        site = random.choice(SITES)
        # Surface dirt: some rows use service_year as integer, some as string with quotes
        # Surface dirt: power_rating_kw mixed with power_rating (no unit)
        rating = random.randint(15, 80)
        rating_field = f"{rating}kw" if i % 4 == 0 else str(rating)

        row = {
            "equipment_id": f"EQ-{i:05d}",
            "model": model,
            # Semantic dirt: 5% rows have model misspelled
            "model": "JGA6" if (i == 7 or i == 42) else model,
            "site": site,
            "service_year": str(random.randint(2018, 2024)) if i % 3 == 0 else random.randint(2018, 2024),
            "power_rating": rating_field,
            "last_maintained": (datetime(2026, 1, 1) - timedelta(days=random.randint(1, 720))).strftime("%Y-%m-%d"),
            # Semantic dirt: customer_id format varies — old equipment uses NUM-XXXX, new uses C-NNN
            "customer_id": f"NUM-{random.randint(1000, 9999)}" if i < 100 else f"C-{random.randint(100, 999)}",
        }
        rows.append(row)

    # Surface dirt: 3 rows with Unicode encoding artifacts in model
    if len(rows) > 50:
        rows[3]["model"] = "JG-A6​"  # zero-width space
        rows[51]["model"] = "JG A8"  # non-breaking space
        rows[99]["model"] = "JG-B12 "  # trailing space

    return rows


# ---------- Tickets ----------

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
PRIORITIES = ["P1", "P2", "P3", "high", "medium", "low", "1", "2", "3"]  # naming chaos


def gen_tickets(n: int = 500, equipment_ids: list[str] = None) -> list[dict]:
    assert equipment_ids is not None
    rows: list[dict] = []
    for i in range(n):
        # Surface dirt: timestamp format mixed
        ts_choice = random.random()
        ts_dt = datetime(2026, 5, 1) - timedelta(hours=random.randint(0, 24 * 90))
        if ts_choice < 0.67:
            ts_str = ts_dt.replace(tzinfo=timezone.utc).isoformat()
        elif ts_choice < 0.90:
            # Chinese local format, no tz
            ts_str = ts_dt.strftime("%Y年%m月%d日 %H:%M")
        else:
            # Unix epoch
            ts_str = str(int(ts_dt.timestamp()))

        eq_id = random.choice(equipment_ids)
        # Semantic dirt: 7% tickets reference an equipment_id that was decommissioned
        # (we'll inject these as IDs that don't exist in equipment master)
        if i % 14 == 0:
            eq_id = f"EQ-{99000 + i}"  # broken FK

        # Surface dirt: priority field uses 9 different values across departments
        priority = random.choice(PRIORITIES)

        row = {
            "ticket_no": f"T-2026-Q2-{i:05d}",
            "ts": ts_str,
            "equipment_id": eq_id,
            "fault_desc": random.choice(FAULT_DESCRIPTIONS_CN),
            "alarm_code": random.choice(ALARM_CODES),
            "priority": priority,
            # Customer phone — PII, must be masked downstream
            "reporter_phone": f"+65-{random.randint(80000000, 99999999)}" if random.random() < 0.6 else f"+86-138{random.randint(10000000, 99999999)}",
            # Semantic dirt: 'team' field has 3 different conventions across sites
            "team": random.choice(["机械组", "电气组", "Mech", "Elec", "M-team", "E-team"]),
        }
        rows.append(row)
    return rows


# ---------- WorkOrders ----------

ENGINEERS = [f"ENG-{i:03d}" for i in range(1, 49)]  # 48 engineers in book
PARTS = ["P-101", "P-102", "P-203", "P-204", "P-301", "P-401", "P-402"]


def gen_work_orders(n: int = 300, ticket_nos: list[str] = None) -> list[dict]:
    assert ticket_nos is not None
    rows: list[dict] = []
    for i in range(n):
        # Semantic dirt: part_id has prefix variation across sites
        # KL site uses "PART-101" instead of "P-101"
        site_quirk = random.random() < 0.15
        part = random.choice(PARTS)
        if site_quirk:
            part = part.replace("P-", "PART-")

        # Surface dirt: hours_spent is sometimes "2.5", sometimes "2h30m", sometimes minutes
        h = round(random.uniform(0.5, 8.0), 1)
        h_choice = random.random()
        if h_choice < 0.7:
            hours_field = str(h)
        elif h_choice < 0.9:
            hh = int(h)
            mm = int((h - hh) * 60)
            hours_field = f"{hh}h{mm}m"
        else:
            hours_field = str(int(h * 60))  # bare minutes

        row = {
            "wo_id": f"WO-{i:05d}",
            "ticket_no": random.choice(ticket_nos),
            "engineer_id": random.choice(ENGINEERS),
            "part_id": part,
            "hours_spent": hours_field,
            # Semantic dirt: status has 5 different conventions
            "status": random.choice(["closed", "Closed", "已完成", "DONE", "complete"]),
            "completed_at": (datetime(2026, 5, 1) - timedelta(days=random.randint(0, 90))).strftime("%Y-%m-%d %H:%M:%S"),
        }
        rows.append(row)
    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    eq = gen_equipment()
    write_csv(eq, OUT / "equipment.csv")
    print(f"  equipment.csv: {len(eq)} rows -> {OUT/'equipment.csv'}")

    eq_ids = [r["equipment_id"] for r in eq]
    tk = gen_tickets(equipment_ids=eq_ids)
    write_csv(tk, OUT / "tickets.csv")
    print(f"  tickets.csv:   {len(tk)} rows -> {OUT/'tickets.csv'}")

    tk_nos = [r["ticket_no"] for r in tk]
    wo = gen_work_orders(ticket_nos=tk_nos)
    write_csv(wo, OUT / "work_orders.csv")
    print(f"  work_orders.csv: {len(wo)} rows -> {OUT/'work_orders.csv'}")

    print()
    print("Seeded dirt:")
    print("  surface — encoding artifacts, mixed timestamp formats, mixed units")
    print("  semantic — broken FKs, naming inconsistency across sites,")
    print("             priority/status field conventions vary by department")


if __name__ == "__main__":
    main()
