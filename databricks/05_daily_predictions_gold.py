# Databricks notebook source
# MAGIC %md
# MAGIC # 05 — Daily gold predictions
# MAGIC
# MAGIC Once a day this notebook:
# MAGIC 1. Aggregates today's silver scores → top-3 (commodity, country) → `gold_demand_daily`
# MAGIC 2. Predicts next-month India prices for those commodities → `gold_price_forecast`
# MAGIC 3. Runs logistics + net profit + container prioritization → `gold_export_decisions`
# MAGIC
# MAGIC All reference data comes from Delta `ref_*` tables (notebook 01), not local CSVs.

# COMMAND ----------

import sys
from pathlib import Path

sys.path.insert(0, str(Path(".").resolve()))
from conf.config import full_name, model_volume

# COMMAND ----------

# MAGIC %md
# MAGIC ## Knobs for this daily run

# COMMAND ----------

from datetime import datetime

AVAILABLE_CONTAINERS = 6
CONTAINER_TYPE = "20FT"
TOP_N = 3
COST_WEIGHT = 0.7
TIME_WEIGHT = 0.3

RUN_DATE = datetime.now().date()
# Horizon = next calendar month label, e.g. 2026-08
_y = RUN_DATE.year + (1 if RUN_DATE.month == 12 else 0)
_m = 1 if RUN_DATE.month == 12 else RUN_DATE.month + 1
HORIZON_MONTH = f"{_y:04d}-{_m:02d}"
print("run_date=", RUN_DATE, "horizon=", HORIZON_MONTH)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Stage 1 — top demand pairs from silver
# MAGIC Average demand_score per (commodity, country) for today's scored demand news.
# MAGIC Prefer country diversity in the top-N (same rule as local `demand_service`).

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

silver = (
    spark.table(full_name("silver_news_scored"))
    .filter(F.col("news_type") == "demand")
    .filter(F.to_date(F.col("scored_at")) == F.lit(str(RUN_DATE)))
)

# If nothing scored today yet, fall back to the latest scored_at date.
if silver.count() == 0:
    latest = spark.table(full_name("silver_news_scored")).agg(F.max("scored_at").alias("m")).collect()[0]["m"]
    if latest is None:
        raise RuntimeError("silver_news_scored is empty — run notebook 03 first")
    silver = (
        spark.table(full_name("silver_news_scored"))
        .filter(F.col("news_type") == "demand")
        .filter(F.to_date(F.col("scored_at")) == F.to_date(F.lit(latest)))
    )
    print("No rows for today; using latest scored date:", latest)

agg = (
    silver.groupBy("commodity", "country")
    .agg(
        F.avg("demand_score").alias("demand_score"),
        F.count("*").alias("mentions"),
    )
)

ranked_pdf = agg.orderBy(F.col("demand_score").desc(), F.col("mentions").desc()).toPandas()

selected = []
used_countries = set()
for _, row in ranked_pdf.iterrows():
    if row["country"] in used_countries:
        continue
    selected.append(row.to_dict())
    used_countries.add(row["country"])
    if len(selected) >= TOP_N:
        break
if len(selected) < TOP_N:
    for _, row in ranked_pdf.iterrows():
        d = row.to_dict()
        if any(s["commodity"] == d["commodity"] and s["country"] == d["country"] for s in selected):
            continue
        selected.append(d)
        if len(selected) >= TOP_N:
            break

for i, s in enumerate(selected):
    s["rank"] = i + 1
    s["run_date"] = RUN_DATE
    s["horizon_month"] = HORIZON_MONTH
    s["demand_score"] = float(s["demand_score"])
    s["mentions"] = int(s["mentions"])

import pandas as pd

demand_out = pd.DataFrame(selected)[
    ["run_date", "rank", "commodity", "country", "demand_score", "mentions", "horizon_month"]
]
print(demand_out)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write `gold_demand_daily`
# MAGIC Replace today's partition-style rows (delete same run_date, then append).

# COMMAND ----------

