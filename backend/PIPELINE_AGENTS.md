# How the automated Export AI pipeline is connected (multi-agent)

## Agents (in order)

1. **News Agent** (`news_fetcher.py`)
   - Calls verified news APIs (no manual paste needed)
   - **GDELT** — global media index (research-grade)
   - **Google News RSS** — public authenticated news search
   - **NewsAPI.org** — optional if `NEWS_API_KEY` is set
   - Builds two bundles: country-commodity demand news + India mandi price news

2. **Demand Agent** (`demand.py` → `Demand_prediction/predict_top3_from_news.py`)
   - Reads live demand news with Groq + your demand ML model
   - Outputs top country + commodity opportunities (scores change with news)

3. **Price Agent** (`price.py` + XGBoost)
   - Reads India price news
   - Predicts next-month INR/quintal
   - News sentiment adjustment so different news → different prices

4. **Logistics Agent** (`logistics.py`)
   - Best India port → destination port + net profit

5. **Container Agent** (`containers.py`)
   - Allocates scarce containers by priority

6. **Explain Agent** (`explain.py` + Groq)
   - Demand + Price explanations only
   - **Not hardcoded** — Groq writes fresh text from live facts/news

7. **RAG Agent** (`rag.py` vector DB)
   - Chroma (or sklearn vector store fallback)
   - Indexed from your CSV datasets + GDELT trade headlines
   - **No .md knowledge files**

## Trigger

UI **Run Analysis** → `POST /api/pipeline` with `auto_news: true`
→ News Agent fetches → other agents run → Groq explains → UI shows results

Optional: **Fetch Live News** button → `GET /api/fetch-live-news` only.
