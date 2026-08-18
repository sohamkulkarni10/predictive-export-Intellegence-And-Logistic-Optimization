"""
AI explanations for Demand + Price — Groq LLM only (not hardcoded).

If Groq fails, returns an explicit error string so UI does not show fake text.
"""

from __future__ import annotations

import json
import re
from typing import Any

from llm import ask_llm, llm_status

AGENT_KEYS = ["demand_agent", "price_agent"]


def _demand_facts(result: dict[str, Any]) -> str:
    lines = ["Horizon: " + str(result.get("horizon_month"))]
    demand = result.get("stage1_demand") or {}
    if demand.get("ai_explanation"):
        lines.append("Model note: " + str(demand["ai_explanation"])[:500])
    for o in demand.get("top_opportunities") or []:
        lines.append(
            f"- {o.get('commodity')} in {o.get('country')}: "
            f"demand_score={o.get('demand_score')}, "
            f"direction={o.get('predicted_direction')}, "
            f"pct={o.get('demand_percentage')}, "
            f"news={o.get('news_snippet')}"
        )
    # Include a short sample of live news so Groq can cite why
    live = (result.get("news_fetch") or {}).get("demand_news") or result.get("inputs", {}).get("demand_news_preview")
    if live:
        lines.append("LIVE DEMAND NEWS SAMPLE:\n" + str(live)[:1200])
    return "\n".join(lines)


def _price_facts(result: dict[str, Any]) -> str:
    lines = ["Prices are INR per quintal."]
    for p in (result.get("stage2_prices") or {}).get("predictions") or []:
        lines.append(
            f"- {p.get('commodity')}: current INR {p.get('current_price_inr')}/quintal "
            f"-> next INR {p.get('predicted_next_month_price_inr')}/quintal "
            f"({p.get('predicted_change_pct')}%, news_adj={p.get('news_adjustment_pct')}%)"
        )
    live = (result.get("news_fetch") or {}).get("price_news") or result.get("inputs", {}).get("price_news_preview")
    if live:
        lines.append("LIVE INDIA PRICE NEWS SAMPLE:\n" + str(live)[:1200])
    return "\n".join(lines)


def _parse_json(text: str) -> dict[str, str] | None:
    cleaned = text.replace("```json", "").replace("```", "").strip()
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
    if not isinstance(data, dict):
        return None
    out = {}
    for k in AGENT_KEYS:
        v = data.get(k)
        if isinstance(v, str) and v.strip():
            out[k] = v.strip()
    return out if len(out) == len(AGENT_KEYS) else None


def build_explanations(result: dict[str, Any]) -> tuple[dict[str, str], dict[str, Any]]:
    status = llm_status()
    meta = {"enabled": status["enabled"], "model": status["model"], "source": "groq_required"}

    if not status["enabled"]:
        msg = (
            "Groq LLM is not configured. Set GROQ_API_KEY in backend/.env. "
            "Demand/Price AI explanations are LLM-only (not hardcoded)."
        )
        return {"demand_agent": msg, "price_agent": msg}, {**meta, "source": "error_no_key"}

    prompt = f"""
You are Export AI explanation agents (Demand Agent + Price Agent).
Write fresh explanations from the facts and LIVE NEWS below.
Do NOT use template / hardcoded sentences. Be specific to these numbers and headlines.

DEMAND FACTS:
{_demand_facts(result)}

PRICE FACTS:
{_price_facts(result)}

Return ONLY JSON:
{{
  "demand_agent": "For each country+commodity: INCREASE or DECREASE, by how much, WHY from the live news. 4-7 sentences.",
  "price_agent": "For each commodity: India price INCREASE or DECREASE next month, INR and %, WHY from India market news. 4-7 sentences."
}}
"""
    raw = ask_llm(
        prompt,
        system=(
            "You are Groq-powered Export AI. Return only JSON with demand_agent and price_agent. "
            "Never invent logistics/container advice. Use the provided live news."
        ),
    )
    if not raw:
        msg = "Groq call failed (rate limit/network). Retry analysis for LLM explanations."
        return {"demand_agent": msg, "price_agent": msg}, {**meta, "source": "error_groq"}

    parsed = _parse_json(raw)
    if not parsed:
        msg = "Groq returned unreadable JSON. Retry analysis."
        return {"demand_agent": msg, "price_agent": msg}, {**meta, "source": "error_parse"}

    meta["source"] = "groq"
    return parsed, meta
