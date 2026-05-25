"""ch15-mcp state — per-run identifiers shared by up.py / run.py / down.py.

Saved to data/ch15-state.json after `make up`. run.py and down.py read it.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

DEMO_DIR = Path(__file__).resolve().parents[2]
STATE_FILE = DEMO_DIR / "data" / "ch15-state.json"

# Stable resource names (deterministic; one demo per account/region).
DDB_TABLE = "fde-book-ch15-ticket-context"
RUNTIME_NAME = "hesheng_ticket_mcp"
PROJECT_NAME = "ch15hesheng"
REGISTRY_NAME = "hesheng-mcp-registry"
RECORD_NAME = "hesheng-ticket-context-mcp"


@dataclass
class State:
    ddb_table_arn: str = ""
    runtime_arn: str = ""
    runtime_role_name: str = ""
    deploy_mode: str = "local"  # "local" or "agentcore-runtime"
    # Registry is best-effort (preview API; SCPs often block).
    registry_id: str = ""
    registry_arn: str = ""
    record_id: str = ""
    record_arn: str = ""
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