spark.sql(
    f"DELETE FROM {full_name('gold_demand_daily')} WHERE run_date = DATE '{RUN_DATE}'"
)
(
    spark.createDataFrame(demand_out)
    .write.format("delta")
    .mode("append")
    .saveAsTable(full_name("gold_demand_daily"))
)
print("Wrote gold_demand_daily")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Stage 2 — next-month price forecasts
# MAGIC Load the price bundle. Build news features from today's **price** silver titles
# MAGIC (keyword counts, same idea as local `price_service`).
# MAGIC Current price + MA features come from `ref_monthly_price`.

# COMMAND ----------

import joblib
import numpy as np

price_bundle = joblib.load(f"{model_volume()}/price_model_bundle.joblib")
price_model = price_bundle["model"]
PRICE_FEATURES = price_bundle["features"]

POS_WORDS = [
    "surge", "rise", "rising", "increase", "up", "bullish", "rally",
    "strong demand", "shortage", "tight", "higher", "firm",
]
NEG_WORDS = [
    "fall", "falling", "drop", "decline", "down", "bearish", "surplus",
    "glut", "weak demand", "lower", "soft", "eased",
]


def news_feats_from_titles(titles: list, commodity: str) -> dict:
    relevant = [t for t in titles if commodity.lower() in (t or "").lower()]
    text = " ".join(relevant) if relevant else " ".join(titles)
    lower = text.lower()
    pos = sum(1 for w in POS_WORDS if w in lower)
    neg = sum(1 for w in NEG_WORDS if w in lower)
    total = max(1, pos + neg + 2)
    avg = (pos - neg) / total
    growth = min(1.2, max(-0.8, (pos + neg) / total - 0.25))
    return {
        "total_news": float(max(1, pos + neg + 1)),
        "average_sentiment": float(avg),
        "positive_news": float(pos),
        "negative_news": float(neg),
        "neutral_news": float(max(0, total - pos - neg)),
        "news_growth": float(growth),
    }


price_titles = [
    r["title_english"]
    for r in (
        spark.table(full_name("silver_news_scored"))
        .filter(F.col("news_type") == "price")
        .select("title_english")
        .limit(500)
        .collect()
    )
]
if not price_titles:
    # Fall back to demand titles if no price news landed yet
    price_titles = [s.get("commodity", "") for s in selected]

monthly = spark.table(full_name("ref_monthly_price")).toPandas()

price_rows = []
commodities = list({s["commodity"] for s in selected})
for commodity in commodities:
    hist = monthly[monthly["commodity"].str.lower() == commodity.lower()].copy()
    if hist.empty:
        print("No price history for", commodity, "- skip")
        continue
    hist = hist.sort_values(["year", "month"])
    row = hist.iloc[-1]
    price = float(row["price"])
    ma7 = float(row["MA7"]) if pd.notna(row.get("MA7")) else price
    ma30 = float(row["MA30"]) if pd.notna(row.get("MA30")) else price
    price_change = float(row.get("price_change", 0) or 0)
    price_pct_change = float(row.get("price_pct_change", 0) or 0)
    news = news_feats_from_titles(price_titles, commodity)
    feats = {
        **news,
        "price_change": price_change,
        "price_pct_change": price_pct_change,
        "ma_spread": (ma7 - ma30) / max(price, 1e-6),
        "momentum": price_change / max(price, 1e-6),
        "news_intensity": float(np.log1p(news["total_news"])),
    }
    X = pd.DataFrame([{k: feats[k] for k in PRICE_FEATURES}])
    pred_return = float(np.clip(price_model.predict(X)[0], -0.35, 0.35))
    predicted = price * (1.0 + pred_return)
    price_rows.append({
        "run_date": RUN_DATE,
        "commodity": commodity,
        "current_price_inr": round(price, 2),
        "predicted_next_month_price_inr": round(predicted, 2),
        "predicted_change_pct": round(pred_return * 100, 2),
        "horizon_month": HORIZON_MONTH,
    })

