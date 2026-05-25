"""Set up AWS resources for the Ch9 demo.

Creates (in us-east-1):
- S3 bucket: fde-book-ch9-{account}-raw
- Athena query results bucket: fde-book-ch9-{account}-athena
- Glue database: fde_book_ch9_raw
- Glue Crawler that reads s3://...-raw/ and registers tables

Idempotent — safe to re-run.

Run from repo root:
    python demos/ch9-data/scripts/02-setup-aws.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"
sts = boto3.client("sts", region_name=REGION)
ACCOUNT = sts.get_caller_identity()["Account"]

RAW_BUCKET = f"fde-book-ch9-{ACCOUNT}-raw"
ATHENA_BUCKET = f"fde-book-ch9-{ACCOUNT}-athena"
DB_NAME = "fde_book_ch9_raw"
CRAWLER_NAME = "fde-book-ch9-crawler"
ROLE_NAME = "fde-book-ch9-glue-role"

s3 = boto3.client("s3", region_name=REGION)
glue = boto3.client("glue", region_name=REGION)
iam = boto3.client("iam", region_name=REGION)


def create_bucket(name: str) -> None:
    try:
        s3.head_bucket(Bucket=name)
        print(f"  S3 bucket {name} exists")
    except ClientError as e:
        if e.response["Error"]["Code"] in ("404", "NoSuchBucket"):
            s3.create_bucket(Bucket=name)  # us-east-1 doesn't take LocationConstraint
            print(f"  Created S3 bucket {name}")
        else:
            raise


def create_glue_role() -> str:
    trust = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "glue.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }
    try:
        r = iam.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust),
            Description="Glue role for FDE book Ch9 demo",
        )
        print(f"  Created IAM role {ROLE_NAME}")
        arn = r["Role"]["Arn"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "EntityAlreadyExists":
            arn = iam.get_role(RoleName=ROLE_NAME)["Role"]["Arn"]
            print(f"  IAM role {ROLE_NAME} exists")
        else:
            raise

    # Attach managed policies
    for policy in [
        "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole",
        "arn:aws:iam::aws:policy/AmazonS3FullAccess",
    ]:
        try:
            iam.attach_role_policy(RoleName=ROLE_NAME, PolicyArn=policy)
        except ClientError:
            pass  # already attached
    return arn


def create_glue_database() -> None:
    try:
        glue.create_database(DatabaseInput={"Name": DB_NAME})
        print(f"  Created Glue database {DB_NAME}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "AlreadyExistsException":
            print(f"  Glue database {DB_NAME} exists")
        else:
            raise


def upload_data() -> None:
    raw_dir = Path(__file__).resolve().parent.parent / "data" / "raw"
    if not raw_dir.exists():
        print(f"  ERR: {raw_dir} doesn't exist. Run 01-generate-data.py first.")
        sys.exit(1)

    for f in raw_dir.glob("*.csv"):
        # Use folder-per-table layout so Glue Crawler creates one table per folder
        table_name = f.stem  # equipment / tickets / work_orders
        key = f"raw/{table_name}/{f.name}"
        s3.upload_file(str(f), RAW_BUCKET, key)
        print(f"  Uploaded {f.name} -> s3://{RAW_BUCKET}/{key}")


def create_crawler(role_arn: str) -> None:
    targets = {
        "S3Targets": [
            {"Path": f"s3://{RAW_BUCKET}/raw/equipment/"},
            {"Path": f"s3://{RAW_BUCKET}/raw/tickets/"},
            {"Path": f"s3://{RAW_BUCKET}/raw/work_orders/"},
        ]
    }
    try:
        glue.create_crawler(
            Name=CRAWLER_NAME,
            Role=role_arn,
            DatabaseName=DB_NAME,
            Targets=targets,
            SchemaChangePolicy={
                "UpdateBehavior": "UPDATE_IN_DATABASE",
                "DeleteBehavior": "LOG",
            },
        )
        print(f"  Created Glue crawler {CRAWLER_NAME}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "AlreadyExistsException":
            glue.update_crawler(
                Name=CRAWLER_NAME,
                Role=role_arn,
                DatabaseName=DB_NAME,
                Targets=targets,
            )
            print(f"  Updated Glue crawler {CRAWLER_NAME}")
        else:
            raise


def run_crawler() -> None:
    print("\nRunning crawler ...")
    glue.start_crawler(Name=CRAWLER_NAME)
    while True:
        r = glue.get_crawler(Name=CRAWLER_NAME)
        state = r["Crawler"]["State"]
        print(f"  state: {state}", flush=True)
        if state == "READY":
            break
        time.sleep(10)
    last = r["Crawler"].get("LastCrawl", {})
    print(f"  status: {last.get('Status')}, tables: {last.get('TablesCreated', 0)} created, {last.get('TablesUpdated', 0)} updated")


def show_tables() -> None:
    print("\nTables registered in Glue Data Catalog:")
    for t in glue.get_tables(DatabaseName=DB_NAME)["TableList"]:
        cols = t["StorageDescriptor"]["Columns"]
        print(f"  {t['Name']}: {len(cols)} columns")
        for c in cols:
            print(f"    {c['Name']}: {c['Type']}")
        print()


def write_outputs() -> None:
    out = {
        "region": REGION,
        "account": ACCOUNT,
        "raw_bucket": RAW_BUCKET,
        "athena_bucket": ATHENA_BUCKET,
        "database": DB_NAME,
        "crawler": CRAWLER_NAME,
        "role": ROLE_NAME,
    }
    p = Path(__file__).resolve().parent.parent / "data" / "stack-outputs.json"
    p.write_text(json.dumps(out, indent=2))
    print(f"\nStack outputs -> {p}")


def main() -> None:
    print(f"Setting up Ch9 demo in account {ACCOUNT} region {REGION}\n")
    create_bucket(RAW_BUCKET)
    create_bucket(ATHENA_BUCKET)
    role_arn = create_glue_role()
    print("Waiting 10s for IAM role to propagate ...")
    time.sleep(10)
    create_glue_database()
    upload_data()
    create_crawler(role_arn)
    run_crawler()
    show_tables()
    write_outputs()


if __name__ == "__main__":
    main()
