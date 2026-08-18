# EXPORTINTEL AI — Complete Project Documentation

**Product name:** ExportIntel AI (Export AI)  
**Purpose:** Indian agricultural export decision support system  
**Document type:** Technical + Functional Explanation  
**Version:** 1.0  
**Date:** July 2026  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [What the System Does](#3-what-the-system-does)
4. [End-to-End Architecture](#4-end-to-end-architecture)
5. [Complete Folder & File Guide](#5-complete-folder--file-guide)
6. [Demand Prediction Module (Deep Dive)](#6-demand-prediction-module-deep-dive)
7. [Commodity Price Prediction Module (Deep Dive)](#7-commodity-price-prediction-module-deep-dive)
8. [Logistics Module (Deep Dive)](#8-logistics-module-deep-dive)
9. [Container Prioritization](#9-container-prioritization)
10. [Backend API](#10-backend-api)
11. [RAG Assistant](#11-rag-assistant)
12. [Frontend UI](#12-frontend-ui)
13. [Databricks / Optional Cloud Path](#13-databricks--optional-cloud-path)
14. [Tech Stack — Why We Chose It](#14-tech-stack--why-we-chose-it)
15. [Alternatives Considered and Why Not Used](#15-alternatives-considered-and-why-not-used)
16. [Data Flow & Formulas](#16-data-flow--formulas)
17. [How to Run the Project](#17-how-to-run-the-project)
18. [Security & Demo Auth Notes](#18-security--demo-auth-notes)
19. [Limitations & Future Improvements](#19-limitations--future-improvements)
20. [Glossary](#20-glossary)

---

## 1. Executive Summary

**ExportIntel AI** helps an Indian exporter answer practical questions such as:

- Which **country + commodity** looks strongest next month based on news?
- What will the **India mandi / buy price** be next month (INR per quintal)?
- Which **India port → foreign port** route is best (cost + time)?
- What is the estimated **net profit**?
- If only a few containers are available, **which shipment should go first**?
- What **documents / tariff / export basics** should I know? (RAG assistant)

The system is **not a hard-coded dashboard**. It combines:

1. Your trained **ML models** (demand + price)
2. **LLM-based sentiment / news feature extraction** (Groq)
3. **Rule + CSV logistics optimization**
4. **Container allocation scoring**
5. **RAG Q&A** over local export knowledge documents
6. A **React** UI + **Flask** API + **SQLite** persistence

---

## 2. Problem Statement

Indian agri exporters often face fragmented decision-making:

| Challenge | Without this system | With ExportIntel AI |
|---|---|---|
| Market signal reading | Manual news reading | Automated sentiment + flags from news |
| Demand prioritization | Gut feel | Trained demand model + ranking |
| Price expectation | Spreadsheet guess | XGBoost next-month price |
| Route choice | Call freight agent only | Multi-port cost/time ranking |
| Profit estimate | Incomplete | Sell − Buy − Logistics |
| Limited containers | Random allocation | Priority scoring |
| Compliance questions | Search many websites | Local RAG assistant |

---

## 3. What the System Does

### Stage pipeline (live web app)

```text
User pastes Demand News + Price News (+ available containers)
                    │
                    ▼
        ┌───────────────────────┐
        │  Stage 1: Demand ML   │  → top country-commodity opportunities
        └───────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Stage 2: Price ML    │  → next-month INR/quintal
        └───────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Stage 3: Logistics  │  → best route + cost + net profit
        └───────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ Stage 4: Containers   │  → allocate scarce containers
        └───────────────────────┘
                    │
                    ▼
        Explanations (Groq) + Save run to SQLite + Show Dashboard
```

Separately, the **AI Assistant** answers export/tariff questions using RAG (`backend/rag.py`).

---

## 4. End-to-End Architecture

```text
┌──────────────────────── Frontend (React + Vite) ────────────────────────┐
│ Landing | Login | Dashboard | Demand | Price | Logistics | Containers   │
│ Analytics | Agents | Knowledge | AI Assistant (RAG UI)                  │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ HTTP /api/*
                                  ▼
┌──────────────────────── Backend (Flask :5001) ──────────────────────────┐
│ app.py → pipeline.py → demand.py / price.py / logistics.py / containers │
│ auth.py | db.py (SQLite) | rag.py | llm.py | explain.py                 │
└───────┬───────────────┬──────────────────┬──────────────────────────────┘
        │               │                  │
        ▼               ▼                  ▼
 Demand_prediction   commodities        Logistics + Logistics_Costs
 (joblib model)      (XGBoost pkl)      (CSV costs + trade sell prices)
        │               │
        └─────── Groq LLM for news feature extraction / explanations ─────┘
```

---

## 5. Complete Folder & File Guide

### 5.1 Root: `Export_AI/`

| Item | Why it exists |
|---|---|
| `README.md` | Quick start guide |
| `backend/` | Live API used by the website |
| `frontend/` | React user interface |
| `Demand_prediction/` | Demand model training + inference |
| `commodities/` | Price model training + inference |
| `Logistics/` | Port/freight CSVs + route optimizer engine |
| `Logistics_Costs/` | Precomputed India→world cost lookup used by live backend |
| `Container_prioritization/` | Container allocation algorithm |
| `databricks/` | Optional cloud/streaming/training notebooks |
| Root CSVs (`monthly_price.csv`, `gdelt_news.csv`, etc.) | Research / older datasets used while building models |

Many root-level CSVs are **historical working files**. The live app primarily uses models and folders listed above.

---

### 5.2 `Demand_prediction/`

| File / Asset | Role |
|---|---|
| `demand_model_bundle.joblib` | Trained demand model bundle (loaded at prediction time) |
| `demand_agent_tools.py` | Loads model, builds monthly features, predicts demand probability |
| `predict_top3_from_news.py` | Main entry: news → Groq/offline sentiment features → model → top N |
| `demand_agent.py` | Standalone agent CLI / helper |
| `train_model.py` | Training script |
| `demand_future.ipynb` | Notebook used to develop/train demand model |
| `countries_news_sentiment.ipynb` | Sentiment labeling / analysis workflow |
| `news_translate_dataset.ipynb` | Translation / English normalization workflow |
| `generate_synthetic_news.py` | Creates synthetic news + sentiment fields for more training data |
| `synthetic_news_dataset.csv` | Synthetic news dataset |
| `final_news_dataset_*.csv` / cleaned English CSVs | Historical labeled news used as demand history/lags |
| Forecast CSVs (`next_month_demand_predictions.csv`, rankings, etc.) | Offline batch forecast outputs for analysis |

**Why this folder exists:** Demand is learned from news indicators (sentiment, shortage, production, price flags, export opportunity) plus monthly history.

---

### 5.3 `commodities/`

| File / Asset | Role |
|---|---|
| `commodity_xgboost_generalized.pkl` | Primary live price model |
| `commodity_xgboost.pkl` / older pkls | Older model versions / backups |
| `price_agent_tools.py` | Loads model and predicts next price |
| `monthly_price.csv` | Current market series (used as “current price”) |
| `training_dataset.csv` / `price_features.csv` / `price_long.csv` | Training feature tables |
| Commodity master CSVs (Wheat, Onion, Coffee, etc.) | Raw/cleaned mandi history |
| `final1.ipynb`, `future_price1.ipynb` | Training / experimentation notebooks |
| `pivot_dataset.py`, `wheat.py` | Data preparation utilities |

**Why this folder exists:** Price prediction needs market history + news sentiment features in a consistent INR/quintal unit.

---

### 5.4 `Logistics/`

| File | Role |
|---|---|
| `ports.csv` | Indian ports (id, name, UN/LOCODE, lat/lon) |
| `destination_ports.csv` | Foreign ports by country |
| `freight_rates.csv` | Scheduled ocean freight + transit days |
| `port_charges.csv` | Terminal handling style charges |
| `container_cost.csv` | 20FT/40FT payload + container operating cost |
| `inland_rates.csv` | Truck/rail USD per ton-km |
| `commodity_origins.csv` | Buy hubs (e.g., Onion→Nashik, Wheat→Ludhiana) |
| `commodity_country_trade.csv` | Avg export sell USD/ton + typical quantity |
| `data_loader.py` | Loads/joins CSVs, resolves origin & destination |
| `cost_model.py` | Haversine distance, inland cost, freight lookup/estimate |
| `optimizer.py` | Builds all route candidates and ranks them |
| `decision_engine.py` | Converts #1 route into decision text + optional JSON |
| `pipeline_bridge.py` | Connects demand/price outputs into logistics |
| `optimize_route.py` | CLI for one commodity→country optimization |
| `output/latest_decision.json` | Latest offline CLI decision dump |
| `output/full_pipeline_decision.json` | Offline full-pipeline sample snapshot |
| `output/onion_saudi.json` | Example single-lane decision |

**Important:** Live website primarily uses **`Logistics_Costs`** for fast route cost lookup and `commodity_country_trade.csv` for sell price. The detailed `Logistics/` optimizer is the engine/data source and offline tooling.

---

### 5.5 `Logistics_Costs/`

| File | Role |
|---|---|
| `india_to_world_port_costs.csv` | Precomputed India port → destination port costs |
| `cost_lookup.py` | Finds best/cheapest route for a country |
| `build_costs_dataset.py` | Rebuilds the precomputed CSV from `Logistics/*.csv` |
| `README.md` | Notes for this module |

**Why:** Recomputing every Haversine/freight combination on each API request is slower. Precompute once, lookup many times.

---

### 5.6 `Container_prioritization/`

| File | Role |
|---|---|
| `prioritize.py` | Scores lanes and allocates limited containers |
| `__init__.py` | Package marker |

Priority score mix (approximate):

- 40% demand
- 35% profit
- 15% logistics cost efficiency
- 10% transit time efficiency

---

### 5.7 `backend/`

| File | Role |
|---|---|
| `app.py` | Flask routes: health, login, pipeline, RAG, latest |
| `pipeline.py` | Orchestrates demand → price → logistics → containers → explanations |
| `demand.py` | Wrapper calling `Demand_prediction/predict_top3_from_news.py` |
| `price.py` | Wrapper calling commodities price tools + news features |
| `logistics.py` | Profit + lane planning using Logistics_Costs + trade CSV |
| `containers.py` | Bridge to prioritization module |
| `auth.py` | Demo username/password login + token |
| `db.py` | SQLite schema + save/load pipeline runs & logistics costs |
| `export_ai.db` | SQLite database file (live run storage) |
| `rag.py` | TF-IDF retrieval + Groq answer generation |
| `rag_docs/*.md` | Knowledge documents for RAG |
| `llm.py` | Groq client helper |
| `explain.py` | Stage-wise AI explanations for dashboard |
| `samples.py` | Sample news for UI demo |
| `train_demand.py` / `train_price.py` | Convenience training entrypoints |
| `requirements.txt` | Python dependencies |
| `.env` / `.env.example` | Groq API key and model settings |
| `run_backend.bat` | Windows helper to start backend |

---

### 5.8 `frontend/`

| Path | Role |
|---|---|
| `src/main.jsx` | App bootstrap |
| `src/App.jsx` | Routes |
| `src/api.js` | Calls Flask APIs |
| `src/context/AppContext.jsx` | Auth + shared app state |
| `src/hooks/useAnalysis.js` | Runs pipeline analysis |
| `src/pages/*` | Landing, Login, Dashboard, Demand, Price, Logistics, Containers, Analytics, Agents, Knowledge, Assistant |
| `src/components/layout/*` | Sidebar, header, shell |
| `src/components/LoginPage.jsx` | Login form |
| `src/components/rag/TradeAssistant.jsx` | RAG chat UI |
| `src/styles.css` | Global styling |
| `vite.config.js` | Dev server + `/api` proxy to port 5001 |
| `package.json` | Frontend dependencies |

---

### 5.9 `databricks/` (optional)

Contains notebooks/jobs for catalog setup, Kafka streaming bronze/silver, model training, and gold predictions. Useful for cloud-scale deployment; **not required** for local demo.

---

## 6. Demand Prediction Module (Deep Dive)

### 6.1 Goal
Predict a **next-month news-based demand probability** for a country–commodity pair (not physical import tonnage, because clean quantity history was not available in the news dataset).

### 6.2 Input
Free-text news (one or many paragraphs) mentioning countries + commodities in the supported set.

Supported countries (examples): Bangladesh, China, Germany, Indonesia, Japan, Malaysia, Nepal, Netherlands, Saudi Arabia, Singapore, Sri Lanka, Vietnam.

Supported commodities: Coffee, Cotton, Maize, Onion, Soybean, Sugar, Turmeric, Wheat.

### 6.3 Sentiment / feature extraction (on inputted news only)

Prefer Groq LLM extraction of fields matching your training schema:

- `sentiment_score` (−1 to 1)
- `shortage_flag`, `production_drop`, `production_rise`
- `price_increase`, `price_decrease`
- `export_opportunity_score` (0–100)
- `confidence` (0–1)

If Groq fails → offline keyword fallback.

### 6.4 Model inference
`demand_agent_tools.predict_demand()`:

1. Loads `demand_model_bundle.joblib`
2. Loads historical news CSV for lag/monthly context
3. Appends current news features into the latest month
4. Builds monthly aggregates
5. Predicts current demand probability
6. Projects one month ahead with a bounded recent trend

Output includes:

- predicted demand probability / percentage
- direction label (Strong Increase → Strong Decrease)
- trend vs current month
- forecast month

### 6.5 Top-3 selection
`predict_top3_from_news.py` scores all extracted pairs, prefers country diversity, returns top N with AI explanation.

---

## 7. Commodity Price Prediction Module (Deep Dive)

### 7.1 Goal
Predict **next-month India price in INR per quintal**.

### 7.2 Current price source
From `commodities/monthly_price.csv` (preferred month used in code: 2026-06), including:

- price
- price_change / price_pct_change
- MA7, MA30

### 7.3 News features for price
From price news text (Groq preferred, keyword fallback):

- total_news
- average_sentiment
- positive/negative/neutral news counts
- news_growth

### 7.4 Model
`commodity_xgboost_generalized.pkl` via `price_agent_tools.predict_price()`.

Generalized mode predicts a return and applies:

```text
predicted_price = current_price × (1 + predicted_return)
```

Then clipped to a realistic band around current price (e.g., ±35%) for stability.

### 7.5 Why next-month price matters
It becomes the **India buy cost** in net-profit calculation.

---

## 8. Logistics Module (Deep Dive)

### 8.1 Physical journey modeled

```text
Origin farm/mandi → inland truck/rail → Indian port → ocean → foreign port
```

### 8.2 Cost components considered

| Component | Source |
|---|---|
| Inland haulage | distance × inland rate (truck/rail) |
| Origin port charges | `port_charges.csv` |
| Destination port charges | approx 0.8 × origin THC (or precomputed) |
| Container cost | `container_cost.csv` |
| Ocean freight | `freight_rates.csv` or distance estimate |

### 8.3 Distance math
Haversine great-circle distance from lat/lon, with circuity factors:

- inland road ≈ ×1.25
- sea route ≈ ×1.35 (when estimating)

### 8.4 Route ranking score

```text
score = 0.7 × normalized(cost) + 0.3 × normalized(transit_days)
```

Lower score is better.

### 8.5 Offline decision JSON
`decision_engine.save_decision()` writes a human + machine readable decision:

- decision_summary
- action_plan
- best_route + cost_breakdown
- alternative_route
- top_routes

CLI default file: `Logistics/output/latest_decision.json`.

### 8.6 Live backend logistics
`backend/logistics.py` uses:

- route/cost from `Logistics_Costs`
- sell price + typical quantity from `commodity_country_trade.csv`
- buy price from ML predicted INR/quintal

---

## 9. Container Prioritization

When containers are scarce (example: 6 × 20FT):

1. Score each profitable lane
2. Rank by priority score
3. Allocate more containers to higher scores
4. Mark `export_first` lane

This turns prediction into an operational plan.

---

## 10. Backend API

### Key endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Model/LLM/DB status |
| POST | `/api/login` | Demo auth |
| POST | `/api/logout` | Clear token |
| GET | `/api/sample-news` | Demo news text |
| POST | `/api/pipeline` | Full analysis run |
| POST | `/api/rag/ask` | RAG assistant |
| GET | `/api/latest` | Latest stored run |
| GET | `/api/logistics-costs` | Stored cost rows |

### Persistence
Live runs save to **SQLite** (`export_ai.db`), not to `full_pipeline_decision.json`.

Tables include:

- `pipeline_runs` — full JSON result per run
- `logistics_costs` — cost breakdown rows

---

## 11. RAG Assistant

File: `backend/rag.py`

### What RAG means here
**Retrieval-Augmented Generation**:

1. Retrieve relevant paragraphs from local markdown docs
2. Generate answer with Groq using that context

### Retrieval technology used
- scikit-learn **TF-IDF**
- **Cosine similarity**
- In-memory index (no dedicated vector database)

### Knowledge docs
- `india_export_tariff_guide.md`
- `import_export_faq.md`
- `destination_market_notes.md`

### Methods returned
- `tfidf_rag_groq` when Groq works
- `tfidf_only` extractive fallback when Groq unavailable

RAG is for **Q&A help**, not for demand/price numeric prediction.

---

## 12. Frontend UI

### Pages
- Landing page (marketing + login entry)
- Login gate
- Dashboard overview
- Demand / Price / Logistics / Containers detail pages
- Analytics & Global Trade views
- Agent reasoning explanations
- Knowledge base page
- AI Assistant (RAG)

### Auth UX
Demo accounts (see auth section). Exporter password configured as `india@11` in current codebase.

### Design stack
React + Vite + React Router + Recharts + Lucide icons.

Vite proxies `/api` → `http://127.0.0.1:5001`.

---

## 13. Databricks / Optional Cloud Path

The `databricks/` folder demonstrates a future production pattern:

- bronze streaming ingest
- silver scoring
- gold daily predictions
- scheduled jobs

Local project runs without Databricks.

---

## 14. Tech Stack — Why We Chose It

| Layer | Choice | Why chosen |
|---|---|---|
| Frontend | React + Vite | Fast UI development, component model, easy local demo |
| Routing | React Router | Clear multi-page app structure |
| Charts | Recharts | Simple React charts for KPIs |
| Backend | Flask | Lightweight Python API that easily imports ML scripts |
| Language (ML/API) | Python | Ecosystem for pandas/sklearn/xgboost/joblib |
| Demand model | joblib bundle (XGBoost-style tabular model) | Fits structured monthly news features well |
| Price model | XGBoost | Strong tabular regressor for price/news features |
| News understanding | Groq LLM (`llama-3.3-70b-versatile`) | Fast/cheap-enough structured extraction from free text |
| Logistics | CSV + deterministic optimizer | Transparent, auditable costs; no black-box freight API needed for MVP |
| Cost acceleration | Precomputed `Logistics_Costs` | Faster API responses |
| Storage | SQLite | Zero-ops local persistence |
| RAG retrieval | TF-IDF | Simple, no infra, good for small curated docs |
| Auth (demo) | In-memory users + token | Enough for classroom/demo login gate |

---

## 15. Alternatives Considered and Why Not Used

### 15.1 Backend framework

| Alternative | Why not used (for this project stage) |
|---|---|
| FastAPI | Excellent, but Flask was enough and simpler for notebook-style ML imports |
| Django | Heavier (ORM/admin) than needed for an ML decision API |
| Node.js backend | Would complicate calling Python ML models |

### 15.2 Frontend

| Alternative | Why not used |
|---|---|
| Next.js | SSR/SEO less critical for authenticated exporter desk |
| Angular / Vue | Team/stack preference and React ecosystem fit charts/UI faster |
| Pure HTML/JS | Harder to maintain multi-page intelligence UI |

### 15.3 Demand / Price models

| Alternative | Why not used now |
|---|---|
| LSTM / Transformers time-series | Need denser clean quantity/price sequences; harder to explain |
| Prophet | Good for univariate seasonality; weaker with multi news flags |
| Random Forest only | Often slightly weaker than boosted trees on this tabular mix |
| Pure LLM numeric prediction | Unstable numbers; harder to audit than trained model |

**Decision:** use LLM for **feature extraction**, ML model for **numeric prediction**.

### 15.4 Vector databases for RAG

| Alternative | Why not used now |
|---|---|
| FAISS | Extra dependency; overkill for 3 markdown files |
| Chroma / Pinecone / Weaviate | Need embeddings infra/cost; better when docs grow large |
| Elasticsearch | Ops-heavy for local demo |

**Decision:** TF-IDF is enough for small trusted knowledge base.

### 15.5 Database

| Alternative | Why not used now |
|---|---|
| PostgreSQL / MySQL | Better for multi-user production, but heavier local setup |
| MongoDB | Less natural for relational run/cost tables in this MVP |

### 15.6 Auth

| Alternative | Why not used now |
|---|---|
| Auth0 / Firebase Auth | External dependency for a demo |
| Full JWT + hashed password DB | Needed for production; demo users sufficient for current scope |

### 15.7 Live freight APIs

| Alternative | Why not used now |
|---|---|
| Freightos / carrier APIs | Paid, credentialed, rate volatility; CSV gives controllable reproducible demo |

### 15.8 Hard-coded predictions

Not used for demand/price outputs. Predictions come from models + news features.  
CSVs are used for **reference costs/origins/trade averages**, which is expected in logistics planning.

---

## 16. Data Flow & Formulas

### 16.1 Net profit

```text
Buy USD/ton = (Predicted_INR_per_quintal × 10) / 83.5
Sell USD/ton = avg_export_price_usd_per_ton (trade CSV)
Logistics USD/ton = route cost_per_ton_usd

Net USD/ton = Sell − Buy − Logistics
Total INR ≈ Net USD/ton × quantity_tons × 83.5
```

### 16.2 Is next-month price used?
**Yes.** Predicted next-month India price is the buy side.

### 16.3 Are quantities used?
**Yes**, but as planning quantities:

- preferred from `typical_quantity_tons` in trade CSV
- else container payload × containers

Demand ML does **not** predict import tonnage.

### 16.4 Costs included in logistics
Included: inland, origin port, destination port, container, ocean freight.  
Not fully included: foreign import duty, buyer inland delivery, full cargo value insurance, financing, agent commissions.

---

## 17. How to Run the Project

### Prerequisites
- Python 3.10+ recommended
- Node.js 18+
- Groq API key in `backend/.env`

```env
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

### Start backend

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Runs on `http://127.0.0.1:5001`

### Start frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`

### Demo login (current)
- exporter / `india@11`
- demo / `demo@123`
- admin / `admin@123`

### Optional rebuild logistics costs

```bash
cd Logistics_Costs
python build_costs_dataset.py
```

### Optional offline logistics CLI

```bash
cd Logistics
python optimize_route.py --commodity Wheat --country Bangladesh --qty 100
```

Saves `output/latest_decision.json`.

---

## 18. Security & Demo Auth Notes

- Current auth is **demo-grade** (plain passwords in `auth.py`).
- Suitable for local presentation / academic demo.
- Before any real deployment: hash passwords, use proper sessions/JWT, HTTPS, secrets manager, role-based access, and rotate any exposed API keys.

---

## 19. Limitations & Future Improvements

### Current limitations
1. Demand target is news-based probability, not physical import quantity.
2. Trade sell prices are averages, not live contracted prices.
3. Logistics costs are dataset/schedule approximations.
4. RAG is TF-IDF (keywordish), not deep semantic embeddings.
5. Auth is demo only.
6. `Logistics/output/*.json` are offline snapshots, not live UI storage.

### Recommended upgrades
1. Replace TF-IDF with embeddings + Chroma/FAISS when docs grow.
2. Move SQLite → PostgreSQL for multi-user.
3. Add hashed auth + roles (exporter/admin/analyst).
4. Integrate live freight/rate APIs where budget allows.
5. Add model monitoring (prediction drift, news quality checks).
6. Package with Docker Compose for one-command deploy.
7. Expand evaluation metrics dashboards for demand/price backtesting.

---

## 20. Glossary

| Term | Meaning |
|---|---|
| INR/quintal | Indian rupees per 100 kg |
| Ton | 10 quintals |
| FOB | Free On Board (buyer pays ocean freight) |
| CIF | Cost, Insurance, Freight (seller includes freight/insurance) |
| UN/LOCODE | Standard port location code |
| THC | Terminal Handling Charges |
| RAG | Retrieval-Augmented Generation |
| TF-IDF | Term Frequency–Inverse Document Frequency |
| XGBoost | Gradient boosted trees algorithm |
| joblib | Python serialization format commonly used for sklearn/xgb models |
| Groq | Hosted LLM inference provider used for extraction/explanations |

---

## Appendix A — Decision JSON (offline logistics) field guide

Typical fields in `latest_decision.json`:

- `recommend_export`: boolean recommendation flag
- `decision_summary`: plain-English decision
- `purchase_guidance`: where/what price guidance
- `demand_guidance`: demand score interpretation
- `action_plan`: numbered operational steps
- `best_route`: chosen ports, mode, days, score
- `cost_breakdown_usd`: inland/port/container/ocean/total
- `alternative_route`: second-best option
- `top_routes`: ranked candidate list

---

## Appendix B — “Is anything hard-coded?”

| Item | Hard-coded? |
|---|---|
| Demand/price numeric outputs | No — ML models |
| Sentiment on input news | No — Groq/offline extraction on your pasted news |
| Port coordinates / freight tables | Reference CSVs (expected for logistics) |
| Demo passwords | Yes (demo auth) |
| Offline JSON samples | Static until regenerated by CLI/scripts |

---

## Appendix C — Module ownership map

| Question user asks | Module that answers |
|---|---|
| Where is demand rising? | Demand_prediction + backend/demand.py |
| What will India price be? | commodities + backend/price.py |
| Which route/port? | Logistics / Logistics_Costs |
| Will I make profit? | backend/logistics.py profit formula |
| Which container first? | Container_prioritization |
| What documents/tariffs? | backend/rag.py |
| Show me charts/UI | frontend |

---

**End of Document**

Prepared for project understanding, viva/presentation, and technical handover.  
Primary codebase root: `Export_AI/`
