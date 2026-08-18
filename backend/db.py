"""
Simple SQLite store for logistics cost parts + last pipeline run.

Tables:
  logistics_costs  — every route cost breakdown
  pipeline_runs    — latest full JSON result
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent / "export_ai.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS logistics_costs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                created_at TEXT,
                commodity TEXT,
                country TEXT,
                india_port TEXT,
                destination_port TEXT,
                quantity_tons REAL,
                inland_cost_usd REAL,
                origin_port_charge_usd REAL,
                destination_port_charge_usd REAL,
                container_cost_usd REAL,
                ocean_freight_usd REAL,
                total_logistics_cost_usd REAL,
                cost_per_ton_usd REAL,
                buy_cost_inr_per_quintal REAL,
                sell_price_usd_per_ton REAL,
                net_profit_inr REAL,
                net_profit_usd_per_ton REAL,
                total_transit_days REAL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT UNIQUE,
                created_at TEXT,
                result_json TEXT
            )
            """
        )
        conn.commit()


def save_logistics_costs(run_id: str, lanes: list[dict[str, Any]]) -> None:
    init_db()
    now = datetime.now().isoformat(timespec="seconds")
    rows = []
    for lane in lanes:
        if not lane.get("ok"):
            continue
        bd = lane.get("cost_breakdown") or {}
        profit = lane.get("profit") or {}
        rows.append(
            (
                run_id,
                now,
                lane.get("commodity"),
                lane.get("country"),
                lane.get("india_port"),
                lane.get("destination_port"),
                lane.get("quantity_tons"),
                bd.get("inland_cost_usd"),
                bd.get("origin_port_charge_usd"),
                bd.get("destination_port_charge_usd"),
                bd.get("container_cost_usd"),
                bd.get("ocean_freight_usd"),
                bd.get("total_logistics_cost_usd"),
                lane.get("cost_per_ton_usd"),
                lane.get("predicted_india_price_inr"),
                lane.get("avg_export_price_usd_per_ton"),
                profit.get("net_profit_inr"),
                profit.get("net_profit_usd_per_ton"),
                lane.get("total_transit_days"),
            )
        )
    with _conn() as conn:
        conn.executemany(
            """
            INSERT INTO logistics_costs (
                run_id, created_at, commodity, country, india_port, destination_port,
                quantity_tons, inland_cost_usd, origin_port_charge_usd, destination_port_charge_usd,
                container_cost_usd, ocean_freight_usd, total_logistics_cost_usd, cost_per_ton_usd,
                buy_cost_inr_per_quintal, sell_price_usd_per_ton, net_profit_inr,
                net_profit_usd_per_ton, total_transit_days
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()


def save_pipeline_run(run_id: str, result: dict[str, Any]) -> None:
    init_db()
    now = datetime.now().isoformat(timespec="seconds")
    with _conn() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO pipeline_runs (run_id, created_at, result_json)
            VALUES (?, ?, ?)
            """,
            (run_id, now, json.dumps(result, default=str)),
        )
        conn.commit()


def get_latest() -> dict[str, Any]:
    init_db()
    with _conn() as conn:
        row = conn.execute(
            "SELECT result_json, created_at, run_id FROM pipeline_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if not row:
            return {"source": "none", "message": "No pipeline run yet. Run POST /api/pipeline first."}
        data = json.loads(row["result_json"])
        return {"source": "sqlite", "run_id": row["run_id"], "created_at": row["created_at"], "pipeline": data}


def get_logistics_from_db(run_id: str | None = None) -> list[dict[str, Any]]:
    init_db()
    with _conn() as conn:
        if run_id:
            cur = conn.execute(
                "SELECT * FROM logistics_costs WHERE run_id = ? ORDER BY id",
                (run_id,),
            )
        else:
            latest = conn.execute(
                "SELECT run_id FROM logistics_costs ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if not latest:
                return []
            cur = conn.execute(
                "SELECT * FROM logistics_costs WHERE run_id = ? ORDER BY id",
                (latest["run_id"],),
            )
        return [dict(r) for r in cur.fetchall()]


def databricks_enabled() -> bool:
    return False
