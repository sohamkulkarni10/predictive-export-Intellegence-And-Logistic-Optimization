# Databricks notebook source
# MAGIC %md
# MAGIC # 04 — Train demand + price models, log to MLflow, register
# MAGIC
# MAGIC Ports the anti-overfit training from:
# MAGIC - `backend/train_demand_model.py`
# MAGIC - `backend/train_price_model.py`
# MAGIC
# MAGIC Reads training rows from Delta (`ref_demand_training`, `ref_price_training`).
# MAGIC Writes joblib bundles to the model Volume (used by notebook 03) and registers
# MAGIC models in the Unity Catalog model registry.

# COMMAND ----------

import sys
from pathlib import Path

sys.path.insert(0, str(Path(".").resolve()))
from conf.config import demand_model_name, full_name, model_volume, price_model_name

# COMMAND ----------

# MAGIC %md
# MAGIC ## Imports + MLflow setup

# COMMAND ----------

import json
import os
import tempfile

import joblib
import mlflow
import mlflow.sklearn
import mlflow.xgboost
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, r2_score
from sklearn.model_selection import GroupKFold, StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBRegressor

mlflow.set_registry_uri("databricks-uc")
os.makedirs(model_volume(), exist_ok=True)

# COMMAND ----------

# MAGIC %md
# MAGIC # Part A — Demand model
# MAGIC
# MAGIC **Why this design**
# MAGIC - Only ~1.3k news rows → deep neural nets overfit easily.
# MAGIC - **TF-IDF + LogisticRegression / Ridge** with strong L2 (`C≈0.3`, `alpha=8`) shrinks weights.
# MAGIC - Inference uses **title text only** (no commodity/country leak at predict time).
# MAGIC - We track **train accuracy vs CV accuracy** — a large gap means overfitting.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Build demand_score label (same formula as local trainer)

# COMMAND ----------

def build_demand_score(df: pd.DataFrame) -> pd.Series:
    score = (
        (df["export_opportunity_score"].fillna(0) / 100.0) * df["confidence"].fillna(0).clip(0, 1)
        + 0.12 * df["shortage_flag"].fillna(0)
        + 0.08 * df["production_drop"].fillna(0)
        + 0.05 * (df["sentiment_score"].fillna(0) < 0).astype(float)
        - 0.08 * df["production_rise"].fillna(0)
    )
    return score.clip(0, 1)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load demand training rows from Delta

# COMMAND ----------

demand_pdf = spark.table(full_name("ref_demand_training")).toPandas()
demand_pdf = demand_pdf.dropna(subset=["title_english", "commodity", "country"]).copy()
demand_pdf["title_english"] = demand_pdf["title_english"].astype(str).str.strip()
demand_pdf = demand_pdf[demand_pdf["title_english"].str.len() > 10].reset_index(drop=True)
demand_pdf["demand_score"] = build_demand_score(demand_pdf)
print("Demand rows:", len(demand_pdf))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Train demand models + log to MLflow

# COMMAND ----------

X_text = demand_pdf["title_english"].astype(str).to_numpy(dtype=object)
y_commodity = demand_pdf["commodity"].astype(str).to_numpy(dtype=object)
y_country = demand_pdf["country"].astype(str).to_numpy(dtype=object)
y_score = demand_pdf["demand_score"].astype(float).to_numpy()

commodity_le = LabelEncoder().fit(y_commodity)
country_le = LabelEncoder().fit(y_country)
y_c = commodity_le.transform(y_commodity)
y_k = country_le.transform(y_country)

commodity_clf = Pipeline([
    ("tfidf", TfidfVectorizer(
        max_features=2500, ngram_range=(1, 2), min_df=3, max_df=0.9,
        sublinear_tf=True, stop_words="english",
    )),
    ("clf", LogisticRegression(
        C=0.35, max_iter=2500, class_weight="balanced",
        solver="lbfgs", random_state=42,
    )),
])

country_clf = Pipeline([
    ("tfidf", TfidfVectorizer(
        max_features=2500, ngram_range=(1, 2), min_df=3, max_df=0.9,
        sublinear_tf=True, stop_words="english",
    )),
    ("clf", LogisticRegression(
        C=0.3, max_iter=2500, class_weight="balanced",
        solver="lbfgs", random_state=42,
    )),
])

score_model = Pipeline([
    ("tfidf", TfidfVectorizer(
        max_features=2200, ngram_range=(1, 2), min_df=3, max_df=0.9,
        sublinear_tf=True, stop_words="english",
    )),
    ("reg", Ridge(alpha=8.0, random_state=42)),
])

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
commodity_pred = cross_val_predict(commodity_clf, X_text, y_c, cv=skf)
country_pred = cross_val_predict(country_clf, X_text, y_k, cv=skf)

