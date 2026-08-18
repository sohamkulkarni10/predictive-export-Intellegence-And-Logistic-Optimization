# Databricks notebook source
# MAGIC %md
# MAGIC # 03 — Bronze → silver_news_scored
# MAGIC
# MAGIC Takes new bronze rows, cleans the title, scores them with the demand model,
# MAGIC and writes one silver row per article.
# MAGIC
# MAGIC **Why a pandas UDF?**
# MAGIC A row-wise Python UDF calls Python once per row (very slow).
# MAGIC A pandas UDF gets a whole batch of titles as a pandas Series, runs the
# MAGIC sklearn models in vectorized form once per batch, and returns a DataFrame.
# MAGIC Same logic, far less overhead.

# COMMAND ----------

import sys
from pathlib import Path

sys.path.insert(0, str(Path(".").resolve()))
from conf.config import full_name, model_volume

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load the demand model bundle
# MAGIC Prefer the joblib artifact on the Volume (written by notebook 04).
# MAGIC Falls back to MLflow registry download if the file is missing.

# COMMAND ----------

import joblib
import numpy as np
import pandas as pd
from pyspark.sql import functions as F
from pyspark.sql.functions import pandas_udf
from pyspark.sql.types import (
    DoubleType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

BUNDLE_PATH = f"{model_volume()}/demand_model_bundle.joblib"

# Broadcast so every executor gets one copy without re-reading per row.
bundle = joblib.load(BUNDLE_PATH)
broadcast_bundle = spark.sparkContext.broadcast(bundle)
print("Loaded demand bundle:", bundle.get("version"), "metrics keys:", list(bundle.get("metrics", {}).keys()))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Title cleaner
# MAGIC Strip whitespace / collapse spaces. Keep it boring on purpose — the TF-IDF
# MAGIC vectorizer already lowercases and removes English stop words.

# COMMAND ----------

def clean_title(text: str) -> str:
    if text is None:
        return ""
    return " ".join(str(text).split()).strip()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Sentiment helper (keyword, same idea as local price_service)
# MAGIC Lightweight — not an extra ML model. Gives silver its sentiment columns.

# COMMAND ----------

POS_WORDS = [
    "surge", "rise", "rising", "increase", "up", "bullish", "rally",
    "strong demand", "shortage", "tight", "higher", "firm",
]
NEG_WORDS = [
    "fall", "falling", "drop", "decline", "down", "bearish", "surplus",
    "glut", "weak demand", "lower", "soft", "eased",
]


def simple_sentiment(title: str) -> tuple:
    lower = (title or "").lower()
    pos = sum(1 for w in POS_WORDS if w in lower)
    neg = sum(1 for w in NEG_WORDS if w in lower)
    if pos == 0 and neg == 0:
        return "neutral", 0.0
    score = (pos - neg) / max(pos + neg, 1)
    if score > 0.15:
        label = "positive"
    elif score < -0.15:
        label = "negative"
    else:
        label = "neutral"
    return label, float(score)

# COMMAND ----------

# MAGIC %md
# MAGIC ## pandas UDF — score a batch of titles
# MAGIC Returns commodity, country, demand_score, sentiment, sentiment_score.

# COMMAND ----------

score_schema = StructType([
    StructField("commodity", StringType()),
    StructField("country", StringType()),
    StructField("demand_score", DoubleType()),
    StructField("sentiment", StringType()),
    StructField("sentiment_score", DoubleType()),
])


@pandas_udf(score_schema)
def score_titles(titles: pd.Series) -> pd.DataFrame:
    b = broadcast_bundle.value
    commodity_model = b["commodity_model"]
    country_model = b["country_model"]
    score_model = b["score_model"]
    commodity_le = b["commodity_encoder"]
    country_le = b["country_encoder"]

    cleaned = titles.fillna("").map(clean_title)
    X = cleaned.to_numpy(dtype=object)

    # Vectorized predict over the whole batch (this is the pandas_udf win).
    c_ids = commodity_model.predict(X)
    k_ids = country_model.predict(X)
    c_proba = commodity_model.predict_proba(X)
    k_proba = country_model.predict_proba(X)
    raw_scores = np.clip(score_model.predict(X), 0, 1)

    commodities = commodity_le.inverse_transform(c_ids)
    countries = country_le.inverse_transform(k_ids)
    c_conf = c_proba.max(axis=1)
    k_conf = k_proba.max(axis=1)
    blended = np.clip(0.7 * raw_scores + 0.15 * c_conf + 0.15 * k_conf, 0, 1)

    sentiments = []
    sent_scores = []
    for t in cleaned:
        lab, sc = simple_sentiment(t)
        sentiments.append(lab)
        sent_scores.append(sc)

    return pd.DataFrame({
        "commodity": commodities.astype(str),
        "country": countries.astype(str),
        "demand_score": blended.astype(float),
        "sentiment": sentiments,
        "sentiment_score": sent_scores,
    })

# COMMAND ----------

# MAGIC %md
# MAGIC ## Select bronze rows not yet in silver
# MAGIC Anti-join on `event_id` so re-runs are idempotent.

# COMMAND ----------

bronze = spark.table(full_name("bronze_news"))
silver_existing = spark.table(full_name("silver_news_scored")).select("event_id")

new_rows = (
    bronze.alias("b")
    .join(silver_existing.alias("s"), on="event_id", how="left_anti")
    .filter(F.col("title").isNotNull())
)

print("New bronze rows to score:", new_rows.count())

# COMMAND ----------

# MAGIC %md
# MAGIC ## Score and write silver

# COMMAND ----------

scored = (
    new_rows
    .withColumn("title_english", F.trim(F.col("title")))
    .withColumn("pred", score_titles(F.col("title_english")))
    .select(
        F.col("event_id"),
        F.col("news_type"),
        F.col("published_at"),
        F.col("title_english"),
        F.col("pred.commodity").alias("commodity"),
        F.col("pred.country").alias("country"),
        F.col("pred.demand_score").alias("demand_score"),
        F.col("pred.sentiment").alias("sentiment"),
        F.col("pred.sentiment_score").alias("sentiment_score"),
        F.current_timestamp().alias("scored_at"),
    )
)

(
    scored.write.format("delta")
    .mode("append")
    .saveAsTable(full_name("silver_news_scored"))
)

print("Appended to", full_name("silver_news_scored"))
display(scored.limit(20))
