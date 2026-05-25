"""`make up` — bring core resources online.

Idempotent: re-running is safe. Resources created:
- 3 S3 buckets (raw / athena results / manuals)
- IAM role for Glue
- Glue database + 3 EXTERNAL TABLES with explicit OpenCSVSerde
  (we skip Glue Crawler because the original ch9 demo showed it fails
  on Chinese fault_desc with embedded commas — explicit schema is
  more reliable for this dataset)
- 4 Athena views (the Hesheng ontology)
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

# Make the in-tree package importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from hesheng_core import config, ontology  # noqa: E402

CORE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = CORE_DIR / "data" / "raw"
MANUALS_DIR = CORE_DIR / "manuals"


def main() -> None:
    sts = boto3.client("sts")
    account = sts.get_caller_identity()["Account"]
    cfg = config.derive(account=account)
    print(f"Bringing up hesheng-core in {cfg.region} / account {account}")

    s3 = boto3.client("s3", region_name=cfg.region)
    iam = boto3.client("iam", region_name=cfg.region)
    glue = boto3.client("glue", region_name=cfg.region)

    # 1. Buckets
    for b in [cfg.raw_bucket, cfg.athena_bucket, cfg.manuals_bucket]:
        try:
            s3.head_bucket(Bucket=b)
            print(f"  bucket exists: {b}")
        except ClientError:
            s3.create_bucket(Bucket=b)
            print(f"  created bucket: {b}")

    # 2. IAM role
    trust = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "glue.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }],
    }
    try:
        iam.create_role(
            RoleName=cfg.role,
            AssumeRolePolicyDocument=json.dumps(trust),
            Description="Glue role for FDE book Hesheng demos",
        )
        print(f"  created role: {cfg.role}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "EntityAlreadyExists":
            print(f"  role exists: {cfg.role}")
        else:
            raise
    for p in [
        "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole",
        "arn:aws:iam::aws:policy/AmazonS3FullAccess",
    ]:
        try:
            iam.attach_role_policy(RoleName=cfg.role, PolicyArn=p)
        except ClientError:
            pass
    time.sleep(8)  # IAM propagation

    # 3. Generate + upload data
    if not (RAW_DIR / "equipment.csv").exists():
        print("  generating synthetic CSVs ...")
        from generate_data import main as gen
        gen()
    for f in RAW_DIR.glob("*.csv"):
        key = f"raw/{f.stem}/{f.name}"
        s3.upload_file(str(f), cfg.raw_bucket, key)
        print(f"  uploaded {f.name} -> s3://{cfg.raw_bucket}/{key}")

    # 4. Manuals (used by Ch7 / Ch9.7)
    if MANUALS_DIR.exists() and any(MANUALS_DIR.iterdir()):
        for f in MANUALS_DIR.glob("*.md"):
            s3.upload_file(str(f), cfg.manuals_bucket, f"manuals/{f.name}")
            print(f"  uploaded {f.name} -> s3://{cfg.manuals_bucket}/manuals/{f.name}")

    # 5. Glue database + tables (explicit schema)
    try:
        glue.create_database(DatabaseInput={"Name": cfg.database})
        print(f"  created db: {cfg.database}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "AlreadyExistsException":
            print(f"  db exists: {cfg.database}")
        else:
            raise

    TABLES = {
        "equipment": [
            ("equipment_id", "string"), ("model", "string"),
            ("site", "string"), ("service_year", "string"),
            ("power_rating", "string"), ("last_maintained", "string"),
            ("customer_id", "string"),
        ],
        "tickets": [
            ("ticket_no", "string"), ("ts", "string"),
            ("equipment_id", "string"), ("fault_desc", "string"),
            ("alarm_code", "string"), ("priority", "string"),
            ("reporter_phone", "string"), ("team", "string"),
        ],
        "work_orders": [
            ("wo_id", "string"), ("ticket_no", "string"),
            ("engineer_id", "string"), ("part_id", "string"),
            ("hours_spent", "string"), ("status", "string"),
            ("completed_at", "string"),
        ],
    }

    def make_table(name: str, columns: list[tuple[str, str]]) -> dict:
        return {
            "Name": name,
            "StorageDescriptor": {
                "Columns": [{"Name": c, "Type": t} for c, t in columns],
                "Location": f"s3://{cfg.raw_bucket}/raw/{name}/",
                "InputFormat": "org.apache.hadoop.mapred.TextInputFormat",
                "OutputFormat": "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
                "SerdeInfo": {
                    "SerializationLibrary": "org.apache.hadoop.hive.serde2.OpenCSVSerde",
                    "Parameters": {"separatorChar": ",", "quoteChar": '"', "escapeChar": "\\"},
                },
            },
            "TableType": "EXTERNAL_TABLE",
            "Parameters": {"classification": "csv", "skip.header.line.count": "1"},
        }

    for name, cols in TABLES.items():
        try:
            glue.delete_table(DatabaseName=cfg.database, Name=name)
        except ClientError:
            pass
        glue.create_table(DatabaseName=cfg.database, TableInput=make_table(name, cols))
        print(f"  created table: {name} ({len(cols)} cols)")

    # 6. Persist config so chapter demos can find resources
    config.write(cfg)
    print(f"\n  stack-outputs.json -> {config.STACK_OUTPUTS}")

    # 7. Ontology views
    print("\nCreating ontology views ...")
    from hesheng_core import athena
    for name, sql in ontology.all_view_specs(cfg.database):
        athena.create_view(cfg, name, sql)
        print(f"  view ready: {name}")

    print("\nhesheng-core is up. Run `make smoke` to verify.")


if __name__ == "__main__":
    main()
