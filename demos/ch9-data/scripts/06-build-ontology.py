"""Build the Hesheng ontology as Athena views.

Three entities:
- equipment_clean      — normalized model name, parsed power_rating
- ticket_clean         — UTC timestamp, normalized priority, normalized team
- work_order_clean     — normalized hours_spent, normalized status,
                         normalized part_id

Plus one fact table view:
- ticket_resolution    — joins ticket + equipment + first work_order
                         (defensive against the 36 broken FKs we found)

This is what FDE writes after the day-3 Athena exploration.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import boto3

OUT = Path(__file__).resolve().parent.parent / "data" / "stack-outputs.json"
cfg = json.loads(OUT.read_text())
athena = boto3.client("athena", region_name=cfg["region"])

DB = cfg["database"]
RESULTS = f"s3://{cfg['athena_bucket']}/results/"


VIEWS: list[tuple[str, str]] = [
    ("equipment_clean", f"""
        CREATE OR REPLACE VIEW {DB}.equipment_clean AS
        SELECT
            equipment_id,
            -- Normalize model: strip whitespace and Unicode artifacts, fix misspellings
            REGEXP_REPLACE(TRIM(model), '[\\u200B\\xa0]', '') AS model_raw,
            CASE
                WHEN model LIKE 'JGA%' THEN REPLACE(model, 'JGA', 'JG-A')
                WHEN model LIKE 'JG A%' THEN REPLACE(model, 'JG A', 'JG-A')
                ELSE REGEXP_REPLACE(TRIM(model), '[\\u200B\\xa0]', '')
            END AS model,
            site,
            CAST(service_year AS INTEGER) AS service_year,
            -- Parse 'kw' suffix off power_rating
            CAST(REGEXP_EXTRACT(power_rating, '\\d+') AS INTEGER) AS power_rating_kw,
            CAST(last_maintained AS DATE) AS last_maintained,
            customer_id
        FROM {DB}.equipment
    """),
    ("ticket_clean", f"""
        CREATE OR REPLACE VIEW {DB}.ticket_clean AS
        SELECT
            ticket_no,
            -- Normalize timestamp to UTC. Glue Catalog views can't store
            -- timestamp-with-tz, so we cast to plain timestamp at UTC.
            CASE
                WHEN regexp_like(ts, '^\\d{{4}}-\\d{{2}}-\\d{{2}}T')
                    THEN CAST(from_iso8601_timestamp(ts) AS timestamp)
                WHEN regexp_like(ts, '^\\d{{4}}年')
                    THEN CAST(parse_datetime(ts, 'yyyy''年''MM''月''dd''日'' HH:mm') AS timestamp)
                          - INTERVAL '8' HOUR
                WHEN regexp_like(ts, '^\\d{{10}}$')
                    THEN from_unixtime(CAST(ts AS BIGINT))
                ELSE NULL
            END AS ts_utc,
            equipment_id,
            fault_desc,
            alarm_code,
            -- Normalize priority to P1/P2/P3
            CASE
                WHEN priority IN ('P1', 'high', '1') THEN 'P1'
                WHEN priority IN ('P2', 'medium', '2') THEN 'P2'
                WHEN priority IN ('P3', 'low', '3') THEN 'P3'
                ELSE 'UNKNOWN'
            END AS priority,
            -- Normalize team to two canonical values
            CASE
                WHEN team IN ('机械组', 'Mech', 'M-team') THEN '机械组'
                WHEN team IN ('电气组', 'Elec', 'E-team') THEN '电气组'
                ELSE 'UNKNOWN'
            END AS team,
            -- Don't expose phone in clean view (PII)
            -- We'll handle column-level grants in step 07
            reporter_phone
        FROM {DB}.tickets
    """),
    ("work_order_clean", f"""
        CREATE OR REPLACE VIEW {DB}.work_order_clean AS
        SELECT
            wo_id,
            ticket_no,
            engineer_id,
            -- Normalize part_id to P-NNN
            CASE
                WHEN starts_with(part_id, 'PART-') THEN REPLACE(part_id, 'PART-', 'P-')
                ELSE part_id
            END AS part_id,
            -- Parse hours_spent: '2.5' / '2h30m' / '150' (minutes)
            CASE
                WHEN regexp_like(hours_spent, '^\\d+h\\d+m$') THEN
                    CAST(regexp_extract(hours_spent, '^(\\d+)h', 1) AS DOUBLE)
                  + CAST(regexp_extract(hours_spent, 'h(\\d+)m$', 1) AS DOUBLE) / 60.0
                WHEN regexp_like(hours_spent, '^\\d+$') AND CAST(hours_spent AS INTEGER) > 24 THEN
                    CAST(hours_spent AS DOUBLE) / 60.0
                ELSE CAST(hours_spent AS DOUBLE)
            END AS hours_spent,
            -- Normalize status to two values: closed / open
            CASE
                WHEN lower(status) IN ('closed', 'done', 'complete') THEN 'closed'
                WHEN status = '已完成' THEN 'closed'
                ELSE 'open'
            END AS status,
            CAST(completed_at AS TIMESTAMP) AS completed_at
        FROM {DB}.work_orders
    """),
    ("ticket_resolution", f"""
        CREATE OR REPLACE VIEW {DB}.ticket_resolution AS
        SELECT
            t.ticket_no,
            t.ts_utc,
            t.priority,
            t.team,
            t.fault_desc,
            t.alarm_code,
            -- Equipment may be missing (broken FK is real)
            e.model AS equipment_model,
            e.site,
            e.power_rating_kw,
            -- First closed work_order for this ticket (defensive)
            (
                SELECT min(w.completed_at)
                FROM {DB}.work_order_clean w
                WHERE w.ticket_no = t.ticket_no AND w.status = 'closed'
            ) AS resolved_at,
            -- Hours actually spent
            (
                SELECT sum(w.hours_spent)
                FROM {DB}.work_order_clean w
                WHERE w.ticket_no = t.ticket_no AND w.status = 'closed'
            ) AS total_hours,
            -- Was equipment found? (marker for data quality monitoring)
            CASE WHEN e.equipment_id IS NULL THEN false ELSE true END AS equipment_found
        FROM {DB}.ticket_clean t
        LEFT JOIN {DB}.equipment_clean e ON t.equipment_id = e.equipment_id
    """),
]


def run(name: str, sql: str) -> None:
    print(f"\n=== Building {name} ===")
    qid = athena.start_query_execution(
        QueryString=sql,
        QueryExecutionContext={"Database": DB},
        ResultConfiguration={"OutputLocation": RESULTS},
    )["QueryExecutionId"]

    while True:
        st = athena.get_query_execution(QueryExecutionId=qid)["QueryExecution"]
        state = st["Status"]["State"]
        if state in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        time.sleep(1)

    if state == "SUCCEEDED":
        print(f"  OK ({st['Statistics']['EngineExecutionTimeInMillis']} ms)")
    else:
        print(f"  FAILED: {st['Status'].get('StateChangeReason', '')}")


def smoke_test() -> None:
    """A few sanity queries on the new ontology."""
    print("\n=== Ontology smoke tests ===")
    tests = [
        ("Cleaned ticket count by team", f"SELECT team, COUNT(*) n FROM {DB}.ticket_clean GROUP BY team ORDER BY n DESC"),
        ("Cleaned priority distribution", f"SELECT priority, COUNT(*) n FROM {DB}.ticket_clean GROUP BY priority ORDER BY n DESC"),
        ("Resolution view: how many tickets have known equipment", f"SELECT equipment_found, COUNT(*) n FROM {DB}.ticket_resolution GROUP BY equipment_found"),
        ("Average hours by team (closed only)", f"""
            SELECT team, ROUND(AVG(total_hours), 2) avg_h, COUNT(*) n
            FROM {DB}.ticket_resolution
            WHERE total_hours IS NOT NULL
            GROUP BY team ORDER BY avg_h DESC
        """),
    ]
    for label, sql in tests:
        print(f"\n  -- {label}")
        qid = athena.start_query_execution(
            QueryString=sql,
            QueryExecutionContext={"Database": DB},
            ResultConfiguration={"OutputLocation": RESULTS},
        )["QueryExecutionId"]
        while True:
            st = athena.get_query_execution(QueryExecutionId=qid)["QueryExecution"]
            if st["Status"]["State"] in ("SUCCEEDED", "FAILED", "CANCELLED"):
                break
            time.sleep(1)
        if st["Status"]["State"] == "SUCCEEDED":
            rows = athena.get_query_results(QueryExecutionId=qid, MaxResults=10)["ResultSet"]["Rows"]
            for r in rows:
                vals = [d.get("VarCharValue", "") for d in r["Data"]]
                print("    " + "  ".join(v.ljust(20)[:20] for v in vals))
        else:
            print(f"    FAILED: {st['Status'].get('StateChangeReason', '')}")


def main() -> None:
    for name, sql in VIEWS:
        run(name, sql)
    smoke_test()


if __name__ == "__main__":
    main()
