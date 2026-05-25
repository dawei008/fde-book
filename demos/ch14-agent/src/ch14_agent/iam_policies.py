"""ch14-agent — IAM policy document factories.

Pulled out of aws_resources.py so the policy JSON doesn't dominate that
file. Three policy documents are generated here:

  - lambda_trust_policy()           — assume-role for Lambda service
  - gateway_trust_policy()          — assume-role for AgentCore Gateway
  - runtime_invoke_tools_policy()   — Lambda + Athena + S3 grants for the
                                       AgentCore Runtime CDK role
"""

from __future__ import annotations


def lambda_trust_policy() -> dict:
    return {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }],
    }


def gateway_trust_policy() -> dict:
    return {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }],
    }


def gateway_invoke_lambda_policy(region: str, account: str, lambda_name: str) -> dict:
    return {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": "lambda:InvokeFunction",
            "Resource": f"arn:aws:lambda:{region}:{account}:function:{lambda_name}",
        }],
    }


def runtime_invoke_tools_policy(cfg, lambda_arn: str) -> dict:
    return {
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow",
             "Action": ["lambda:InvokeFunction"],
             "Resource": lambda_arn},
            {"Effect": "Allow", "Action": [
                "athena:StartQueryExecution", "athena:GetQueryExecution",
                "athena:GetQueryResults", "athena:StopQueryExecution",
                "athena:GetWorkGroup",
                "glue:GetTable", "glue:GetTables", "glue:GetDatabase",
                "glue:GetDatabases", "glue:GetPartitions", "glue:GetPartition",
            ], "Resource": "*"},
            {"Effect": "Allow", "Action": [
                "s3:GetObject", "s3:PutObject", "s3:ListBucket",
                "s3:GetBucketLocation", "s3:HeadBucket",
            ], "Resource": [
                f"arn:aws:s3:::{cfg.raw_bucket}",
                f"arn:aws:s3:::{cfg.raw_bucket}/*",
                f"arn:aws:s3:::{cfg.athena_bucket}",
                f"arn:aws:s3:::{cfg.athena_bucket}/*",
                f"arn:aws:s3:::{cfg.manuals_bucket}",
                f"arn:aws:s3:::{cfg.manuals_bucket}/*",
            ]},
        ],
    }


def gateway_target_schema(lambda_arn: str) -> dict:
    """The targetConfiguration dict for CreateGatewayTarget MCP-Lambda type."""
    return {"mcp": {"lambda": {
        "lambdaArn": lambda_arn,
        "toolSchema": {"inlinePayload": [{
            "name": "lookup_alarm_code",
            "description": "Look up Hesheng alarm code meaning and team.",
            "inputSchema": {
                "type": "object",
                "properties": {"code": {"type": "string"}},
                "required": ["code"],
            },
        }]},
    }}}
