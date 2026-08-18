import pandas as pd
import joblib
import numpy as np
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_GEN = _ROOT / "commodity_xgboost_generalized.pkl"
_OLD = _ROOT / "commodity_xgboost.pkl"
_BACKEND = _ROOT.parent / "backend" / "models" / "price_model_bundle.joblib"

_model = None
_mode = None  # "generalized" | "legacy" | "bundle"


def _load():
    global _model, _mode
    if _model is not None:
        return _model, _mode
    if _GEN.exists():
        _model = joblib.load(_GEN)
        _mode = "generalized"
    elif _OLD.exists():
        _model = joblib.load(_OLD)
        _mode = "legacy"
    elif _BACKEND.exists():
        bundle = joblib.load(_BACKEND)
        _model = bundle["model"]
        _mode = "bundle"
    else:
        raise FileNotFoundError(
            "Price model missing. Run: python backend/train_price.py"
        )
    return _model, _mode


FEATURES = [
    "total_news",
    "average_sentiment",
    "positive_news",
    "negative_news",
    "neutral_news",
    "news_growth",
    "price",
    "price_change",
    "price_pct_change",
    "MA7",
    "MA30",
]


def predict_price(data):
    """Predict next commodity price (INR/quintal) from news + market features."""
    model, mode = _load()
    price = float(data.get("price") or 1)

    if mode in {"generalized", "bundle"}:
        row = {
            "total_news": data.get("total_news", 0),
            "average_sentiment": data.get("average_sentiment", 0),
            "positive_news": data.get("positive_news", 0),
            "negative_news": data.get("negative_news", 0),
            "neutral_news": data.get("neutral_news", 0),
            "news_growth": data.get("news_growth", 0),
            "price_change": data.get("price_change", 0),
            "price_pct_change": data.get("price_pct_change", 0),
            "ma_spread": (
                (float(data.get("MA7", price)) - float(data.get("MA30", price)))
                / max(price, 1e-6)
            ),
            "momentum": float(data.get("price_change", 0)) / max(price, 1e-6),
            "news_intensity": float(np.log1p(float(data.get("total_news", 0) or 0))),
        }
        pred_return = float(model.predict(pd.DataFrame([row]))[0])
        return float(price * (1.0 + pred_return))

    df = pd.DataFrame([data])[FEATURES]
    return float(model.predict(df)[0])
