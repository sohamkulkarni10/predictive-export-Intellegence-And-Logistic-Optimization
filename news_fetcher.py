"""
Live news fetcher — fresh headlines each click (no URL links, max 10 each).

Demand news  = ONLY our demand countries + our commodities
Price news   = ONLY our commodities, anywhere in India
"""

from __future__ import annotations

import os
import random
import re
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

# Must match Demand_prediction allow-lists
COMMODITIES = ["wheat", "onion", "sugar", "coffee", "cotton", "maize", "soybean", "turmeric"]
DEMAND_COUNTRIES = [
    "Bangladesh", "China", "Germany", "Indonesia", "Japan", "Malaysia",
    "Nepal", "Netherlands", "Saudi Arabia", "Singapore", "Sri Lanka", "Vietnam",
]

# Broad India geography (any part of India OK for price news)
INDIA_MARKERS = (
    "india", "indian", "mandi", "msp", "fci", "apmc", "nizamabad", "nashik",
    "punjab", "haryana", "kerala", "gujarat", "maharashtra", "rajasthan",
    "uttar pradesh", "madhya pradesh", "karnataka", "tamil nadu", "andhra",
    "telangana", "west bengal", "bihar", "odisha", "delhi", "agra", "indore",
    "lasalgaon", "solapur", "ahmedabad", "ludhiana", "kanpur", "kochi",
    "chennai", "mumbai", "kolkata", "hyderabad", "bengaluru", "bangalore",
)

USER_AGENT = "ExportAI/1.0 (research; educational export intelligence)"
MAX_NEWS = 10
HTTP_TIMEOUT = 10


def _http_get(url: str, timeout: int = HTTP_TIMEOUT) -> bytes:
    sep = "&" if "?" in url else "?"
    bust = f"{url}{sep}_ts={int(time.time() * 1000)}&_r={random.randint(1000, 9999)}"
    req = Request(
        bust,
        headers={"User-Agent": USER_AGENT, "Accept": "*/*", "Cache-Control": "no-cache"},
    )
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _clean(text: str) -> str:
    text = re.sub(r"https?://\S+", "", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:220]


def _has_commodity(title: str) -> bool:
    t = (title or "").lower()
    return any(c in t for c in COMMODITIES)


def _has_demand_country(title: str) -> bool:
    t = (title or "").lower()
    return any(c.lower() in t for c in DEMAND_COUNTRIES)


def _has_india(title: str) -> bool:
    t = (title or "").lower()
    return any(m in t for m in INDIA_MARKERS)


def _is_junk(title: str) -> bool:
    t = (title or "").lower()
    if len(t) < 18:
        return True
    junk = [
        "jan delay", "parklichter", "bishop cotton", "football", "bollywood",
        "ipl ", "cricket", "hollywood", "movie", "celebrity",
    ]
    return any(j in t for j in junk)


def _is_demand_relevant(title: str) -> bool:
    """Strict: our commodity AND our demand country."""
    if _is_junk(title):
        return False
    return _has_commodity(title) and _has_demand_country(title)


def _is_india_price_relevant(title: str) -> bool:
    """Strict: our commodity AND India (any region)."""
    if _is_junk(title):
        return False
    return _has_commodity(title) and _has_india(title)


def _from_gdelt(query: str, maxrecords: int = 10) -> list[dict[str, str]]:
    params = {
        "query": query,
        "mode": "ArtList",
        "maxrecords": str(maxrecords),
        "format": "json",
        "sort": "HybridRel",
    }
    url = "https://api.gdeltproject.org/api/v2/doc/doc?" + urlencode(params)
    try:
        import json

        data = json.loads(_http_get(url, timeout=4).decode("utf-8", errors="replace"))
    except Exception as exc:
        print("GDELT error:", exc)
        return []
    out = []
    for a in data.get("articles") or []:
        title = _clean(a.get("title") or "")
        if len(title) < 18:
            continue
        out.append({"title": title, "source": a.get("domain") or "gdelt", "provider": "GDELT"})
    return out


