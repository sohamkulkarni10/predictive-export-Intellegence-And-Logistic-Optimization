"""
Simple demand agent: multiple country/commodity news → top 3 next-month demands.

Uses your existing demand_model_bundle.joblib via demand_agent_tools.
Uses Groq only to read news features + write a short explanation.

Run:
    python predict_top3_from_news.py
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from groq import Groq

from demand_agent_tools import predict_demand

BASE = Path(__file__).resolve().parent
load_dotenv(BASE / ".env")
load_dotenv(BASE.parent / "backend" / ".env")

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()

# Only countries / commodities present in Demand_prediction datasets
ALLOWED_COUNTRIES = {
    "Bangladesh", "China", "Germany", "Indonesia", "Japan", "Malaysia",
    "Nepal", "Netherlands", "Saudi Arabia", "Singapore", "Sri Lanka", "Vietnam",
}
ALLOWED_COMMODITIES = {
    "Coffee", "Cotton", "Maize", "Onion", "Soybean", "Sugar", "Turmeric", "Wheat",
}


def _canon_country(name: str) -> str | None:
    key = name.strip().lower()
    aliases = {"uae": None, "united arab emirates": None, "india": None, "usa": None}
    if key in aliases:
        return None
    for c in ALLOWED_COUNTRIES:
        if c.lower() == key:
            return c
    return None


def _canon_commodity(name: str) -> str | None:
    key = name.strip().lower()
    for c in ALLOWED_COMMODITIES:
        if c.lower() == key:
            return c
    return None


def _client() -> Groq:
    key = (os.getenv("GROQ_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("Set GROQ_API_KEY in Demand_prediction/.env or backend/.env")
    return Groq(api_key=key)


def ask_groq(system: str, user: str, json_mode: bool = False) -> str:
    payload: dict[str, Any] = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0,
        "max_tokens": 900,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    resp = _client().chat.completions.create(**payload)
    text = (resp.choices[0].message.content or "").strip()
    if not text:
        raise RuntimeError("Empty Groq response")
    return text


def _parse_json(text: str) -> dict[str, Any]:
    cleaned = text.replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise ValueError(f"Groq did not return JSON:\n{text}")
        data = json.loads(match.group(0))
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object")
    return data


def extract_items_from_news(news_text: str) -> list[dict[str, Any]]:
    """Prefer Groq llama (same as Demand_prediction agent). Offline only if Groq fails."""
    try:
        items = _extract_with_groq(news_text)
        for row in items:
            row["extract_source"] = "groq_llama"
        return items
    except Exception as exc:
        print("Groq demand extract failed, using offline keywords:", exc)
        items = _extract_offline(news_text)
        for row in items:
            row["extract_source"] = "offline_keywords"
        return items


def _extract_offline(news_text: str) -> list[dict[str, Any]]:
    """Simple keyword fallback if Groq is unavailable."""
    countries = sorted(ALLOWED_COUNTRIES)
    commodities = sorted(ALLOWED_COMMODITIES)
    chunks = [c.strip() for c in re.split(r"\n\s*\n+|(?<=[.!?])\s+", news_text) if len(c.strip()) > 25]
    if not chunks:
        chunks = [news_text]
    items = []
    for chunk in chunks:
        lower = chunk.lower()
        country = next((c for c in countries if c.lower() in lower), None)
        commodity = next((c for c in commodities if c.lower() in lower), None)
        if not country or not commodity:
            continue
        shortage = int(any(w in lower for w in ["shortage", "tight", "deficit", "stock"]))
        drop = int(any(w in lower for w in ["drought", "delay", "drop", "decline", "crop"]))
        items.append(
            {
                "country": country,
                "commodity": commodity,
                "news_snippet": chunk[:180],
                "sentiment_score": -0.35 if shortage or drop else 0.1,
                "shortage_flag": shortage,
                "production_drop": drop,
                "production_rise": 0,
                "price_increase": int("price" in lower and any(w in lower for w in ["up", "rise", "firm"])),
                "price_decrease": int("price" in lower and any(w in lower for w in ["down", "soft", "fall"])),
                "export_opportunity_score": 70.0 if shortage or drop else 45.0,
                "confidence": 0.65,
            }
        )
    seen = set()
    unique = []
    for row in items:
        key = (row["country"].lower(), row["commodity"].lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def _extract_with_groq(news_text: str) -> list[dict[str, Any]]:
    system = (
        "You extract export-demand signals from commodity news. "
        "Return only JSON. No markdown."
    )
    user = f"""
Read these news items (can be multiple countries/commodities):

{news_text}

Return JSON:
{{
  "items": [
    {{
      "country": "Country Name",
      "commodity": "Commodity Name",
      "news_snippet": "short quote",
      "sentiment_score": 0.0,
      "shortage_flag": 0,
      "production_drop": 0,
      "production_rise": 0,
      "price_increase": 0,
      "price_decrease": 0,
      "export_opportunity_score": 50.0,
      "confidence": 0.6
    }}
  ]
}}

