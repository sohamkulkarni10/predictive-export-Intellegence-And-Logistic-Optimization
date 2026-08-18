"""
CLI for Phase-3 logistics optimization.

Examples:
  python optimize_route.py --commodity Wheat --country Bangladesh --qty 100
  python optimize_route.py --input sample_demand_input.json
  python optimize_route.py --commodity Coffee --country UAE --qty 50 --origin-state Kerala
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from data_loader import list_commodities, list_demand_countries, load_all
from decision_engine import print_decision, recommend_export_route, save_decision


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Optimize India → demand-country export route for a commodity."
    )
    p.add_argument("--input", type=str, help="JSON file with demand/price prediction inputs")
    p.add_argument("--commodity", type=str, help="Commodity name (e.g. Wheat, Coffee)")
    p.add_argument("--country", type=str, help="Demand country (e.g. Bangladesh, UAE)")
    p.add_argument("--qty", type=float, default=100.0, help="Export quantity in tons")
    p.add_argument("--container", type=str, default="20FT", choices=["20FT", "40FT"])
    p.add_argument("--origin-state", type=str, default=None)
    p.add_argument("--origin-city", type=str, default=None)
    p.add_argument("--cost-weight", type=float, default=0.7, help="Weight for minimizing cost")
    p.add_argument("--time-weight", type=float, default=0.3, help="Weight for minimizing transit time")
    p.add_argument("--top", type=int, default=5, help="Number of ranked routes to show")
    p.add_argument("--price", type=float, default=None, help="Predicted India price INR/quintal")
    p.add_argument("--demand-score", type=float, default=None, help="Phase-1 demand score 0-1")
    p.add_argument("--month", type=str, default=None, help="Horizon month YYYY-MM")
    p.add_argument("--out", type=str, default=None, help="Save decision JSON to this path")
    p.add_argument("--list", action="store_true", help="List commodities and countries, then exit")
    return p


def main(argv: list[str] | None = None) -> int:
    # Avoid Windows console crashes on currency / unicode characters
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    args = _build_parser().parse_args(argv)
    data = load_all()

    if args.list:
        print("Commodities:", ", ".join(list_commodities(data["commodity_origins"])))
        print("Countries:  ", ", ".join(list_demand_countries(data["destination_ports"])))
        return 0

    payload: dict = {}
    if args.input:
        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))

    commodity = args.commodity or payload.get("commodity")
    country = args.country or payload.get("demand_country")
    if not commodity or not country:
        print("Error: --commodity and --country are required (or provide --input JSON).", file=sys.stderr)
        return 2

    decision = recommend_export_route(
        commodity=commodity,
        demand_country=country,
        quantity_tons=args.qty if args.input is None else float(payload.get("quantity_tons", args.qty)),
        container_type=args.container if args.input is None else payload.get("container_type", args.container),
        origin_state=args.origin_state or payload.get("origin_state"),
        origin_city=args.origin_city or payload.get("origin_city"),
        cost_weight=args.cost_weight if args.input is None else float(payload.get("cost_weight", args.cost_weight)),
        time_weight=args.time_weight if args.input is None else float(payload.get("time_weight", args.time_weight)),
        top_n=args.top,
        predicted_india_price_inr_per_quintal=(
            args.price
            if args.price is not None
            else payload.get("predicted_india_price_inr_per_quintal")
        ),
        demand_score=args.demand_score if args.demand_score is not None else payload.get("demand_score"),
        horizon_month=args.month or payload.get("horizon_month"),
    )

    print_decision(decision)

    out_path = args.out or str(Path(__file__).parent / "output" / "latest_decision.json")
    saved = save_decision(decision, out_path)
    print(f"\nSaved decision JSON → {saved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
