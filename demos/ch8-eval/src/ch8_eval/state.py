"""ch8-eval state file. Holds AWS resource IDs created by `make up`
so that `make run` and `make down` can find them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

DEMO_DIR = Path(__file__).resolve().parents[2]
STATE_FILE = DEMO_DIR / "data" / "ch8-state.json"

# Resource names — single account per region OK; demo asserts uniqueness.
LAMBDA_NAME = "fde-book-ch8-fault-equivalence"
LAMBDA_ROLE = "fde-book-ch8-lambda-role"
EVALUATOR_NAME = "hesheng_fault_type_v1"


@dataclass
class State:
    region: str = ""
    account: str = ""
    lambda_role_arn: str = ""
    lambda_arn: str = ""
    evaluator_id: str = ""
    evaluator_arn: str = ""
    # If AgentCore CreateEvaluator path is unavailable in the account/region,
    # we fall back to invoking the Lambda directly. This flag records which
    # path was taken so the report can disclose it accurately.
    used_agentcore_register: bool = False
    register_failure_reason: str = ""

    @classmethod
    def load(cls) -> "State":
        if not STATE_FILE.exists():
            raise FileNotFoundError(f"No state file at {STATE_FILE}. Run `make up` first.")
        return cls(**json.loads(STATE_FILE.read_text()))

    @classmethod
    def load_or_empty(cls, region: str, account: str) -> "State":
        if STATE_FILE.exists():
            return cls(**json.loads(STATE_FILE.read_text()))
        return cls(region=region, account=account)

    def save(self) -> None:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(asdict(self), indent=2))
