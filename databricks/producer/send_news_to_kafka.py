"""
Local test producer: push sample daily news to Confluent Cloud topics.

Reads events from sample_news.json and produces to:
  KAFKA_TOPIC_DEMAND  (default export-ai-demand-news)
  KAFKA_TOPIC_PRICE   (default export-ai-price-news)

Required env vars (same names as ARCHITECTURE.md):
  KAFKA_BOOTSTRAP
  KAFKA_API_KEY
  KAFKA_API_SECRET

Optional:
  KAFKA_TOPIC_DEMAND
  KAFKA_TOPIC_PRICE

Usage:
  python send_news_to_kafka.py --dry-run
  python send_news_to_kafka.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


SAMPLE_PATH = Path(__file__).resolve().parent / "sample_news.json"


def load_events() -> dict:
    with SAMPLE_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def env_config() -> dict:
    return {
        "bootstrap": os.environ.get("KAFKA_BOOTSTRAP", ""),
        "api_key": os.environ.get("KAFKA_API_KEY", ""),
        "api_secret": os.environ.get("KAFKA_API_SECRET", ""),
        "topic_demand": os.environ.get("KAFKA_TOPIC_DEMAND", "export-ai-demand-news"),
        "topic_price": os.environ.get("KAFKA_TOPIC_PRICE", "export-ai-price-news"),
    }


def make_producer(cfg: dict):
    # Lazy import so --dry-run works even if confluent-kafka is not installed.
    try:
        from confluent_kafka import Producer
    except ImportError as exc:
        raise SystemExit(
            "confluent-kafka is not installed. Run:\n"
            "  pip install confluent-kafka\n"
            "Or use --dry-run to preview messages without sending."
        ) from exc

    return Producer(
        {
            "bootstrap.servers": cfg["bootstrap"],
            "security.protocol": "SASL_SSL",
            "sasl.mechanisms": "PLAIN",
            "sasl.username": cfg["api_key"],
            "sasl.password": cfg["api_secret"],
        }
    )


def delivery_report(err, msg):
    if err is not None:
        print(f"FAIL topic={msg.topic()} key={msg.key()}: {err}", file=sys.stderr)
    else:
        print(f"OK   topic={msg.topic()} partition={msg.partition()} offset={msg.offset()} key={msg.key()}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Send sample Export AI news to Confluent Cloud")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print messages that would be sent; do not connect to Kafka",
    )
    args = parser.parse_args()

    cfg = env_config()
    data = load_events()
    demand_events = data.get("demand", [])
    price_events = data.get("price", [])

    print(f"Demand events: {len(demand_events)} -> topic {cfg['topic_demand']}")
    print(f"Price events:  {len(price_events)} -> topic {cfg['topic_price']}")

    batches = [
        (cfg["topic_demand"], demand_events),
        (cfg["topic_price"], price_events),
    ]

    if args.dry_run:
        for topic, events in batches:
            for ev in events:
                payload = json.dumps(ev, ensure_ascii=False)
                print(f"[dry-run] {topic} key={ev.get('event_id')} bytes={len(payload)}")
                print(f"          title={ev.get('title', '')[:80]}")
        print("Dry run complete — nothing sent.")
        return 0

    missing = [k for k in ("bootstrap", "api_key", "api_secret") if not cfg[k]]
    if missing:
        print(
            "Missing env vars: "
            + ", ".join(
                {
                    "bootstrap": "KAFKA_BOOTSTRAP",
                    "api_key": "KAFKA_API_KEY",
                    "api_secret": "KAFKA_API_SECRET",
                }[m]
                for m in missing
            ),
            file=sys.stderr,
        )
        return 1

    producer = make_producer(cfg)
    for topic, events in batches:
        for ev in events:
            key = str(ev.get("event_id", "")).encode("utf-8")
            value = json.dumps(ev, ensure_ascii=False).encode("utf-8")
            producer.produce(topic=topic, key=key, value=value, callback=delivery_report)
            producer.poll(0)

    producer.flush(30)
    print("All messages flushed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
