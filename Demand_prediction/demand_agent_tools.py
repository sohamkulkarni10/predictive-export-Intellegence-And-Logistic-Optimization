"""
Tools used by demand_agent.py.

The model predicts a NEWS-BASED next-month demand probability for a
country + commodity. It does not predict physical demand quantity because
clean_english.csv does not contain historical import/demand quantities.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import joblib
import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "demand_model_bundle.joblib"
DATA_CANDIDATES = [
    BASE_DIR / "clean_english.csv",
    BASE_DIR / "final_news_dataset_cleaned_english.csv",
    BASE_DIR / "synthetic_news_dataset.csv",
]

NUMERIC_FEATURES = [
    "article_count",
    "average_sentiment",
    "positive_share",
    "negative_share",
    "neutral_share",
    "shortage_share",
    "production_drop_share",
    "production_rise_share",
    "price_increase_share",
    "price_decrease_share",
    "average_export_opportunity",
    "average_confidence",
    "demand_lag1",
    "article_growth",
    "year",
    "month_number",
]

CATEGORICAL_FEATURES = ["country", "commodity"]
MODEL_FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES


def _find_dataset() -> Path:
    for path in DATA_CANDIDATES:
        if path.exists():
            return path
    names = ", ".join(path.name for path in DATA_CANDIDATES)
    raise FileNotFoundError(
        f"Dataset not found. Put {names} in this folder: {BASE_DIR}"
    )


def _load_bundle() -> Dict[str, Any]:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "demand_model_bundle.joblib was not found. "
            "Run every cell in demand_future.ipynb first."
        )
    return joblib.load(MODEL_PATH)


def _clean_news(df: pd.DataFrame) -> pd.DataFrame:
    required = {
        "commodity", "country", "date", "sentiment", "sentiment_score",
        "shortage_flag", "production_drop", "production_rise",
        "price_increase", "price_decrease", "export_opportunity_score",
        "confidence",
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing columns: {sorted(missing)}")

    result = df.copy()
    result["date"] = pd.to_datetime(result["date"], errors="coerce", utc=True).dt.tz_localize(None)
    result = result.dropna(subset=["date", "country", "commodity"])
    result["country"] = result["country"].astype(str).str.strip()
    result["commodity"] = result["commodity"].astype(str).str.strip()
    result["sentiment"] = (
        result["sentiment"].fillna("neutral").astype(str).str.lower().str.strip()
    )

    numeric_columns = [
        "sentiment_score", "shortage_flag", "production_drop",
        "production_rise", "price_increase", "price_decrease",
        "export_opportunity_score", "confidence",
    ]
    for column in numeric_columns:
        result[column] = pd.to_numeric(result[column], errors="coerce").fillna(0.0)

    result["sentiment_score"] = result["sentiment_score"].clip(-1.0, 1.0)
    result["export_opportunity_score"] = result["export_opportunity_score"].clip(0.0, 100.0)
    result["confidence"] = result["confidence"].clip(0.0, 1.0)
    for column in [
        "shortage_flag", "production_drop", "production_rise",
        "price_increase", "price_decrease",
    ]:
        result[column] = result[column].clip(0.0, 1.0)

    result["month"] = result["date"].dt.to_period("M")
    return result


def _article_demand_signal(df: pd.DataFrame) -> pd.Series:
    """Create a transparent proxy demand probability from news indicators."""
    negative_pressure = (-df["sentiment_score"]).clip(lower=0.0)
    positive_sentiment = df["sentiment_score"].clip(lower=0.0)

    score = (
        0.25
        + 0.25 * df["shortage_flag"]
        + 0.20 * df["production_drop"]
        - 0.12 * df["production_rise"]
        + 0.14 * df["price_increase"]
        - 0.10 * df["price_decrease"]
        + 0.20 * (df["export_opportunity_score"] / 100.0)
        + 0.08 * df["confidence"]
        + 0.08 * negative_pressure
        - 0.03 * positive_sentiment
    )
    return score.clip(0.01, 0.99)


def _monthly_features(news: pd.DataFrame) -> pd.DataFrame:
    frame = news.copy()
    frame["article_demand_signal"] = _article_demand_signal(frame)
    frame["signal_weight"] = 0.25 + frame["confidence"]
    frame["weighted_signal"] = (
        frame["article_demand_signal"] * frame["signal_weight"]
    )

    frame["positive_value"] = (frame["sentiment"] == "positive").astype(float)
    frame["negative_value"] = (frame["sentiment"] == "negative").astype(float)
    frame["neutral_value"] = (~frame["sentiment"].isin(["positive", "negative"])).astype(float)

    monthly = (
        frame.groupby(["country", "commodity", "month"], as_index=False)
        .agg(
            article_count=("date", "size"),
            average_sentiment=("sentiment_score", "mean"),
            positive_share=("positive_value", "mean"),
            negative_share=("negative_value", "mean"),
            neutral_share=("neutral_value", "mean"),
            shortage_share=("shortage_flag", "mean"),
            production_drop_share=("production_drop", "mean"),
            production_rise_share=("production_rise", "mean"),
            price_increase_share=("price_increase", "mean"),
            price_decrease_share=("price_decrease", "mean"),
            average_export_opportunity=("export_opportunity_score", "mean"),
            average_confidence=("confidence", "mean"),
            weighted_signal_sum=("weighted_signal", "sum"),
            total_weight=("signal_weight", "sum"),
        )
    )
    monthly["current_demand_probability"] = (
        monthly["weighted_signal_sum"] / monthly["total_weight"].replace(0, np.nan)
    ).fillna(0.5).clip(0.01, 0.99)

    monthly = monthly.sort_values(["country", "commodity", "month"]).reset_index(drop=True)
    group_keys = [monthly["country"], monthly["commodity"]]
    monthly["previous_month"] = monthly.groupby(["country", "commodity"])["month"].shift(1)
    monthly["previous_probability"] = monthly.groupby(["country", "commodity"])[
        "current_demand_probability"
    ].shift(1)
    monthly["previous_article_count"] = monthly.groupby(["country", "commodity"])[
        "article_count"
    ].shift(1)

    month_ordinal = monthly["month"].map(lambda value: value.ordinal).astype(float)
    previous_ordinal = monthly["previous_month"].map(
        lambda value: value.ordinal if pd.notna(value) else np.nan
    )
    consecutive = monthly["previous_month"].notna() & (
        month_ordinal - previous_ordinal == 1
    )
    monthly["demand_lag1"] = np.where(
        consecutive,
        monthly["previous_probability"],
        monthly["current_demand_probability"],
    )
    monthly["demand_roll2"] = (
        monthly["current_demand_probability"] + monthly["demand_lag1"]
    ) / 2.0
    monthly["article_growth"] = np.where(
        consecutive,
        (monthly["article_count"] - monthly["previous_article_count"])
        / monthly["previous_article_count"].clip(lower=1.0),
        0.0,
    )
    monthly["article_growth"] = monthly["article_growth"].replace(
        [np.inf, -np.inf], 0.0
    ).clip(-5.0, 5.0)
    monthly["year"] = monthly["month"].dt.year.astype(int)
    monthly["month_number"] = monthly["month"].dt.month.astype(int)
    return monthly


def _normalise_news_features(news_features: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    values: Dict[str, Any] = {
        "sentiment_score": 0.0,
        "shortage_flag": 0,
        "production_drop": 0,
        "production_rise": 0,
        "price_increase": 0,
        "price_decrease": 0,
        "export_opportunity_score": 0.0,
        "confidence": 0.5,
    }
    if news_features:
        values.update(news_features)

    values["sentiment_score"] = float(np.clip(float(values["sentiment_score"]), -1.0, 1.0))
    values["export_opportunity_score"] = float(
        np.clip(float(values["export_opportunity_score"]), 0.0, 100.0)
    )
    values["confidence"] = float(np.clip(float(values["confidence"]), 0.0, 1.0))
    for key in [
        "shortage_flag", "production_drop", "production_rise",
        "price_increase", "price_decrease",
    ]:
        values[key] = int(float(values[key]) >= 0.5)

    if values["sentiment_score"] > 0.15:
        values["sentiment"] = "positive"
    elif values["sentiment_score"] < -0.15:
        values["sentiment"] = "negative"
    else:
        values["sentiment"] = "neutral"
    return values


def _prediction_label(probability: float) -> str:
    if probability >= 0.70:
        return "Strong Increase"
    if probability >= 0.58:
        return "Increase"
    if probability >= 0.45:
        return "Stable"
    if probability >= 0.32:
        return "Decrease"
    return "Strong Decrease"


def predict_demand(
    country: str,
    commodity: str,
    news_features: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Predict next-month news-based demand for one country and commodity.

    news_features may contain:
    sentiment_score, shortage_flag, production_drop, production_rise,
    price_increase, price_decrease, export_opportunity_score, confidence.
    """
    bundle = _load_bundle()
    model = bundle["model"]
    data_path = _find_dataset()
    news = _clean_news(pd.read_csv(data_path))

    country_text = str(country).strip()
    commodity_text = str(commodity).strip()
    country_match = news["country"].str.casefold() == country_text.casefold()
    commodity_match = news["commodity"].str.casefold() == commodity_text.casefold()

    canonical_country = (
        news.loc[country_match, "country"].iloc[0] if country_match.any() else country_text.title()
    )
    canonical_commodity = (
        news.loc[commodity_match, "commodity"].iloc[0]
        if commodity_match.any()
        else commodity_text.title()
    )

    pair = news[country_match & commodity_match].copy()
    used_fallback_history = pair.empty
    if pair.empty:
        # Use all available history as a neutral baseline for unseen combinations.
        pair = news.copy()
        pair["country"] = canonical_country
        pair["commodity"] = canonical_commodity

    if news_features is not None:
        values = _normalise_news_features(news_features)
        current_month = pair["month"].max()
        new_row = {
            "commodity": canonical_commodity,
            "country": canonical_country,
            "date": current_month.to_timestamp(how="end").normalize(),
            "sentiment": values["sentiment"],
            "sentiment_score": values["sentiment_score"],
            "shortage_flag": values["shortage_flag"],
            "production_drop": values["production_drop"],
            "production_rise": values["production_rise"],
            "price_increase": values["price_increase"],
            "price_decrease": values["price_decrease"],
            "export_opportunity_score": values["export_opportunity_score"],
            "confidence": values["confidence"],
            "month": current_month,
        }
        pair = pd.concat([pair, pd.DataFrame([new_row])], ignore_index=True)

    monthly = _monthly_features(pair)
    #latest = monthly.sort_values("month").iloc[-1].copy()
    latest = monthly.sort_values("month").iloc[-1].copy(deep=True)
    latest["country"] = canonical_country
    latest["commodity"] = canonical_commodity

    model_input = pd.DataFrame([{feature: latest[feature] for feature in MODEL_FEATURES}])
    current = float(np.clip(model.predict(model_input)[0], 0.01, 0.99))

    # Project one month ahead from the recent country-commodity history.
    
    #history_values = monthly.sort_values("month")["current_demand_probability"].tail(4).to_numpy(dtype=float)
    history_values = (
    monthly.sort_values("month")["current_demand_probability"]
    .tail(4)
    .to_numpy(dtype=float)
    .copy()
    )
    if len(history_values) > 0:
        history_values[-1] = current
    if len(history_values) >= 2:
        x = np.arange(len(history_values), dtype=float)
        trend_slope = float(np.polyfit(x, history_values, 1)[0])
    else:
        trend_slope = 0.0
    trend_slope = float(np.clip(trend_slope, -0.10, 0.10))

    predicted = float(np.clip(current + 0.65 * trend_slope, 0.01, 0.99))
    change = predicted - current

    forecast_month = latest["month"] + 1
    if change > 0.02:
        trend = "Rising"
    elif change < -0.02:
        trend = "Falling"
    else:
        trend = "Stable"

    return {
        "forecast_month": str(forecast_month),
        "country": canonical_country,
        "commodity": canonical_commodity,
        "predicted_demand_probability": round(predicted, 4),
        "predicted_demand_percentage": round(predicted * 100.0, 2),
        "predicted_direction": _prediction_label(predicted),
        "trend_vs_current_month": trend,
        "current_demand_percentage": round(current * 100.0, 2),
        "probability_change_points": round(change * 100.0, 2),
        "trend_slope_per_month": round(trend_slope, 4),
        "latest_month_articles": int(latest["article_count"]),
        "average_confidence": round(float(latest["average_confidence"]), 4),
        "used_fallback_history": bool(used_fallback_history),
        "method": "XGBoost monthly demand signal + recent trend projection",
    }


def recommend_top_commodities(country: str, top_n: int = 3) -> list[Dict[str, Any]]:
    """Rank available commodities for one country using latest news history."""
    data_path = _find_dataset()
    news = _clean_news(pd.read_csv(data_path))
    country_text = str(country).strip()
    country_match = news["country"].str.casefold() == country_text.casefold()
    if country_match.any():
        canonical_country = news.loc[country_match, "country"].iloc[0]
        commodities = sorted(news.loc[country_match, "commodity"].dropna().unique())
    else:
        canonical_country = country_text.title()
        commodities = sorted(news["commodity"].dropna().unique())

    results = [predict_demand(canonical_country, commodity) for commodity in commodities]
    results.sort(
        key=lambda item: (
            item["predicted_demand_probability"],
            item["average_confidence"],
            item["latest_month_articles"],
        ),
        reverse=True,
    )
    return results[: max(1, int(top_n))]
