"""Resolve the AWS resource names used across chapter demos.

A chapter demo uses:

    from hesheng_core import config
    cfg = config.load()
    print(cfg.raw_bucket, cfg.database)

The config is the bridge between `make up` (which creates resources
and writes stack-outputs.json) and chapter demos (which read it).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

# Default region for the entire FDE book demos; override via FDE_BOOK_REGION
DEFAULT_REGION = os.environ.get("FDE_BOOK_REGION", "us-east-1")

CORE_DIR = Path(__file__).resolve().parents[2]  # demos/hesheng-core
STACK_OUTPUTS = CORE_DIR / "data" / "stack-outputs.json"


@dataclass(frozen=True)
class Config:
    region: str
    account: str
    raw_bucket: str
    athena_bucket: str
    manuals_bucket: str
    database: str
    crawler: str
    role: str

    @property
    def athena_results_uri(self) -> str:
        return f"s3://{self.athena_bucket}/results/"


def load(path: Path | None = None) -> Config:
    """Read stack-outputs.json. Raises FileNotFoundError if `make up` hasn't run."""
    p = path or STACK_OUTPUTS
    if not p.exists():
        raise FileNotFoundError(
            f"hesheng-core not initialized. Run `make up` from demos/hesheng-core/ first.\n"
            f"Expected: {p}"
        )
    raw = json.loads(p.read_text())
    return Config(
        region=raw["region"],
        account=raw["account"],
        raw_bucket=raw["raw_bucket"],
        athena_bucket=raw["athena_bucket"],
        manuals_bucket=raw["manuals_bucket"],
        database=raw["database"],
        crawler=raw["crawler"],
        role=raw["role"],
    )


def write(c: Config) -> None:
    """Used by setup script, not by chapter demos."""
    STACK_OUTPUTS.parent.mkdir(parents=True, exist_ok=True)
    STACK_OUTPUTS.write_text(json.dumps({
        "region": c.region,
        "account": c.account,
        "raw_bucket": c.raw_bucket,
        "athena_bucket": c.athena_bucket,
        "manuals_bucket": c.manuals_bucket,
        "database": c.database,
        "crawler": c.crawler,
        "role": c.role,
    }, indent=2))


def derive(account: str, region: str = DEFAULT_REGION) -> Config:
    """Compute resource names from account+region. Used by setup."""
    return Config(
        region=region,
        account=account,
        raw_bucket=f"fde-book-hesheng-{account}-raw",
        athena_bucket=f"fde-book-hesheng-{account}-athena",
        manuals_bucket=f"fde-book-hesheng-{account}-manuals",
        database="fde_book_hesheng",
        crawler="fde-book-hesheng-crawler",
        role="fde-book-hesheng-glue-role",
    )
