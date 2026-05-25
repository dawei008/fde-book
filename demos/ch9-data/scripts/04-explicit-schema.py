"""When Glue Crawler can't infer headers, register schema explicitly.

This is what FDE actually does in real projects: Glue Crawler is a
30-minute exploration tool, not the production schema source. For
anything with non-trivial CSV (quoted commas, embedded newlines,
Chinese text), you write the schema yourself. boto3 + Glue API
takes 20 lines.

We delete the bad auto-generated tickets and work_orders tables and
re-create them with the correct schema using LazySimpleSerDe options
that handle quoted CSV properly (well — properly enough; Athena's
OpenCSVSerDe is the right SerDe for quoted CSV with embedded commas).
"""

from __future__ import annotations

import json
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

OUT = Path(__file__).resolve().parent.parent / "data" / "stack-outputs.json"
cfg = json.loads(OUT.read_text())
glue = boto3.client("glue", region_name=cfg["region"])

DB = cfg["database"]
RAW = cfg["raw_bucket"]


def make_table(name: str, columns: list[tuple[str, str]]) -> dict:
    return {
        "Name": name,
        "StorageDescriptor": {
            "Columns": [{"Name": c, "Type": t} for c, t in columns],
            "Location": f"s3://{RAW}/raw/{name}/",
            "InputFormat": "org.apache.hadoop.mapred.TextInputFormat",
            "OutputFormat": "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
            "SerdeInfo": {
                "SerializationLibrary": "org.apache.hadoop.hive.serde2.OpenCSVSerde",
                "Parameters": {
                    "separatorChar": ",",
                    "quoteChar": '"',
                    "escapeChar": "\\",
                },
            },
        },
        "TableType": "EXTERNAL_TABLE",
        "Parameters": {
            "classification": "csv",
            "skip.header.line.count": "1",  # Athena/Glue convention
        },
    }


TABLES = {
    "tickets": [
        ("ticket_no", "string"),
        ("ts", "string"),
        ("equipment_id", "string"),
        ("fault_desc", "string"),
        ("alarm_code", "string"),
        ("priority", "string"),
        ("reporter_phone", "string"),
        ("team", "string"),
    ],
    "work_orders": [
        ("wo_id", "string"),
        ("ticket_no", "string"),
        ("engineer_id", "string"),
        ("part_id", "string"),
        ("hours_spent", "string"),
        ("status", "string"),
        ("completed_at", "string"),
    ],
}


def upsert_table(name: str, columns: list[tuple[str, str]]) -> None:
    table_input = make_table(name, columns)
    try:
        glue.delete_table(DatabaseName=DB, Name=name)
        print(f"  Deleted existing {name}")
    except ClientError:
        pass

    glue.create_table(DatabaseName=DB, TableInput=table_input)
    print(f"  Created table {name} with {len(columns)} columns + OpenCSVSerde")


def main() -> None:
    for name, cols in TABLES.items():
        upsert_table(name, cols)
    print("\nFinal table list:")
    for t in glue.get_tables(DatabaseName=DB)["TableList"]:
        ncols = len(t["StorageDescriptor"]["Columns"])
        print(f"  {t['Name']}: {ncols} columns")


if __name__ == "__main__":
    main()
