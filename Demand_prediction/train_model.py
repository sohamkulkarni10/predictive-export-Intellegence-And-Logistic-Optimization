"""
Train demand_model_bundle.joblib from available news CSV.
Run once:  python train_model.py
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBRegressor

BASE = Path(__file__).resolve().parent
DATA_CANDIDATES = [
    BASE / "clean_english.csv",
    BASE / "final_news_dataset_cleaned_english.csv",
    BASE / "synthetic_news_dataset.csv",
]
MODEL_PATH = BASE / "demand_model_bundle.joblib"

NUMERIC = [
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
CATEGORICAL = ["country", "commodity"]


def _find_data() -> Path:
    for path in DATA_CANDIDATES:
        if path.exists():
            return path
    raise FileNotFoundError("No news CSV found in Demand_prediction/")


def _article_signal(df: pd.DataFrame) -> pd.Series:
    neg = (-df["sentiment_score"]).clip(lower=0.0)
    pos = df["sentiment_score"].clip(lower=0.0)
    score = (
        0.25
        + 0.25 * df["shortage_flag"]
        + 0.20 * df["production_drop"]
        - 0.12 * df["production_rise"]
        + 0.14 * df["price_increase"]
        - 0.10 * df["price_decrease"]
        + 0.20 * (df["export_opportunity_score"] / 100.0)
        + 0.08 * df["confidence"]
        + 0.08 * neg
        - 0.03 * pos
    )
    return score.clip(0.01, 0.99)


def _monthly(news: pd.DataFrame) -> pd.DataFrame:
    frame = news.copy()
    frame["article_demand_signal"] = _article_signal(frame)
    frame["signal_weight"] = 0.25 + frame["confidence"]
    frame["weighted_signal"] = frame["article_demand_signal"] * frame["signal_weight"]
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
    monthly["previous_month"] = monthly.groupby(["country", "commodity"])["month"].shift(1)
    monthly["previous_probability"] = monthly.groupby(["country", "commodity"])[
        "current_demand_probability"
    ].shift(1)
    monthly["previous_article_count"] = monthly.groupby(["country", "commodity"])[
        "article_count"
    ].shift(1)

    month_ord = monthly["month"].map(lambda v: v.ordinal).astype(float)
    prev_ord = monthly["previous_month"].map(lambda v: v.ordinal if pd.notna(v) else np.nan)
    consecutive = monthly["previous_month"].notna() & (month_ord - prev_ord == 1)

    monthly["demand_lag1"] = np.where(
        consecutive, monthly["previous_probability"], monthly["current_demand_probability"]
    )
    monthly["article_growth"] = np.where(
        consecutive,
        (monthly["article_count"] - monthly["previous_article_count"])
        / monthly["previous_article_count"].clip(lower=1.0),
        0.0,
    )
    monthly["article_growth"] = monthly["article_growth"].replace([np.inf, -np.inf], 0.0).clip(-5, 5)
    monthly["year"] = monthly["month"].dt.year.astype(int)
    monthly["month_number"] = monthly["month"].dt.month.astype(int)

    # next-month target
    monthly["target"] = monthly.groupby(["country", "commodity"])[
        "current_demand_probability"
    ].shift(-1)
    return monthly.dropna(subset=["target"]).reset_index(drop=True)


def train() -> Path:
    path = _find_data()
    print("Training from:", path)
    news = pd.read_csv(path)
    news["date"] = pd.to_datetime(news["date"], errors="coerce")
    news = news.dropna(subset=["date", "country", "commodity"]).copy()
    news["country"] = news["country"].astype(str).str.strip()
    news["commodity"] = news["commodity"].astype(str).str.strip()
    news["sentiment"] = news["sentiment"].fillna("neutral").astype(str).str.lower().str.strip()
    for col in [
        "sentiment_score", "shortage_flag", "production_drop", "production_rise",
        "price_increase", "price_decrease", "export_opportunity_score", "confidence",
    ]:
        news[col] = pd.to_numeric(news[col], errors="coerce").fillna(0.0)
    news["month"] = news["date"].dt.to_period("M")

    monthly = _monthly(news)
    X = monthly[CATEGORICAL + NUMERIC]
    y = monthly["target"].astype(float)

    model = Pipeline(
        steps=[
            (
                "prep",
                ColumnTransformer(
                    transformers=[
                        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
                        ("num", "passthrough", NUMERIC),
                    ]
                ),
            ),
            (
                "xgb",
                XGBRegressor(
                    n_estimators=120,
                    max_depth=4,
                    learning_rate=0.08,
                    subsample=0.9,
                    colsample_bytree=0.9,
                    random_state=42,
                    n_jobs=2,
                ),
            ),
        ]
    )
    model.fit(X, y)
    bundle = {
        "model": model,
        "features": CATEGORICAL + NUMERIC,
        "source_csv": path.name,
        "rows_trained": int(len(monthly)),
    }
    joblib.dump(bundle, MODEL_PATH)
    print("Saved:", MODEL_PATH)
    return MODEL_PATH


if __name__ == "__main__":
    train()
