"""
Phase-3 integration helper.

Call this after Phase-1 (demand) and Phase-2 (India price) predictions.
"""

from __future__ import annotations

from typing import Any, Optional

from decision_engine import recommend_export_route, save_decision


def from_predictions(
    commodity: str,
    demand_country: str,
    *,
    quantity_tons: Optional[float] = None,
    container_type: str = "20FT",
    origin_state: Optional[str] = None,
    predicted_india_price_inr_per_quintal: Optional[float] = None,
    demand_score: Optional[float] = None,
    horizon_month: Optional[str] = None,
    cost_weight: float = 0.7,
    time_weight: float = 0.3,
    planning_containers: int = 1,
    save_path: Optional[str] = None,
) -> dict[str, Any]:
    """
    Bridge API for the full Export AI pipeline.

    Pass quantity_tons=None when import quantity is unknown (planning mode).
    """
    decision = recommend_export_route(
        commodity=commodity,
        demand_country=demand_country,
        quantity_tons=quantity_tons,
        container_type=container_type,
        origin_state=origin_state,
        cost_weight=cost_weight,
        time_weight=time_weight,
        planning_containers=planning_containers,
        predicted_india_price_inr_per_quintal=predicted_india_price_inr_per_quintal,
        demand_score=demand_score,
        horizon_month=horizon_month,
    )
    if save_path:
        save_decision(decision, save_path)
    return decision


if __name__ == "__main__":
    # Quick demo using sample-style inputs
    demo = from_predictions(
        commodity="Wheat",
        demand_country="Bangladesh",
        quantity_tons=100,
        predicted_india_price_inr_per_quintal=2450,
        demand_score=0.86,
        horizon_month="2026-08",
        save_path="output/pipeline_demo_decision.json",
    )
    from decision_engine import print_decision

    print_decision(demo)
