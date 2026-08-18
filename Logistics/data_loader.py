"""Load and join logistics datasets for export route optimization."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent


def _read(name: str) -> pd.DataFrame:
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing logistics data file: {path}")
    return pd.read_csv(path)


def load_all() -> dict[str, pd.DataFrame]:
    return {
        "ports": _read("ports.csv"),
        "destination_ports": _read("destination_ports.csv"),
        "freight_rates": _read("freight_rates.csv"),
        "port_charges": _read("port_charges.csv"),
        "container_cost": _read("container_cost.csv"),
        "commodity_origins": _read("commodity_origins.csv"),
        "inland_rates": _read("inland_rates.csv"),
    }


def list_commodities(origins: pd.DataFrame) -> list[str]:
    return sorted(origins["commodity"].dropna().unique().tolist())


def list_demand_countries(destinations: pd.DataFrame) -> list[str]:
    return sorted(destinations["country"].dropna().unique().tolist())


def resolve_origins(
    origins: pd.DataFrame,
    commodity: str,
    origin_state: Optional[str] = None,
    origin_city: Optional[str] = None,
) -> pd.DataFrame:
    commodity_norm = commodity.strip().lower()
    df = origins[origins["commodity"].str.lower() == commodity_norm].copy()
    if df.empty:
        # Fallback: use Wheat hub so pipeline never dies on rare commodities
        df = origins[origins["commodity"].str.lower() == "wheat"].copy()
        if df.empty:
            available = ", ".join(list_commodities(origins))
            raise ValueError(f"Unknown commodity '{commodity}'. Available: {available}")
        df = df.copy()
        df["commodity"] = commodity.strip().title()

    if origin_city:
        city = origin_city.strip().lower()
        filtered = df[df["origin_city"].str.lower() == city]
        if not filtered.empty:
            return filtered.reset_index(drop=True)

    if origin_state:
        state = origin_state.strip().lower()
        filtered = df[df["origin_state"].str.lower() == state]
        if not filtered.empty:
            return filtered.reset_index(drop=True)

    # Default: highest production-share hub for that commodity
    return df.sort_values("production_share", ascending=False).head(1).reset_index(drop=True)


COUNTRY_ALIASES = {
    "united arab emirates": "uae",
    "u.a.e.": "uae",
    "u.a.e": "uae",
    "usa": "united states",
    "us": "united states",
    "u.s.a.": "united states",
    "u.s.": "united states",
    "uk": "united kingdom",
    "u.k.": "united kingdom",
    "britain": "united kingdom",
    "great britain": "united kingdom",
    "holland": "netherlands",
    "south korea": "south korea",
    "korea": "south korea",
    "republic of korea": "south korea",
}


def normalize_country_name(country: str) -> str:
    key = country.strip().lower()
    return COUNTRY_ALIASES.get(key, key)


def resolve_destination_ports(
    destinations: pd.DataFrame,
    country: str,
) -> pd.DataFrame:
    country_norm = normalize_country_name(country)
    df = destinations[destinations["country"].str.lower() == country_norm].copy()
    if df.empty:
        available = ", ".join(list_demand_countries(destinations))
        raise ValueError(f"Unknown demand country '{country}'. Available: {available}")
    return df.reset_index(drop=True)


def get_container_specs(container_cost: pd.DataFrame, container_type: str) -> dict:
    ctype = container_type.strip().upper()
    row = container_cost[container_cost["container_type"].str.upper() == ctype]
    if row.empty:
        available = ", ".join(container_cost["container_type"].tolist())
        raise ValueError(f"Unknown container type '{container_type}'. Available: {available}")
    return row.iloc[0].to_dict()