price_out = pd.DataFrame(price_rows)
print(price_out)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write `gold_price_forecast`

# COMMAND ----------

spark.sql(
    f"DELETE FROM {full_name('gold_price_forecast')} WHERE run_date = DATE '{RUN_DATE}'"
)
(
    spark.createDataFrame(price_out)
    .write.format("delta")
    .mode("append")
    .saveAsTable(full_name("gold_price_forecast"))
)
print("Wrote gold_price_forecast")
price_map = {
    r["commodity"]: r["predicted_next_month_price_inr"] for r in price_rows
}

# COMMAND ----------

# MAGIC %md
# MAGIC ## Stage 3 — logistics helpers (ported from `Logistics/`)
# MAGIC Plain functions. Dataframes come from Delta `ref_*` tables.

# COMMAND ----------

import math

INR_PER_USD = 83.5
EXPORT_OVERHEAD_RATE = 0.02
EARTH_RADIUS_KM = 6371.0
OCEAN_USD_PER_TEU_NM_20FT = 0.22
OCEAN_USD_PER_TEU_NM_40FT = 0.37
AVG_VESSEL_SPEED_KNOTS = 16.0
NM_PER_KM = 0.539957

COUNTRY_ALIASES = {
    "united arab emirates": "uae", "u.a.e.": "uae", "u.a.e": "uae",
    "usa": "united states", "us": "united states", "u.s.a.": "united states",
    "uk": "united kingdom", "u.k.": "united kingdom", "britain": "united kingdom",
    "holland": "netherlands", "korea": "south korea", "republic of korea": "south korea",
}


def haversine_km(lat1, lon1, lat2, lon2):
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def load_logistics():
    return {
        "ports": spark.table(full_name("ref_ports")).toPandas(),
        "destination_ports": spark.table(full_name("ref_destination_ports")).toPandas(),
        "freight_rates": spark.table(full_name("ref_freight_rates")).toPandas(),
        "port_charges": spark.table(full_name("ref_port_charges")).toPandas(),
        "container_cost": spark.table(full_name("ref_container_cost")).toPandas(),
        "commodity_origins": spark.table(full_name("ref_commodity_origins")).toPandas(),
        "inland_rates": spark.table(full_name("ref_inland_rates")).toPandas(),
    }


def resolve_origin(origins, commodity):
    df = origins[origins["commodity"].str.lower() == commodity.strip().lower()]
    if df.empty:
        raise ValueError(f"Unknown commodity '{commodity}'")
    return df.sort_values("production_share", ascending=False).iloc[0]


def resolve_dest_ports(destinations, country):
    key = COUNTRY_ALIASES.get(country.strip().lower(), country.strip().lower())
    df = destinations[destinations["country"].str.lower() == key]
    if df.empty:
        raise ValueError(f"Unknown demand country '{country}'")
    return df


def inland_cost_and_days(olat, olon, plat, plon, qty, inland_rates):
    distance_km = haversine_km(olat, olon, plat, plon)
    mode = "Rail" if distance_km >= 400 else "Truck"
    rate_row = inland_rates[inland_rates["mode"].str.lower() == mode.lower()]
    if rate_row.empty:
        rate_row = inland_rates.iloc[[0]]
    rate = float(rate_row.iloc[0]["rate_usd_per_ton_km"])
    min_charge = float(rate_row.iloc[0]["min_charge_usd"])
    speed = float(rate_row.iloc[0]["avg_speed_kmph"])
    road_km = distance_km * 1.25
    cost = max(min_charge, road_km * rate * qty)
    days = max(0.5, road_km / speed / 24.0)
    return {
        "inland_mode": mode,
        "inland_distance_km": round(road_km, 1),
        "inland_cost_usd": round(cost, 2),
        "inland_days": round(days, 2),
    }


