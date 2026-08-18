# Databricks + Kafka — simple steps

Daily flow:
News → Kafka → Databricks Bronze → Silver score → Gold predictions → Flask/UI

## Topics (Confluent Cloud)
- `export-ai-demand-news`
- `export-ai-price-news`

## Secrets (Databricks scope `export-ai`)
```
kafka-bootstrap
kafka-api-key
kafka-api-secret
groq-api-key
```

## Run notebooks in order
1. `00_setup_catalog_tables.py` — create catalog/tables  
2. `01_upload_reference_data.py` — ports, freight, training CSVs  
3. `02_kafka_stream_bronze.py` — stream Kafka news into Delta  
4. `03_score_silver.py` — clean / label news  
5. `04_train_models.py` — demand + price models  
6. `05_daily_predictions_gold.py` — daily predictions + profit  

Or run job: `jobs/export_ai_job.json`

## Send sample news to Kafka
```bash
cd databricks/producer
python send_news_to_kafka.py
```

Set env: `KAFKA_BOOTSTRAP`, `KAFKA_API_KEY`, `KAFKA_API_SECRET`