Rules:
- One item per clear country+commodity pair mentioned.
- country MUST be one of: Bangladesh, China, Germany, Indonesia, Japan, Malaysia, Nepal, Netherlands, Saudi Arabia, Singapore, Sri Lanka, Vietnam.
- commodity MUST be one of: Coffee, Cotton, Maize, Onion, Soybean, Sugar, Turmeric, Wheat.
- Skip pairs not in those lists.
- sentiment_score between -1 and 1.
- Flags are 0 or 1.
- export_opportunity_score 0 to 100.
- confidence 0 to 1.
"""
    raw = ask_groq(system, user, json_mode=True)
    data = _parse_json(raw)
    items = data.get("items") or []
    cleaned = []
    for row in items:
        country = _canon_country(str(row.get("country", "")))
        commodity = _canon_commodity(str(row.get("commodity", "")))
        if not country or not commodity:
            continue
        cleaned.append(
            {
                "country": country,
                "commodity": commodity,
                "news_snippet": str(row.get("news_snippet", ""))[:200],
                "sentiment_score": float(np_clip(row.get("sentiment_score", 0), -1, 1)),
                "shortage_flag": int(bool(row.get("shortage_flag", 0))),
                "production_drop": int(bool(row.get("production_drop", 0))),
                "production_rise": int(bool(row.get("production_rise", 0))),
                "price_increase": int(bool(row.get("price_increase", 0))),
                "price_decrease": int(bool(row.get("price_decrease", 0))),
                "export_opportunity_score": float(np_clip(row.get("export_opportunity_score", 50), 0, 100)),
                "confidence": float(np_clip(row.get("confidence", 0.6), 0, 1)),
            }
        )
    if not cleaned:
        raise ValueError("Groq returned no items in dataset countries/commodities")
    return cleaned


def np_clip(value: Any, lo: float, hi: float) -> float:
    try:
        v = float(value)
    except Exception:
        v = lo
    return max(lo, min(hi, v))


def explain_top3(news_text: str, top3: list[dict[str, Any]]) -> str:
    system = (
        "You are an Indian export demand advisor. "
        "Explain results in simple English for an exporter."
    )
    user = f"""
NEWS:
{news_text[:1500]}

TOP 3 MODEL RESULTS:
{json.dumps(top3, indent=2)}

Write 4-6 short sentences:
- which 3 country+commodity pairs look strongest next month
- why (shortage / production / sentiment)
- one clear export tip
"""
    try:
        return ask_groq(system, user, json_mode=False)
    except Exception as exc:
        return f"Top 3 demand opportunities ready. (AI explanation unavailable: {exc})"


def predict_top3_from_news(news_text: str, top_n: int = 3) -> dict[str, Any]:
    """
    Main entry used by backend pipeline.
    Input: one or many news paragraphs about countries + commodities.
    Output: top N next-month demand opportunities + AI explanation.
    """
    if not news_text or not str(news_text).strip():
        raise ValueError("news_text is required")

    items = extract_items_from_news(news_text)
    if not items:
        raise ValueError("Could not find country/commodity pairs in the news")

    scored: list[dict[str, Any]] = []
    for item in items:
        country = _canon_country(item["country"])
        commodity = _canon_commodity(item["commodity"])
        if not country or not commodity:
            continue
        features = {
            "sentiment_score": item["sentiment_score"],
            "shortage_flag": item["shortage_flag"],
            "production_drop": item["production_drop"],
            "production_rise": item["production_rise"],
            "price_increase": item["price_increase"],
            "price_decrease": item["price_decrease"],
            "export_opportunity_score": item["export_opportunity_score"],
            "confidence": item["confidence"],
        }
        pred = predict_demand(country, commodity, news_features=features)
        scored.append(
            {
                "country": pred["country"],
                "commodity": pred["commodity"],
                "demand_score": pred["predicted_demand_probability"],
                "demand_percentage": pred["predicted_demand_percentage"],
                "predicted_direction": pred["predicted_direction"],
                "trend_vs_current_month": pred["trend_vs_current_month"],
                "forecast_month": pred["forecast_month"],
                "news_snippet": item["news_snippet"],
                "method": pred["method"],
            }
        )

    # Prefer country diversity in top N
    scored.sort(key=lambda x: x["demand_score"], reverse=True)
    selected: list[dict[str, Any]] = []
    used_countries: set[str] = set()
    for row in scored:
        if row["country"] in used_countries:
            continue
        selected.append(row)
        used_countries.add(row["country"])
        if len(selected) >= top_n:
            break
    if len(selected) < top_n:
        for row in scored:
            if row in selected:
                continue
            selected.append(row)
            if len(selected) >= top_n:
                break

    for i, row in enumerate(selected):
        row["rank"] = i + 1

    explanation = explain_top3(news_text, selected)
    sources = {i.get("extract_source") for i in items}
    return {
        "top_opportunities": selected,
        "top_countries": [o["country"] for o in selected],
        "commodities_involved": sorted({o["commodity"] for o in selected}),
        "articles_parsed": len(items),
        "ai_explanation": explanation,
        "method": "demand_model_bundle + groq_llama-3.3-70b-versatile",
        "groq_model": GROQ_MODEL,
        "extract_source": "groq_llama" if "groq_llama" in sources else "offline_keywords",
        "note": "Top demand countries/commodities for next month from YOUR news input.",
    }


def main() -> None:
    sample = """
Bangladesh wheat imports surge as domestic stocks tighten.
Saudi Arabia faces onion shortage after delayed shipments; traders seek Indian supply.
Germany sugar refiners report tighter stocks; import tenders expected next month.
"""
    print("Demand Top-3 Agent")
    print("Paste news (blank line to use sample), or type 'exit'.")
    while True:
        print("\nEnter news (end with empty line):")
        lines = []
        while True:
            line = input()
            if line.strip().lower() in {"exit", "quit"}:
                return
            if line == "" and lines:
                break
            if line == "" and not lines:
                lines = [sample]
                break
            lines.append(line)
        news = "\n".join(lines).strip()
        try:
            result = predict_top3_from_news(news, top_n=3)
            print(json.dumps(result, indent=2))
        except Exception as exc:
            print("ERROR:", exc)


if __name__ == "__main__":
    main()
