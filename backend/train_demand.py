"""
Train demand models (single copy — run: python train_demand.py).

In:  Demand_prediction/final_news_dataset_cleaned_english.csv
Out: models/demand_model_bundle.joblib + demand_metrics.json

Predicts commodity, country, and demand_score from news text.
Uses TF-IDF + logistic/Ridge with strong regularization to limit overfitting on ~1.3k rows.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    r2_score,
)
from sklearn.model_selection import GroupKFold, StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Demand_prediction" / "final_news_dataset_cleaned_english.csv"
OUT = Path(__file__).resolve().parent / "models"
OUT.mkdir(parents=True, exist_ok=True)


def build_demand_score(df: pd.DataFrame) -> pd.Series:
    score = (
        (df["export_opportunity_score"].fillna(0) / 100.0) * df["confidence"].fillna(0).clip(0, 1)
        + 0.12 * df["shortage_flag"].fillna(0)
        + 0.08 * df["production_drop"].fillna(0)
        + 0.05 * (df["sentiment_score"].fillna(0) < 0).astype(float)
        - 0.08 * df["production_rise"].fillna(0)
    )
    return score.clip(0, 1)


def make_text(df: pd.DataFrame) -> pd.Series:
    return (
        df["title_english"].fillna("").astype(str)
        + " "
        + df["commodity"].fillna("").astype(str)
        + " "
        + df["country"].fillna("").astype(str)
    )


def train():
    df = pd.read_csv(DATA)
    df = df.dropna(subset=["title_english", "commodity", "country"]).copy()
    df["title_english"] = df["title_english"].astype(str).str.strip()
    df = df[df["title_english"].str.len() > 10].reset_index(drop=True)
    df["demand_score"] = build_demand_score(df)

    # Text-only inference features (commodity/country not leaked at predict time)
    X_text = df["title_english"].astype(str).to_numpy(dtype=object)
    y_commodity = df["commodity"].astype(str).to_numpy(dtype=object)
    y_country = df["country"].astype(str).to_numpy(dtype=object)
    y_score = df["demand_score"].astype(float).to_numpy()

    commodity_le = LabelEncoder().fit(y_commodity)
    country_le = LabelEncoder().fit(y_country)
    y_c = commodity_le.transform(y_commodity)
    y_k = country_le.transform(y_country)

    tfidf = TfidfVectorizer(
        max_features=2500,
        ngram_range=(1, 2),
        min_df=3,
        max_df=0.9,
        sublinear_tf=True,
        stop_words="english",
    )

    # Commodity classifier — stronger L2 to shrink overfit gap
    commodity_clf = Pipeline(
        [
            ("tfidf", tfidf),
            (
                "clf",
                LogisticRegression(
                    C=0.35,
                    max_iter=2500,
                    class_weight="balanced",
                    solver="lbfgs",
                    random_state=42,
                ),
            ),
        ]
    )

    country_clf = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    max_features=2500,
                    ngram_range=(1, 2),
                    min_df=3,
                    max_df=0.9,
                    sublinear_tf=True,
                    stop_words="english",
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    C=0.3,
                    max_iter=2500,
                    class_weight="balanced",
                    solver="lbfgs",
                    random_state=42,
                ),
            ),
        ]
    )

    # Demand score: TF-IDF + Ridge (linear = better generalization)
    score_model = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    max_features=2200,
                    ngram_range=(1, 2),
                    min_df=3,
                    max_df=0.9,
                    sublinear_tf=True,
                    stop_words="english",
                ),
            ),
            ("reg", Ridge(alpha=8.0, random_state=42)),
        ]
    )

    metrics = {}

    # Stratified CV for classifiers
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    commodity_pred = cross_val_predict(commodity_clf, X_text, y_c, cv=skf)
    country_pred = cross_val_predict(country_clf, X_text, y_k, cv=skf)
    metrics["commodity_accuracy_cv"] = float(accuracy_score(y_c, commodity_pred))
    metrics["commodity_f1_macro_cv"] = float(f1_score(y_c, commodity_pred, average="macro"))
    metrics["country_accuracy_cv"] = float(accuracy_score(y_k, country_pred))
    metrics["country_f1_macro_cv"] = float(f1_score(y_k, country_pred, average="macro"))

    # Group by commodity for score model to reduce leakage across similar rows
    gkf = GroupKFold(n_splits=5)
    score_oof = np.zeros(len(y_score))
    for train_idx, test_idx in gkf.split(X_text, y_score, groups=y_commodity):
        m = Pipeline(
            [
                (
                    "tfidf",
                    TfidfVectorizer(
                        max_features=2200,
                        ngram_range=(1, 2),
                        min_df=3,
                        max_df=0.9,
                        sublinear_tf=True,
                        stop_words="english",
                    ),
                ),
                ("reg", Ridge(alpha=8.0, random_state=42)),
            ]
        )
        m.fit(X_text[train_idx], y_score[train_idx])
        score_oof[test_idx] = m.predict(X_text[test_idx])

    score_oof = np.clip(score_oof, 0, 1)
    metrics["demand_mae_cv"] = float(mean_absolute_error(y_score, score_oof))
    metrics["demand_r2_cv"] = float(r2_score(y_score, score_oof))
    metrics["n_rows"] = int(len(df))
    metrics["commodities"] = commodity_le.classes_.tolist()
    metrics["countries"] = country_le.classes_.tolist()

    # Fit final models on all data
    commodity_clf.fit(X_text, y_c)
    country_clf.fit(X_text, y_k)
    score_model.fit(X_text, y_score)

    # Train vs CV gap sanity (overfit check on commodity)
    train_acc = accuracy_score(y_c, commodity_clf.predict(X_text))
    metrics["commodity_train_accuracy"] = float(train_acc)
    metrics["commodity_overfit_gap"] = float(train_acc - metrics["commodity_accuracy_cv"])

    artifact = {
        "commodity_model": commodity_clf,
        "country_model": country_clf,
        "score_model": score_model,
        "commodity_encoder": commodity_le,
        "country_encoder": country_le,
        "metrics": metrics,
        "version": "demand_v2_generalized",
    }
    path = OUT / "demand_model_bundle.joblib"
    joblib.dump(artifact, path)
    (OUT / "demand_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print("Saved", path)
    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    train()