def _from_google_news_rss(query: str, maxrecords: int = 10) -> list[dict[str, str]]:
    url = (
        "https://news.google.com/rss/search?"
        + urlencode({"q": query, "hl": "en-IN", "gl": "IN", "ceid": "IN:en"})
    )
    try:
        root = ET.fromstring(_http_get(url))
    except Exception as exc:
        print("Google News RSS error:", exc)
        return []
    out = []
    for item in root.findall("./channel/item")[:maxrecords]:
        title = _clean(item.findtext("title") or "")
        source = _clean(item.findtext("source") or "google_news")
        if len(title) < 18:
            continue
        out.append({"title": title, "source": source, "provider": "GoogleNewsRSS"})
    return out


def _from_newsapi(query: str, maxrecords: int = 10) -> list[dict[str, str]]:
    key = (os.getenv("NEWS_API_KEY") or "").strip()
    if not key:
        return []
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": str(maxrecords),
        "apiKey": key,
    }
    url = "https://newsapi.org/v2/everything?" + urlencode(params)
    try:
        import json

        data = json.loads(_http_get(url).decode("utf-8", errors="replace"))
    except Exception as exc:
        print("NewsAPI error:", exc)
        return []
    out = []
    for a in data.get("articles") or []:
        title = _clean(a.get("title") or "")
        if len(title) < 18 or title.lower() == "[removed]":
            continue
        out.append(
            {
                "title": title,
                "source": (a.get("source") or {}).get("name") or "newsapi",
                "provider": "NewsAPI",
            }
        )
    return out


