/**
 * Colourful intelligence showcase posters — real pipeline data only.
 */
import { fmtInr, fmtNum, fmtPct, fmtUsd } from "../utils";

function demandStatus(dir) {
  const d = String(dir || "").toLowerCase();
  if (d.includes("increase") || d.includes("rising") || d.includes("strong")) {
    return { label: "INCREASING", tone: "up" };
  }
  if (d.includes("decrease") || d.includes("fall")) {
    return { label: "DECREASING", tone: "down" };
  }
  return { label: "STABLE", tone: "flat" };
}

export default function ShowcaseRail({ result }) {
  const demand = result?.stage1_demand?.top_opportunities?.[0];
  const price = (result?.stage2_prices?.predictions || []).find((p) => !p.error);
  const lane = (result?.stage3_logistics || []).find((l) => l.ok !== false);

  const panels = [
    {
      key: "demand",
      tone: "lime",
      label: "DEMAND INTELLIGENCE",
      title: demand ? `${demand.country}` : "Run analysis",
      value: demand ? fmtNum(demand.demand_score, 2) : "—",
      valueLabel: "Demand score",
      lines: demand
        ? [
            demand.commodity,
            demandStatus(demand.predicted_direction).label,
            demand.news_snippet || "Top ranked opportunity",
          ]
        : ["Awaiting news + pipeline", "No mock values shown", "Paste headlines to begin"],
    },
    {
      key: "price",
      tone: "blue",
      label: "PRICE INTELLIGENCE",
      title: price?.commodity || "Run analysis",
      value: price ? fmtInr(price.predicted_next_month_price_inr) : "—",
      valueLabel: "Predicted next month",
      lines: price
        ? [
            `Current ${fmtInr(price.current_price_inr)}`,
            fmtPct(price.predicted_change_pct),
            result?.horizon_month || "Next month",
          ]
        : ["Mandi → forecast", "INR / quintal", "Live after pipeline"],
    },
    {
      key: "route",
      tone: "orange",
      label: "ROUTE INTELLIGENCE",
      title: lane ? `${lane.country}` : "Run analysis",
      value: lane ? fmtUsd(lane.net_profit_usd_per_ton, 1) : "—",
      valueLabel: "Net profit / ton",
      lines: lane
        ? [
            `${lane.origin || "Origin"} → ${lane.india_port || "Port"}`,
            `${lane.destination_port || "Dest"} · ${fmtNum(lane.total_transit_days, 0)}d`,
            lane.commodity,
          ]
        : ["India → world ports", "Transit + profit", "Live after logistics"],
    },
  ];

  return (
    <section className="ed-showcase" id="intelligence">
      <div className="ed-showcase-rail">
        {panels.map((p) => (
          <article key={p.key} className={`ed-poster ed-poster--${p.tone}`}>
            <p className="ed-poster-label">{p.label}</p>
            <h3>{p.title}</h3>
            <p className="ed-poster-meta">{p.valueLabel}</p>
            <p className="ed-poster-value">{p.value}</p>
            <ul>
              {p.lines.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </article>
        ))}
      </div>
    </section>
  );
}