def lookup_or_estimate_freight(freight_rates, sport, dport, container_type):
    mask = (
        (freight_rates["source_port_id"] == int(sport["port_id"]))
        & (freight_rates["destination_port_id"] == int(dport["destination_port_id"]))
        & (freight_rates["container_type"].str.upper() == container_type.upper())
    )
    rows = freight_rates.loc[mask]
    if not rows.empty:
        r = rows.iloc[0]
        return {
            "freight_cost_usd_per_container": float(r["freight_cost_usd"]),
            "ocean_transit_days": float(r["transit_days"]),
            "service_type": str(r["service_type"]),
        }
    # Distance model fallback
    sea_km = haversine_km(
        float(sport["latitude"]), float(sport["longitude"]),
        float(dport["latitude"]), float(dport["longitude"]),
    ) * 1.35
    sea_nm = sea_km * NM_PER_KM
    rate = OCEAN_USD_PER_TEU_NM_40FT if container_type.upper().startswith("40") else OCEAN_USD_PER_TEU_NM_20FT
    return {
        "freight_cost_usd_per_container": round(max(250.0, sea_nm * rate), 2),
        "ocean_transit_days": round(max(3.0, (sea_nm / AVG_VESSEL_SPEED_KNOTS) / 24.0 + 1.5), 1),
        "service_type": "Estimated",
    }


def best_route(commodity, country, data, container_type=CONTAINER_TYPE):
    """Pick the lowest cost/time-weighted India→destination route for 1 container."""
    origin = resolve_origin(data["commodity_origins"], commodity)
    dest_ports = resolve_dest_ports(data["destination_ports"], country)
    container = data["container_cost"][
        data["container_cost"]["container_type"].str.upper() == container_type.upper()
    ].iloc[0]
    max_payload = float(container["max_payload_tons"])
    n_containers = 1
    quantity_tons = n_containers * max_payload
    container_unit_cost = float(container["total_container_cost_usd"])

    rows = []
    for _, sport in data["ports"].iterrows():
        inland = inland_cost_and_days(
            float(origin["latitude"]), float(origin["longitude"]),
            float(sport["latitude"]), float(sport["longitude"]),
            quantity_tons, data["inland_rates"],
        )
        pc = data["port_charges"][data["port_charges"]["port_id"] == int(sport["port_id"])]
        loading_port_charge = float(pc.iloc[0]["total_port_charge_usd"]) if not pc.empty else 210.0

        for _, dport in dest_ports.iterrows():
            freight = lookup_or_estimate_freight(data["freight_rates"], sport, dport, container_type)
            ocean_cost = freight["freight_cost_usd_per_container"] * n_containers
            container_cost = container_unit_cost * n_containers
            dest_port_charge = loading_port_charge * 0.8 * n_containers
            origin_port_charge = loading_port_charge * n_containers
            total_logistics = (
                inland["inland_cost_usd"] + origin_port_charge + dest_port_charge
                + container_cost + ocean_cost
            )
            total_days = inland["inland_days"] + freight["ocean_transit_days"] + 2.0
            rows.append({
                "commodity": commodity,
                "country": country,
                "india_port": sport["port_name"],
                "destination_port": dport["port_name"],
                "origin_city": origin["origin_city"],
                "origin_state": origin["origin_state"],
                "inland_mode": inland["inland_mode"],
                "inland_distance_km": inland["inland_distance_km"],
                "total_logistics_cost_usd": round(total_logistics, 2),
                "total_transit_days": round(total_days, 1),
                "cost_per_ton_usd": round(total_logistics / quantity_tons, 2),
                "cost_per_container_usd": round(total_logistics / n_containers, 2),
                "service_type": freight["service_type"],
                "ocean_transit_days": freight["ocean_transit_days"],
                "payload_tons": max_payload,
            })

    cand = pd.DataFrame(rows)
    # Normalize cost + time, lower score is better
    def _norm(s):
        mn, mx = s.min(), s.max()
        return pd.Series([0.0] * len(s), index=s.index) if mx == mn else (s - mn) / (mx - mn)

    tw = COST_WEIGHT + TIME_WEIGHT
    cw, tmw = COST_WEIGHT / tw, TIME_WEIGHT / tw
    cand["score"] = cw * _norm(cand["total_logistics_cost_usd"]) + tmw * _norm(cand["total_transit_days"])
    return cand.sort_values(["score", "total_logistics_cost_usd"]).iloc[0].to_dict()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Profit + container prioritization (ported from backend services)

