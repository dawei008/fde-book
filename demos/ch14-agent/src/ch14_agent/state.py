"""ch14-agent state — per-run identifiers shared by up.py / run.py / down.py.

Saved to data/ch14-state.json after `make up`. run.py and down.py read it.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

DEMO_DIR = Path(__file__).resolve().parents[2]
STATE_FILE = DEMO_DIR / "data" / "ch14-state.json"

# Stable resource names (deterministic; one demo per account/region).
LAMBDA_NAME = "fde-book-ch14-alarm-tool"
LAMBDA_ROLE = "fde-book-ch14-lambda-role"
GATEWAY_NAME = "hesheng-data-gateway"
RUNTIME_NAME = "ch14_hesheng_agent"
PROJECT_NAME = "ch14hesheng"


@dataclass
class State:
    lambda_arn: str = ""
    lambda_role_arn: str = ""
    # Gateway / Runtime are best-effort; empty string means "not deployed".
    gateway_arn: str = ""
    gateway_url: str = ""
    runtime_arn: str = ""
    runtime_endpoint: str = ""
    deploy_mode: str = "local"  # "local" or "agentcore-runtime"
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
