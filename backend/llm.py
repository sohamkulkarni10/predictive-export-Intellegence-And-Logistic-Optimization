"""
Groq LLM helper — uses llama-3.3-70b-versatile (same as Demand_prediction).

Loads keys from backend/.env and Demand_prediction/.env
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(Path(__file__).resolve().parent / ".env")
load_dotenv(ROOT / "Demand_prediction" / ".env")

DEFAULT_MODEL = "llama-3.3-70b-versatile"


def llm_status() -> dict:
    key = (os.getenv("GROQ_API_KEY") or "").strip()
    model = (os.getenv("GROQ_MODEL") or DEFAULT_MODEL).strip() or DEFAULT_MODEL
    return {"enabled": bool(key), "model": model}


def ask_llm(prompt: str, system: str = "You are Export AI helper for Indian exporters.") -> str | None:
    key = (os.getenv("GROQ_API_KEY") or "").strip()
    if not key:
        return None

    model = (os.getenv("GROQ_MODEL") or DEFAULT_MODEL).strip() or DEFAULT_MODEL

    try:
        from groq import Groq

        client = Groq(api_key=key)
        response = client.chat.completions.create(
            model=model,
            temperature=0.25,
            max_tokens=900,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        text = (response.choices[0].message.content or "").strip()
        return text or None
    except Exception as e:
        print("Groq error:", e)
        return None
