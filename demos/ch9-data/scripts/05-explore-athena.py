"""Explore the data through Athena — find the dirt.

This is what FDE does on day 3: write 5-6 SELECT queries that surface
every kind of dirty data, count it, and decide what cleanup pipeline
to build.

The queries here are meant to be both runnable AND read in the chapter.
Keep them small.
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


# Six exploratory queries, named by what they expose
QUERIES = {
    "Q1_total_counts": f"""
        SELECT 'equipment' tbl, COUNT(*) n FROM {DB}.equipment
        UNION ALL SELECT 'tickets', COUNT(*) FROM {DB}.tickets
        UNION ALL SELECT 'work_orders', COUNT(*) FROM {DB}.work_orders
    """,
    "Q2_timestamp_format_distribution": f"""
        SELECT
            CASE
                WHEN regexp_like(ts, '^\\d{{4}}-\\d{{2}}-\\d{{2}}T') THEN 'iso8601'
                WHEN regexp_like(ts, '^\\d{{4}}年') THEN 'cn_local_no_tz'
                WHEN regexp_like(ts, '^\\d{{10}}$') THEN 'unix_epoch'
                ELSE 'unknown'
            END AS fmt,
            COUNT(*) n
        FROM {DB}.tickets
        GROUP BY 1 ORDER BY n DESC
    """,
    "Q3_priority_naming_chaos": f"""
        SELECT priority, COUNT(*) n
        FROM {DB}.tickets
        GROUP BY priority ORDER BY n DESC
    """,
    "Q4_team_naming_chaos": f"""
        SELECT team, COUNT(*) n
        FROM {DB}.tickets
        GROUP BY team ORDER BY n DESC
    """,
    "Q5_broken_fk_to_equipment": f"""
        SELECT t.equipment_id, COUNT(*) tickets_with_unknown_eq
        FROM {DB}.tickets t
        LEFT JOIN {DB}.equipment e ON t.equipment_id = e.equipment_id
        WHERE e.equipment_id IS NULL
        GROUP BY t.equipment_id
        ORDER BY tickets_with_unknown_eq DESC
        LIMIT 10
    """,
    "Q6_part_id_format_variation": f"""
        SELECT
            CASE WHEN starts_with(part_id, 'PART-') THEN 'PART-prefix'
                 WHEN starts_with(part_id, 'P-') THEN 'P-prefix'
                 ELSE 'other' END AS fmt,
            COUNT(*) n
        FROM {DB}.work_orders
        GROUP BY 1
    """,
}


def run_query(name: str, sql: str) -> list[list[str]]:
    print(f"\n=== {name} ===")
    sql_clean = " ".join(sql.split())
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

    if state != "SUCCEEDED":
        print(f"  FAILED: {st['Status'].get('StateChangeReason', '')}")
        return []

    scanned_mb = st["Statistics"]["DataScannedInBytes"] / (1024 * 1024)
    elapsed_ms = st["Statistics"]["EngineExecutionTimeInMillis"]
    print(f"  scanned: {scanned_mb:.2f} MB | engine: {elapsed_ms} ms")

    # First page of results
    rows = athena.get_query_results(QueryExecutionId=qid, MaxResults=20)["ResultSet"]["Rows"]
    out = []
    for r in rows:
        out.append([d.get("VarCharValue", "") for d in r["Data"]])
    for r in out:
        print("    " + "  ".join(c.ljust(25)[:25] for c in r))
    return out


def main() -> None:
    print(f"Athena exploration on database {DB}")
    print(f"Results bucket: {RESULTS}")
    for name, sql in QUERIES.items():
        run_query(name, sql)


if __name__ == "__main__":
    main()
