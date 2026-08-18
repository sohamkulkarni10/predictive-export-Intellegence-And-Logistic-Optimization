# Databricks notebook source
# MAGIC %md
# MAGIC # 00 — Create catalog, schema, and Delta tables
# MAGIC
# MAGIC Creates Unity Catalog objects for Export AI.
# MAGIC Table/column names match `ARCHITECTURE.md` exactly — the Flask backend reads these.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load shared config
# MAGIC Reads catalog/schema from secrets or env (`DATABRICKS_CATALOG`, `DATABRICKS_SCHEMA`).

# COMMAND ----------

import sys
from pathlib import Path

sys.path.insert(0, str(Path(".").resolve()))
from conf.config import catalog, schema, full_name

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create catalog and schema
# MAGIC `IF NOT EXISTS` so re-running this notebook is safe.

# COMMAND ----------

spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog()}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog()}.{schema()}")
print(f"Ready: {catalog()}.{schema()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze — raw Kafka payloads (append only)
# MAGIC One row per news event. We keep `raw_payload` so we can reprocess later if scoring logic changes.

# COMMAND ----------

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {full_name('bronze_news')} (
  event_id     STRING    COMMENT 'unique id from producer',
  news_type    STRING    COMMENT 'demand or price',
  source       STRING    COMMENT 'publisher/domain',
  published_at TIMESTAMP COMMENT 'article timestamp',
  title        STRING    COMMENT 'headline',
  body         STRING    COMMENT 'optional article text',
  language     STRING    COMMENT 'e.g. en',
  ingested_at  TIMESTAMP COMMENT 'stream write time',
  raw_payload  STRING    COMMENT 'original Kafka JSON value'
)
USING DELTA
COMMENT 'Bronze: raw Kafka news events, append only'
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver — cleaned + ML scored
# MAGIC One row per article after title cleaning and demand-model scoring.

# COMMAND ----------

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {full_name('silver_news_scored')} (
  event_id       STRING    COMMENT 'from bronze',
  news_type      STRING    COMMENT 'demand or price',
  published_at   TIMESTAMP,
  title_english  STRING    COMMENT 'cleaned headline used by models',
  commodity      STRING    COMMENT 'predicted by demand model',
  country        STRING    COMMENT 'predicted by demand model',
  demand_score   DOUBLE    COMMENT '0..1',
  sentiment      STRING    COMMENT 'positive / neutral / negative',
  sentiment_score DOUBLE   COMMENT '-1..1',
  scored_at      TIMESTAMP
)
USING DELTA
COMMENT 'Silver: cleaned headlines with demand model scores'
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold — daily demand opportunities
# MAGIC Top (commodity, country) pairs for the day's run. Flask reads this for Stage 1.

# COMMAND ----------

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {full_name('gold_demand_daily')} (
  run_date       DATE,
  rank           INT,
  commodity      STRING,
  country        STRING,
  demand_score   DOUBLE,
  mentions       INT,
  horizon_month  STRING
)
USING DELTA
COMMENT 'Gold: top demand opportunities per daily run'
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold — next-month India price forecasts
# MAGIC One row per commodity for the day's run. Flask reads this for Stage 2.

# COMMAND ----------

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {full_name('gold_price_forecast')} (
  run_date                        DATE,
  commodity                       STRING,
  current_price_inr               DOUBLE,
  predicted_next_month_price_inr  DOUBLE,
  predicted_change_pct            DOUBLE,
  horizon_month                   STRING
)
USING DELTA
COMMENT 'Gold: next-month India price predictions'
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold — final export decisions + container allocation
# MAGIC End of the daily pipeline. Flask reads this for Stages 3–5.

# COMMAND ----------

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {full_name('gold_export_decisions')} (
  run_date               DATE,
  priority_rank          INT,
  commodity              STRING,
  country                STRING,
  india_port             STRING,
  destination_port       STRING,
  cost_per_ton_usd       DOUBLE,
  net_profit_usd_per_ton DOUBLE,
  containers_allocated   INT,
  export_first           BOOLEAN,
  decision_summary       STRING,
  llm_explanation        STRING
)
USING DELTA
COMMENT 'Gold: final ranked export decisions with container allocation'
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Reference tables (not in ARCHITECTURE.md)
# MAGIC Static CSVs used by training and the logistics optimizer.
# MAGIC Created empty here; notebook 01 loads the data.

# COMMAND ----------

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {full_name('ref_ports')} (
  port_id INT, port_name STRING, port_type STRING, state STRING,
  nearest_city STRING, unlocode STRING, latitude DOUBLE, longitude DOUBLE
) USING DELTA
""")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {full_name('ref_destination_ports')} (
  destination_port_id INT, country STRING, port_name STRING, unlocode STRING,
  latitude DOUBLE, longitude DOUBLE, region STRING, port_type STRING
) USING DELTA
""")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {full_name('ref_freight_rates')} (
  freight_id INT, source_port_id INT, destination_port_id INT,
  container_type STRING, freight_cost_usd DOUBLE, transit_days DOUBLE,
  service_type STRING, currency STRING
) USING DELTA
""")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {full_name('ref_port_charges')} (
  port_id INT, port_name STRING, loading_charge_usd DOUBLE,
  terminal_handling_charge_usd DOUBLE, documentation_charge_usd DOUBLE,
  customs_processing_charge_usd DOUBLE, inspection_charge_usd DOUBLE,
  total_port_charge_usd DOUBLE
) USING DELTA
""")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {full_name('ref_container_cost')} (
  container_type STRING, max_payload_tons DOUBLE, container_rental_usd DOUBLE,
  container_handling_usd DOUBLE, container_cleaning_usd DOUBLE,
  container_insurance_usd DOUBLE, total_container_cost_usd DOUBLE
) USING DELTA
""")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {full_name('ref_commodity_origins')} (
  commodity STRING, origin_state STRING, origin_city STRING,
  latitude DOUBLE, longitude DOUBLE, production_share DOUBLE, notes STRING
) USING DELTA
""")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {full_name('ref_inland_rates')} (
  mode STRING, rate_usd_per_ton_km DOUBLE, min_charge_usd DOUBLE,
  avg_speed_kmph DOUBLE, notes STRING
) USING DELTA
""")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {full_name('ref_demand_training')} (
  commodity STRING, country STRING, date STRING, source STRING,
  title_english STRING, sentiment STRING, sentiment_score DOUBLE,
  shortage_flag INT, production_drop INT, production_rise INT,
  price_increase INT, price_decrease INT,
  export_opportunity_score DOUBLE, confidence DOUBLE
) USING DELTA
""")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {full_name('ref_price_training')} (
  commodity STRING, year INT, month INT, price DOUBLE,
  price_change DOUBLE, price_pct_change DOUBLE, MA7 DOUBLE, MA30 DOUBLE,
  total_news DOUBLE, average_sentiment DOUBLE, positive_news DOUBLE,
  negative_news DOUBLE, neutral_news DOUBLE, news_growth DOUBLE, next_price DOUBLE
) USING DELTA
""")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {full_name('ref_monthly_price')} (
  commodity STRING, year INT, month INT, price DOUBLE,
  price_change DOUBLE, price_pct_change DOUBLE, MA7 DOUBLE, MA30 DOUBLE
) USING DELTA
""")

print("All Delta tables created.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify
# MAGIC List every table we just created.

# COMMAND ----------

display(spark.sql(f"SHOW TABLES IN {catalog()}.{schema()}"))