# GroupKFold for score model — reduce leakage across same-commodity rows
gkf = GroupKFold(n_splits=5)
score_oof = np.zeros(len(y_score))
for train_idx, test_idx in gkf.split(X_text, y_score, groups=y_commodity):
    m = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=2200, ngram_range=(1, 2), min_df=3, max_df=0.9,
            sublinear_tf=True, stop_words="english",
        )),
        ("reg", Ridge(alpha=8.0, random_state=42)),
    ])
    m.fit(X_text[train_idx], y_score[train_idx])
    score_oof[test_idx] = m.predict(X_text[test_idx])
score_oof = np.clip(score_oof, 0, 1)

commodity_clf.fit(X_text, y_c)
country_clf.fit(X_text, y_k)
score_model.fit(X_text, y_score)

train_acc = float(accuracy_score(y_c, commodity_clf.predict(X_text)))
cv_acc = float(accuracy_score(y_c, commodity_pred))
demand_metrics = {
    "commodity_accuracy_cv": cv_acc,
    "commodity_f1_macro_cv": float(f1_score(y_c, commodity_pred, average="macro")),
    "country_accuracy_cv": float(accuracy_score(y_k, country_pred)),
    "country_f1_macro_cv": float(f1_score(y_k, country_pred, average="macro")),
    "demand_mae_cv": float(mean_absolute_error(y_score, score_oof)),
    "demand_r2_cv": float(r2_score(y_score, score_oof)),
    "commodity_train_accuracy": train_acc,
    "commodity_overfit_gap": float(train_acc - cv_acc),
    "n_rows": int(len(demand_pdf)),
}

demand_artifact = {
    "commodity_model": commodity_clf,
    "country_model": country_clf,
    "score_model": score_model,
    "commodity_encoder": commodity_le,
    "country_encoder": country_le,
    "metrics": demand_metrics,
    "version": "demand_v2_generalized",
}

demand_bundle_path = f"{model_volume()}/demand_model_bundle.joblib"
joblib.dump(demand_artifact, demand_bundle_path)
print("Saved", demand_bundle_path)
print(json.dumps(demand_metrics, indent=2))

with mlflow.start_run(run_name="demand_tfidf_logistic_ridge") as run:
    mlflow.log_params({
        "model_family": "tfidf_logistic_ridge",
        "commodity_C": 0.35,
        "country_C": 0.3,
        "ridge_alpha": 8.0,
        "max_features_clf": 2500,
    })
    mlflow.log_metrics({
        "commodity_accuracy_cv": demand_metrics["commodity_accuracy_cv"],
        "commodity_f1_macro_cv": demand_metrics["commodity_f1_macro_cv"],
        "country_accuracy_cv": demand_metrics["country_accuracy_cv"],
        "country_f1_macro_cv": demand_metrics["country_f1_macro_cv"],
        "commodity_overfit_gap": demand_metrics["commodity_overfit_gap"],
        "demand_mae_cv": demand_metrics["demand_mae_cv"],
    })
    # Log the full sklearn bundle as an artifact (pandas UDF loads this).
    mlflow.log_artifact(demand_bundle_path)
    # Register the commodity classifier as the UC "model" entry point.
    mlflow.sklearn.log_model(
        commodity_clf,
        artifact_path="model",
        registered_model_name=demand_model_name(),
    )
    print("Demand MLflow run:", run.info.run_id)

# COMMAND ----------

# MAGIC %md
# MAGIC # Part B — Price model
# MAGIC
# MAGIC **Why predict % change, not absolute next price**
# MAGIC Absolute `next_price` correlates ~0.99 with last month's price.
# MAGIC A model can look "accurate" (low MAE) while ignoring news entirely.
# MAGIC We predict `return = (next - price) / price`, then reconstruct
# MAGIC `next_price = price * (1 + return)`.
# MAGIC
# MAGIC **Why time-ordered split (not random)**
# MAGIC Prices are a time series. Random splits leak future months into training.
# MAGIC We evaluate on the latest 20% of months.
# MAGIC
# MAGIC **Why strong XGBoost regularization**
# MAGIC Shallow trees (`max_depth=3`), L1/L2, subsample, early stopping —
# MAGIC so the model cannot memorize every commodity-month.

# COMMAND ----------

PRICE_FEATURES = [
    "total_news", "average_sentiment", "positive_news", "negative_news",
    "neutral_news", "news_growth", "price_change", "price_pct_change",
    "ma_spread", "momentum", "news_intensity",
]


def prepare_price(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.dropna(subset=["price", "next_price", "commodity"]).reset_index(drop=True)
    for c in [
        "total_news", "average_sentiment", "positive_news", "negative_news",
        "neutral_news", "news_growth", "price_change", "price_pct_change", "MA7", "MA30",
    ]:
        if c not in df.columns:
            df[c] = 0.0
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)

    price = pd.to_numeric(df["price"], errors="coerce")
    next_price = pd.to_numeric(df["next_price"], errors="coerce")
    df = df[(price > 0) & next_price.notna()].copy()
    price = df["price"].astype(float)
    df["target_return"] = ((df["next_price"].astype(float) - price) / price).clip(-0.35, 0.35)
    df["ma_spread"] = ((df["MA7"] - df["MA30"]) / price.replace(0, np.nan)).fillna(0.0)
    df["momentum"] = (df["price_change"] / price.replace(0, np.nan)).fillna(0.0)
    df["news_intensity"] = np.log1p(df["total_news"].clip(lower=0))
    df["year"] = pd.to_numeric(df["year"], errors="coerce").fillna(0).astype(int)
    df["month"] = pd.to_numeric(df["month"], errors="coerce").fillna(0).astype(int)
    df["ym"] = df["year"] * 100 + df["month"]
    return df

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load price training rows + time-ordered split

