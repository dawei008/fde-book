"""Thin Athena wrappers used by chapter demos.

Two functions:
- query(cfg, sql) — synchronous SELECT that returns rows
- create_view(cfg, name, sql) — CREATE OR REPLACE VIEW
"""

from __future__ import annotations

import time

import boto3

from .config import Config


def _client(cfg: Config):
    return boto3.client("athena", region_name=cfg.region)


def _wait(client, qid: str) -> dict:
    while True:
        st = client.get_query_execution(QueryExecutionId=qid)["QueryExecution"]
        if st["Status"]["State"] in ("SUCCEEDED", "FAILED", "CANCELLED"):
            return st
        time.sleep(1)


def query(cfg: Config, sql: str, *, max_rows: int = 50) -> list[list[str]]:
    """Run SELECT, return up to max_rows; row 0 is the header."""
    client = _client(cfg)
    sql = sql.strip().rstrip(";").strip()
    qid = client.start_query_execution(
        QueryString=sql,
        QueryExecutionContext={"Database": cfg.database},
        ResultConfiguration={"OutputLocation": cfg.athena_results_uri},
    )["QueryExecutionId"]
    st = _wait(client, qid)
    if st["Status"]["State"] != "SUCCEEDED":
        raise RuntimeError(
            f"Athena query failed: {st['Status'].get('StateChangeReason', '')}\nSQL: {sql[:300]}"
        )
    rows = client.get_query_results(QueryExecutionId=qid, MaxResults=max_rows)["ResultSet"]["Rows"]
    return [[d.get("VarCharValue", "") for d in r["Data"]] for r in rows]


def create_view(cfg: Config, name: str, select_sql: str) -> None:
    """CREATE OR REPLACE VIEW <db>.<name> AS <select_sql>."""
    client = _client(cfg)
    full = f"CREATE OR REPLACE VIEW {cfg.database}.{name} AS {select_sql.strip()}"
    qid = client.start_query_execution(
        QueryString=full,
        QueryExecutionContext={"Database": cfg.database},
        ResultConfiguration={"OutputLocation": cfg.athena_results_uri},
    )["QueryExecutionId"]
    st = _wait(client, qid)
    if st["Status"]["State"] != "SUCCEEDED":
        raise RuntimeError(
            f"View create failed: {st['Status'].get('StateChangeReason', '')}"
        )
