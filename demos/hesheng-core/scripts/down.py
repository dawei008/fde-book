"""`make down` — full teardown. Idempotent."""

from __future__ import annotations

import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from hesheng_core import config  # noqa: E402


def empty_and_delete_bucket(s3, name: str) -> None:
    try:
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=name):
            if "Contents" in page:
                s3.delete_objects(
                    Bucket=name,
                    Delete={"Objects": [{"Key": o["Key"]} for o in page["Contents"]]},
                )
        s3.delete_bucket(Bucket=name)
        print(f"  deleted: {name}")
    except ClientError as e:
        if e.response["Error"]["Code"] in ("NoSuchBucket", "404"):
            print(f"  no-op: {name}")
        else:
            raise


def main() -> None:
    try:
        cfg = config.load()
    except FileNotFoundError:
        print("Nothing to tear down — stack-outputs.json not present.")
        return

    print(f"Tearing down hesheng-core in {cfg.region} ...")

    glue = boto3.client("glue", region_name=cfg.region)
    s3 = boto3.client("s3", region_name=cfg.region)
    iam = boto3.client("iam", region_name=cfg.region)

    # Glue
    try:
        for t in glue.get_tables(DatabaseName=cfg.database)["TableList"]:
            glue.delete_table(DatabaseName=cfg.database, Name=t["Name"])
        glue.delete_database(Name=cfg.database)
        print(f"  deleted db: {cfg.database}")
    except ClientError as e:
        print(f"  db cleanup: {e.response['Error']['Code']}")

    # S3
    for b in [cfg.raw_bucket, cfg.athena_bucket, cfg.manuals_bucket]:
        empty_and_delete_bucket(s3, b)

    # IAM
    try:
        for p in iam.list_attached_role_policies(RoleName=cfg.role)["AttachedPolicies"]:
            iam.detach_role_policy(RoleName=cfg.role, PolicyArn=p["PolicyArn"])
        iam.delete_role(RoleName=cfg.role)
        print(f"  deleted role: {cfg.role}")
    except ClientError as e:
        print(f"  role cleanup: {e.response['Error']['Code']}")

    # Outputs file
    if config.STACK_OUTPUTS.exists():
        config.STACK_OUTPUTS.unlink()
        print(f"  removed: {config.STACK_OUTPUTS.name}")

    print("\nhesheng-core torn down.")


if __name__ == "__main__":
    main()
