"""
Export AI Flask API — login + pipeline + logistics DB + RAG.
"""

from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

from auth import login, logout, verify_token
from db import get_latest, get_logistics_from_db, init_db
from llm import llm_status
from samples import SAMPLE_DEMAND, SAMPLE_PRICE

BACKEND = Path(__file__).resolve().parent
DEMAND_MODEL = BACKEND.parent / "Demand_prediction" / "demand_model_bundle.joblib"
PRICE_MODEL = BACKEND.parent / "commodities" / "commodity_xgboost_generalized.pkl"

app = Flask(__name__)
CORS(app)
init_db()


def _token_from_request() -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return request.headers.get("X-Auth-Token")


@app.get("/api/health")
def health():
    status = llm_status()
    return jsonify(
        {
            "status": "ok",
            "demand_model": DEMAND_MODEL.exists(),
            "price_model": PRICE_MODEL.exists()
            or (BACKEND / "models" / "price_model_bundle.joblib").exists(),
            "groq_enabled": status["enabled"],
            "groq_model": status["model"],
            "database": str(BACKEND / "export_ai.db"),
        }
    )


@app.post("/api/login")
def api_login():
    body = request.get_json(force=True, silent=True) or {}
    result = login(body.get("username") or "", body.get("password") or "")
    if not result:
        return jsonify({"error": "Invalid username or password"}), 401
    return jsonify(result)


@app.post("/api/logout")
def api_logout():
    logout(_token_from_request())
    return jsonify({"ok": True})


@app.get("/api/sample-news")
def sample_news():
    return jsonify({"demand_news": SAMPLE_DEMAND, "price_news": SAMPLE_PRICE})


@app.get("/api/fetch-live-news")
@app.post("/api/fetch-live-news")
def fetch_live_news_api():
    """News Agent: auto-fetch India + country commodity news from verified APIs."""
    from news_fetcher import fetch_live_news

    try:
        data = fetch_live_news()
        resp = jsonify(data)
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        return resp
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/rag/rebuild")
def rag_rebuild():
    from rag import build_vector_db

    try:
        return jsonify(build_vector_db(force=True))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/pipeline")
def pipeline():
    from pipeline import run_pipeline

    user = verify_token(_token_from_request())
    if not user:
        return jsonify({"error": "Please login first"}), 401
    body = request.get_json(force=True, silent=True) or {}
    try:
        # Default auto_news=True → News Agent fetches live headlines
        auto_news = body.get("auto_news", True)
        if isinstance(auto_news, str):
            auto_news = auto_news.strip().lower() in {"1", "true", "yes"}
        result = run_pipeline(
            body.get("demand_news") or "",
            body.get("price_news") or "",
            available_containers=int(body.get("available_containers", 6)),
            container_type=str(body.get("container_type", "20FT")),
            top_n=int(body.get("top_n", 3)),
            cost_weight=float(body.get("cost_weight", 0.7)),
            time_weight=float(body.get("time_weight", 0.3)),
            auto_news=bool(auto_news),
        )
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/rag/ask")
def rag_ask():
    from rag import ask_rag

    body = request.get_json(force=True, silent=True) or {}
    try:
        return jsonify(ask_rag(body.get("question") or "", top_k=int(body.get("top_k", 3))))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/api/latest")
def latest():
    return jsonify(get_latest())


@app.get("/api/logistics-costs")
def logistics_costs():
    run_id = request.args.get("run_id")
    return jsonify({"rows": get_logistics_from_db(run_id)})


if __name__ == "__main__":
    try:
        import sys

        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    app.run(host="0.0.0.0", port=5001, debug=True, use_reloader=False)