# COMMAND ----------

def estimate_net_profit(demand_score, predicted_india_price_inr, cost_per_ton_usd, payload_tons, containers_allocated=0):
    buy_usd_t = (float(predicted_india_price_inr) * 10.0) / INR_PER_USD
    demand = float(max(0.0, min(1.0, demand_score)))
    margin_rate = 0.05 + 0.22 * demand
    logistics = float(cost_per_ton_usd)
    logistics_penalty = max(0.0, (logistics - 80.0) * 0.05)
    revenue_usd_t = buy_usd_t * (1.0 + margin_rate) + logistics
    cost_usd_t = buy_usd_t + logistics + buy_usd_t * EXPORT_OVERHEAD_RATE + logistics_penalty
    net_per_ton = revenue_usd_t - cost_usd_t
    return {
        "net_profit_usd_per_ton": round(net_per_ton, 2),
        "net_profit_usd_per_container": round(net_per_ton * float(payload_tons), 2),
        "net_profit_usd_for_allocation": round(net_per_ton * float(payload_tons) * int(containers_allocated), 2),
    }


def _norm_list(values):
    if not values:
        return []
    mn, mx = min(values), max(values)
    if mx == mn:
        return [0.5 for _ in values]
    return [(v - mn) / (mx - mn) for v in values]


def prioritize_containers(opportunities, available_containers=AVAILABLE_CONTAINERS):
    demand = [float(o["demand_score"]) for o in opportunities]
    prices = [float(o.get("predicted_india_price_inr") or 0) for o in opportunities]
    costs = [float(o.get("cost_per_ton_usd") or 1) for o in opportunities]
    days = [float(o.get("total_transit_days") or 1) for o in opportunities]
    profits = [float(o.get("net_profit_usd_per_ton") or 0) for o in opportunities]

    d_n = _norm_list(demand)
    buy_n = [1 - x for x in _norm_list(prices)]
    cost_n = [1 - x for x in _norm_list(costs)]
    time_n = [1 - x for x in _norm_list(days)]
    profit_n = _norm_list(profits)
    log_n = [0.6 * c + 0.4 * t for c, t in zip(cost_n, time_n)]

    scored = []
    for i, opp in enumerate(opportunities):
        priority = 0.35 * d_n[i] + 0.20 * buy_n[i] + 0.20 * log_n[i] + 0.25 * profit_n[i]
        scored.append({**opp, "priority_score": round(priority, 4)})
    scored.sort(key=lambda x: x["priority_score"], reverse=True)

    remaining = available_containers
    allocations = []
    for i, row in enumerate(scored):
        if remaining <= 0:
            allocations.append({**row, "containers_allocated": 0, "export_first": False, "priority_rank": i + 1})
            continue
        weights = [max(0.05, s["priority_score"]) for s in scored[i:]]
        weight_sum = sum(weights) or 1.0
        share = max(1, int(round(remaining * (weights[0] / weight_sum))))
        share = min(share, remaining)
        leftover = len(scored) - i - 1
        if leftover > 0 and remaining - share < leftover:
            share = max(1, remaining - leftover)
        allocations.append({
            **row,
            "containers_allocated": int(share),
            "export_first": i == 0,
            "priority_rank": i + 1,
        })
        remaining -= share
    if remaining > 0 and allocations:
        allocations[0]["containers_allocated"] += remaining
    return allocations

# COMMAND ----------

# MAGIC %md
# MAGIC ## Run logistics + profit + containers for each top opportunity

# COMMAND ----------

