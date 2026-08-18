"""
Vector DB RAG (Chroma) — NO .md knowledge files.

Indexed from trusted / original project datasets + live GDELT trade headlines:
  - Demand_prediction/*.csv  (your labeled demand / forecast datasets)
  - commodities/training_dataset.csv + monthly_price.csv
  - Logistics/*.csv (ports, freight, charges)
  - Fresh GDELT trade/tariff/export headlines (verified global media index)

Ask → retrieve top chunks from Chroma → Groq answers using ONLY retrieved text.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import pandas as pd

from llm import ask_llm, llm_status

ROOT = Path(__file__).resolve().parents[1]
BACKEND = Path(__file__).resolve().parent
CHROMA_DIR = BACKEND / "vector_db" / "chroma"
COLLECTION = "export_ai_trusted_kb"

_client = None
_collection = None


def _get_collection():
    """Lazy-load Chroma persistent collection (falls back to sklearn store)."""
    global _client, _collection
    if _collection is not None:
        return _collection

    try:
        import chromadb
        from chromadb.config import Settings

        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
        _collection = _client.get_or_create_collection(
            name=COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
        return _collection
    except Exception as exc:
        print("Chroma unavailable, using sklearn vector store:", exc)
        _collection = "_sklearn_"
        return _collection


# ---- sklearn fallback vector store (still NOT .md files) ----
_SK_PATH = BACKEND / "vector_db" / "sklearn_store.joblib"
_sk_store = None


def _sk_load():
    global _sk_store
    if _sk_store is not None:
        return _sk_store
    import joblib

    if _SK_PATH.exists():
        _sk_store = joblib.load(_SK_PATH)
    else:
        _sk_store = {"rows": [], "vectorizer": None, "matrix": None}
    return _sk_store


def _sk_save(store):
    import joblib

    _SK_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(store, _SK_PATH)


def _uid(*parts: str) -> str:
    raw = "|".join(parts)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _store_count() -> int:
    col = _get_collection()
    if col == "_sklearn_":
        return len((_sk_load().get("rows") or []))
    return int(col.count())


def _chunk_rows(rows: list[dict[str, str]]) -> None:
    col = _get_collection()
    if not rows:
        return
    if col == "_sklearn_":
        from sklearn.feature_extraction.text import TfidfVectorizer

        store = _sk_load()
        # merge by id
        by_id = {r["id"]: r for r in store.get("rows") or []}
        for r in rows:
            by_id[r["id"]] = r
        merged = list(by_id.values())
        vec = TfidfVectorizer(stop_words="english", max_features=8000, ngram_range=(1, 2))
        matrix = vec.fit_transform([r["text"] for r in merged])
        store = {"rows": merged, "vectorizer": vec, "matrix": matrix}
        _sk_save(store)
        global _sk_store
        _sk_store = store
        return

    batch = 100
    for i in range(0, len(rows), batch):
        part = rows[i : i + batch]
        col.upsert(
            ids=[r["id"] for r in part],
            documents=[r["text"] for r in part],
            metadatas=[{"source": r["source"], "title": r["title"]} for r in part],
        )


def _load_demand_csvs() -> list[dict[str, str]]:
    folder = ROOT / "Demand_prediction"
    out = []
    files = [
        "synthetic_news_dataset.csv",
        "all_country_commodity_demand_forecasts.csv",
        "top3_demand_recommendations.csv",
        "monthly_country_commodity_predictions.csv",
        "global_commodity_ranking.csv",
    ]
    for name in files:
        path = folder / name
        if not path.exists():
            continue
        try:
            df = pd.read_csv(path)
        except Exception:
            continue
        # Prefer news-like columns
        cols = {c.lower(): c for c in df.columns}
        title_col = cols.get("title_english") or cols.get("title") or cols.get("news")
        for idx, row in df.head(400).iterrows():
            if title_col and pd.notna(row.get(title_col)):
                text = str(row[title_col])
                commodity = str(row.get(cols.get("commodity", "commodity"), ""))
                country = str(row.get(cols.get("country", "country"), ""))
                extra = f" Commodity={commodity}. Country={country}."
                body = f"[Demand dataset:{name}] {text}.{extra}"
            else:
                # structured forecast row
                body = f"[Demand forecast:{name}] " + ", ".join(
                    f"{c}={row[c]}" for c in df.columns[:8] if pd.notna(row.get(c))
                )
            if len(body) < 40:
                continue
            out.append(
                {
                    "id": _uid("demand", name, str(idx), body[:80]),
                    "source": f"Demand_prediction/{name}",
                    "title": f"Demand record {name}#{idx}",
                    "text": body[:1200],
                }
            )
    return out


def _load_price_csvs() -> list[dict[str, str]]:
    folder = ROOT / "commodities"
    out = []
    for name in ("training_dataset.csv", "monthly_price.csv"):
        path = folder / name
        if not path.exists():
            continue
        df = pd.read_csv(path)
        # Keep recent rows per commodity
        if {"commodity", "year", "month", "price"}.issubset(df.columns):
            df = df.sort_values(["year", "month"]).groupby("commodity", as_index=False).tail(8)
        for idx, row in df.iterrows():
            body = (
                f"[India price dataset:{name}] commodity={row.get('commodity')}, "
                f"year={row.get('year')}, month={row.get('month')}, "
                f"price_INR_per_quintal={row.get('price')}, "
                f"price_change={row.get('price_change')}, "
                f"MA7={row.get('MA7')}, MA30={row.get('MA30')}."
            )
            out.append(
                {
                    "id": _uid("price", name, str(idx)),
                    "source": f"commodities/{name}",
                    "title": f"Price {row.get('commodity')} {row.get('year')}-{row.get('month')}",
                    "text": body,
                }
            )
    return out


def _load_logistics_csvs() -> list[dict[str, str]]:
    folder = ROOT / "Logistics"
    out = []
    mapping = {
        "ports.csv": "Indian export ports reference",
        "destination_ports.csv": "Destination country ports reference",
        "freight_rates.csv": "Ocean freight rate schedule",
        "port_charges.csv": "Indian port charges schedule",
        "container_cost.csv": "Container cost schedule",
        "commodity_origins.csv": "Commodity origin hubs in India",
        "inland_rates.csv": "Inland truck/rail haulage rates",
    }
    for name, title in mapping.items():
        path = folder / name
        if not path.exists():
            continue
        df = pd.read_csv(path)
        for idx, row in df.head(300).iterrows():
            body = f"[Logistics dataset:{name} | {title}] " + ", ".join(
                f"{c}={row[c]}" for c in df.columns if pd.notna(row.get(c))
            )
            out.append(
                {
                    "id": _uid("logistics", name, str(idx)),
                    "source": f"Logistics/{name}",
                    "title": f"{title} row {idx}",
                    "text": body[:1200],
                }
            )
    return out


def _load_live_trade_headlines() -> list[dict[str, str]]:
    """Trusted live media via GDELT for tariff / export / IEC style questions."""
    try:
        from news_fetcher import _from_gdelt
    except Exception:
        return []
    queries = [
        "India export IEC OR tariff OR phytosanitary OR HS code",
        "India agricultural export onion OR wheat OR sugar OR coffee documentation",
        "CIF FOB shipping bill Indian exporter customs",
    ]
    out = []
    for q in queries:
        for a in _from_gdelt(q, maxrecords=12):
            body = (
                f"[Live GDELT trade news] {a['title']}. "
                f"Source domain={a.get('source')}. URL={a.get('url')}."
            )
            out.append(
                {
                    "id": _uid("gdelt", a.get("url") or a["title"]),
                    "source": "GDELT",
                    "title": a["title"][:120],
                    "text": body[:1200],
                }
            )
    return out


def build_vector_db(force: bool = False) -> dict[str, Any]:
    existing = _store_count()
    if existing > 50 and not force:
        return {"status": "ready", "chunks": existing, "rebuilt": False, "engine": "chroma_or_sklearn"}

    rows = []
    rows += _load_demand_csvs()
    rows += _load_price_csvs()
    rows += _load_logistics_csvs()
    rows += _load_live_trade_headlines()
    uniq = {r["id"]: r for r in rows}
    _chunk_rows(list(uniq.values()))
    return {
        "status": "ready",
        "chunks": _store_count(),
        "rebuilt": True,
        "added": len(uniq),
        "engine": "chromadb" if _get_collection() != "_sklearn_" else "sklearn_tfidf_vectors",
    }


def ask_rag(question: str, top_k: int = 5) -> dict[str, Any]:
    if not question or not question.strip():
        raise ValueError("question is required")

    info = build_vector_db(force=False)
    col = _get_collection()
    retrieved = []

    if col == "_sklearn_":
        from sklearn.metrics.pairwise import cosine_similarity

        store = _sk_load()
        rows = store.get("rows") or []
        vec = store.get("vectorizer")
        matrix = store.get("matrix")
        if not rows or vec is None or matrix is None:
            return {
                "question": question,
                "answer": "Vector DB is empty. Rebuild knowledge base first.",
                "sources": [],
                "used_llm": False,
                "method": "empty",
                "vector_db": info,
            }
        q = vec.transform([question.strip()])
        sims = cosine_similarity(q, matrix).ravel()
        idx = sims.argsort()[::-1][:top_k]
        for i in idx:
            retrieved.append(
                {
                    "score": round(float(sims[i]), 4),
                    "source": rows[i]["source"],
                    "title": rows[i]["title"],
                    "text": rows[i]["text"],
                }
            )
    else:
        result = col.query(
            query_texts=[question.strip()],
            n_results=min(top_k, max(1, col.count())),
        )
        docs = (result.get("documents") or [[]])[0]
        metas = (result.get("metadatas") or [[]])[0]
        dists = (result.get("distances") or [[]])[0]
        for i, doc in enumerate(docs):
            meta = metas[i] if i < len(metas) else {}
            dist = float(dists[i]) if i < len(dists) else 1.0
            retrieved.append(
                {
                    "score": round(max(0.0, 1.0 - dist), 4),
                    "source": meta.get("source", "vector_db"),
                    "title": meta.get("title", "chunk"),
                    "text": doc,
                }
            )

    status = llm_status()
    used_llm = False
    method = "vector_extractive"

    if not retrieved:
        answer = "Vector DB has no matching chunks yet. Rebuild the knowledge base."
    elif status["enabled"]:
        context = "\n\n".join(
            f"[{r['title']} | {r['source']}]\n{r['text'][:900]}" for r in retrieved
        )
        prompt = (
            f"Question: {question.strip()}\n\n"
            f"Trusted retrieved context (datasets + GDELT):\n{context}\n\n"
            "Answer using ONLY this context. If insufficient, say what is missing. "
            "Be concise for an Indian exporter (under 180 words)."
        )
        llm_answer = ask_llm(
            prompt,
            system=(
                "You are Export AI RAG. Use only provided vector-DB context from "
                "original datasets and GDELT. No invented laws."
            ),
        )
        if llm_answer:
            answer = llm_answer
            used_llm = True
            method = "vector_rag_groq"
        else:
            answer = " ".join(r["text"][:280] for r in retrieved[:3])
    else:
        answer = (
            "Groq is offline. Retrieved trusted snippets: "
            + " | ".join(r["text"][:220] for r in retrieved[:3])
        )

    return {
        "question": question,
        "answer": answer,
        "sources": retrieved,
        "used_llm": used_llm,
        "method": method,
        "vector_db": {
            "engine": info.get("engine"),
            "chunks": info.get("chunks"),
            "path": str(CHROMA_DIR if col != "_sklearn_" else _SK_PATH),
        },
    }
