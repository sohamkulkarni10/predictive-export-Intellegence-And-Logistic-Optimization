"""
Stage 2 — Price prediction in INR per quintal.

Current price taken from commodities/monthly_price.csv for 2026-06
(June 2026 — your latest complete mandi month in the dataset).
Next-month price predicted with commodities/price_agent_tools.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
COMM = ROOT / "commodities"
if str(COMM) not in sys.path:
    sys.path.insert(0, str(COMM))

from price_agent_tools import predict_price  # noqa: E402
from llm import ask_llm  # noqa: E402

MONTHLY = COMM / "monthly_price.csv"
TRAIN = COMM / "training_dataset.csv"

# Your dataset "current" month (2026 June)
CURRENT_YEAR = 2026
CURRENT_MONTH = 6

ALLOWED_COMMODITIES = {
    "Coffee", "Cotton", "Maize", "Onion", "Soybean", "Sugar", "Turmeric", "Wheat"
}

POS = ["surge", "rise", "rising", "increase", "up", "bullish", "rally", "shortage", "tight", "higher", "firm"]
NEG = ["fall", "falling", "drop", "decline", "down", "bearish", "surplus", "glut", "lower", "soft", "eased"]


def _current_market(commodity: str) -> dict[str, float]:
    src = MONTHLY if MONTHLY.exists() else TRAIN
    df = pd.read_csv(src)
    df = df[df["commodity"].str.lower() == commodity.lower()].copy()
    if df.empty:
        raise ValueError(f"No price history for {commodity}")

    # Prefer exact 2026-06 row (per quintal INR in your dataset)
    june = df[(df["year"] == CURRENT_YEAR) & (df["month"] == CURRENT_MONTH)]
    if not june.empty:
        row = june.iloc[-1]
    else:
        df = df.sort_values(["year", "month"])
        row = df.iloc[-1]

    price = float(row["price"])
    return {
        "price": price,
        "price_change": float(row.get("price_change", 0) or 0),
        "price_pct_change": float(row.get("price_pct_change", 0) or 0),
        "MA7": float(row["MA7"]) if pd.notna(row.get("MA7")) else price,
        "MA30": float(row["MA30"]) if pd.notna(row.get("MA30")) else price,
        "as_of": f"{int(row['year']):04d}-{int(row['month']):02d}",
    }


def _news_feats_simple(news_text: str, commodity: str) -> dict[str, float]:
    parts = re.split(r"[\n.]+", news_text)
    relevant = [p for p in parts if commodity.lower() in p.lower()]
    text = " ".join(relevant) if relevant else news_text
    lower = text.lower()
    pos = sum(1 for w in POS if w in lower)
    neg = sum(1 for w in NEG if w in lower)
    total = max(1, pos + neg + 2)
    return {
        "total_news": float(max(1, pos + neg + 1)),
        "average_sentiment": float((pos - neg) / total),
        "positive_news": float(pos),
        "negative_news": float(neg),
        "neutral_news": float(max(0, total - pos - neg)),
        "news_growth": float(min(1.2, max(-0.8, (pos + neg) / total - 0.25))),
    }


def _news_feats_groq(news_text: str, commodity: str) -> dict[str, float] | None:
    prompt = f"""
Analyse India market news for {commodity}. Return ONLY JSON:
{{
  "total_news": 10,
  "average_sentiment": -0.2,
  "positive_news": 3,
  "negative_news": 5,
  "neutral_news": 2,
  "news_growth": 0.1
}}

NEWS:
{news_text[:2000]}
"""
    raw = ask_llm(prompt, system="Return only JSON for commodity price features.")
    if not raw:
        return None
    cleaned = raw.replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not m:
            return None
        try:
            data = json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    try:
        return {
            "total_news": float(data.get("total_news", 10)),
            "average_sentiment": float(data.get("average_sentiment", 0)),
            "positive_news": float(data.get("positive_news", 0)),
            "negative_news": float(data.get("negative_news", 0)),
            "neutral_news": float(data.get("neutral_news", 0)),
            "news_growth": float(data.get("news_growth", 0)),
        }
    except Exception:
        return None


def _news_price_adjustment(news: dict[str, float]) -> float:
    """
    Extra %-move from news so prediction changes with input.
    Example: strong bullish ~ +4%, strong bearish ~ -4%.
    """
    sentiment = float(news.get("average_sentiment", 0) or 0)  # roughly -1 .. +1
    pos = float(news.get("positive_news", 0) or 0)
    neg = float(news.get("negative_news", 0) or 0)
    growth = float(news.get("news_growth", 0) or 0)
    intensity = min(1.0, (pos + neg) / 8.0)
    # sentiment is main driver; growth adds a little
    adj = (0.045 * sentiment) + (0.015 * max(-1.0, min(1.0, growth)))
    return float(adj * (0.35 + 0.65 * intensity))


def predict_commodity_price(commodity: str, news_text: str) -> dict[str, Any]:
    name = commodity.strip().title()
    if name not in ALLOWED_COMMODITIES:
        # try case-insensitive match to allowed set
        matched = next((c for c in ALLOWED_COMMODITIES if c.lower() == commodity.lower()), None)
        if not matched:
            raise ValueError(f"{commodity} not in price dataset commodities")
        name = matched

    market = _current_market(name)
    # Keyword news features — deterministic, so bullish/bearish news changes the price
    news = _news_feats_simple(news_text, name)

    features = {**news, **{k: market[k] for k in ("price", "price_change", "price_pct_change", "MA7", "MA30")}}
    current = float(market["price"])
    base_pred = float(predict_price(features))
    # Model alone was almost ignoring news — add explicit news adjustment
    news_adj = _news_price_adjustment(news)
    predicted = base_pred * (1.0 + news_adj)
    predicted = float(np.clip(predicted, current * 0.65, current * 1.35))
    change_pct = ((predicted - current) / max(current, 1e-6)) * 100.0
    change_inr = predicted - current
    direction = "Increase" if change_pct > 0.3 else ("Decrease" if change_pct < -0.3 else "Stable")

    return {
        "commodity": name,
        "current_price_inr": round(current, 2),
        "current_as_of": market["as_of"],
        "predicted_next_month_price_inr": round(predicted, 2),
        "predicted_change_inr": round(change_inr, 2),
        "predicted_change_pct": round(change_pct, 2),
        "direction": direction,
        "unit": "INR_per_quintal",
        "news_adjustment_pct": round(news_adj * 100.0, 2),
        "note": (
            f"Current = dataset {market['as_of']} (INR/quintal). "
            f"Next month = XGBoost + news sentiment adjustment ({news_adj*100:+.2f}%)."
        ),
    }


def predict_prices(commodities: list[str], news_text: str) -> dict[str, Any]:
    if not news_text or not str(news_text).strip():
        raise ValueError("price_news is required")
    preds = []
    for c in commodities:
        try:
            preds.append(predict_commodity_price(c, news_text))
        except Exception as exc:
            preds.append({
                "commodity": c,
                "error": str(exc),
                "current_price_inr": None,
                "predicted_next_month_price_inr": None,
            })
    return {
        "predictions": preds,
        "horizon": "next_month",
        "currency": "INR_per_quintal",
        "current_month_used": f"{CURRENT_YEAR:04d}-{CURRENT_MONTH:02d}",
        "note": "Current price from commodities dataset 2026-06 (INR per quintal).",
    }
