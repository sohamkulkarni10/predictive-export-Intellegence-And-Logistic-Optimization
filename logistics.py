"""
Stage 3 — Logistics using Logistics_Costs dataset + trade sell prices.

Profit = sell (trade CSV) - buy (predicted India price) - logistics (Logistics_Costs)
Only profitable lanes should be shown by the pipeline.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LOGISTICS = ROOT / "Logistics"
COSTS = ROOT / "Logistics_Costs"
if str(COSTS) not in sys.path:
    sys.path.insert(0, str(COSTS))
if str(LOGISTICS) not in sys.path:
    sys.path.insert(0, str(LOGISTICS))

from cost_lookup import best_route_for_country, list_countries  # noqa: E402
from data_loader import get_container_specs, load_all  # noqa: E402

# Fixed FX for all logistics / profit display (user rate)
INR_PER_USD = 96.3
TRADE_CSV = LOGISTICS / "commodity_country_trade.csv"


def usd_to_inr(amount_usd: float | None) -> float:
    if amount_usd is None:
        return 0.0
    return round(float(amount_usd) * INR_PER_USD, 2)


def load_trade() -> pd.DataFrame:
    df = pd.read_csv(TRADE_CSV)
    df["commodity"] = df["commodity"].astype(str).str.strip()
    df["country"] = df["country"].astype(str).str.strip()
    return df


def lookup_trade(commodity: str, country: str) -> dict[str, Any] | None:
    df = load_trade()
    match = df[
        (df["commodity"].str.lower() == commodity.lower())
        & (df["country"].str.lower() == country.lower())
    ]
    if match.empty:
        same = df[df["commodity"].str.lower() == commodity.lower()]
        if same.empty:
            return None
        return {
            "commodity": commodity,
            "country": country,
            "avg_export_price_usd_per_ton": float(same["avg_export_price_usd_per_ton"].mean()),
            "typical_quantity_tons": float(same["typical_quantity_tons"].mean()),
            "fallback": True,
        }
    row = match.iloc[0]
    return {
        "commodity": commodity,
        "country": country,
        "avg_export_price_usd_per_ton": float(row["avg_export_price_usd_per_ton"]),
        "typical_quantity_tons": float(row["typical_quantity_tons"]),
        "fallback": False,
    }


def trade_pairs_for_commodity(commodity: str) -> list[dict[str, Any]]:
    df = load_trade()
    rows = df[df["commodity"].str.lower() == commodity.lower()]
    return [
        {
            "commodity": r["commodity"],
            "country": r["country"],
            "avg_export_price_usd_per_ton": float(r["avg_export_price_usd_per_ton"]),
            "typical_quantity_tons": float(r["typical_quantity_tons"]),
        }
        for _, r in rows.iterrows()
    ]


def container_payload_tons(container_type: str = "20FT") -> float:
    data = load_all()
    container = get_container_specs(data["container_cost"], container_type)
    return float(container["max_payload_tons"])


def quintal_inr_to_usd_per_ton(price_inr_per_quintal: float) -> float:
    return (float(price_inr_per_quintal) * 10.0) / INR_PER_USD


def estimate_net_profit(
    *,
    commodity: str,
    country: str,
    demand_score: float,
    predicted_india_price_inr: float,
    cost_per_ton_usd: float,
    cost_per_container_usd: float,
    payload_tons: float,
    containers_allocated: int = 0,
    avg_export_price_usd_per_ton: float | None = None,
    quantity_tons: float | None = None,
) -> dict[str, Any]:
    buy_usd_t = quintal_inr_to_usd_per_ton(predicted_india_price_inr)
    sell_usd_t = float(avg_export_price_usd_per_ton or 0)
    if sell_usd_t <= 0:
        sell_usd_t = buy_usd_t * (1.10 + 0.18 * float(max(0, min(1, demand_score))))

    logistics = float(cost_per_ton_usd)
    net_usd_t = sell_usd_t - buy_usd_t - logistics
    qty = float(quantity_tons or (payload_tons * max(1, containers_allocated or 1)))
    net_total_usd = net_usd_t * qty
    net_total_inr = net_total_usd * INR_PER_USD
    net_per_container_usd = net_usd_t * float(payload_tons)

    net_per_container_inr = usd_to_inr(net_per_container_usd)
    alloc_usd = net_per_container_usd * int(containers_allocated)
    return {
        "commodity": commodity,
        "country": country,
        "buy_cost_usd_per_ton": round(buy_usd_t, 2),
        "buy_cost_inr_per_ton": usd_to_inr(buy_usd_t),
        "buy_cost_inr_per_quintal": round(float(predicted_india_price_inr), 2),
        "sell_price_usd_per_ton": round(sell_usd_t, 2),
        "sell_price_inr_per_ton": usd_to_inr(sell_usd_t),
        "logistics_cost_usd_per_ton": round(logistics, 2),
        "logistics_cost_inr_per_ton": usd_to_inr(logistics),
        "logistics_cost_inr_per_container": usd_to_inr(cost_per_container_usd),
        "quantity_tons": round(qty, 2),
        "net_profit_usd_per_ton": round(net_usd_t, 2),
        "net_profit_usd_per_container": round(net_per_container_usd, 2),
        "net_profit_usd_for_allocation": round(alloc_usd, 2),
        "net_profit_inr": round(net_total_inr, 2),
        "net_profit_inr_per_ton": usd_to_inr(net_usd_t),
        "net_profit_inr_per_container": net_per_container_inr,
        "net_profit_inr_for_allocation": usd_to_inr(alloc_usd),
        "fx_inr_per_usd": INR_PER_USD,
        "currency": "INR",
        "formula": "sell(trade) - buy(predicted INR/quintal) - logistics; display in INR @ 96.3/USD",
    }


def plan_lane(
    *,
    commodity: str,
    country: str,
    demand_score: float,
    predicted_india_price_inr: float | None,
    container_type: str,
    payload_tons: float,
    horizon_month: str,
    cost_weight: float = 0.7,
    time_weight: float = 0.3,
) -> dict[str, Any]:
    trade = lookup_trade(commodity, country)
    quantity = float(trade["typical_quantity_tons"]) if trade else payload_tons
    sell_price = float(trade["avg_export_price_usd_per_ton"]) if trade else None

    route = best_route_for_country(country, container_type=container_type)
    if route is None:
        return {
            "commodity": commodity,
            "country": country,
            "demand_score": float(demand_score),
            "predicted_india_price_inr": predicted_india_price_inr,
            "ok": False,
            "error": f"No logistics cost row for country '{country}' in Logistics_Costs",
            "cost_per_ton_usd": 9999.0,
            "total_transit_days": 999.0,
            "net_profit_usd_per_ton": -9999.0,
            "net_profit_inr": -9999.0,
        }

    cost_per_ton = float(route["cost_per_ton_usd"])
    cost_per_ctr = float(route["cost_per_container_usd"])
    payload = float(route.get("payload_tons") or payload_tons)

    profit = estimate_net_profit(
        commodity=commodity,
        country=country,
        demand_score=float(demand_score),
        predicted_india_price_inr=float(predicted_india_price_inr or 0),
        cost_per_ton_usd=cost_per_ton,
        cost_per_container_usd=cost_per_ctr,
        payload_tons=payload,
        containers_allocated=0,
        avg_export_price_usd_per_ton=sell_price,
        quantity_tons=quantity,
    )

    # Attach profit on alternate paths; keep only positive later in pipeline
    all_paths = []
    for p in route.get("all_paths") or []:
        p_profit = estimate_net_profit(
            commodity=commodity,
            country=country,
            demand_score=float(demand_score),
            predicted_india_price_inr=float(predicted_india_price_inr or 0),
            cost_per_ton_usd=float(p["cost_per_ton_usd"]),
            cost_per_container_usd=float(p["total_logistics_cost_usd"]),
            payload_tons=payload,
            containers_allocated=0,
            avg_export_price_usd_per_ton=sell_price,
            quantity_tons=quantity,
        )
        if p_profit["net_profit_usd_per_ton"] <= 0:
            continue
        all_paths.append(
            {
                "india_port": p["india_port"],
                "destination_port": p["destination_port"],
                "total_logistics_cost_usd": p["total_logistics_cost_usd"],
                "total_logistics_cost_inr": usd_to_inr(p["total_logistics_cost_usd"]),
                "total_transit_days": p["total_transit_days"],
                "cost_per_ton_usd": p["cost_per_ton_usd"],
                "cost_per_ton_inr": usd_to_inr(p["cost_per_ton_usd"]),
                "net_profit_inr": p_profit["net_profit_inr"],
                "net_profit_inr_per_ton": p_profit["net_profit_inr_per_ton"],
                "net_profit_usd_per_ton": p_profit["net_profit_usd_per_ton"],
            }
        )
    all_paths.sort(key=lambda x: x["net_profit_inr"], reverse=True)

    cost_per_ton_inr = usd_to_inr(cost_per_ton)
    cost_per_ctr_inr = usd_to_inr(cost_per_ctr)
    sell_inr = usd_to_inr(sell_price) if sell_price else 0

    decision_summary = (
        f"EXPORT DECISION: Export {commodity} from {route['india_port']} "
        f"({route['india_unlocode']}) to {route['destination_port']} "
        f"({route['destination_unlocode']}, {country}). "
        f"Logistics ₹{cost_per_ton_inr:,.0f}/ton (FX ₹{INR_PER_USD}/USD), "
        f"transit ~{route['total_transit_days']} days. "
        f"Buy ~₹{predicted_india_price_inr:,.0f}/quintal for {horizon_month}."
    )

    return {
        "commodity": commodity,
        "country": country,
        "demand_score": float(demand_score),
        "predicted_india_price_inr": predicted_india_price_inr,
        "avg_export_price_usd_per_ton": sell_price,
        "avg_export_price_inr_per_ton": sell_inr,
        "quantity_tons": quantity,
        "india_port": route["india_port"],
        "india_unlocode": route["india_unlocode"],
        "destination_port": route["destination_port"],
        "destination_unlocode": route["destination_unlocode"],
        "origin": f"{route['india_state']} hub",
        "cost_per_ton_usd": cost_per_ton,
        "cost_per_ton_inr": cost_per_ton_inr,
        "cost_per_container_usd": cost_per_ctr,
        "cost_per_container_inr": cost_per_ctr_inr,
        "total_transit_days": route["total_transit_days"],
        "service_type": route["service_type"],
        "fx_inr_per_usd": INR_PER_USD,
        "decision_summary": decision_summary,
        "action_plan": [
            f"1. Buy {commodity} in India at ~₹{predicted_india_price_inr:,.0f}/quintal.",
            f"2. Move cargo to {route['india_port']}.",
            f"3. Ship to {route['destination_port']}, {country}.",
            f"4. Sell near ₹{sell_inr:,.0f}/ton (trade average @ ₹{INR_PER_USD}/USD).",
        ],
        "purchase_guidance": (
            f"Buy {commodity} near predicted ₹{predicted_india_price_inr:,.0f}/quintal "
            f"for {horizon_month}."
        ),
        "all_paths": all_paths,
        "cost_breakdown": {
            "ocean_freight_usd": route["ocean_freight_usd"],
            "ocean_freight_inr": usd_to_inr(route["ocean_freight_usd"]),
            "origin_port_charge_usd": route["origin_port_charge_usd"],
            "origin_port_charge_inr": usd_to_inr(route["origin_port_charge_usd"]),
            "destination_port_charge_usd": route["destination_port_charge_usd"],
            "destination_port_charge_inr": usd_to_inr(route["destination_port_charge_usd"]),
            "container_cost_usd": route["container_cost_usd"],
            "container_cost_inr": usd_to_inr(route["container_cost_usd"]),
            "total_logistics_cost_usd": route["cost_per_container_usd"],
            "total_logistics_cost_inr": cost_per_ctr_inr,
            "cost_per_ton_usd": cost_per_ton,
            "cost_per_ton_inr": cost_per_ton_inr,
            "fx_inr_per_usd": INR_PER_USD,
            "source": route["source"],
        },
        "profit": profit,
        "net_profit_usd_per_ton": profit["net_profit_usd_per_ton"],
        "net_profit_inr_per_ton": profit["net_profit_inr_per_ton"],
        "net_profit_inr": profit["net_profit_inr"],
        "ok": True,
        "error": None,
        "available_cost_countries": list_countries()[:20],
    }
