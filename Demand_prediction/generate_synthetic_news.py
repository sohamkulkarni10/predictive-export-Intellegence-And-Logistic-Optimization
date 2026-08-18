"""
1) Remove duplicate news rows (same title + same country)
2) Generate realistic synthetic agricultural news
3) Apply the same Agricultural Export Intelligence Analyst field schema
   used in the notebooks (sentiment, flags, export opportunity, confidence)
4) Merge synthetic + deduped original into one dataset
"""

from __future__ import annotations

import random
import re
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\Lenovo\Desktop\Export_AI\Demand_prediction")
INPUT_CSV = ROOT / "final_news_dataset_without_india.csv"
BACKUP_CSV = ROOT / "final_news_dataset_without_india_backup.csv"
DEDUP_CSV = ROOT / "final_news_dataset_without_india_deduped.csv"
SYNTH_CSV = ROOT / "synthetic_news_dataset.csv"
MERGED_CSV = ROOT / "final_news_dataset_with_synthetic.csv"
REPORT = ROOT / "synthetic_merge_report.txt"

COLUMNS = [
    "commodity",
    "country",
    "date",
    "source",
    "title_english",
    "sentiment",
    "sentiment_score",
    "shortage_flag",
    "production_drop",
    "production_rise",
    "price_increase",
    "price_decrease",
    "export_opportunity_score",
    "confidence",
]

RNG = random.Random(42)

SOURCES_BY_COUNTRY = {
    "Saudi Arabia": ["albayan.ae", "arabnews.com", "saudigazette.com.sa", "northafricapost.com", "finance.ifeng.com"],
    "Bangladesh": ["thedailystar.net", "bd-pratidin.com", "dailyinqilab.com", "jugantor.com", "bssnews.net"],
    "Germany": ["merkur.de", "farmer.pl", "handelsblatt.com", "dw.com", "reuters.com"],
    "Vietnam": ["baomoi.com", "vietnamnews.vn", "tuoitre.vn", "vnexpress.net", "saigontimes.vn"],
    "Netherlands": ["dutchnews.nl", "nos.nl", "foodnavigator.com", "agroberichtenbuitenland.nl", "reuters.com"],
    "Singapore": ["asiaone.com", "straitstimes.com", "channelnewsasia.com", "businesstimes.com.sg", "todayonline.com"],
    "Sri Lanka": ["ft.lk", "dailynews.lk", "island.lk", "economynext.com", "newsfirst.lk"],
    "Japan": ["japantimes.co.jp", "nikkei.com", "asahi.com", "mainichi.jp", "hea.china.com"],
    "Nepal": ["ekantipur.com", "kathmandupost.com", "myrepublica.nagariknetwork.com", "thehimalayantimes.com"],
    "China": ["finance.eastmoney.com", "finance.sina.com.cn", "163.com", "yicai.com", "baijiahao.baidu.com"],
    "Indonesia": ["jakartapost.com", "kompas.com", "tempo.co", "antaranews.com", "bisnis.com"],
    "Malaysia": ["thestar.com.my", "nst.com.my", "malaymail.com", "bernama.com", "kwongwah.com.my"],
}

GLOBAL_SOURCES = [
    "thehindubusinessline.com",
    "economictimes.indiatimes.com",
    "reuters.com",
    "bloomberg.com",
    "hellenicshippingnews.com",
    "finance.yahoo.com",
    "livemint.com",
    "indianexpress.com",
]