data = load_logistics()
lanes = []
for opp in selected:
    commodity, country = opp["commodity"], opp["country"]
    try:
        route = best_route(commodity, country, data)
        pred_price = float(price_map.get(commodity, 0))
        profit = estimate_net_profit(
            demand_score=float(opp["demand_score"]),
            predicted_india_price_inr=pred_price,
            cost_per_ton_usd=float(route["cost_per_ton_usd"]),
            payload_tons=float(route["payload_tons"]),
            containers_allocated=0,
        )
        summary = (
            f"Export {commodity} from {route['india_port']} to {route['destination_port']} "
            f"({country}). Inland {route['inland_mode']} from {route['origin_city']}. "
            f"~${route['cost_per_ton_usd']}/ton, transit ~{route['total_transit_days']} days."
        )
        lanes.append({
            "commodity": commodity,
            "country": country,
            "demand_score": float(opp["demand_score"]),
            "predicted_india_price_inr": pred_price,
            "india_port": route["india_port"],
            "destination_port": route["destination_port"],
            "cost_per_ton_usd": float(route["cost_per_ton_usd"]),
            "total_transit_days": float(route["total_transit_days"]),
            "net_profit_usd_per_ton": profit["net_profit_usd_per_ton"],
            "payload_tons": float(route["payload_tons"]),
            "decision_summary": summary,
            "ok": True,
        })
    except Exception as exc:
        print("Lane failed:", commodity, country, exc)
        lanes.append({
            "commodity": commodity,
            "country": country,
            "demand_score": float(opp["demand_score"]),
            "predicted_india_price_inr": float(price_map.get(commodity, 0)),
            "india_port": None,
            "destination_port": None,
            "cost_per_ton_usd": 9999.0,
            "total_transit_days": 999.0,
            "net_profit_usd_per_ton": -9999.0,
            "payload_tons": 28.0,
            "decision_summary": f"Failed: {exc}",
            "ok": False,
        })

valid = [L for L in lanes if L.get("ok")]
if not valid:
    raise RuntimeError("Logistics failed for all opportunities")

allocations = prioritize_containers(valid, AVAILABLE_CONTAINERS)

# Rebuild profit with allocated containers
decision_rows = []
for a in allocations:
    profit = estimate_net_profit(
        demand_score=a["demand_score"],
        predicted_india_price_inr=a["predicted_india_price_inr"],
        cost_per_ton_usd=a["cost_per_ton_usd"],
        payload_tons=a["payload_tons"],
        containers_allocated=a["containers_allocated"],
    )
    # Plain-Python fallback explanation. Flask replaces this with Groq text
    # when a GROQ_API_KEY is present (rule from ARCHITECTURE.md).
    fallback_explanation = (
        f"Rank {a['priority_rank']}: {a['commodity']} to {a['country']} gets "
        f"{a['containers_allocated']} container(s) based on demand "
        f"{a['demand_score']:.2f}, logistics ${a['cost_per_ton_usd']}/ton and "
        f"net profit ${profit['net_profit_usd_per_ton']}/ton."
    )
    decision_rows.append({
        "run_date": RUN_DATE,
        "priority_rank": int(a["priority_rank"]),
        "commodity": a["commodity"],
        "country": a["country"],
        "india_port": a["india_port"],
        "destination_port": a["destination_port"],
        "cost_per_ton_usd": float(a["cost_per_ton_usd"]),
        "net_profit_usd_per_ton": float(profit["net_profit_usd_per_ton"]),
        "containers_allocated": int(a["containers_allocated"]),
        "export_first": bool(a["export_first"]),
        "decision_summary": a["decision_summary"],
        "llm_explanation": fallback_explanation,
    })

decisions_out = pd.DataFrame(decision_rows)
print(decisions_out)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write `gold_export_decisions`

# COMMAND ----------

spark.sql(
    f"DELETE FROM {full_name('gold_export_decisions')} WHERE run_date = DATE '{RUN_DATE}'"
)
(
    spark.createDataFrame(decisions_out)
    .write.format("delta")
    .mode("append")
    .saveAsTable(full_name("gold_export_decisions"))
)
print("Wrote gold_export_decisions")
print("Daily gold run complete for", RUN_DATE)
