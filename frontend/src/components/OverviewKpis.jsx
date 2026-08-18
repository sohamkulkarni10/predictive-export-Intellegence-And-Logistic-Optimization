/**
 * Overview KPI strip — premium widgets with sparklines / badges.
 * Same props and data sources as before.
 */
import { fmtNum, fmtUsd } from "../utils";
import { sparkFromSeed } from "../vizData";
import { IconBox, IconGlobe, IconRoute, IconShip, IconSpark, IconTrendUp } from "./Icons";
import { MiniSparkline } from "./VizPrimitives";

export default function OverviewKpis({ result, containers }) {
  if (!result) {
    return (
      <div className="kpi-strip">
        {[
          "Top Export Opportunity",
          "Highest Demand Score",
          "Best Profit / Ton",
          "Recommended Route",
          "Containers Available",
          "Forecast Horizon",
        ].map((label, i) => (
          <article key={label} className="metric-card metric-card--idle metric-card--premium">
            <p className="metric-label">{label}</p>
            <p className="metric-value">—</p>
            <p className="metric-sub">Run analysis to populate</p>
            <MiniSparkline data={sparkFromSeed(i + 1)} stroke="#94a3b8" fill="rgba(148,163,184,0.12)" />
          </article>
        ))}
      </div>
    );
  }

  const first = result.final_decisions?.export_first || {};
  const demand = result.stage1_demand?.top_opportunities?.[0];
  const lanes = result.stage3_logistics || [];
  const bestLane = [...lanes]
    .filter((l) => l.ok !== false)
    .sort((a, b) => Number(b.net_profit_usd_per_ton || 0) - Number(a.net_profit_usd_per_ton || 0))[0];

  const cards = [
    {
      label: "Top Export Opportunity",
      value:
        first.commodity && first.country
          ? `${first.commodity} → ${first.country}`
          : "—",
      sub: first.containers != null ? `${first.containers} containers first` : "Priority shipment",
      tone: "blue",
      Icon: IconShip,
      badge: "Lead",
      trend: "+12%",
      spark: sparkFromSeed(2, 8, 48, 20),
      stroke: "#2563eb",
    },
    {
      label: "Highest Demand Score",
      value: demand ? fmtNum(demand.demand_score, 2) : "—",
      sub: demand ? `${demand.commodity} in ${demand.country}` : "No demand row",
      tone: "cyan",
      Icon: IconGlobe,
      badge: "Demand",
      trend: demand ? `${Math.round(Number(demand.demand_score) * 100)}%` : "—",
      spark: sparkFromSeed(5, 8, 55, 22),
      stroke: "#06b6d4",
    },
    {
      label: "Best Profit / Ton",
      value: bestLane ? fmtUsd(bestLane.net_profit_usd_per_ton, 1) : "—",
      sub: bestLane ? `${bestLane.commodity} → ${bestLane.country}` : "No lane",
      tone: "green",
      Icon: IconTrendUp,
      badge: Number(bestLane?.net_profit_usd_per_ton) >= 0 ? "Profit" : "Loss",
      trend: bestLane ? fmtUsd(bestLane.net_profit_usd_per_ton, 0) : "—",
      spark: sparkFromSeed(8, 8, 42, 28),
      stroke: "#10b981",
    },
    {
      label: "Recommended Route",
      value:
        bestLane?.india_port && bestLane?.destination_port
          ? `${bestLane.india_port}`
          : "—",
      sub: bestLane?.destination_port || "Awaiting route",
      tone: "orange",
      Icon: IconRoute,
      badge: "Route",
      trend: bestLane?.total_transit_days != null ? `${bestLane.total_transit_days}d` : "—",
      spark: sparkFromSeed(11, 8, 36, 16),
      stroke: "#f97316",
    },
    {
      label: "Containers Available",
      value: String(result.inputs?.available_containers ?? containers ?? "—"),
      sub: result.inputs?.container_type || "Container budget",
      tone: "navy",
      Icon: IconBox,
      badge: "TEU",
      trend: "Budget",
      spark: sparkFromSeed(14, 8, 50, 12),
      stroke: "#0b3c5d",
    },
    {
      label: "Forecast Horizon",
      value: result.horizon_month || "—",
      sub: "Next-month planning window",
      tone: "gold",
      Icon: IconSpark,
      badge: "Horizon",
      trend: "Next",
      spark: sparkFromSeed(17, 8, 45, 14),
      stroke: "#f59e0b",
    },
  ];

  return (
    <div className="kpi-strip">
      {cards.map((c) => (
        <article key={c.label} className={`metric-card metric-card--premium metric-card--${c.tone}`}>
          <div className="metric-top">
            <span className="metric-icon">
              <c.Icon />
            </span>
            <span className="metric-label">{c.label}</span>
            <span className="metric-badge">{c.badge}</span>
          </div>
          <p className="metric-value">{c.value}</p>
          <div className="metric-foot">
            <p className="metric-sub">{c.sub}</p>
            <span className="metric-trend">{c.trend}</span>
          </div>
          <MiniSparkline data={c.spark} stroke={c.stroke} fill={`${c.stroke}22`} />
        </article>
      ))}
    </div>
  );
}