# (title template, label defaults calibrated to notebook output patterns)
EVENT_TEMPLATES = [
    (
        "{country} faces {commodity} shortage as stocks fall to multi-year lows",
        dict(sentiment="Negative", sentiment_score=-0.5, shortage_flag=1, production_drop=0, production_rise=0,
             price_increase=1, price_decrease=0, export_opportunity_score=80, confidence=0.8),
    ),
    (
        "Food security alert: {commodity} supplies tighten across {country}",
        dict(sentiment="Negative", sentiment_score=-0.5, shortage_flag=1, production_drop=0, production_rise=0,
             price_increase=0, price_decrease=0, export_opportunity_score=80, confidence=0.9),
    ),
    (
        "{country} warns of possible {commodity} rationing amid supply crunch",
        dict(sentiment="Negative", sentiment_score=-1.0, shortage_flag=1, production_drop=0, production_rise=0,
             price_increase=1, price_decrease=0, export_opportunity_score=80, confidence=0.8),
    ),
    (
        "Import demand for {commodity} surges in {country} after domestic shortfall",
        dict(sentiment="Positive", sentiment_score=0.8, shortage_flag=1, production_drop=1, production_rise=0,
             price_increase=0, price_decrease=0, export_opportunity_score=80, confidence=0.9),
    ),
    (
        "Drought cuts {commodity} harvest in {country}; farmers report steep losses",
        dict(sentiment="Negative", sentiment_score=-0.5, shortage_flag=0, production_drop=1, production_rise=0,
             price_increase=1, price_decrease=0, export_opportunity_score=20, confidence=0.6),
    ),
    (
        "Heatwave damages {commodity} crop yields across key regions of {country}",
        dict(sentiment="Negative", sentiment_score=-0.5, shortage_flag=1, production_drop=1, production_rise=0,
             price_increase=0, price_decrease=0, export_opportunity_score=20, confidence=0.6),
    ),
    (
        "Floods disrupt {commodity} production and logistics in {country}",
        dict(sentiment="Negative", sentiment_score=-0.5, shortage_flag=0, production_drop=1, production_rise=0,
             price_increase=0, price_decrease=0, export_opportunity_score=20, confidence=0.6),
    ),
    (
        "Pest outbreak threatens {commodity} output in {country} this season",
        dict(sentiment="Negative", sentiment_score=-0.5, shortage_flag=0, production_drop=1, production_rise=0,
             price_increase=0, price_decrease=0, export_opportunity_score=20, confidence=0.5),
    ),
    (
        "{country} reports record {commodity} harvest; output rises for second year",
        dict(sentiment="Positive", sentiment_score=0.8, shortage_flag=0, production_drop=0, production_rise=1,
             price_increase=0, price_decrease=0, export_opportunity_score=20, confidence=0.9),
    ),
    (
        "New high-yield {commodity} varieties boost production in {country}",
        dict(sentiment="Positive", sentiment_score=0.8, shortage_flag=0, production_drop=0, production_rise=1,
             price_increase=0, price_decrease=0, export_opportunity_score=0, confidence=0.9),
    ),
    (
        "Favorable monsoon lifts {commodity} acreage and yields in {country}",
        dict(sentiment="Positive", sentiment_score=0.8, shortage_flag=0, production_drop=0, production_rise=1,
             price_increase=0, price_decrease=1, export_opportunity_score=20, confidence=0.8),
    ),
    (
        "{commodity} prices jump in {country} as wholesale markets tighten",
        dict(sentiment="Negative", sentiment_score=-0.5, shortage_flag=0, production_drop=0, production_rise=0,
             price_increase=1, price_decrease=0, export_opportunity_score=50, confidence=0.6),
    ),
    (
        "{country} retailers raise {commodity} prices amid rising import costs",
        dict(sentiment="Negative", sentiment_score=-1.0, shortage_flag=0, production_drop=0, production_rise=0,
             price_increase=1, price_decrease=0, export_opportunity_score=20, confidence=0.5),
    ),
    (
        "{commodity} prices ease in {country} after fresh arrivals hit markets",
        dict(sentiment="Positive", sentiment_score=0.5, shortage_flag=0, production_drop=0, production_rise=0,
             price_increase=0, price_decrease=1, export_opportunity_score=50, confidence=0.5),
    ),
    (
        "Falling {commodity} prices pressure farmers in {country}",
        dict(sentiment="Negative", sentiment_score=-0.5, shortage_flag=0, production_drop=0, production_rise=0,
             price_increase=0, price_decrease=1, export_opportunity_score=0, confidence=0.6),
    ),
    (
        "{country} plans to increase {commodity} imports to stabilize domestic supply",
        dict(sentiment="Positive", sentiment_score=0.8, shortage_flag=0, production_drop=0, production_rise=0,
             price_increase=0, price_decrease=0, export_opportunity_score=80, confidence=0.9),
    ),
    (
        "{country} opens new tender for {commodity} purchases from global suppliers",
        dict(sentiment="Positive", sentiment_score=0.8, shortage_flag=0, production_drop=0, production_rise=0,
             price_increase=0, price_decrease=0, export_opportunity_score=80, confidence=0.9),
    ),
    (
        "Trade deal may ease {commodity} tariffs for shipments into {country}",
        dict(sentiment="Positive", sentiment_score=0.8, shortage_flag=0, production_drop=0, production_rise=0,
             price_increase=0, price_decrease=0, export_opportunity_score=80, confidence=0.8),
    ),
    (
        "{country} cuts import duty on {commodity} to cool retail inflation",
        dict(sentiment="Positive", sentiment_score=0.8, shortage_flag=0, production_drop=0, production_rise=0,
             price_increase=0, price_decrease=0, export_opportunity_score=80, confidence=0.9),
    ),
    (
        "{country} imposes temporary restriction on {commodity} exports",
        dict(sentiment="Negative", sentiment_score=-0.5, shortage_flag=0, production_drop=0, production_rise=0,
             price_increase=1, price_decrease=0, export_opportunity_score=20, confidence=0.6),
    ),
    (
        "Government of {country} announces subsidy support for {commodity} farmers",
        dict(sentiment="Neutral", sentiment_score=0.0, shortage_flag=0, production_drop=0, production_rise=0,
             price_increase=0, price_decrease=0, export_opportunity_score=20, confidence=0.5),
    ),
    (
        "{country} agriculture ministry reviews {commodity} market outlook for next quarter",
        dict(sentiment="Neutral", sentiment_score=0.0, shortage_flag=0, production_drop=0, production_rise=0,
             price_increase=0, price_decrease=0, export_opportunity_score=0, confidence=0.0),
    ),
    (
        "Analysts say {commodity} trade flows to {country} remain stable this month",
        dict(sentiment="Neutral", sentiment_score=0.0, shortage_flag=0, production_drop=0, production_rise=0,
             price_increase=0, price_decrease=0, export_opportunity_score=20, confidence=0.5),
    ),
    (
        "{country} ports report normal {commodity} handling volumes despite weather delays",
        dict(sentiment="Neutral", sentiment_score=0.0, shortage_flag=0, production_drop=0, production_rise=0,
             price_increase=0, price_decrease=0, export_opportunity_score=0, confidence=0.0),
    ),
    (
        "Exporters eye {country} as a growing {commodity} destination in Asia",
        dict(sentiment="Positive", sentiment_score=0.8, shortage_flag=0, production_drop=0, production_rise=0,
             price_increase=0, price_decrease=0, export_opportunity_score=80, confidence=0.9),
    ),
    (
        "Logistics costs for {commodity} shipments to {country} rise on higher freight rates",
        dict(sentiment="Negative", sentiment_score=-0.5, shortage_flag=0, production_drop=0, production_rise=0,
             price_increase=0, price_decrease=0, export_opportunity_score=20, confidence=0.6),
    ),
    (
        "{country} stockpiles strategic {commodity} reserves ahead of festival demand",
        dict(sentiment="Positive", sentiment_score=0.5, shortage_flag=0, production_drop=0, production_rise=0,
             price_increase=0, price_decrease=0, export_opportunity_score=50, confidence=0.8),
    ),
    (
        "Quality concerns slow {commodity} imports into {country} markets",
        dict(sentiment="Negative", sentiment_score=-0.5, shortage_flag=0, production_drop=0, production_rise=0,
             price_increase=0, price_decrease=0, export_opportunity_score=20, confidence=0.6),
    ),
    (
        "Strong retail demand for {commodity} products continues in {country}",
        dict(sentiment="Positive", sentiment_score=0.8, shortage_flag=0, production_drop=0, production_rise=0,
             price_increase=0, price_decrease=0, export_opportunity_score=80, confidence=0.9),
    ),
    (
        "{country} processors increase {commodity} crushing and refining capacity",
        dict(sentiment="Positive", sentiment_score=0.8, shortage_flag=0, production_drop=0, production_rise=0,
             price_increase=0, price_decrease=0, export_opportunity_score=60, confidence=0.8),
    ),
    (
        "Shipping delays leave {country} {commodity} importers scrambling for cargo",
        dict(sentiment="Negative", sentiment_score=-0.5, shortage_flag=1, production_drop=0, production_rise=0,
             price_increase=0, price_decrease=0, export_opportunity_score=80, confidence=0.8),
    ),
    (
        "Currency weakness makes {commodity} imports costlier for {country} buyers",
        dict(sentiment="Negative", sentiment_score=-0.5, shortage_flag=0, production_drop=0, production_rise=0,
             price_increase=1, price_decrease=0, export_opportunity_score=20, confidence=0.6),
    ),
    (
        "Bilateral talks focus on expanding {commodity} trade with {country}",
        dict(sentiment="Positive", sentiment_score=0.8, shortage_flag=0, production_drop=0, production_rise=0,
             price_increase=0, price_decrease=0, export_opportunity_score=80, confidence=0.9),
    ),
    (
        "Early forecasts point to weaker {commodity} sowing in {country}",
        dict(sentiment="Negative", sentiment_score=-0.5, shortage_flag=0, production_drop=1, production_rise=0,
             price_increase=0, price_decrease=0, export_opportunity_score=20, confidence=0.6),
    ),
    (
        "Rainfall deficit raises concerns for {commodity} planting in {country}",
        dict(sentiment="Negative", sentiment_score=-0.5, shortage_flag=0, production_drop=1, production_rise=0,
             price_increase=0, price_decrease=0, export_opportunity_score=20, confidence=0.6),
    ),
    (
        "Private traders boost {commodity} bookings destined for {country}",
        dict(sentiment="Positive", sentiment_score=0.8, shortage_flag=0, production_drop=0, production_rise=0,
             price_increase=0, price_decrease=0, export_opportunity_score=80, confidence=0.9),
    ),
    (
        "Policy uncertainty hangs over {commodity} contracts linked to {country}",
        dict(sentiment="Neutral", sentiment_score=0.0, shortage_flag=0, production_drop=0, production_rise=0,
             price_increase=0, price_decrease=0, export_opportunity_score=20, confidence=0.3),
    ),
    (
        "{country} consumers shift to cheaper substitutes as {commodity} stays expensive",
        dict(sentiment="Negative", sentiment_score=-0.5, shortage_flag=0, production_drop=0, production_rise=0,
             price_increase=1, price_decrease=0, export_opportunity_score=20, confidence=0.5),
    ),
]

