# Databricks notebook source
# MAGIC %md
# MAGIC # 01 — Upload reference data into Delta
# MAGIC
# MAGIC Loads Logistics CSVs + demand/price training CSVs into the `ref_*` Delta tables.
# MAGIC Run this **once** after notebook 00 (or whenever the CSVs change).
# MAGIC
# MAGIC ## How to point at the files
# MAGIC Upload the repo (or just the CSV folders) to a Unity Catalog Volume, then set
# MAGIC `DATA_ROOT` below. Example Volume path:
# MAGIC `/Volumes/export_ai/main/raw/`
# MAGIC with subfolders `Logistics/`, `commodities/`, `Demand_prediction/`.

# COMMAND ----------

import sys
from pathlib import Path

sys.path.insert(0, str(Path(".").resolve()))
from conf.config import full_name

# COMMAND ----------

# MAGIC %md
# MAGIC ## Set the data root
# MAGIC Change this to wherever you uploaded the CSVs on Databricks.

# COMMAND ----------

from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

# Point this at your Volume (or DBFS) copy of the repo data folders.
DATA_ROOT = "/Volumes/export_ai/main/raw"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Helper: overwrite a ref table from a CSV with an explicit schema
# MAGIC We never use `inferSchema` — column types must stay stable for the optimizer.

# COMMAND ----------

def load_csv_overwrite(relative_path: str, table: str, schema_obj: StructType) -> int:
    path = f"{DATA_ROOT}/{relative_path}"
    df = (
        spark.read.format("csv")
        .option("header", "true")
        .schema(schema_obj)
        .load(path)
    )
    df.write.format("delta").mode("overwrite").saveAsTable(full_name(table))
    n = df.count()
    print(f"{table}: {n} rows from {path}")
    return n

# COMMAND ----------

# MAGIC %md
# MAGIC ## Logistics CSVs → `ref_*` tables

# COMMAND ----------

load_csv_overwrite(
    "Logistics/ports.csv",
    "ref_ports",
    StructType([
        StructField("port_id", IntegerType()),
        StructField("port_name", StringType()),
        StructField("port_type", StringType()),
        StructField("state", StringType()),
        StructField("nearest_city", StringType()),
        StructField("unlocode", StringType()),
        StructField("latitude", DoubleType()),
        StructField("longitude", DoubleType()),
    ]),
)

load_csv_overwrite(
    "Logistics/destination_ports.csv",
    "ref_destination_ports",
    StructType([
        StructField("destination_port_id", IntegerType()),
        StructField("country", StringType()),
        StructField("port_name", StringType()),
        StructField("unlocode", StringType()),
        StructField("latitude", DoubleType()),
        StructField("longitude", DoubleType()),
        StructField("region", StringType()),
        StructField("port_type", StringType()),
    ]),
)

load_csv_overwrite(
    "Logistics/freight_rates.csv",
    "ref_freight_rates",
    StructType([
        StructField("freight_id", IntegerType()),
        StructField("source_port_id", IntegerType()),
        StructField("destination_port_id", IntegerType()),
        StructField("container_type", StringType()),
        StructField("freight_cost_usd", DoubleType()),
        StructField("transit_days", DoubleType()),
        StructField("service_type", StringType()),
        StructField("currency", StringType()),
    ]),
)

load_csv_overwrite(
    "Logistics/port_charges.csv",
    "ref_port_charges",
    StructType([
        StructField("port_id", IntegerType()),
        StructField("port_name", StringType()),
        StructField("loading_charge_usd", DoubleType()),
        StructField("terminal_handling_charge_usd", DoubleType()),
        StructField("documentation_charge_usd", DoubleType()),
        StructField("customs_processing_charge_usd", DoubleType()),
        StructField("inspection_charge_usd", DoubleType()),
        StructField("total_port_charge_usd", DoubleType()),
    ]),
)

load_csv_overwrite(
    "Logistics/container_cost.csv",
    "ref_container_cost",
    StructType([
        StructField("container_type", StringType()),
        StructField("max_payload_tons", DoubleType()),
        StructField("container_rental_usd", DoubleType()),
        StructField("container_handling_usd", DoubleType()),
        StructField("container_cleaning_usd", DoubleType()),
        StructField("container_insurance_usd", DoubleType()),
        StructField("total_container_cost_usd", DoubleType()),
    ]),
)

load_csv_overwrite(
    "Logistics/commodity_origins.csv",
    "ref_commodity_origins",
    StructType([
        StructField("commodity", StringType()),
        StructField("origin_state", StringType()),
        StructField("origin_city", StringType()),
        StructField("latitude", DoubleType()),
        StructField("longitude", DoubleType()),
        StructField("production_share", DoubleType()),
        StructField("notes", StringType()),
    ]),
)

load_csv_overwrite(
    "Logistics/inland_rates.csv",
    "ref_inland_rates",
    StructType([
        StructField("mode", StringType()),
        StructField("rate_usd_per_ton_km", DoubleType()),
        StructField("min_charge_usd", DoubleType()),
        StructField("avg_speed_kmph", DoubleType()),
        StructField("notes", StringType()),
    ]),
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Training CSVs → demand + price reference tables

# COMMAND ----------

load_csv_overwrite(
    "Demand_prediction/final_news_dataset_cleaned_english.csv",
    "ref_demand_training",
    StructType([
        StructField("commodity", StringType()),
        StructField("country", StringType()),
        StructField("date", StringType()),
        StructField("source", StringType()),
        StructField("title_english", StringType()),
        StructField("sentiment", StringType()),
        StructField("sentiment_score", DoubleType()),
        StructField("shortage_flag", IntegerType()),
        StructField("production_drop", IntegerType()),
        StructField("production_rise", IntegerType()),
        StructField("price_increase", IntegerType()),
        StructField("price_decrease", IntegerType()),
        StructField("export_opportunity_score", DoubleType()),
        StructField("confidence", DoubleType()),
    ]),
)

load_csv_overwrite(
    "commodities/training_dataset.csv",
    "ref_price_training",
    StructType([
        StructField("commodity", StringType()),
        StructField("year", IntegerType()),
        StructField("month", IntegerType()),
        StructField("price", DoubleType()),
        StructField("price_change", DoubleType()),
        StructField("price_pct_change", DoubleType()),
        StructField("MA7", DoubleType()),
        StructField("MA30", DoubleType()),
        StructField("total_news", DoubleType()),
        StructField("average_sentiment", DoubleType()),
        StructField("positive_news", DoubleType()),
        StructField("negative_news", DoubleType()),
        StructField("neutral_news", DoubleType()),
        StructField("news_growth", DoubleType()),
        StructField("next_price", DoubleType()),
    ]),
)

load_csv_overwrite(
    "commodities/monthly_price.csv",
    "ref_monthly_price",
    StructType([
        StructField("commodity", StringType()),
        StructField("year", IntegerType()),
        StructField("month", IntegerType()),
        StructField("price", DoubleType()),
        StructField("price_change", DoubleType()),
        StructField("price_pct_change", DoubleType()),
        StructField("MA7", DoubleType()),
        StructField("MA30", DoubleType()),
    ]),
)

print("Reference data upload complete.")
