"""Verify all ch11-vpc resources are gone."""

from __future__ import annotations

import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

DEMO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO_DIR / "src"))
sys.path.insert(0, str(DEMO_DIR.parent / "hesheng-core" / "src"))

from ch11_vpc.state import LAMBDA_NAME, LAMBDA_ROLE, NAME_TAG, VPC_CIDR  # noqa: E402
from hesheng_core import config  # noqa: E402


def main() -> None:
    cfg = config.load()
    leftover: list[str] = []

    ec2 = boto3.client("ec2", region_name=cfg.region)
    iam = boto3.client("iam", region_name=cfg.region)
    lam = boto3.client("lambda", region_name=cfg.region)

    try:
        lam.get_function(FunctionName=LAMBDA_NAME)
        leftover.append(f"Lambda still present: {LAMBDA_NAME}")
    except lam.exceptions.ResourceNotFoundException:
        pass

    try:
        iam.get_role(RoleName=LAMBDA_ROLE)
        leftover.append(f"IAM role still present: {LAMBDA_ROLE}")
    except iam.exceptions.NoSuchEntityException:
        pass

    vpcs = ec2.describe_vpcs(Filters=[
        {"Name": "cidr", "Values": [VPC_CIDR]},
        {"Name": "tag:Demo", "Values": ["ch11-vpc"]},
    ])["Vpcs"]
    if vpcs:
        leftover.append(f"VPC still present: {vpcs[0]['VpcId']}")

    eps = ec2.describe_vpc_endpoints(Filters=[
        {"Name": "tag:Demo", "Values": ["ch11-vpc"]},
    ])["VpcEndpoints"]
    if eps:
        leftover.append(f"VPC endpoint still present: {eps[0]['VpcEndpointId']}")

    if leftover:
        print("LEFTOVERS DETECTED:")
        for l in leftover:
            print(f"  - {l}")
        sys.exit(1)
    print("Clean. No ch11-vpc resources remain.")


if __name__ == "__main__":
    main()
