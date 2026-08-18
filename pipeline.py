"""
Full pipeline: demand (Groq llama) → price → logistics → containers → explanations.

Rules:
- Demand uses Demand_prediction Groq agent + your model
- Logistics costs from Logistics_Costs dataset
- Negative net-profit lanes are hidden; profitable alternatives are shown instead
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from containers import prioritize_containers
from db import save_logistics_costs, save_pipeline_run
from demand import predict_top_demand
from explain import build_explanations
from logistics import (
    container_payload_tons,
    estimate_net_profit,
    plan_lane,
    trade_pairs_for_commodity,
)
from price import predict_prices


def _next_month_label() -> str:
    now = datetime.now()
    year = now.year + (1 if now.month == 12 else 0)
    month = 1 if now.month == 12 else now.month + 1
    return f"{year:04d}-{month:02d}"


def _is_profitable(lane: dict[str, Any]) -> bool:
    if not lane.get("ok"):
        return False
    profit = lane.get("net_profit_usd_per_ton")
    if profit is None and lane.get("profit"):
        profit = lane["profit"].get("net_profit_usd_per_ton")
    return float(profit or 0) > 0


def _plan_many(
    candidates: list[dict[str, Any]],
    price_map: dict[str, float],
    *,
    container_type: str,
    payload: float,
    horizon: str,
    cost_weight: float,
    time_weight: float,
) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    lanes: list[dict[str, Any]] = []
    for opp in candidates:
        key = (str(opp["commodity"]).lower(), str(opp["country"]).lower())
        if key in seen:
            continue
        seen.add(key)
        price = price_map.get(opp["commodity"])
        if price is None:
            # try case-insensitive
            for k, v in price_map.items():
                if k.lower() == str(opp["commodity"]).lower():
                    price = v
                    break
        lane = plan_lane(
            commodity=opp["commodity"],
            country=opp["country"],
            demand_score=float(opp.get("demand_score") or 0.5),
            predicted_india_price_inr=price,
            container_type=container_type,
            payload_tons=payload,
            horizon_month=horizon,
            cost_weight=cost_weight,
            time_weight=time_weight,
        )
        lanes.append(lane)
    return lanes


def _expand_profitable_alternatives(
    base_ops: list[dict[str, Any]],
    price_map: dict[str, float],
    *,
    container_type: str,
    payload: float,
    horizon: str,
    cost_weight: float,
    time_weight: float,
    need: int,
) -> list[dict[str, Any]]:
    """If demand lanes lose money, try other trade countries for same commodities."""
    extra: list[dict[str, Any]] = []
    tried = {(o["commodity"].lower(), o["country"].lower()) for o in base_ops}
    for opp in base_ops:
        for pair in trade_pairs_for_commodity(opp["commodity"]):
            key = (pair["commodity"].lower(), pair["country"].lower())
            if key in tried:
                continue
            tried.add(key)
            extra.append(
                {
                    "commodity": pair["commodity"],
                    "country": pair["country"],
                    "demand_score": float(opp.get("demand_score") or 0.45) * 0.92,
                    "evidence": "trade_alt_for_profit",
                }
            )
    if not extra:
        return []
    return _plan_many(
        extra,
        price_map,
        container_type=container_type,
        payload=payload,
        horizon=horizon,
        cost_weight=cost_weight,
        time_weight=time_weight,
    )


def run_pipeline(
    demand_news: str = "",
    price_news: str = "",
    *,
    available_containers: int = 6,
    container_type: str = "20FT",
    top_n: int = 3,
    cost_weight: float = 0.7,
    time_weight: float = 0.3,
    auto_news: bool = True,
) -> dict[str, Any]:
    """
    Automated multi-agent pipeline:
      News Agent (GDELT/Google/NewsAPI) → Demand Agent → Price Agent
      → Logistics Agent → Container Agent → Groq Explain Agent
    """
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    horizon = _next_month_label()
    payload = container_payload_tons(container_type)

    news_fetch = None
    demand_news = (demand_news or "").strip()
    price_news = (price_news or "").strip()

    # News Agent — auto fetch from verified APIs unless user pasted override
    if auto_news or not demand_news:
        from news_fetcher import fetch_live_news

        news_fetch = fetch_live_news()
        if auto_news or not demand_news:
            demand_news = news_fetch["demand_news"]
        if auto_news or not price_news:
            price_news = news_fetch["price_news"]

    price_news = price_news or demand_news
    if not demand_news:
        raise ValueError("No demand news available (API fetch failed and no paste provided)")

    # Stage 1 — ask for more candidates so we can drop loss-making ones
    demand = predict_top_demand(demand_news, top_n=max(top_n + 4, 7))
    opportunities = demand["top_opportunities"]
    commodities = sorted({o["commodity"] for o in opportunities})

    # Stage 2
    prices = predict_prices(commodities, price_news)
    price_map = {
        p["commodity"]: p.get("predicted_next_month_price_inr")
        for p in prices["predictions"]
        if p.get("predicted_next_month_price_inr") is not None
    }

    # Stage 3 — plan + keep only positive profit
    logistics_raw = _plan_many(
        opportunities,
        price_map,
        container_type=container_type,
        payload=payload,
        horizon=horizon,
        cost_weight=cost_weight,
        time_weight=time_weight,
    )
    profitable = [l for l in logistics_raw if _is_profitable(l)]

    if len(profitable) < top_n:
        alts = _expand_profitable_alternatives(
            opportunities,
            price_map,
            container_type=container_type,
            payload=payload,
            horizon=horizon,
            cost_weight=cost_weight,
            time_weight=time_weight,
            need=top_n,
        )
        for lane in alts:
            if not _is_profitable(lane):
                continue
            key = (lane["commodity"].lower(), lane["country"].lower())
            if any(
                (p["commodity"].lower(), p["country"].lower()) == key for p in profitable
            ):
                continue
            profitable.append(lane)
            if len(profitable) >= top_n:
                break

    profitable.sort(
        key=lambda x: (
            float(x.get("net_profit_usd_per_ton") or 0),
            float(x.get("demand_score") or 0),
        ),
        reverse=True,
    )
    logistics_results = profitable[:top_n]

    if not logistics_results:
        raise RuntimeError(
            "No profitable export lanes found for this news. "
            "Try different country/commodity news or check trade sell prices."
        )

    # Demand list must be ranked by DEMAND SCORE (highest first),
    # not by logistics profit order — keeps dashboard/cards consistent.
    shown_ops = []
    for lane in logistics_results:
        shown_ops.append(
            {
                "commodity": lane["commodity"],
                "country": lane["country"],
                "demand_score": float(lane.get("demand_score") or 0),
                "predicted_direction": "Profitable",
                "news_snippet": next(
                    (
                        o.get("news_snippet")
                        for o in opportunities
                        if o["commodity"] == lane["commodity"]
                        and o["country"] == lane["country"]
                    ),
                    f"{lane['commodity']} demand in {lane['country']}",
                ),
                "evidence": "demand_model + profitable_filter",
            }
        )
    shown_ops.sort(key=lambda o: float(o.get("demand_score") or 0), reverse=True)
    for i, opp in enumerate(shown_ops):
        opp["rank"] = i + 1
    demand["top_opportunities"] = shown_ops
    demand["top_countries"] = [o["country"] for o in shown_ops]
    demand["commodities_involved"] = sorted({o["commodity"] for o in shown_ops})
    demand["note"] = (
        "Top opportunities after demand model + Groq news read. "
        "Loss-making lanes are hidden; profitable alternatives shown instead."
    )
    demand["hidden_loss_making"] = [
        {
            "commodity": l.get("commodity"),
            "country": l.get("country"),
            "net_profit_usd_per_ton": l.get("net_profit_usd_per_ton"),
        }
        for l in logistics_raw
        if l.get("ok") and not _is_profitable(l)
    ]

    # Stage 4
    prioritization = prioritize_containers(
        logistics_results,
        available_containers=available_containers,
        container_type=container_type,
    )

    alloc_map = {(a["commodity"], a["country"]): a for a in prioritization["allocations"]}
    final_lanes = []
    for lane in logistics_results:
        alloc = alloc_map.get((lane["commodity"], lane["country"]), {})
        ctrs = int(alloc.get("containers_allocated") or 0)
        profit = estimate_net_profit(
            commodity=lane["commodity"],
            country=lane["country"],
            demand_score=float(lane.get("demand_score") or 0),
            predicted_india_price_inr=float(lane.get("predicted_india_price_inr") or 0),
            cost_per_ton_usd=float(lane.get("cost_per_ton_usd") or 0),
            cost_per_container_usd=float(lane.get("cost_per_container_usd") or 0),
            payload_tons=payload,
            containers_allocated=ctrs,
            avg_export_price_usd_per_ton=lane.get("avg_export_price_usd_per_ton"),
            quantity_tons=payload * max(ctrs, 1),
        )
        # filter path list to profitable only
        paths = [p for p in (lane.get("all_paths") or []) if float(p.get("net_profit_usd_per_ton") or 0) > 0]
        final_lanes.append(
            {
                **lane,
                "all_paths": paths,
                "priority_rank": alloc.get("priority_rank"),
                "priority_score": alloc.get("priority_score"),
                "containers_allocated": ctrs,
                "export_first": alloc.get("export_first", False),
                "profit": profit,
                "net_profit_usd_per_ton": profit["net_profit_usd_per_ton"],
                "net_profit_inr": profit["net_profit_inr"],
                "net_profit_inr_per_ton": profit["net_profit_inr_per_ton"],
                "net_profit_inr_per_container": profit["net_profit_inr_per_container"],
                "net_profit_usd_for_allocation": profit["net_profit_usd_for_allocation"],
                "net_profit_inr_for_allocation": profit["net_profit_inr_for_allocation"],
                "fx_inr_per_usd": profit["fx_inr_per_usd"],
            }
        )

    final_lanes.sort(key=lambda x: (x.get("priority_rank") is None, x.get("priority_rank") or 999))

    # price cards only for shown commodities
    shown_commodities = {l["commodity"] for l in logistics_results}
    price_cards = [p for p in prices["predictions"] if p.get("commodity") in shown_commodities]
    prices = {**prices, "predictions": price_cards or prices["predictions"]}

    result: dict[str, Any] = {
        "run_id": run_id,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "horizon_month": horizon,
        "pipeline_agents": [
            "News Agent (GDELT / Google News / NewsAPI)",
            "Demand Agent (ML + Groq)",
            "Price Agent (XGBoost + news adjustment)",
            "Logistics Agent",
            "Container Agent",
            "Explain Agent (Groq LLM)",
        ],
        "news_fetch": news_fetch,
        "inputs": {
            "available_containers": available_containers,
            "container_type": container_type,
            "top_n": top_n,
            "auto_news": auto_news,
            "demand_news_preview": demand_news[:500],
            "price_news_preview": price_news[:500],
        },
        "stage1_demand": demand,
        "stage2_prices": prices,
        "stage3_logistics": logistics_results,
        "stage4_container_priority": prioritization,
        "final_decisions": {
            "summary": prioritization["summary"],
            "export_first": prioritization["export_first"],
            "lanes": final_lanes,
            "price_cards": prices["predictions"],
        },
    }

    explanations, llm_meta = build_explanations(result)
    result["agent_explanations"] = explanations
    result["llm"] = llm_meta

    save_logistics_costs(run_id, logistics_results)
    save_pipeline_run(run_id, result)
    return result
