"""
Lookup precomputed India → world port logistics costs.
Dataset folder: Logistics_Costs/
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

DIR = Path(__file__).resolve().parent
CSV = DIR / "india_to_world_port_costs.csv"
_cache: pd.DataFrame | None = None


def load_costs() -> pd.DataFrame:
    global _cache
    if _cache is None:
        if not CSV.exists():
            from build_costs_dataset import build

            build()
        _cache = pd.read_csv(CSV)
    return _cache


def best_route_for_country(
    country: str,
    container_type: str = "20FT",
) -> dict[str, Any] | None:
    """Cheapest India port → destination country port for container type."""
    df = load_costs()
    ctype = container_type.strip().upper()
    country_norm = country.strip().lower()
    subset = df[
        (df["destination_country"].str.lower() == country_norm)
        & (df["container_type"].str.upper() == ctype)
    ].copy()
    if subset.empty:
        # try alias UAE
        aliases = {"united arab emirates": "uae", "u.a.e.": "uae", "usa": "united states"}
        alt = aliases.get(country_norm)
        if alt:
            subset = df[
                (df["destination_country"].str.lower() == alt)
                & (df["container_type"].str.upper() == ctype)
            ].copy()
    if subset.empty:
        return None

    subset = subset.sort_values(
        ["logistics_cost_per_ton_usd", "transit_days"]
    ).reset_index(drop=True)
    best = subset.iloc[0]
    alts = subset.head(8).to_dict(orient="records")
    return {
        "india_port": best["india_port"],
        "india_unlocode": best["india_unlocode"],
        "india_state": best["india_state"],
        "destination_port": best["destination_port"],
        "destination_unlocode": best["destination_unlocode"],
        "destination_country": best["destination_country"],
        "container_type": best["container_type"],
        "ocean_freight_usd": float(best["ocean_freight_usd"]),
        "origin_port_charge_usd": float(best["origin_port_charge_usd"]),
        "destination_port_charge_usd": float(best["destination_port_charge_usd"]),
        "container_cost_usd": float(best["container_cost_usd"]),
        "cost_per_container_usd": float(best["logistics_cost_per_container_usd"]),
        "cost_per_ton_usd": float(best["logistics_cost_per_ton_usd"]),
        "total_transit_days": float(best["transit_days"]),
        "service_type": best["service_type"],
        "payload_tons": float(best["max_payload_tons"]),
        "all_paths": [
            {
                "india_port": r["india_port"],
                "destination_port": r["destination_port"],
                "total_logistics_cost_usd": float(r["logistics_cost_per_container_usd"]),
                "cost_per_ton_usd": float(r["logistics_cost_per_ton_usd"]),
                "total_transit_days": float(r["transit_days"]),
            }
            for r in alts
        ],
        "source": "Logistics_Costs/india_to_world_port_costs.csv",
    }


def list_countries() -> list[str]:
    return sorted(load_costs()["destination_country"].dropna().unique().tolist())
