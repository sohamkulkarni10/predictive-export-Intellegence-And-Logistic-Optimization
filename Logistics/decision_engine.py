"""Turn ranked routes into a clear exporter decision."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from optimizer import optimize_routes


INR_PER_USD = 96.3  # settlement rate for decision display


def _fmt_money(usd: float) -> str:
    return f"₹{usd * INR_PER_USD:,.0f} (${usd:,.2f})"


def build_decision(
    ranked: pd.DataFrame,
    predicted_india_price_inr_per_quintal: Optional[float] = None,
    demand_score: Optional[float] = None,
    horizon_month: Optional[str] = None,
) -> dict[str, Any]:
    if ranked.empty:
        raise ValueError("No ranked routes to decide on")

    best = ranked.iloc[0]
    alt = ranked.iloc[1].to_dict() if len(ranked) > 1 else None

    purchase_note = None
    if predicted_india_price_inr_per_quintal is not None:
        purchase_note = (
            f"Buy {best['commodity']} in India near {best['origin_city']}, "
            f"{best['origin_state']} at predicted ~INR {predicted_india_price_inr_per_quintal:,.0f}/quintal"
            + (f" for {horizon_month}" if horizon_month else "")
            + "."
        )

    demand_note = None
    if demand_score is not None:
        demand_note = (
            f"Demand signal for {best['demand_country']} is {demand_score:.2f} "
            f"(higher = stronger next-month demand)."
        )

    planning_mode = bool(best.get("planning_mode", False))
    if planning_mode:
        decision_text = (
            f"EXPORT DECISION: Export {best['commodity']} "
            f"from {best['india_port']} ({best['india_unlocode']}, {best['india_port_state']}) "
            f"to {best['destination_port']} ({best['destination_unlocode']}, {best['demand_country']}). "
            f"Plan on {best['container_type']} containers. "
            f"Move cargo inland by {best['inland_mode']} from {best['origin_city']} "
            f"({best['inland_distance_km']} km). "
            f"Estimated logistics {_fmt_money(best['cost_per_ton_usd'])}/ton "
            f"(~{_fmt_money(float(best['total_logistics_cost_usd']) / max(int(best['containers_required']), 1))}/container), "
            f"transit ~{best['total_transit_days']} days via {best['service_type']} service."
        )
        action_plan = [
            f"1. Procure {best['commodity']} near {best['origin_city']}, {best['origin_state']} "
            f"(volume follows allocated containers).",
            f"2. Book inland {best['inland_mode'].lower()} haul to {best['india_port']} "
            f"({best['india_unlocode']}).",
            f"3. Reserve allocated {best['container_type']} containers "
            f"and complete export documentation / customs at Indian port.",
            f"4. Book ocean freight {best['india_unlocode']} → {best['destination_unlocode']} "
            f"({best['service_type']}, ~{best['ocean_transit_days']} sea days).",
            f"5. Clear cargo at {best['destination_port']}, {best['demand_country']}.",
        ]
    else:
        decision_text = (
            f"EXPORT DECISION: Ship {best['quantity_tons']} tons of {best['commodity']} "
            f"from {best['india_port']} ({best['india_unlocode']}, {best['india_port_state']}) "
            f"to {best['destination_port']} ({best['destination_unlocode']}, {best['demand_country']}) "
            f"using {best['containers_required']} x {best['container_type']} containers. "
            f"Move cargo inland by {best['inland_mode']} from {best['origin_city']} "
            f"({best['inland_distance_km']} km). "
            f"Expected door-to-port logistics cost {_fmt_money(best['total_logistics_cost_usd'])} "
            f"({_fmt_money(best['cost_per_ton_usd'])}/ton), transit ~{best['total_transit_days']} days "
            f"via {best['service_type']} service."
        )
        action_plan = [
            f"1. Procure {best['quantity_tons']} tons of {best['commodity']} near "
            f"{best['origin_city']}, {best['origin_state']}.",
            f"2. Book inland {best['inland_mode'].lower()} haul to {best['india_port']} "
            f"({best['india_unlocode']}).",
            f"3. Reserve {best['containers_required']} x {best['container_type']} containers "
            f"and complete export documentation / customs at Indian port.",
            f"4. Book ocean freight {best['india_unlocode']} → {best['destination_unlocode']} "
            f"({best['service_type']}, ~{best['ocean_transit_days']} sea days).",
            f"5. Clear cargo at {best['destination_port']}, {best['demand_country']}.",
        ]

    cost_breakdown = {
        "inland_cost_usd": float(best["inland_cost_usd"]),
        "origin_port_charge_usd": float(best["origin_port_charge_usd"]),
        "destination_port_charge_usd": float(best["destination_port_charge_usd"]),
        "container_cost_usd": float(best["container_cost_usd"]),
        "ocean_freight_usd": float(best["ocean_freight_usd"]),
        "total_logistics_cost_usd": float(best["total_logistics_cost_usd"]),
        "cost_per_ton_usd": float(best["cost_per_ton_usd"]),
    }

    result = {
        "recommend_export": True,
        "decision_summary": decision_text,
        "purchase_guidance": purchase_note,
        "demand_guidance": demand_note,
        "action_plan": action_plan,
        "best_route": {
            "rank": int(best["rank"]),
            "commodity": best["commodity"],
            "origin": f"{best['origin_city']}, {best['origin_state']}",
            "india_port": best["india_port"],
            "india_unlocode": best["india_unlocode"],
            "destination_port": best["destination_port"],
            "destination_unlocode": best["destination_unlocode"],
            "demand_country": best["demand_country"],
            "container_type": best["container_type"],
            "containers_required": int(best["containers_required"]),
            "inland_mode": best["inland_mode"],
            "service_type": best["service_type"],
            "freight_source": best["freight_source"],
            "total_transit_days": float(best["total_transit_days"]),
            "optimization_score": float(best["optimization_score"]),
            "cost_breakdown_usd": cost_breakdown,
        },
        "alternative_route": None,
        "top_routes": ranked.to_dict(orient="records"),
    }

    if alt:
        result["alternative_route"] = {
            "india_port": alt["india_port"],
            "destination_port": alt["destination_port"],
            "total_logistics_cost_usd": float(alt["total_logistics_cost_usd"]),
            "total_transit_days": float(alt["total_transit_days"]),
            "why_second": (
                "Next-best option if preferred port is congested or vessel space is unavailable."
            ),
        }

    return result


def recommend_export_route(
    commodity: str,
    demand_country: str,
    quantity_tons: Optional[float] = None,
    container_type: str = "20FT",
    origin_state: Optional[str] = None,
    origin_city: Optional[str] = None,
    cost_weight: float = 0.7,
    time_weight: float = 0.3,
    top_n: int = 5,
    planning_containers: int = 1,
    predicted_india_price_inr_per_quintal: Optional[float] = None,
    demand_score: Optional[float] = None,
    horizon_month: Optional[str] = None,
) -> dict[str, Any]:
    """
    End-to-end Phase-3 API.

    Plug in Phase-1 (demand country + commodity + demand_score) and
    Phase-2 (predicted India price) outputs here.

    Pass quantity_tons=None to plan by container (no import quantity needed).
    """
    ranked = optimize_routes(
        commodity=commodity,
        demand_country=demand_country,
        quantity_tons=quantity_tons,
        container_type=container_type,
        origin_state=origin_state,
        origin_city=origin_city,
        cost_weight=cost_weight,
        time_weight=time_weight,
        top_n=top_n,
        planning_containers=planning_containers,
    )
    return build_decision(
        ranked,
        predicted_india_price_inr_per_quintal=predicted_india_price_inr_per_quintal,
        demand_score=demand_score,
        horizon_month=horizon_month,
    )


def save_decision(decision: dict[str, Any], path: str | Path) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    # Compact top_routes for JSON readability is fine as-is
    with out.open("w", encoding="utf-8") as f:
        json.dump(decision, f, indent=2, ensure_ascii=False, default=str)
    return out


def print_decision(decision: dict[str, Any]) -> None:
    best = decision["best_route"]
    bd = best["cost_breakdown_usd"]

    print("=" * 72)
    print(" EXPORT AI - LOGISTICS OPTIMIZATION DECISION")
    print("=" * 72)
    print()
    print(decision["decision_summary"])
    print()
    if decision.get("purchase_guidance"):
        print("Purchase:", decision["purchase_guidance"])
    if decision.get("demand_guidance"):
        print("Demand:  ", decision["demand_guidance"])
    print()
    print("Action plan:")
    for step in decision["action_plan"]:
        print(" ", step)
    print()
    print("Cost breakdown (USD):")
    print(f"  Inland haulage     : {bd['inland_cost_usd']:,.2f}")
    print(f"  Origin port charges: {bd['origin_port_charge_usd']:,.2f}")
    print(f"  Dest. port charges : {bd['destination_port_charge_usd']:,.2f}")
    print(f"  Containers         : {bd['container_cost_usd']:,.2f}")
    print(f"  Ocean freight      : {bd['ocean_freight_usd']:,.2f}")
    print(f"  TOTAL              : {bd['total_logistics_cost_usd']:,.2f}")
    print(f"  Per ton            : {bd['cost_per_ton_usd']:,.2f}")
    print()
    if decision.get("alternative_route"):
        alt = decision["alternative_route"]
        print(
            f"Alternative: {alt['india_port']} → {alt['destination_port']} | "
            f"${alt['total_logistics_cost_usd']:,.2f} | {alt['total_transit_days']} days"
        )
        print(f"  ({alt['why_second']})")
    print()
    print("Top ranked routes:")
    for row in decision["top_routes"]:
        print(
            f"  #{row['rank']}  {row['india_port']} → {row['destination_port']} | "
            f"${row['total_logistics_cost_usd']:,.2f} | {row['total_transit_days']}d | "
            f"score={row['optimization_score']}"
        )
    print("=" * 72)
