"""
Build Logistics_Costs/india_to_world_port_costs.csv
from Logistics freight + ports + destination + port charges + container cost.
Run once:  python build_costs_dataset.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "Logistics"
OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)


def build() -> Path:
    ports = pd.read_csv(LOG / "ports.csv").rename(
        columns={
            "port_id": "india_port_id",
            "port_name": "india_port",
            "unlocode": "india_unlocode",
            "state": "india_state",
        }
    )
    dest = pd.read_csv(LOG / "destination_ports.csv").rename(
        columns={
            "port_name": "destination_port",
            "unlocode": "destination_unlocode",
            "country": "destination_country",
        }
    )
    fr = pd.read_csv(LOG / "freight_rates.csv")
    pc = pd.read_csv(LOG / "port_charges.csv")[
        ["port_id", "total_port_charge_usd"]
    ].rename(columns={"port_id": "india_port_id", "total_port_charge_usd": "origin_port_charge_usd"})
    cc = pd.read_csv(LOG / "container_cost.csv")[
        ["container_type", "total_container_cost_usd", "max_payload_tons"]
    ]

    m = fr.merge(ports, left_on="source_port_id", right_on="india_port_id", how="inner")
    m = m.merge(dest, on="destination_port_id", how="inner")
    m = m.merge(pc, on="india_port_id", how="left")
    m = m.merge(cc, on="container_type", how="left")

    m["origin_port_charge_usd"] = m["origin_port_charge_usd"].fillna(200)
    m["destination_port_charge_usd"] = (m["origin_port_charge_usd"] * 0.8).round(2)
    m["ocean_freight_usd"] = m["freight_cost_usd"].astype(float)
    m["container_cost_usd"] = m["total_container_cost_usd"].astype(float)
    m["transit_days"] = m["transit_days"].astype(float)
    m["logistics_cost_per_container_usd"] = (
        m["ocean_freight_usd"]
        + m["origin_port_charge_usd"]
        + m["destination_port_charge_usd"]
        + m["container_cost_usd"]
    ).round(2)
    m["logistics_cost_per_ton_usd"] = (
        m["logistics_cost_per_container_usd"] / m["max_payload_tons"].clip(lower=1)
    ).round(2)

    out_df = m[
        [
            "india_port_id",
            "india_port",
            "india_unlocode",
            "india_state",
            "destination_port_id",
            "destination_country",
            "destination_port",
            "destination_unlocode",
            "container_type",
            "ocean_freight_usd",
            "origin_port_charge_usd",
            "destination_port_charge_usd",
            "container_cost_usd",
            "logistics_cost_per_container_usd",
            "logistics_cost_per_ton_usd",
            "max_payload_tons",
            "transit_days",
            "service_type",
        ]
    ].drop_duplicates()

    path = OUT / "india_to_world_port_costs.csv"
    out_df.to_csv(path, index=False)
    print(f"Saved {len(out_df)} rows -> {path}")
    return path


if __name__ == "__main__":
    build()
