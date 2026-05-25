"""Tear down everything created by steps 02-07.

Order matters — Glue resources must go before S3 buckets, IAM role last.
"""

from __future__ import annotations

import json
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

OUT = Path(__file__).resolve().parent.parent / "data" / "stack-outputs.json"
cfg = json.loads(OUT.read_text())
REGION = cfg["region"]

s3 = boto3.client("s3", region_name=REGION)
glue = boto3.client("glue", region_name=REGION)
iam = boto3.client("iam", region_name=REGION)


def empty_bucket(name: str) -> None:
    try:
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=name):
            if "Contents" in page:
                s3.delete_objects(
                    Bucket=name,
                    Delete={"Objects": [{"Key": o["Key"]} for o in page["Contents"]]},
                )
        print(f"  Emptied bucket {name}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchBucket":
            print(f"  Bucket {name} doesn't exist")
        else:
            raise


def delete_bucket(name: str) -> None:
    try:
        s3.delete_bucket(Bucket=name)
        print(f"  Deleted bucket {name}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchBucket":
            return
        raise


def main() -> None:
    print("Tearing down Ch9 demo...")

    # Glue
    try:
        glue.delete_crawler(Name=cfg["crawler"])
        print(f"  Deleted crawler {cfg['crawler']}")
    except ClientError:
        pass

    try:
        glue.delete_classifier(Name="fde-book-ch9-csv-quoted")
        print("  Deleted classifier fde-book-ch9-csv-quoted")
    except ClientError:
        pass

    try:
        # Drop all tables in db
        for t in glue.get_tables(DatabaseName=cfg["database"])["TableList"]:
            glue.delete_table(DatabaseName=cfg["database"], Name=t["Name"])
        glue.delete_database(Name=cfg["database"])
        print(f"  Deleted database {cfg['database']}")
    except ClientError:
        pass

    # S3
    for b in [cfg["raw_bucket"], cfg["athena_bucket"], cfg.get("kb_bucket", "")]:
        if not b:
            continue
        empty_bucket(b)
        delete_bucket(b)

    # IAM (detach policies first)
    role = cfg["role"]
    try:
        for p in iam.list_attached_role_policies(RoleName=role)["AttachedPolicies"]:
            iam.detach_role_policy(RoleName=role, PolicyArn=p["PolicyArn"])
        iam.delete_role(RoleName=role)
        print(f"  Deleted role {role}")
    except ClientError as e:
        print(f"  Role cleanup: {e.response['Error']['Code']}")

    print("\nTeardown complete.")


if __name__ == "__main__":
    main()
