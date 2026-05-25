"""ch11-vpc `make up` — VPC (no IGW/NAT) + private subnet + SG +
bedrock-runtime interface endpoint with a policy that allow-lists only
haiku-4.5 + Lambda in the subnet. Idempotent via data/ch11-state.json.
"""
from __future__ import annotations

import io
import json
import sys
import time
import zipfile
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

DEMO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO_DIR / "src"))
sys.path.insert(0, str(DEMO_DIR.parent / "hesheng-core" / "src"))

from ch11_vpc.state import (  # noqa: E402
    LAMBDA_NAME, LAMBDA_ROLE, NAME_TAG, State, SUBNET_CIDR, VPC_CIDR,
    endpoint_policy_doc,
)
from hesheng_core import config  # noqa: E402

TAGS = [{"Key": "Project", "Value": "fde-book"},
        {"Key": "Demo", "Value": "ch11-vpc"}]


def tag(ec2, rid: str, suffix: str) -> None:
    ec2.create_tags(Resources=[rid],
                    Tags=TAGS + [{"Key": "Name", "Value": f"{NAME_TAG}-{suffix}"}])


def ensure_vpc(ec2, state: State) -> None:
    if state.vpc_id:
        try:
            ec2.describe_vpcs(VpcIds=[state.vpc_id])
            print(f"  vpc already present: {state.vpc_id}"); return
        except ClientError:
            state.vpc_id = ""
    state.vpc_id = ec2.create_vpc(CidrBlock=VPC_CIDR)["Vpc"]["VpcId"]
    ec2.modify_vpc_attribute(VpcId=state.vpc_id, EnableDnsSupport={"Value": True})
    ec2.modify_vpc_attribute(VpcId=state.vpc_id, EnableDnsHostnames={"Value": True})
    tag(ec2, state.vpc_id, "vpc")
    print(f"  created vpc: {state.vpc_id}")


def ensure_subnet(ec2, state: State, region: str) -> None:
    if state.subnet_id:
        try:
            ec2.describe_subnets(SubnetIds=[state.subnet_id])
            print(f"  subnet already present: {state.subnet_id}"); return
        except ClientError:
            state.subnet_id = ""
    s = ec2.create_subnet(VpcId=state.vpc_id, CidrBlock=SUBNET_CIDR,
                          AvailabilityZone=f"{region}a")["Subnet"]
    state.subnet_id = s["SubnetId"]
    tag(ec2, state.subnet_id, "subnet-private")
    rts = ec2.describe_route_tables(
        Filters=[{"Name": "vpc-id", "Values": [state.vpc_id]}])["RouteTables"]
    state.route_table_id = rts[0]["RouteTableId"]
    print(f"  created subnet: {state.subnet_id}")


def ensure_sg(ec2, state: State) -> None:
    if state.sg_id:
        try:
            ec2.describe_security_groups(GroupIds=[state.sg_id])
            print(f"  sg already present: {state.sg_id}"); return
        except ClientError:
            state.sg_id = ""
    state.sg_id = ec2.create_security_group(
        VpcId=state.vpc_id, GroupName=f"{NAME_TAG}-sg",
        Description="ch11 demo self-ref 443 for Lambda to endpoint")["GroupId"]
    tag(ec2, state.sg_id, "sg")
    ec2.authorize_security_group_ingress(GroupId=state.sg_id, IpPermissions=[{
        "IpProtocol": "tcp", "FromPort": 443, "ToPort": 443,
        "UserIdGroupPairs": [{"GroupId": state.sg_id}]}])
    print(f"  created sg: {state.sg_id} (self -> self :443)")


def ensure_endpoint(ec2, state: State, region: str, account: str) -> None:
    if state.endpoint_id:
        try:
            ec2.describe_vpc_endpoints(VpcEndpointIds=[state.endpoint_id])
            print(f"  endpoint already present: {state.endpoint_id}"); return
        except ClientError:
            state.endpoint_id = ""
    e = ec2.create_vpc_endpoint(
        VpcEndpointType="Interface", VpcId=state.vpc_id,
        ServiceName=f"com.amazonaws.{region}.bedrock-runtime",
        SubnetIds=[state.subnet_id], SecurityGroupIds=[state.sg_id],
        PrivateDnsEnabled=True,
        PolicyDocument=json.dumps(endpoint_policy_doc(account)),
        TagSpecifications=[{"ResourceType": "vpc-endpoint",
                            "Tags": TAGS + [{"Key": "Name",
                                "Value": f"{NAME_TAG}-bedrock-endpoint"}]}],
    )["VpcEndpoint"]
    state.endpoint_id = e["VpcEndpointId"]
    state.endpoint_policy_mode = "modelid-restricted"
    print(f"  created vpc endpoint: {state.endpoint_id} (policy: haiku-only)")
    for _ in range(40):
        st = ec2.describe_vpc_endpoints(
            VpcEndpointIds=[state.endpoint_id])["VpcEndpoints"][0]["State"]
        if st == "available":
            print("  endpoint available"); return
        time.sleep(3)
    raise RuntimeError("endpoint did not become available in 120s")