TITLE_VARIATIONS = [
    "{base}",
    "{base} | Market Watch",
    "{base} - Agriculture Report",
    "{base}: officials urge caution",
    "{base}, traders say",
    "Latest: {base}",
    "{base} - seasonal update",
]


def normalize_title(text: str) -> str:
    text = str(text).strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s]", "", text)
    return text


def make_date(start: datetime, end: datetime) -> str:
    delta = (end - start).total_seconds()
    ts = start + timedelta(seconds=RNG.randint(0, int(delta)))
    minute = (ts.minute // 15) * 15
    ts = ts.replace(minute=minute, second=0, microsecond=0)
    return ts.strftime("%Y%m%dT%H%M%SZ")


def pick_source(country: str) -> str:
    local = SOURCES_BY_COUNTRY.get(country, [])
    return RNG.choice(local + GLOBAL_SOURCES)


def apply_sentiment_labels(base_labels: dict) -> dict:
    """
    Same output fields as the notebook Groq pipeline for the slim CSV.
    Light jitter keeps scores realistic while staying on observed value grids.
    """
    labels = dict(base_labels)
    if labels["confidence"] > 0 and RNG.random() < 0.12:
        labels["confidence"] = round(max(0.0, min(1.0, labels["confidence"] + RNG.choice([-0.1, 0.1]))), 1)
    if labels["export_opportunity_score"] > 0 and RNG.random() < 0.10:
        labels["export_opportunity_score"] = int(
            max(0, min(100, labels["export_opportunity_score"] + RNG.choice([-10, 10])))
        )
    # snap sentiment_score to common notebook values
    score_grid = [-1.0, -0.8, -0.5, 0.0, 0.5, 0.8, 1.0]
    labels["sentiment_score"] = min(score_grid, key=lambda x: abs(x - float(labels["sentiment_score"])))
    return labels


def generate_synthetic_rows(
    commodities: list[str],
    countries: list[str],
    commodity_weights: list[float],
    country_weights: list[float],
    n: int,
    existing_keys: set[tuple[str, str]],
) -> pd.DataFrame:
    start = datetime(2026, 4, 1)
    end = datetime(2026, 6, 30, 23, 45)
    rows = []
    seen = set(existing_keys)
    attempts = 0

    while len(rows) < n and attempts < n * 25:
        attempts += 1
        commodity = RNG.choices(commodities, weights=commodity_weights, k=1)[0]
        country = RNG.choices(countries, weights=country_weights, k=1)[0]
        template, base_labels = RNG.choice(EVENT_TEMPLATES)
        base_title = template.format(commodity=commodity, country=country)
        title = RNG.choice(TITLE_VARIATIONS).format(base=base_title)
        key = (normalize_title(title), country.lower())
        if key in seen:
            title = f"{base_title} ({RNG.choice(['April', 'May', 'June'])} {RNG.randint(2025, 2026)} briefing)"
            key = (normalize_title(title), country.lower())
            if key in seen:
                continue
        seen.add(key)
        labels = apply_sentiment_labels(base_labels)
        rows.append(
            {
                "commodity": commodity,
                "country": country,
                "date": make_date(start, end),
                "source": pick_source(country),
                "title_english": title,
                **labels,
            }
        )
    return pd.DataFrame(rows, columns=COLUMNS)


def main() -> None:
    df = pd.read_csv(INPUT_CSV)
    original_n = len(df)
    if not BACKUP_CSV.exists():
        df.to_csv(BACKUP_CSV, index=False)

    df["_norm_title"] = df["title_english"].map(normalize_title)
    before = len(df)
    df_dedup = df.drop_duplicates(subset=["_norm_title", "country"], keep="first").copy()
    removed = before - len(df_dedup)
    df_dedup = df_dedup.drop(columns=["_norm_title"])[COLUMNS]
    df_dedup.to_csv(DEDUP_CSV, index=False)

    n_synth = max(800, len(df_dedup))
    commodity_counts = df_dedup["commodity"].value_counts()
    country_counts = df_dedup["country"].value_counts()
    existing_keys = {
        (normalize_title(t), str(c).lower())
        for t, c in zip(df_dedup["title_english"], df_dedup["country"])
    }

    synth = generate_synthetic_rows(
        commodities=commodity_counts.index.tolist(),
        countries=country_counts.index.tolist(),
        commodity_weights=commodity_counts.values.astype(float).tolist(),
        country_weights=country_counts.values.astype(float).tolist(),
        n=n_synth,
        existing_keys=existing_keys,
    )
    synth.to_csv(SYNTH_CSV, index=False)

    merged = pd.concat([df_dedup, synth], ignore_index=True)
    merged["_norm_title"] = merged["title_english"].map(normalize_title)
    merged = merged.drop_duplicates(subset=["_norm_title", "country"], keep="first")
    merged = merged.drop(columns=["_norm_title"])[COLUMNS]
    merged.to_csv(MERGED_CSV, index=False)

    report = [
        "Synthetic news + sentiment merge report",
        "=" * 50,
        f"Original rows: {original_n}",
        f"Original backup: {BACKUP_CSV.name}",
        f"Duplicates removed (same news + same country): {removed}",
        f"Deduped rows: {len(df_dedup)} -> {DEDUP_CSV.name}",
        f"Synthetic rows: {len(synth)} -> {SYNTH_CSV.name}",
        f"Merged rows: {len(merged)} -> {MERGED_CSV.name}",
        "",
        "Synthetic sentiment:",
        synth["sentiment"].value_counts().to_string(),
        "",
        "Merged sentiment:",
        merged["sentiment"].value_counts().to_string(),
        "",
        "Synthetic commodities:",
        synth["commodity"].value_counts().to_string(),
        "",
        "Sample synthetic:",
    ]
    for _, r in synth.head(10).iterrows():
        report.append(
            f"  [{r['commodity']}/{r['country']}] {r['sentiment']} ({r['sentiment_score']}) "
            f"opp={r['export_opportunity_score']} | {r['title_english'][:110]}"
        )

    REPORT.write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
