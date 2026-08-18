# Databricks notebook source
# MAGIC %md
# MAGIC # 02 — Kafka → bronze_news (Structured Streaming)
# MAGIC
# MAGIC Reads continuous news from **Confluent Cloud** (both demand + price topics)
# MAGIC and appends rows to `bronze_news`.
# MAGIC
# MAGIC Auth: SASL_SSL + PLAIN (API key + secret).

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load config (secrets → env fallback)

# COMMAND ----------

import sys
from pathlib import Path

sys.path.insert(0, str(Path(".").resolve()))
from conf.config import (
    checkpoint_base,
    full_name,
    kafka_api_key,
    kafka_api_secret,
    kafka_bootstrap,
    kafka_jaas_config,
    kafka_topic_demand,
    kafka_topic_price,
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Explicit JSON schema for Kafka message values
# MAGIC Matches `producer/sample_news.json`. No `inferSchema`.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import StringType, StructField, StructType, TimestampType

news_schema = StructType([
    StructField("event_id", StringType(), False),
    StructField("news_type", StringType(), False),
    StructField("source", StringType(), True),
    StructField("published_at", StringType(), True),  # ISO string; cast below
    StructField("title", StringType(), True),
    StructField("body", StringType(), True),
    StructField("language", StringType(), True),
])

bootstrap = kafka_bootstrap()
topics = f"{kafka_topic_demand()},{kafka_topic_price()}"
jaas = kafka_jaas_config()

assert bootstrap, "KAFKA_BOOTSTRAP / kafka-bootstrap secret is required"
assert kafka_api_key() and kafka_api_secret(), "Kafka API key/secret required"

print(f"Bootstrap: {bootstrap}")
print(f"Topics:    {topics}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Read the Kafka stream
# MAGIC `subscribe` takes both topics in one comma-separated string.
# MAGIC StartingOffsets `earliest` is useful for demos; switch to `latest` in production
# MAGIC if you do not want historical replay on a fresh checkpoint.

# COMMAND ----------

raw = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", bootstrap)
    .option("kafka.security.protocol", "SASL_SSL")
    .option("kafka.sasl.mechanism", "PLAIN")
    .option("kafka.sasl.jaas.config", jaas)
    .option("subscribe", topics)
    .option("startingOffsets", "earliest")
    .option("failOnDataLoss", "false")
    .load()
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Parse JSON value → bronze columns
# MAGIC Kafka gives `value` as binary. We keep the original string in `raw_payload`
# MAGIC and stamp `ingested_at` at write time.

# COMMAND ----------

parsed = (
    raw.select(
        F.col("value").cast("string").alias("raw_payload"),
        F.col("topic"),
        F.col("timestamp").alias("kafka_timestamp"),
    )
    .withColumn("j", F.from_json(F.col("raw_payload"), news_schema))
    .select(
        F.col("j.event_id").alias("event_id"),
        F.col("j.news_type").alias("news_type"),
        F.col("j.source").alias("source"),
        F.to_timestamp(F.col("j.published_at")).alias("published_at"),
        F.col("j.title").alias("title"),
        F.col("j.body").alias("body"),
        F.col("j.language").alias("language"),
        F.current_timestamp().alias("ingested_at"),
        F.col("raw_payload"),
    )
    .filter(F.col("event_id").isNotNull())
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write to bronze_news (checkpointed)
# MAGIC
# MAGIC **Trigger tradeoff**
# MAGIC - `availableNow=True` — process everything currently in Kafka, then **stop**.
# MAGIC   Good for scheduled jobs / demos / cost control (cluster can shut down).
# MAGIC - `processingTime="10 seconds"` (continuous micro-batches) — keeps running
# MAGIC   and picks up news within seconds. Needs a long-lived job cluster; costs more.
# MAGIC
# MAGIC Default below: `availableNow` so a Databricks Job run finishes cleanly.
# MAGIC Uncomment the continuous trigger for a 24/7 streaming job.

# COMMAND ----------

checkpoint = f"{checkpoint_base()}/bronze_news"
target = full_name("bronze_news")

query = (
    parsed.writeStream.format("delta")
    .outputMode("append")
    .option("checkpointLocation", checkpoint)
    .trigger(availableNow=True)          # <-- batch-style catch-up, then stop
    # .trigger(processingTime="10 seconds")  # <-- continuous; comment availableNow above
    .toTable(target)
)

query.awaitTermination()
print(f"Stream finished. Wrote to {target}. Checkpoint: {checkpoint}")
