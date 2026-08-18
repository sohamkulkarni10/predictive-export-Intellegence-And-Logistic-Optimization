"""
Stage 1 — Demand: call Demand_prediction/predict_top3_from_news.py

Uses your trained demand_model_bundle.joblib + Groq news reading.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEMAND_DIR = ROOT / "Demand_prediction"
if str(DEMAND_DIR) not in sys.path:
    sys.path.insert(0, str(DEMAND_DIR))

from predict_top3_from_news import predict_top3_from_news  # noqa: E402


def predict_top_demand(news_text: str, top_n: int = 3) -> dict[str, Any]:
    result = predict_top3_from_news(news_text, top_n=top_n)
    # Keep API shape used by pipeline / frontend
    opportunities = []
    for row in result["top_opportunities"]:
        opportunities.append(
            {
                "rank": row["rank"],
                "commodity": row["commodity"],
                "country": row["country"],
                "demand_score": float(row["demand_score"]),
                "demand_percentage": row.get("demand_percentage"),
                "predicted_direction": row.get("predicted_direction"),
                "trend_vs_current_month": row.get("trend_vs_current_month"),
                "forecast_month": row.get("forecast_month"),
                "news_snippet": row.get("news_snippet"),
                "mentions": 1,
                "evidence": "demand_model_bundle",
            }
        )
    return {
        "top_opportunities": opportunities,
        "top_countries": result["top_countries"],
        "commodities_involved": result["commodities_involved"],
        "method": result["method"],
        "articles_parsed": result["articles_parsed"],
        "ai_explanation": result.get("ai_explanation"),
        "note": result.get("note"),
    }
