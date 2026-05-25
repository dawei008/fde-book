"""Ch7-rag state file: tracks the KB / OpenSearch / IAM resources we created.

Why a separate state file from hesheng-core/stack-outputs.json:
ch7-rag owns its own resources (KB, OpenSearch collection, KB role).
hesheng-core only owns the manuals bucket. Tearing down ch7-rag must
not touch hesheng-core state.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

DEMO_DIR = Path(__file__).resolve().parents[2]  # demos/ch7-rag
STATE_FILE = DEMO_DIR / "data" / "ch7-state.json"

KB_NAME = "fde-book-ch7-hesheng-manuals"
COLLECTION_NAME = "fde-book-ch7"  # OpenSearch Serverless name (<=32 chars, lowercase)
KB_ROLE = "fde-book-ch7-kb-role"
ENCRYPTION_POLICY = "fde-book-ch7-enc"
NETWORK_POLICY = "fde-book-ch7-net"
DATA_ACCESS_POLICY = "fde-book-ch7-data"
INDEX_NAME = "fde-book-ch7-index"


@dataclass
class State:
    region: str
    account: str
    kb_id: str | None = None
    data_source_id: str | None = None
    collection_id: str | None = None
    collection_arn: str | None = None
    collection_endpoint: str | None = None
    role_arn: str | None = None

    def save(self) -> None:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(asdict(self), indent=2))

    @classmethod
    def load(cls) -> "State":
        if not STATE_FILE.exists():
            raise FileNotFoundError(f"ch7-rag not initialized. Run `make up` first. Missing: {STATE_FILE}")
        return cls(**json.loads(STATE_FILE.read_text()))

    @classmethod
    def load_or_empty(cls, region: str, account: str) -> "State":
        if STATE_FILE.exists():
            return cls(**json.loads(STATE_FILE.read_text()))
        return cls(region=region, account=account)
