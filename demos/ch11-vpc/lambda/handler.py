"""ch11-vpc Lambda handler. Lives in the private subnet (no NAT, no IGW).

The ONLY route to bedrock-runtime is via the VPC interface endpoint we
attach in `up.py`. That endpoint has a resource-policy that allow-lists
exactly one inference profile. So:

  - converse(haiku-4.5)  -> SUCCESS  (allowed by endpoint policy)
  - converse(opus-4.7)   -> AccessDeniedException at the endpoint layer

The Lambda's IAM role lets it call both models. The denial is purely
a network-perimeter concern, which is the Ch11 point.
"""

from __future__ import annotations

import json
import os

import boto3
from botocore.exceptions import ClientError


def handler(event, _ctx):
    model_id = event.get("model_id") or os.environ.get("DEFAULT_MODEL", "")
    region = os.environ.get("AWS_REGION", "us-east-1")

    # No endpoint_url override — boto3 resolves to bedrock-runtime.<region>
    # which, inside the VPC, is rewritten by the endpoint's PrivateDnsName
    # to the interface ENI in our private subnet.
    client = boto3.client("bedrock-runtime", region_name=region)

    try:
        resp = client.converse(
            modelId=model_id,
            messages=[{
                "role": "user",
                "content": [{"text": "Reply with exactly: VPC_OK"}],
            }],
            inferenceConfig={"maxTokens": 16, "temperature": 0.0},
        )
        text = resp["output"]["message"]["content"][0]["text"]
        return {
            "ok": True,
            "model_id": model_id,
            "response_text": text.strip(),
            "input_tokens": resp.get("usage", {}).get("inputTokens"),
            "output_tokens": resp.get("usage", {}).get("outputTokens"),
        }
    except ClientError as e:
        return {
            "ok": False,
            "model_id": model_id,
            "error_code": e.response.get("Error", {}).get("Code"),
            "error_message": str(e),
        }
    except Exception as e:  # noqa: BLE001
        return {
            "ok": False,
            "model_id": model_id,
            "error_code": type(e).__name__,
            "error_message": str(e),
        }


if __name__ == "__main__":
    # Local smoke test (would NOT exercise the VPC path).
    print(json.dumps(handler({"model_id": os.environ.get("MODEL_ID", "")}, None), indent=2))
