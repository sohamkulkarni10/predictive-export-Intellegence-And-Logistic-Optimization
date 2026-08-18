"""
Train next-month India price model (single copy — run: python train_price.py).

In:  commodities/training_dataset.csv
Out: models/price_model_bundle.joblib + price_metrics.json

Predicts monthly RETURN (not absolute price) because absolute next_price correlates
~0.99 with current price and looks falsely accurate. Reconstructs:
    next_price = price * (1 + y_hat)
Regularization: shallow trees, L1/L2, early stopping, GroupKFold by commodity.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import GroupKFold
from xgboost import XGBRegressor

ROOT = Path(__file__).resolve().parents[1]
TRAIN_CSV = ROOT / "commodities" / "training_dataset.csv"
OUT = Path(__file__).resolve().parent / "models"
OUT.mkdir(parents=True, exist_ok=True)

FEATURES = [
    "total_news",
    "average_sentiment",
    "positive_news",
    "negative_news",
    "neutral_news",
    "news_growth",
    "price_change",
    "price_pct_change",
    "ma_spread",       # (MA7 - MA30) / price
    "momentum",        # price_change / price
    "news_intensity",  # total_news scaled
]


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.dropna(subset=["price", "next_price", "commodity"]).reset_index(drop=True)
    for c in [
        "total_news",
        "average_sentiment",
        "positive_news",
        "negative_news",
        "neutral_news",
        "news_growth",
        "price_change",
        "price_pct_change",
        "MA7",
        "MA30",
    ]:
        if c not in df.columns:
            df[c] = 0.0
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)

    price = pd.to_numeric(df["price"], errors="coerce")
    next_price = pd.to_numeric(df["next_price"], errors="coerce")
    df = df[(price > 0) & next_price.notna()].copy()
    price = df["price"].astype(float)
    df["target_return"] = (df["next_price"].astype(float) - price) / price
    # Clip extreme returns (data errors / spikes)
    df["target_return"] = df["target_return"].clip(-0.35, 0.35)
    df["ma_spread"] = ((df["MA7"] - df["MA30"]) / price.replace(0, np.nan)).fillna(0.0)
    df["momentum"] = (df["price_change"] / price.replace(0, np.nan)).fillna(0.0)
    df["news_intensity"] = np.log1p(df["total_news"].clip(lower=0))
    # Drop absolute price level from features to force learning dynamics/news
    return df


def train():
    raw = pd.read_csv(TRAIN_CSV)
    df = prepare(raw)
    X = df[FEATURES].astype(float)
    y = df["target_return"].astype(float)
    groups = df["commodity"].astype(str)

    gkf = GroupKFold(n_splits=5)
    oof = np.zeros(len(df))
    fold_metrics = []

    for fold, (tr, te) in enumerate(gkf.split(X, y, groups=groups), start=1):
        model = XGBRegressor(
            n_estimators=400,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.7,
            colsample_bytree=0.7,
            min_child_weight=5,
            reg_alpha=1.0,
            reg_lambda=3.0,
            gamma=0.05,
            random_state=42 + fold,
            n_jobs=2,
            early_stopping_rounds=40,
        )
        model.fit(
            X.iloc[tr],
            y.iloc[tr],
            eval_set=[(X.iloc[te], y.iloc[te])],
            verbose=False,
        )
        pred = model.predict(X.iloc[te])
        oof[te] = pred
        # Evaluate on reconstructed prices
        price_te = df.iloc[te]["price"].astype(float).values
        true_next = df.iloc[te]["next_price"].astype(float).values
        pred_next = price_te * (1.0 + pred)
        fold_metrics.append(
            {
                "fold": fold,
                "return_mae": float(mean_absolute_error(y.iloc[te], pred)),
                "price_mae": float(mean_absolute_error(true_next, pred_next)),
                "price_mape": float(
                    np.mean(np.abs((true_next - pred_next) / np.maximum(true_next, 1e-6))) * 100
                ),
                "best_iteration": int(getattr(model, "best_iteration", 0) or 0),
            }
        )

    price_all = df["price"].astype(float).values
    true_next_all = df["next_price"].astype(float).values
    pred_next_all = price_all * (1.0 + oof)

    metrics = {
        "cv_folds": fold_metrics,
        "cv_return_mae": float(mean_absolute_error(y, oof)),
        "cv_price_mae": float(mean_absolute_error(true_next_all, pred_next_all)),
        "cv_price_mape_pct": float(
            np.mean(np.abs((true_next_all - pred_next_all) / np.maximum(true_next_all, 1e-6))) * 100
        ),
        "cv_return_r2": float(r2_score(y, oof)),
        "n_rows": int(len(df)),
        "features": FEATURES,
        "target": "monthly_return",
        "note": "Predicts return then reconstructs next_price = price*(1+return)",
    }

    # Final model with early stopping on held-out commodities mix via last fold style split
    # Use 80/20 random within groups carefully: fit on all with conservative params + fixed trees
    final = XGBRegressor(
        n_estimators=180,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.7,
        colsample_bytree=0.7,
        min_child_weight=5,
        reg_alpha=1.0,
        reg_lambda=3.0,
        gamma=0.05,
        random_state=42,
        n_jobs=2,
    )
    final.fit(X, y)

    train_pred = final.predict(X)
    train_next = price_all * (1.0 + train_pred)
    metrics["train_price_mape_pct"] = float(
        np.mean(np.abs((true_next_all - train_next) / np.maximum(true_next_all, 1e-6))) * 100
    )
    metrics["overfit_gap_mape"] = float(
        metrics["train_price_mape_pct"] - metrics["cv_price_mape_pct"]
    )

    artifact = {
        "model": final,
        "features": FEATURES,
        "metrics": metrics,
        "version": "price_v2_return_xgb",
    }
    path = OUT / "price_model_bundle.joblib"
    joblib.dump(artifact, path)
    # Also overwrite commodities path for compatibility
    joblib.dump(final, ROOT / "commodities" / "commodity_xgboost_generalized.pkl")
    (OUT / "price_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print("Saved", path)
    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    train()
