# Export AI — Databricks + Confluent Cloud setup

This folder is the **data + ML layer**. Daily news arrives on Kafka (Confluent Cloud), Databricks streams it into Delta (bronze → silver → gold), and the Flask backend reads the gold tables for the UI.

Notebooks are `.py` files in Databricks **source format** (git-friendly). Import the `databricks/` folder as a Databricks Repo, or import each file as a notebook.

---

## 1. Create Confluent Cloud cluster + topics

1. Sign up / log in at [Confluent Cloud](https://confluent.cloud/).
2. Create a **Basic** cluster (any cloud region close to your Databricks workspace).
3. Create an **API key** (Cluster API key) — save the key and secret.
4. Create two topics (1 partition each is fine for demos):

| Topic name | Purpose |
|---|---|
| `export-ai-demand-news` | Demand / opportunity headlines |
| `export-ai-price-news` | India commodity price headlines |

5. Copy the **Bootstrap server** (looks like `pkc-xxxxx.region.aws.confluent.cloud:9092`).

CLI (optional, if you use `confluent` CLI):

```bash
confluent kafka topic create export-ai-demand-news --partitions 1
confluent kafka topic create export-ai-price-news --partitions 1
```

---

## 2. Databricks secret scope + secrets

Install the [Databricks CLI](https://docs.databricks.com/dev-tools/cli/index.html) and authenticate (`databricks auth login` or a personal access token).

```bash
# Create the scope once
databricks secrets create-scope --scope export-ai

# Kafka / Confluent
databricks secrets put --scope export-ai --key kafka-bootstrap
# paste: pkc-xxxxx.region.aws.confluent.cloud:9092

databricks secrets put --scope export-ai --key kafka-api-key
# paste: your Confluent API key

databricks secrets put --scope export-ai --key kafka-api-secret
# paste: your Confluent API secret

# Optional overrides (defaults match ARCHITECTURE.md)
databricks secrets put --scope export-ai --key kafka-topic-demand
# paste: export-ai-demand-news

databricks secrets put --scope export-ai --key kafka-topic-price
# paste: export-ai-price-news

# Groq (used later by Flask, optional here)
databricks secrets put --scope export-ai --key groq-api-key
# paste: your Groq key
```

`conf/config.py` reads these first via `dbutils.secrets.get`, then falls back to env vars (`KAFKA_BOOTSTRAP`, `KAFKA_API_KEY`, …).

Also set catalog/schema (env or secrets):

```
DATABRICKS_CATALOG=export_ai
DATABRICKS_SCHEMA=main
```

---

## 3. Import the notebooks

**Option A — Databricks Repo (recommended)**  
Add this Git repo in Databricks → Repos. Notebooks live under `databricks/`.

**Option B — Import files**  
Workspace → Import → each `0x_*.py` file (Databricks recognizes `# Databricks notebook source`).

Create a Unity Catalog **Volume** for raw CSVs, checkpoints, and model bundles:

```sql
CREATE VOLUME IF NOT EXISTS export_ai.main.raw;
CREATE VOLUME IF NOT EXISTS export_ai.main.checkpoints;
CREATE VOLUME IF NOT EXISTS export_ai.main.models;
```

Upload these folders into `/Volumes/export_ai/main/raw/`:

- `Logistics/` (all CSVs)
- `commodities/` (`training_dataset.csv`, `monthly_price.csv`)
- `Demand_prediction/` (`final_news_dataset_cleaned_english.csv`)

---

## 4. Run 00 and 01 once

| Notebook | What it does |
|---|---|
| `00_setup_catalog_tables` | Creates catalog, schema, bronze/silver/gold + `ref_*` tables |
| `01_upload_reference_data` | Loads CSVs from the Volume into `ref_*` Delta tables |

Open each notebook and **Run all**. In 01, confirm `DATA_ROOT = "/Volumes/export_ai/main/raw"` matches your upload.

---

## 5. Run 04 to train and register models

Open `04_train_models` → Run all.

This:

- Trains the demand model (TF-IDF + LogisticRegression / Ridge)
- Trains the price model (XGBoost on **% return**, then reconstructs price)
- Logs params/metrics to MLflow
- Registers models in Unity Catalog (`export_ai.main.demand_model`, `export_ai.main.price_model`)
- Writes joblib bundles to `/Volumes/export_ai/main/models/` (used by silver scoring)

Re-run 04 when you get more training data.

---

## 6. Start streaming + schedule daily gold

### Demo / low-cost path (recommended first)

1. Locally, send sample news:

```powershell
cd C:\Users\Lenovo\Desktop\Export_AI\databricks\producer
$env:KAFKA_BOOTSTRAP="pkc-xxxxx.region.aws.confluent.cloud:9092"
$env:KAFKA_API_KEY="..."
$env:KAFKA_API_SECRET="..."
pip install confluent-kafka
python send_news_to_kafka.py --dry-run   # preview
python send_news_to_kafka.py             # send
```

2. Run notebook `02_kafka_stream_bronze` (uses `availableNow` — catches up, then **stops**).
3. Run `03_score_silver`.
4. Run `05_daily_predictions_gold`.

### Scheduled job

Import `jobs/export_ai_job.json` (Jobs API / UI → Create job from JSON).  
It runs daily at 06:00 Asia/Kolkata:

`02 (Kafka→bronze)` → `03 (score silver)` → `05 (gold predictions)`

Edit `git_source.git_url` to your repo before creating the job:

```bash
databricks jobs create --json-file databricks/jobs/export_ai_job.json
```

### Continuous stream (higher cost)

In `02_kafka_stream_bronze`, comment out `.trigger(availableNow=True)` and uncomment `.trigger(processingTime="10 seconds")`.  
Run that notebook as a **separate always-on job** (no schedule end). Keep 03+05 on the daily schedule.

---

## 7. How the Flask backend connects

In `backend/.env` (names from `ARCHITECTURE.md`):

```
DATABRICKS_HOST=https://<workspace>.cloud.databricks.com
DATABRICKS_TOKEN=<personal access token>
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/<warehouse-id>
DATABRICKS_CATALOG=export_ai
DATABRICKS_SCHEMA=main
```

Create a **SQL Warehouse** in Databricks and copy its HTTP path.  
Flask uses the Databricks SQL connector to `SELECT` from:

- `export_ai.main.gold_demand_daily`
- `export_ai.main.gold_price_forecast`
- `export_ai.main.gold_export_decisions`

Endpoint `GET /api/latest` returns those gold rows. Local pipeline (`POST /api/pipeline`) still works without Databricks.

---

## 8. Local file → Databricks equivalent

| Local (today) | Databricks |
|---|---|
| Kafka N/A (paste news in UI) | Confluent topics → `02` → `bronze_news` |
| `backend/train_demand_model.py` | `04_train_models` (demand half) + UC model |
| `backend/train_price_model.py` | `04_train_models` (price half) + UC model |
| `backend/models/*.joblib` | `/Volumes/.../models/*.joblib` |
| `backend/services/demand_service.py` | `03_score_silver` (pandas UDF) + gold stage 1 |
| `backend/services/price_service.py` | `05` stage 2 |
| `Logistics/*.csv` | `ref_ports`, `ref_destination_ports`, … |
| `Logistics/optimizer.py` + `cost_model.py` | Inlined in `05_daily_predictions_gold` |
| `backend/services/profit_service.py` | Inlined in `05` |
| `backend/services/container_service.py` | Inlined in `05` |
| Pipeline result JSON | `gold_demand_daily` + `gold_price_forecast` + `gold_export_decisions` |
| `Demand_prediction/final_news_dataset_cleaned_english.csv` | `ref_demand_training` |
| `commodities/training_dataset.csv` | `ref_price_training` |
| `commodities/monthly_price.csv` | `ref_monthly_price` |

---

## 9. Cost / cluster sizing + how to stop the stream

**Sizing (demo / learning)**

- Single-node or 1-worker `i3.xlarge` / `m5d.large` is enough.
- Prefer `availableNow` on notebook 02 so the cluster **shuts down** after catch-up.
- SQL Warehouse: Serverless or 2X-Small is fine for Flask reads.

**Sizing (production continuous ingest)**

- Keep a small always-on job for Kafka→bronze only.
- Run silver + gold on a schedule (hourly/daily), not continuously.
- Turn off Photon if you do not need it for this workload.

**Stop the stream**

1. Jobs → open the streaming job → **Cancel run** / pause schedule.
2. Or in a notebook: `spark.streams.active` → `query.stop()`.
3. Delete the checkpoint only if you intentionally want to reprocess from `startingOffsets` (normally leave it).

**Delete demo data**

```sql
DELETE FROM export_ai.main.bronze_news;
DELETE FROM export_ai.main.silver_news_scored;
DELETE FROM export_ai.main.gold_demand_daily;
DELETE FROM export_ai.main.gold_price_forecast;
DELETE FROM export_ai.main.gold_export_decisions;
```

---

## File tree

```
databricks/
  README.md
  00_setup_catalog_tables.py
  01_upload_reference_data.py
  02_kafka_stream_bronze.py
  03_score_silver.py
  04_train_models.py
  05_daily_predictions_gold.py
  conf/
    __init__.py
    config.py
  jobs/
    export_ai_job.json
  producer/
    send_news_to_kafka.py
    sample_news.json
```

## Architecture tables (binding)

Column names in bronze / silver / gold match `ARCHITECTURE.md` character-for-character. Do not rename them — Flask depends on them.
