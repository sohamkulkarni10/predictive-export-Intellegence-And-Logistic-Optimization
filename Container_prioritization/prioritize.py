"""
Container prioritization — decide which commodity/country gets scarce containers.

Input: logistics lanes with net profit + demand score
Output: allocation plan for N containers
"""

from __future__ import annotations

from typing import Any


def _norm(values: list[float]) -> list[float]:
    if not values:
        return []
    mn, mx = min(values), max(values)
    if mx == mn:
        return [0.5] * len(values)
    return [(v - mn) / (mx - mn) for v in values]


def prioritize_containers(
    opportunities: list[dict[str, Any]],
    available_containers: int = 6,
    container_type: str = "20FT",
) -> dict[str, Any]:
    """
    Rank lanes by demand + profit + logistics, then split containers.
    Example: 6 containers → maybe 3 to best lane, 2 to next, 1 to third.
    """
    if available_containers < 1:
        raise ValueError("available_containers must be >= 1")
    if not opportunities:
        raise ValueError("No opportunities to prioritize")

    demand = [float(o.get("demand_score", 0) or 0) for o in opportunities]
    profits = [float(o.get("net_profit_inr") or o.get("net_profit_usd_per_ton") or 0) for o in opportunities]
    costs = [float(o.get("cost_per_ton_usd", 1) or 1) for o in opportunities]
    days = [float(o.get("total_transit_days", 1) or 1) for o in opportunities]

    d_n = _norm(demand)
    p_n = _norm(profits)
    c_n = [1 - x for x in _norm(costs)]
    t_n = [1 - x for x in _norm(days)]

    scored = []
    for i, opp in enumerate(opportunities):
        score = 0.40 * d_n[i] + 0.35 * p_n[i] + 0.15 * c_n[i] + 0.10 * t_n[i]
        scored.append({**opp, "priority_score": round(score, 4)})

    scored.sort(key=lambda x: x["priority_score"], reverse=True)

    remaining = available_containers
    allocations = []
    for i, row in enumerate(scored):
        if remaining <= 0:
            allocations.append(
                {
                    **row,
                    "containers_allocated": 0,
                    "export_first": False,
                    "priority_rank": i + 1,
                    "container_type": container_type,
                }
            )
            continue

        leftover = len(scored) - i - 1
        weights = [max(0.05, s["priority_score"]) for s in scored[i:]]
        share = max(1, int(round(remaining * (weights[0] / sum(weights)))))
        share = min(share, remaining)
        if leftover > 0 and remaining - share < leftover:
            share = max(1, remaining - leftover)

        allocations.append(
            {
                **row,
                "containers_allocated": int(share),
                "export_first": i == 0,
                "priority_rank": i + 1,
                "container_type": container_type,
            }
        )
        remaining -= share

    if remaining > 0 and allocations:
        allocations[0]["containers_allocated"] += remaining
        remaining = 0

    first = next((a for a in allocations if a.get("export_first")), allocations[0])
    summary = (
        f"With {available_containers} x {container_type} containers, "
        f"export {first['commodity']} to {first['country']} first "
        f"({first['containers_allocated']} containers) for highest profit priority."
    )
    return {
        "available_containers": available_containers,
        "container_type": container_type,
        "allocations": allocations,
        "export_first": {
            "commodity": first["commodity"],
            "country": first["country"],
            "containers": first["containers_allocated"],
            "priority_score": first["priority_score"],
            "india_port": first.get("india_port"),
            "destination_port": first.get("destination_port"),
            "net_profit_inr": first.get("net_profit_inr"),
            "net_profit_inr_per_ton": first.get("net_profit_inr_per_ton"),
            "net_profit_usd_per_ton": first.get("net_profit_usd_per_ton"),
        },
        "summary": summary,
        "unallocated_containers": remaining,
    }


if __name__ == "__main__":
    demo = [
        {"commodity": "Onion", "country": "Saudi Arabia", "demand_score": 0.86, "net_profit_inr": 42000, "cost_per_ton_usd": 95, "total_transit_days": 12},
        {"commodity": "Wheat", "country": "Bangladesh", "demand_score": 0.78, "net_profit_inr": 28000, "cost_per_ton_usd": 70, "total_transit_days": 8},
        {"commodity": "Sugar", "country": "Germany", "demand_score": 0.71, "net_profit_inr": 31000, "cost_per_ton_usd": 110, "total_transit_days": 22},
    ]
    print(prioritize_containers(demo, available_containers=6))