def _dedupe(articles: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    out = []
    for a in articles:
        key = re.sub(r"[^a-z0-9]+", "", a["title"].lower())[:90]
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(a)
    return out


def _to_news_block(articles: list[dict[str, str]], header: str) -> str:
    lines = [header, f"Fetched at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
    for i, a in enumerate(articles, 1):
        title = _clean(a.get("title") or "")
        source = _clean(a.get("source") or "")
        lines.append(f"{i}. {title}" + (f" ({source})" if source else ""))
    return "\n".join(lines).strip()


def _pick_demand_query() -> tuple[str, str]:
    commodities = COMMODITIES[:]
    countries = DEMAND_COUNTRIES[:]
    random.shuffle(commodities)
    random.shuffle(countries)
    c1, c2, c3 = commodities[0], commodities[1], commodities[2]
    k1, k2, k3 = countries[0], countries[1], countries[2]
    # Force commodity + country in query
    rss = f"({c1} OR {c2} OR {c3}) ({k1} OR {k2} OR {k3}) (import OR shortage OR demand OR tender)"
    country_clause = " OR ".join(f'"{c}"' for c in countries[:6])
    commodity_clause = " OR ".join(commodities)
    gdelt = (
        f"({commodity_clause}) AND ({country_clause}) "
        f"AND (shortage OR import OR demand OR tender) sourcelang:english"
    )
    return rss, gdelt


def _pick_price_query() -> tuple[str, str]:
    commodities = COMMODITIES[:]
    random.shuffle(commodities)
    c1, c2, c3, c4 = commodities[0], commodities[1], commodities[2], commodities[3]
    # Any India region — commodity + India/mandi
    rss = f"({c1} OR {c2} OR {c3} OR {c4}) (India OR mandi OR MSP) (price OR rate OR arrivals)"
    gdelt = (
        f"({' OR '.join(commodities)}) AND (India OR mandi OR MSP) "
        f"sourcelang:english"
    )
    return rss, gdelt


def _gather(jobs: list) -> list[dict[str, str]]:
    articles: list[dict[str, str]] = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(fn, *args) for fn, args in jobs]
        for fut in as_completed(futures):
            try:
                articles.extend(fut.result() or [])
            except Exception as exc:
                print("news job error:", exc)
    return articles


def fetch_demand_news(limit: int = MAX_NEWS) -> dict[str, Any]:
    rss_q, gdelt_q = _pick_demand_query()
    # Extra RSS pass with another country/commodity rotation for coverage
    commodities = COMMODITIES[:]
    countries = DEMAND_COUNTRIES[:]
    random.shuffle(commodities)
    random.shuffle(countries)
    rss2 = (
        f"({commodities[0]} OR {commodities[1]}) "
        f"({countries[0]} OR {countries[1]} OR {countries[2]}) "
        f"(import OR shortage OR demand)"
    )
    jobs = [
        (_from_google_news_rss, (rss_q, 15)),
        (_from_google_news_rss, (rss2, 12)),
        (_from_newsapi, (rss_q, 10)),
        (_from_gdelt, (gdelt_q, 10)),
    ]
    articles = _gather(jobs)
    articles = [a for a in _dedupe(articles) if _is_demand_relevant(a["title"])]
    random.shuffle(articles)
    articles = articles[:limit]
    return {
        "articles": articles,
        "news_text": _to_news_block(
            articles,
            "LIVE DEMAND NEWS (only our countries + commodities, top 10)",
        ),
        "count": len(articles),
    }


def fetch_india_price_news(limit: int = MAX_NEWS) -> dict[str, Any]:
    rss_q, gdelt_q = _pick_price_query()
    commodities = COMMODITIES[:]
    random.shuffle(commodities)
    rss2 = f"({commodities[0]} OR {commodities[1]} OR {commodities[2]}) India (price OR mandi OR crop)"
    jobs = [
        (_from_google_news_rss, (rss_q, 15)),
        (_from_google_news_rss, (rss2, 12)),
        (_from_newsapi, (rss_q, 10)),
        (_from_gdelt, (gdelt_q, 10)),
    ]
    articles = _gather(jobs)
    articles = [a for a in _dedupe(articles) if _is_india_price_relevant(a["title"])]
    random.shuffle(articles)
    articles = articles[:limit]
    return {
        "articles": articles,
        "news_text": _to_news_block(
            articles,
            "LIVE INDIA COMMODITY PRICE NEWS (our commodities, any India region, top 10)",
        ),
        "count": len(articles),
    }


def fetch_live_news() -> dict[str, Any]:
    with ThreadPoolExecutor(max_workers=2) as pool:
        fut_d = pool.submit(fetch_demand_news, MAX_NEWS)
        fut_p = pool.submit(fetch_india_price_news, MAX_NEWS)
        demand = fut_d.result()
        price = fut_p.result()

    demand_titles = {a["title"].lower() for a in demand["articles"]}
    price_articles = [a for a in price["articles"] if a["title"].lower() not in demand_titles]
    if len(price_articles) < 3:
        price_articles = price["articles"]
    price_articles = price_articles[:MAX_NEWS]
    price = {
        "articles": price_articles,
        "news_text": _to_news_block(
            price_articles,
            "LIVE INDIA COMMODITY PRICE NEWS (our commodities, any India region, top 10)",
        ),
        "count": len(price_articles),
    }

    if demand["count"] == 0:
        demand["news_text"] = (
            "LIVE DEMAND NEWS unavailable right now. "
            "Need headlines mentioning our commodities + our countries "
            f"({', '.join(DEMAND_COUNTRIES[:6])}…)."
        )
    if price["count"] == 0:
        price["news_text"] = (
            "LIVE INDIA PRICE NEWS unavailable right now. "
            "Need headlines mentioning our commodities anywhere in India."
        )

    return {
        "fetched_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "providers": ["GDELT", "GoogleNewsRSS", "NewsAPI(optional)"],
        "demand_news": demand["news_text"],
        "price_news": price["news_text"],
        "demand_articles": demand["articles"],
        "price_articles": price["articles"],
        "demand_count": demand["count"],
        "price_count": price["count"],
        "note": (
            "Demand = our countries + commodities only. "
            "Price = our commodities from any part of India. "
            f"Up to {MAX_NEWS} headlines each."
        ),
    }
