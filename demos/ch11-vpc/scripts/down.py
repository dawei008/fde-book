"""ch11-vpc `make down` — tear down everything `up.py` created.

Order matters: Lambda first (it owns ENIs in our subnet), then endpoint
(also creates ENIs), then SG, then subnet, then VPC. Lambda ENI cleanup
is async on the AWS side and can take 30-90s; we poll until the SG is
free of ENIs before deleting it.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

DEMO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO_DIR / "src"))
sys.path.insert(0, str(DEMO_DIR.parent / "hesheng-core" / "src"))

from ch11_vpc.state import LAMBDA_NAME, LAMBDA_ROLE, STATE_FILE, State  # noqa: E402
from hesheng_core import config  # noqa: E402


def del_lambda(lam) -> None:
    try:
        lam.delete_function(FunctionName=LAMBDA_NAME)
        print(f"  deleted lambda: {LAMBDA_NAME}")
    except lam.exceptions.ResourceNotFoundException:
        print(f"  lambda already gone: {LAMBDA_NAME}")


def del_role(iam) -> None:
    try:
        for p in iam.list_attached_role_policies(RoleName=LAMBDA_ROLE)["AttachedPolicies"]:
            iam.detach_role_policy(RoleName=LAMBDA_ROLE, PolicyArn=p["PolicyArn"])
        for n in iam.list_role_policies(RoleName=LAMBDA_ROLE)["PolicyNames"]:
            iam.delete_role_policy(RoleName=LAMBDA_ROLE, PolicyName=n)
        iam.delete_role(RoleName=LAMBDA_ROLE)
        print(f"  deleted role: {LAMBDA_ROLE}")
    except iam.exceptions.NoSuchEntityException:
        print(f"  role already gone: {LAMBDA_ROLE}")


def del_endpoint(ec2, eid: str) -> None:
    if not eid:
        return
    try:
        ec2.delete_vpc_endpoints(VpcEndpointIds=[eid])
        for _ in range(40):
            d = ec2.describe_vpc_endpoints(VpcEndpointIds=[eid])
            if not d["VpcEndpoints"]:
                print(f"  deleted endpoint: {eid}")
                return
            st = d["VpcEndpoints"][0]["State"]
            if st in ("deleted", "DeleteFailed"):
                print(f"  endpoint final state: {st}")
                return
            time.sleep(3)
    except ClientError as e:
        print(f"  endpoint delete warn: {e}")


def wait_enis_drained(ec2, sg_id: str, subnet_id: str) -> None:
    """Lambda VPC ENIs are reclaimed asynchronously by the Lambda service
    and can linger 5-20 minutes after function deletion. Poll up to 25 min,
    and as a last resort try to force-detach + delete any 'available' ENIs
    (Lambda ENIs go through 'in-use' -> 'available' -> auto-deleted).
    """
    f = [{"Name": "group-id", "Values": [sg_id]}] if sg_id else \
        [{"Name": "subnet-id", "Values": [subnet_id]}]
    last_status = ""
    for i in range(250):  # 250 * 6s = 25 min cap
        enis = ec2.describe_network_interfaces(Filters=f)["NetworkInterfaces"]
        if not enis:
            return
        status = ",".join(sorted(set(e["Status"] for e in enis)))
        if status != last_status:
            print(f"  ENIs left: {len(enis)} ({status})")
            last_status = status
        # Once they go 'available', force-delete to skip the auto-reaper.
        for e in enis:
            if e["Status"] == "available":
                try:
                    ec2.delete_network_interface(
                        NetworkInterfaceId=e["NetworkInterfaceId"])
                    print(f"  force-deleted available ENI {e['NetworkInterfaceId']}")
                except ClientError as err:
                    print(f"  ENI delete warn: {err}")
        time.sleep(6)
    print("  warn: ENIs still present after 25 min — rerun `make down` later")


def del_sg(ec2, sg_id: str) -> bool:
    if not sg_id:
        return True
    for _ in range(5):
        try:
            ec2.delete_security_group(GroupId=sg_id)
            print(f"  deleted sg: {sg_id}")
            return True
        except ClientError as e:
            if "DependencyViolation" in str(e):
                time.sleep(15)
                continue
            if "InvalidGroup.NotFound" in str(e):
                return True
            print(f"  sg delete warn: {e}")
            return False
    print(f"  sg still has dependencies: {sg_id}")
    return False


def del_subnet(ec2, subnet_id: str) -> bool:
    if not subnet_id:
        return True
    for _ in range(5):
        try:
            ec2.delete_subnet(SubnetId=subnet_id)
            print(f"  deleted subnet: {subnet_id}")
            return True
        except ClientError as e:
            if "DependencyViolation" in str(e):
                time.sleep(15)
                continue
            if "InvalidSubnetID.NotFound" in str(e):
                return True
            print(f"  subnet delete warn: {e}")
            return False
    return False


def del_vpc(ec2, vpc_id: str) -> bool:
    if not vpc_id:
        return True
    for _ in range(5):
        try:
            ec2.delete_vpc(VpcId=vpc_id)
            print(f"  deleted vpc: {vpc_id}")
            return True
        except ClientError as e:
            if "DependencyViolation" in str(e):
                time.sleep(15)
                continue
            if "InvalidVpcID.NotFound" in str(e):
                return True
            print(f"  vpc delete warn: {e}")
            return False
    return False


def main() -> None:
    cfg = config.load()
    state = State.load_or_empty()

    ec2 = boto3.client("ec2", region_name=cfg.region)
    iam = boto3.client("iam", region_name=cfg.region)
    lam = boto3.client("lambda", region_name=cfg.region)

    print("[1/6] Lambda");          del_lambda(lam)
    print("[2/6] IAM role");        del_role(iam)
    print("[3/6] VPC endpoint");    del_endpoint(ec2, state.endpoint_id)
    print("[4/6] Wait ENIs drain"); wait_enis_drained(ec2, state.sg_id, state.subnet_id)
    print("[5/6] Security group"); ok_sg = del_sg(ec2, state.sg_id)
    print("[5/6] Subnet");         ok_sub = del_subnet(ec2, state.subnet_id)
    print("[6/6] VPC");            ok_vpc = del_vpc(ec2, state.vpc_id)

    if ok_sg and ok_sub and ok_vpc:
        if STATE_FILE.exists():
            STATE_FILE.unlink()
            print(f"  removed {STATE_FILE.name}")
    else:
        print("  state file kept — re-run `make down` after AWS reaps ENIs")
        sys.exit(2)


if __name__ == "__main__":
    main()
