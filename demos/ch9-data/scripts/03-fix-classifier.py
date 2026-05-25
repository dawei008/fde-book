"""Fix the Glue Crawler issue we hit on first run.

Problem: tickets.csv and work_orders.csv came back with col0..col7 headers
instead of the real header line. Why? Glue's default CSV classifier
fails to identify the header row when fields contain quoted commas (the
Chinese fault descriptions in tickets.csv have commas inside quoted
strings).

Fix: register a custom CSV classifier with explicit quote and delimiter,
then re-run crawler.

This is a real FDE first-week problem — exactly the kind of "the data
looks fine but Glue read it wrong" trap that crashes a Discovery week
if you don't catch it.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

OUT = Path(__file__).resolve().parent.parent / "data" / "stack-outputs.json"
cfg = json.loads(OUT.read_text())
glue = boto3.client("glue", region_name=cfg["region"])

CLASSIFIER_NAME = "fde-book-ch9-csv-quoted"
CRAWLER_NAME = cfg["crawler"]


def upsert_classifier() -> None:
    config = {
        "Name": CLASSIFIER_NAME,
        "Delimiter": ",",
        "QuoteSymbol": '"',
        "ContainsHeader": "PRESENT",
        # Header lists for each table
        "Header": [
            "equipment_id", "model", "site", "service_year",
            "power_rating", "last_maintained", "customer_id",
        ],
    }
    # Glue allows only one Header per classifier — but we have 3 tables with
    # different headers. The right approach: drop the explicit Header and
    # let Glue infer from the first row, but force ContainsHeader=PRESENT.
    config = {
        "Name": CLASSIFIER_NAME,
        "Delimiter": ",",
        "QuoteSymbol": '"',
        "ContainsHeader": "PRESENT",
    }
    try:
        glue.create_classifier(CsvClassifier=config)
        print(f"  Created classifier {CLASSIFIER_NAME}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "AlreadyExistsException":
            glue.update_classifier(CsvClassifier=config)
            print(f"  Updated classifier {CLASSIFIER_NAME}")
        else:
            raise


def attach_classifier_and_rerun() -> None:
    glue.update_crawler(
        Name=CRAWLER_NAME,
        Classifiers=[CLASSIFIER_NAME],
    )
    print(f"  Attached classifier to crawler {CRAWLER_NAME}")
    print("\nRe-running crawler ...")
    glue.start_crawler(Name=CRAWLER_NAME)
    while True:
        r = glue.get_crawler(Name=CRAWLER_NAME)
        if r["Crawler"]["State"] == "READY":
            break
        print(f"  state: {r['Crawler']['State']}", flush=True)
        time.sleep(10)
    last = r["Crawler"].get("LastCrawl", {})
    print(f"  status: {last.get('Status')}, tables: {last.get('TablesCreated', 0)} created, {last.get('TablesUpdated', 0)} updated")


def show_tables() -> None:
    print("\nTables AFTER classifier fix:")
    for t in glue.get_tables(DatabaseName=cfg["database"])["TableList"]:
        cols = t["StorageDescriptor"]["Columns"]
        sample_cols = ", ".join(c["Name"] for c in cols[:5])
        print(f"  {t['Name']}: {len(cols)} cols — {sample_cols}{', ...' if len(cols) > 5 else ''}")


def main() -> None:
    upsert_classifier()
    attach_classifier_and_rerun()
    show_tables()


if __name__ == "__main__":
    main()
