"""`make smoke` — run a few queries to confirm core is healthy."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from hesheng_core import athena, config, ontology  # noqa: E402


CHECKS = [
    ("row counts", "SELECT 'equipment' tbl, COUNT(*) n FROM equipment "
                   "UNION ALL SELECT 'tickets', COUNT(*) FROM tickets "
                   "UNION ALL SELECT 'work_orders', COUNT(*) FROM work_orders"),
    (f"{ontology.RESOLUTION_VIEW} sanity",
        f"SELECT equipment_found, COUNT(*) n FROM {ontology.RESOLUTION_VIEW} GROUP BY equipment_found"),
    ("priority normalization",
        f"SELECT priority, COUNT(*) n FROM {ontology.TICKET_CLEAN} GROUP BY priority ORDER BY n DESC"),
    ("team normalization",
        f"SELECT team, COUNT(*) n FROM {ontology.TICKET_CLEAN} GROUP BY team ORDER BY n DESC"),
]


def main() -> None:
    cfg = config.load()
    print(f"Smoke-testing hesheng-core in {cfg.region}\n")
    for label, sql in CHECKS:
        print(f"=== {label} ===")
        rows = athena.query(cfg, sql, max_rows=20)
        for r in rows:
            print("  " + "  ".join(c.ljust(20)[:20] for c in r))
        print()


if __name__ == "__main__":
    main()
