"""ch11-vpc state — resource IDs shared by up.py / run.py / down.py.

Saved to data/ch11-state.json after `make up`. Used by run.py to invoke
the Lambda, and by down.py to tear everything down deterministically.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

DEMO_DIR = Path(__file__).resolve().parents[2]
STATE_FILE = DEMO_DIR / "data" / "ch11-state.json"

# Stable resource names (deterministic; one demo per account/region).
VPC_CIDR = "10.99.0.0/16"
SUBNET_CIDR = "10.99.1.0/24"
NAME_TAG = "fde-book-ch11"
LAMBDA_NAME = "fde-book-ch11-bedrock-caller"
LAMBDA_ROLE = "fde-book-ch11-lambda-role"

# The whole point of the demo: ALLOWED is callable, DENIED is blocked at
# the VPC endpoint policy layer (not at IAM).
ALLOWED_MODEL = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
DENIED_MODEL = "us.anthropic.claude-opus-4-7"


def endpoint_policy_doc(account: str) -> dict:
    """Endpoint policy: allow Converse against the haiku-4.5 inference
    profile (and the FMs it routes to). Anything else gets an implicit
    deny at the endpoint, which surfaces to the SDK as AccessDenied with
    "no VPC endpoint policy allows ..." in the message.
    """
    return {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "AllowOnlyHaiku45",
            "Effect": "Allow",
            "Principal": "*",
            "Action": ["bedrock:InvokeModel",
                       "bedrock:InvokeModelWithResponseStream",
                       "bedrock:Converse", "bedrock:ConverseStream"],
            "Resource": [
                f"arn:aws:bedrock:*:{account}:inference-profile/{ALLOWED_MODEL}",
                "arn:aws:bedrock:*::foundation-model/"
                "anthropic.claude-haiku-4-5-20251001-v1:0",
            ],
        }],
    }


@dataclass
class State:
    vpc_id: str = ""
    subnet_id: str = ""
    sg_id: str = ""
    route_table_id: str = ""
    endpoint_id: str = ""
    endpoint_policy_mode: str = ""  # "modelid-restricted" or "open"
    lambda_arn: str = ""
    lambda_role_arn: str = ""
    notes: list[str] = field(default_factory=list)

    def save(self) -> None:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(asdict(self), indent=2))

    @classmethod
    def load(cls) -> "State":
        if not STATE_FILE.exists():
            raise FileNotFoundError(
                f"No state file. Run `make up` first.\nExpected: {STATE_FILE}"
            )
        raw = json.loads(STATE_FILE.read_text())
        return cls(**raw)

    @classmethod
    def load_or_empty(cls) -> "State":
        if STATE_FILE.exists():
            return cls.load()
        return cls()
