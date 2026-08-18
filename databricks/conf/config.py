"""
Shared config for Export AI Databricks notebooks and the local Kafka producer.

Order of lookup for every secret:
  1. Databricks secret scope  (dbutils.secrets.get)
  2. Environment variable     (os.environ)

Create the secret scope once (Databricks CLI):

  databricks secrets create-scope --scope export-ai

  databricks secrets put --scope export-ai --key kafka-bootstrap
  databricks secrets put --scope export-ai --key kafka-api-key
  databricks secrets put --scope export-ai --key kafka-api-secret
  databricks secrets put --scope export-ai --key groq-api-key
"""

from __future__ import annotations

import os
from typing import Optional


SECRET_SCOPE = os.environ.get("DATABRICKS_SECRET_SCOPE", "export-ai")


def _dbutils():
    """Return dbutils when running inside Databricks; otherwise None."""
    try:
        # Available when this module is %run from a notebook
        return dbutils  # type: ignore[name-defined]
    except NameError:
        pass
    try:
        from pyspark.dbutils import DBUtils
        from pyspark.sql import SparkSession

        spark = SparkSession.getActiveSession()
        if spark is None:
            return None
        return DBUtils(spark)
    except Exception:
        return None


def get_secret(key: str, env_name: Optional[str] = None, default: Optional[str] = None) -> Optional[str]:
    """
    Read one secret.

    key       = name inside the Databricks secret scope (e.g. kafka-api-key)
    env_name  = optional env var override (defaults to KEY with dashes -> underscores, uppercased)
    """
    env_key = env_name or key.replace("-", "_").upper()

    utils = _dbutils()
    if utils is not None:
        try:
            return utils.secrets.get(scope=SECRET_SCOPE, key=key)
        except Exception:
            pass

    value = os.environ.get(env_key)
    if value is not None and value != "":
        return value
    return default


def catalog() -> str:
    return get_secret("databricks-catalog", "DATABRICKS_CATALOG", "export_ai") or "export_ai"


def schema() -> str:
    return get_secret("databricks-schema", "DATABRICKS_SCHEMA", "main") or "main"


def full_name(table: str) -> str:
    """Return catalog.schema.table for Unity Catalog."""
    return f"{catalog()}.{schema()}.{table}"


def kafka_bootstrap() -> str:
    return get_secret("kafka-bootstrap", "KAFKA_BOOTSTRAP", "") or ""


def kafka_api_key() -> str:
    return get_secret("kafka-api-key", "KAFKA_API_KEY", "") or ""


def kafka_api_secret() -> str:
    return get_secret("kafka-api-secret", "KAFKA_API_SECRET", "") or ""


def kafka_topic_demand() -> str:
    return get_secret("kafka-topic-demand", "KAFKA_TOPIC_DEMAND", "export-ai-demand-news") or "export-ai-demand-news"


def kafka_topic_price() -> str:
    return get_secret("kafka-topic-price", "KAFKA_TOPIC_PRICE", "export-ai-price-news") or "export-ai-price-news"


def kafka_jaas_config() -> str:
    """Confluent Cloud SASL/PLAIN login string."""
    key = kafka_api_key()
    secret = kafka_api_secret()
    return (
        "org.apache.kafka.common.security.plain.PlainLoginModule required "
        f'username="{key}" password="{secret}";'
    )


def checkpoint_base() -> str:
    """Volume / DBFS path for Structured Streaming checkpoints."""
    return (
        get_secret("checkpoint-base", "CHECKPOINT_BASE", "/Volumes/export_ai/main/checkpoints")
        or "/Volumes/export_ai/main/checkpoints"
    )


def model_volume() -> str:
    """Where joblib bundles are also written for pandas UDF loading."""
    return (
        get_secret("model-volume", "MODEL_VOLUME", "/Volumes/export_ai/main/models")
        or "/Volumes/export_ai/main/models"
    )


def groq_api_key() -> Optional[str]:
    return get_secret("groq-api-key", "GROQ_API_KEY", None)


def demand_model_name() -> str:
    return f"{catalog()}.{schema()}.demand_model"


def price_model_name() -> str:
    return f"{catalog()}.{schema()}.price_model"
