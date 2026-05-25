"""SQL view definitions for the cleaned Hesheng ontology.

Names and shapes that chapter demos can rely on:

    equipment_clean      — surface-cleaned equipment master
    ticket_clean         — UTC timestamps, normalized priority/team
    work_order_clean     — normalized hours_spent, status, part_id
    ticket_resolution    — fact view joining the three above

The chapter demos read from `ticket_resolution` for most questions.
This file exports both the SQL strings (for setup scripts that build
the views) and the names (for demos that query them).
"""

from __future__ import annotations

EQUIPMENT_CLEAN = "equipment_clean"
TICKET_CLEAN = "ticket_clean"
WORK_ORDER_CLEAN = "work_order_clean"
RESOLUTION_VIEW = "ticket_resolution"


def equipment_clean_sql(db: str) -> str:
    return f"""
        SELECT
            equipment_id,
            CASE
                WHEN model LIKE 'JGA%' THEN REPLACE(model, 'JGA', 'JG-A')
                WHEN model LIKE 'JG A%' THEN REPLACE(model, 'JG A', 'JG-A')
                ELSE REGEXP_REPLACE(TRIM(model), '[\\u200B\\xa0]', '')
            END AS model,
            site,
            CAST(service_year AS INTEGER) AS service_year,
            CAST(REGEXP_EXTRACT(power_rating, '\\d+') AS INTEGER) AS power_rating_kw,
            CAST(last_maintained AS DATE) AS last_maintained,
            customer_id
        FROM {db}.equipment
    """


def ticket_clean_sql(db: str) -> str:
    return f"""
        SELECT
            ticket_no,
            CASE
                WHEN regexp_like(ts, '^\\d{{4}}-\\d{{2}}-\\d{{2}}T')
                    THEN CAST(from_iso8601_timestamp(ts) AS timestamp)
                WHEN regexp_like(ts, '^\\d{{4}}年')
                    THEN CAST(parse_datetime(ts, 'yyyy''年''MM''月''dd''日'' HH:mm') AS timestamp)
                          - INTERVAL '8' HOUR
                WHEN regexp_like(ts, '^\\d{{10}}$')
                    THEN from_unixtime(CAST(ts AS BIGINT))
                ELSE NULL
            END AS ts_utc,
            equipment_id,
            fault_desc,
            alarm_code,
            CASE
                WHEN priority IN ('P1', 'high', '1') THEN 'P1'
                WHEN priority IN ('P2', 'medium', '2') THEN 'P2'
                WHEN priority IN ('P3', 'low', '3') THEN 'P3'
                ELSE 'UNKNOWN'
            END AS priority,
            CASE
                WHEN team IN ('机械组', 'Mech', 'M-team') THEN '机械组'
                WHEN team IN ('电气组', 'Elec', 'E-team') THEN '电气组'
                ELSE 'UNKNOWN'
            END AS team,
            reporter_phone
        FROM {db}.tickets
    """


def work_order_clean_sql(db: str) -> str:
    return f"""
        SELECT
            wo_id,
            ticket_no,
            engineer_id,
            CASE
                WHEN starts_with(part_id, 'PART-') THEN REPLACE(part_id, 'PART-', 'P-')
                ELSE part_id
            END AS part_id,
            CASE
                WHEN regexp_like(hours_spent, '^\\d+h\\d+m$') THEN
                    CAST(regexp_extract(hours_spent, '^(\\d+)h', 1) AS DOUBLE)
                  + CAST(regexp_extract(hours_spent, 'h(\\d+)m$', 1) AS DOUBLE) / 60.0
                WHEN regexp_like(hours_spent, '^\\d+$') AND CAST(hours_spent AS INTEGER) > 24 THEN
                    CAST(hours_spent AS DOUBLE) / 60.0
                ELSE CAST(hours_spent AS DOUBLE)
            END AS hours_spent,
            CASE
                WHEN lower(status) IN ('closed', 'done', 'complete') THEN 'closed'
                WHEN status = '已完成' THEN 'closed'
                ELSE 'open'
            END AS status,
            CAST(completed_at AS TIMESTAMP) AS completed_at
        FROM {db}.work_orders
    """


def resolution_sql(db: str) -> str:
    return f"""
        SELECT
            t.ticket_no, t.ts_utc, t.priority, t.team,
            t.fault_desc, t.alarm_code,
            e.model AS equipment_model, e.site, e.power_rating_kw,
            (
                SELECT min(w.completed_at) FROM {db}.{WORK_ORDER_CLEAN} w
                WHERE w.ticket_no = t.ticket_no AND w.status = 'closed'
            ) AS resolved_at,
            (
                SELECT sum(w.hours_spent) FROM {db}.{WORK_ORDER_CLEAN} w
                WHERE w.ticket_no = t.ticket_no AND w.status = 'closed'
            ) AS total_hours,
            CASE WHEN e.equipment_id IS NULL THEN false ELSE true END AS equipment_found
        FROM {db}.{TICKET_CLEAN} t
        LEFT JOIN {db}.{EQUIPMENT_CLEAN} e ON t.equipment_id = e.equipment_id
    """


def all_view_specs(db: str) -> list[tuple[str, str]]:
    return [
        (EQUIPMENT_CLEAN, equipment_clean_sql(db)),
        (TICKET_CLEAN, ticket_clean_sql(db)),
        (WORK_ORDER_CLEAN, work_order_clean_sql(db)),
        (RESOLUTION_VIEW, resolution_sql(db)),
    ]