def ensure_lambda_role(iam, state: State) -> None:
    trust = {"Version": "2012-10-17", "Statement": [{
        "Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"},
        "Action": "sts:AssumeRole"}]}
    try:
        r = iam.get_role(RoleName=LAMBDA_ROLE)
        state.lambda_role_arn = r["Role"]["Arn"]
        print(f"  role already present: {LAMBDA_ROLE}")
    except iam.exceptions.NoSuchEntityException:
        r = iam.create_role(RoleName=LAMBDA_ROLE,
                            AssumeRolePolicyDocument=json.dumps(trust),
                            Description="ch11-vpc lambda execution role")
        state.lambda_role_arn = r["Role"]["Arn"]
        print(f"  created role: {state.lambda_role_arn}")
    iam.attach_role_policy(RoleName=LAMBDA_ROLE, PolicyArn=(
        "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"))
    # IAM allows BOTH haiku and opus, so denial of opus can ONLY come from
    # the endpoint policy. That's the demo.
    iam.put_role_policy(RoleName=LAMBDA_ROLE, PolicyName="bedrock-converse",
        PolicyDocument=json.dumps({"Version": "2012-10-17", "Statement": [{
            "Effect": "Allow", "Resource": "*",
            "Action": ["bedrock:InvokeModel",
                       "bedrock:InvokeModelWithResponseStream",
                       "bedrock:Converse", "bedrock:ConverseStream"]}]}))


def package_lambda() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("handler.py", (DEMO_DIR / "lambda" / "handler.py").read_bytes())
    return buf.getvalue()


def ensure_lambda(lam, state: State) -> None:
    code = package_lambda()
    vpc = {"SubnetIds": [state.subnet_id], "SecurityGroupIds": [state.sg_id]}
    try:
        f = lam.get_function(FunctionName=LAMBDA_NAME)
        state.lambda_arn = f["Configuration"]["FunctionArn"]
        lam.update_function_code(FunctionName=LAMBDA_NAME, ZipFile=code)
        lam.get_waiter("function_updated").wait(FunctionName=LAMBDA_NAME)
        lam.update_function_configuration(FunctionName=LAMBDA_NAME, VpcConfig=vpc)
        lam.get_waiter("function_updated").wait(FunctionName=LAMBDA_NAME)
        print(f"  lambda already present, updated: {state.lambda_arn}")
        return
    except lam.exceptions.ResourceNotFoundException:
        pass
    # Role propagation can race with Lambda — retry on InvalidParameterValue.
    for _ in range(10):
        try:
            f = lam.create_function(
                FunctionName=LAMBDA_NAME, Runtime="python3.12",
                Role=state.lambda_role_arn, Handler="handler.handler",
                Code={"ZipFile": code}, Timeout=30, MemorySize=256,
                VpcConfig=vpc, Tags={"Project": "fde-book", "Demo": "ch11-vpc"})
            state.lambda_arn = f["FunctionArn"]
            print(f"  created lambda: {state.lambda_arn}")
            break
        except ClientError as e:
            if "cannot be assumed" in str(e) or "InvalidParameterValueException" in str(e):
                time.sleep(5); continue
            raise
    lam.get_waiter("function_active_v2").wait(FunctionName=LAMBDA_NAME)


def main() -> None:
    cfg = config.load()
    print(f"region={cfg.region} account={cfg.account}")
    state = State.load_or_empty()
    ec2 = boto3.client("ec2", region_name=cfg.region)
    iam = boto3.client("iam", region_name=cfg.region)
    lam = boto3.client("lambda", region_name=cfg.region)
    print("[1/5] VPC");          ensure_vpc(ec2, state); state.save()
    print("[2/5] Subnet");       ensure_subnet(ec2, state, cfg.region); state.save()
    print("[3/5] Security group"); ensure_sg(ec2, state); state.save()
    print("[4/5] Bedrock endpoint"); ensure_endpoint(ec2, state, cfg.region, cfg.account); state.save()
    print("[5/5] Lambda role + function")
    ensure_lambda_role(iam, state); state.save()
    ensure_lambda(lam, state); state.save()
    print("\nState saved:")
    for k, v in state.__dict__.items():
        if isinstance(v, str) and v:
            print(f"  {k:24s} = {v}")


if __name__ == "__main__":
    main()
