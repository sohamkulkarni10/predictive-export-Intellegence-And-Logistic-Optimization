"""Multi-criteria export route optimizer (India port -> demand country port)."""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd

from cost_model import (
    containers_needed,
    estimate_freight,
    haversine_km,
    inland_cost_and_days,
    lookup_freight,
    port_charge_usd,
)
from data_loader import (
    get_container_specs,
    load_all,
    resolve_destination_ports,
    resolve_origins,
)


def _normalize(series: pd.Series) -> pd.Series:
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series([0.0] * len(series), index=series.index)
    return (series - mn) / (mx - mn)


def build_candidate_routes(
    commodity: str,
    demand_country: str,
    quantity_tons: Optional[float] = None,
    container_type: str = "20FT",
    origin_state: Optional[str] = None,
    origin_city: Optional[str] = None,
    planning_containers: int = 1,
    data: Optional[dict[str, pd.DataFrame]] = None,
) -> pd.DataFrame:
    """
    Build India->destination route candidates.

    If quantity_tons is None, uses planning_containers (default 1) so routes
    can be compared without knowing import quantity.
    """
    data = data or load_all()
    origin = resolve_origins(
        data["commodity_origins"], commodity, origin_state, origin_city
    ).iloc[0]
    dest_ports = resolve_destination_ports(data["destination_ports"], demand_country)
    container = get_container_specs(data["container_cost"], container_type)
    max_payload = float(container["max_payload_tons"])
    planning_mode = quantity_tons is None
    if planning_mode:
        n_containers = max(1, int(planning_containers))
        quantity_tons = n_containers * max_payload
    else:
        n_containers = containers_needed(float(quantity_tons), max_payload)
    container_unit_cost = float(container["total_container_cost_usd"])

    indian_ports = data["ports"]
    rows: list[dict[str, Any]] = []

    for _, sport in indian_ports.iterrows():
        inland = inland_cost_and_days(
            float(origin["latitude"]),
            float(origin["longitude"]),
            float(sport["latitude"]),
            float(sport["longitude"]),
            quantity_tons,
            data["inland_rates"],
        )
        loading_port_charge = port_charge_usd(data["port_charges"], int(sport["port_id"]))

        for _, dport in dest_ports.iterrows():
            freight = lookup_freight(
                data["freight_rates"],
                int(sport["port_id"]),
                int(dport["destination_port_id"]),
                container_type,
            )
            if freight is None:
                freight = estimate_freight(
                    float(sport["latitude"]),
                    float(sport["longitude"]),
                    float(dport["latitude"]),
                    float(dport["longitude"]),
                    container_type,
                )

            ocean_cost = freight["freight_cost_usd_per_container"] * n_containers
            container_cost = container_unit_cost * n_containers
            # Destination terminal handling approx 0.8x Indian THC bundle
            dest_port_charge = loading_port_charge * 0.8 * n_containers
            origin_port_charge = loading_port_charge * n_containers

            total_logistics = (
                inland["inland_cost_usd"]
                + origin_port_charge
                + dest_port_charge
                + container_cost
                + ocean_cost
            )
            total_days = inland["inland_days"] + freight["ocean_transit_days"] + 2.0  # docs/customs buffer
            sea_distance_km = haversine_km(
                float(sport["latitude"]),
                float(sport["longitude"]),
                float(dport["latitude"]),
                float(dport["longitude"]),
            )

            rows.append(
                {
                    "commodity": commodity,
                    "demand_country": demand_country,
                    "origin_state": origin["origin_state"],
                    "origin_city": origin["origin_city"],
                    "quantity_tons": quantity_tons,
                    "container_type": container_type.upper(),
                    "containers_required": n_containers,
                    "india_port_id": int(sport["port_id"]),
                    "india_port": sport["port_name"],
                    "india_port_state": sport["state"],
                    "india_unlocode": sport["unlocode"],
                    "destination_port_id": int(dport["destination_port_id"]),
                    "destination_port": dport["port_name"],
                    "destination_unlocode": dport["unlocode"],
                    "destination_region": dport["region"],
                    "inland_mode": inland["inland_mode"],
                    "inland_distance_km": inland["inland_distance_km"],
                    "inland_cost_usd": inland["inland_cost_usd"],
                    "inland_days": inland["inland_days"],
                    "origin_port_charge_usd": round(origin_port_charge, 2),
                    "destination_port_charge_usd": round(dest_port_charge, 2),
                    "container_cost_usd": round(container_cost, 2),
                    "ocean_freight_usd": round(ocean_cost, 2),
                    "freight_per_container_usd": freight["freight_cost_usd_per_container"],
                    "service_type": freight["service_type"],
                    "freight_source": freight["freight_source"],
                    "ocean_transit_days": freight["ocean_transit_days"],
                    "sea_distance_km": round(sea_distance_km, 1),
                    "total_logistics_cost_usd": round(total_logistics, 2),
                    "total_transit_days": round(total_days, 1),
                    "cost_per_ton_usd": round(total_logistics / quantity_tons, 2),
                    "cost_per_container_usd": round(total_logistics / n_containers, 2),
                    "planning_mode": planning_mode,
                }
            )

    return pd.DataFrame(rows)


def optimize_routes(
    commodity: str,
    demand_country: str,
    quantity_tons: Optional[float] = None,
    container_type: str = "20FT",
    origin_state: Optional[str] = None,
    origin_city: Optional[str] = None,
    cost_weight: float = 0.7,
    time_weight: float = 0.3,
    top_n: int = 10,
    planning_containers: int = 1,
    data: Optional[dict[str, pd.DataFrame]] = None,
) -> pd.DataFrame:
    """
    Rank all India->destination port pairs for a demand country.

    score = cost_weight * norm(cost) + time_weight * norm(days)
    Lower score is better.
    """
    if cost_weight < 0 or time_weight < 0:
        raise ValueError("Weights must be non-negative")
    total_w = cost_weight + time_weight
    if total_w == 0:
        raise ValueError("At least one of cost_weight / time_weight must be > 0")
    cost_weight, time_weight = cost_weight / total_w, time_weight / total_w

    candidates = build_candidate_routes(
        commodity=commodity,
        demand_country=demand_country,
        quantity_tons=quantity_tons,
        container_type=container_type,
        origin_state=origin_state,
        origin_city=origin_city,
        planning_containers=planning_containers,
        data=data,
    )
    if candidates.empty:
        raise ValueError("No candidate routes found")

    candidates["norm_cost"] = _normalize(candidates["total_logistics_cost_usd"])
    candidates["norm_time"] = _normalize(candidates["total_transit_days"])
    candidates["optimization_score"] = (
        cost_weight * candidates["norm_cost"] + time_weight * candidates["norm_time"]
    ).round(4)

    ranked = candidates.sort_values(
        ["optimization_score", "total_logistics_cost_usd", "total_transit_days", "sea_distance_km"]
    ).reset_index(drop=True)
    ranked.insert(0, "rank", range(1, len(ranked) + 1))
    return ranked.head(top_n).copy()