# COMMAND ----------

price_pdf = prepare_price(spark.table(full_name("ref_price_training")).toPandas())
price_pdf = price_pdf.sort_values("ym").reset_index(drop=True)

# Time-ordered: train on older months, test on the newest 20%.
cut = int(len(price_pdf) * 0.8)
train_df = price_pdf.iloc[:cut]
test_df = price_pdf.iloc[cut:]
print(f"Price rows={len(price_pdf)} train={len(train_df)} test={len(test_df)}")
print(f"Train ym {train_df['ym'].min()}..{train_df['ym'].max()} | Test ym {test_df['ym'].min()}..{test_df['ym'].max()}")

X_train = train_df[PRICE_FEATURES].astype(float)
y_train = train_df["target_return"].astype(float)
X_test = test_df[PRICE_FEATURES].astype(float)
y_test = test_df["target_return"].astype(float)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fit regularized XGBoost on returns + reconstruct prices for metrics

# COMMAND ----------

price_model = XGBRegressor(
    n_estimators=180,
    max_depth=3,           # shallow → less memorize
    learning_rate=0.05,
    subsample=0.7,
    colsample_bytree=0.7,
    min_child_weight=5,
    reg_alpha=1.0,         # L1
    reg_lambda=3.0,         # L2
    gamma=0.05,
    random_state=42,
    n_jobs=2,
)
price_model.fit(X_train, y_train)

def mape(y_true, y_pred):
    return float(np.mean(np.abs((y_true - y_pred) / np.maximum(y_true, 1e-6))) * 100)

test_ret = np.clip(price_model.predict(X_test), -0.35, 0.35)
test_price = test_df["price"].astype(float).values
true_next = test_df["next_price"].astype(float).values
pred_next = test_price * (1.0 + test_ret)

train_ret = np.clip(price_model.predict(X_train), -0.35, 0.35)
train_price = train_df["price"].astype(float).values
train_true_next = train_df["next_price"].astype(float).values
train_pred_next = train_price * (1.0 + train_ret)

price_metrics = {
    "test_return_mae": float(mean_absolute_error(y_test, test_ret)),
    "test_price_mae": float(mean_absolute_error(true_next, pred_next)),
    "test_price_mape_pct": mape(true_next, pred_next),
    "train_price_mape_pct": mape(train_true_next, train_pred_next),
    "overfit_gap_mape": float(mape(train_true_next, train_pred_next) - mape(true_next, pred_next)),
    "n_rows": int(len(price_pdf)),
    "features": PRICE_FEATURES,
    "target": "monthly_return",
    "note": "Predicts return then reconstructs next_price = price*(1+return); time-ordered 80/20 split",
}
print(json.dumps({k: v for k, v in price_metrics.items() if k != "features"}, indent=2))

# Refit on ALL rows for the production artifact (same conservative params).
final_price = XGBRegressor(
    n_estimators=180, max_depth=3, learning_rate=0.05,
    subsample=0.7, colsample_bytree=0.7, min_child_weight=5,
    reg_alpha=1.0, reg_lambda=3.0, gamma=0.05,
    random_state=42, n_jobs=2,
)
final_price.fit(price_pdf[PRICE_FEATURES].astype(float), price_pdf["target_return"].astype(float))

price_artifact = {
    "model": final_price,
    "features": PRICE_FEATURES,
    "metrics": price_metrics,
    "version": "price_v2_return_xgb",
}
price_bundle_path = f"{model_volume()}/price_model_bundle.joblib"
joblib.dump(price_artifact, price_bundle_path)
print("Saved", price_bundle_path)

with mlflow.start_run(run_name="price_return_xgboost") as run:
    mlflow.log_params({
        "target": "monthly_return",
        "max_depth": 3,
        "reg_alpha": 1.0,
        "reg_lambda": 3.0,
        "n_estimators": 180,
        "split": "time_ordered_80_20",
    })
    mlflow.log_metrics({
        "test_price_mae": price_metrics["test_price_mae"],
        "test_price_mape_pct": price_metrics["test_price_mape_pct"],
        "train_price_mape_pct": price_metrics["train_price_mape_pct"],
        "overfit_gap_mape": price_metrics["overfit_gap_mape"],
        "test_return_mae": price_metrics["test_return_mae"],
    })
    mlflow.log_artifact(price_bundle_path)
    mlflow.xgboost.log_model(
        final_price,
        artifact_path="model",
        registered_model_name=price_model_name(),
    )
    print("Price MLflow run:", run.info.run_id)

print("Training complete. Bundles on Volume + models registered in UC.")
