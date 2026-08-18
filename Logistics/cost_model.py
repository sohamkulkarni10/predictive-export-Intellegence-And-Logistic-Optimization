"""Cost and distance helpers for export logistics."""

from __future__ import annotations

import math
from typing import Optional

import pandas as pd


EARTH_RADIUS_KM = 6371.0

# Calibrated from existing freight_rates (~USD per TEU-nm for ocean leg)
OCEAN_USD_PER_TEU_NM_20FT = 0.22
OCEAN_USD_PER_TEU_NM_40FT = 0.37
AVG_VESSEL_SPEED_KNOTS = 16.0
NM_PER_KM = 0.539957


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometers."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def containers_needed(quantity_tons: float, max_payload_tons: float) -> int:
    if quantity_tons <= 0:
        raise ValueError("quantity_tons must be > 0")
    if max_payload_tons <= 0:
        raise ValueError("max_payload_tons must be > 0")
    return max(1, math.ceil(quantity_tons / max_payload_tons))


def inland_cost_and_days(
    origin_lat: float,
    origin_lon: float,
    port_lat: float,
    port_lon: float,
    quantity_tons: float,
    inland_rates: pd.DataFrame,
) -> dict:
    distance_km = haversine_km(origin_lat, origin_lon, port_lat, port_lon)
    # Prefer rail for long hauls
    mode = "Rail" if distance_km >= 400 else "Truck"
    rate_row = inland_rates[inland_rates["mode"].str.lower() == mode.lower()]
    if rate_row.empty:
        rate_row = inland_rates.iloc[[0]]

    rate = float(rate_row.iloc[0]["rate_usd_per_ton_km"])
    min_charge = float(rate_row.iloc[0]["min_charge_usd"])
    speed = float(rate_row.iloc[0]["avg_speed_kmph"])

    # Road/rail distance is longer than great-circle; apply circuity factor
    road_km = distance_km * 1.25
    cost = max(min_charge, road_km * rate * quantity_tons)
    days = max(0.5, road_km / speed / 24.0)

    return {
        "inland_mode": mode,
        "inland_distance_km": round(road_km, 1),
        "inland_cost_usd": round(cost, 2),
        "inland_days": round(days, 2),
    }


def lookup_freight(
    freight_rates: pd.DataFrame,
    source_port_id: int,
    destination_port_id: int,
    container_type: str,
) -> Optional[dict]:
    mask = (
        (freight_rates["source_port_id"] == source_port_id)
        & (freight_rates["destination_port_id"] == destination_port_id)
        & (freight_rates["container_type"].str.upper() == container_type.upper())
    )
    rows = freight_rates.loc[mask]
    if rows.empty:
        return None
    row = rows.iloc[0]
    return {
        "freight_cost_usd_per_container": float(row["freight_cost_usd"]),
        "ocean_transit_days": float(row["transit_days"]),
        "service_type": str(row["service_type"]),
        "freight_source": "schedule",
    }


def estimate_freight(
    src_lat: float,
    src_lon: float,
    dst_lat: float,
    dst_lon: float,
    container_type: str,
) -> dict:
    """Distance-based ocean freight when no schedule row exists."""
    distance_km = haversine_km(src_lat, src_lon, dst_lat, dst_lon)
    # Sea route is longer than great-circle
    sea_km = distance_km * 1.35
    sea_nm = sea_km * NM_PER_KM

    ctype = container_type.upper()
    rate = OCEAN_USD_PER_TEU_NM_40FT if ctype.startswith("40") else OCEAN_USD_PER_TEU_NM_20FT
    freight = max(250.0, sea_nm * rate)
    transit_days = max(3.0, (sea_nm / AVG_VESSEL_SPEED_KNOTS) / 24.0 + 1.5)

    return {
        "freight_cost_usd_per_container": round(freight, 2),
        "ocean_transit_days": round(transit_days, 1),
        "service_type": "Estimated",
        "freight_source": "distance_model",
        "sea_distance_nm": round(sea_nm, 1),
    }


def port_charge_usd(port_charges: pd.DataFrame, port_id: int) -> float:
    row = port_charges[port_charges["port_id"] == port_id]
    if row.empty:
        return 210.0
    return float(row.iloc[0]["total_port_charge_usd"])
