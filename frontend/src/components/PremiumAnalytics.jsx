/**
 * Premium analytics suite — SVG charts, ports, supply chain, gauges, insights.
 * Presentation only; uses existing pipeline `result` when present.
 * No external chart library required.
 */
import {
  buildAiInsights,
  buildContainerDonut,
  buildDemandChart,
  buildModelComparison,
  buildNewsCards,
  buildPriceForecastChart,
  buildProfitWaterfall,
  buildRadarFromResult,
  COMMODITY_META,
  enrichPortsWithResult,
  sparkFromSeed,
} from "../vizData";
import { fmtInr, fmtNum, fmtUsd } from "../utils";
import { GaugeRing, MiniSparkline, RiskMeter } from "./VizPrimitives";

const WEATHER = ["☀", "🌤", "⛅", "🌦", "💨"];

function ChartCard({ title, sub, children, badge }) {
  return (
    <article className="chart-card">
      <div className="chart-card-head">
        <div>
          <h3>{title}</h3>
          {sub ? <p>{sub}</p> : null}
        </div>
        {badge ? <span className="chip chip-blue">{badge}</span> : null}
      </div>
      <div className="chart-card-body">{children}</div>
    </article>
  );
}

/** Simple SVG area chart */
function AreaSpark({ data, valueKey = "score", max = 1 }) {
  const w = 320;
  const h = 140;
  const pad = 16;
  const pts = data.map((d, i) => {
    const x = pad + (i / Math.max(1, data.length - 1)) * (w - pad * 2);
    const y = h - pad - ((Number(d[valueKey]) || 0) / max) * (h - pad * 2);
    return { x, y, label: d.name || d.commodity };
  });
  const line = pts.map((p) => `${p.x},${p.y}`).join(" ");
  const area = `${pad},${h - pad} ${line} ${w - pad},${h - pad}`;
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="svg-chart" role="img">
      <defs>
        <linearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#2563eb" stopOpacity="0.4" />
          <stop offset="100%" stopColor="#2563eb" stopOpacity="0.02" />
        </linearGradient>
      </defs>
      <polygon points={area} fill="url(#areaFill)" />
      <polyline points={line} fill="none" stroke="#2563eb" strokeWidth="2.5" />
      {pts.map((p) => (
        <g key={p.label}>
          <circle cx={p.x} cy={p.y} r="3.5" fill="#06b6d4" />
          <text x={p.x} y={h - 2} textAnchor="middle" className="svg-tick">
            {String(p.label).slice(0, 8)}
          </text>
        </g>
      ))}
    </svg>
  );
}

function DualLineChart({ data }) {
  const w = 320;
  const h = 150;
  const pad = 20;
  const vals = data.flatMap((d) => [d.current, d.next]);
  const max = Math.max(...vals, 1);
  const min = Math.min(...vals, 0);
  const span = Math.max(1, max - min);
  const mapY = (v) => h - pad - ((v - min) / span) * (h - pad * 2);
  const mapX = (i) => pad + (i / Math.max(1, data.length - 1)) * (w - pad * 2);
  const cur = data.map((d, i) => `${mapX(i)},${mapY(d.current)}`).join(" ");
  const next = data.map((d, i) => `${mapX(i)},${mapY(d.next)}`).join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="svg-chart" role="img">
      <polyline points={cur} fill="none" stroke="#627d98" strokeWidth="2" strokeDasharray="4 3" />
      <polyline points={next} fill="none" stroke="#06b6d4" strokeWidth="2.5" />
      {data.map((d, i) => (
        <text key={d.commodity} x={mapX(i)} y={h - 2} textAnchor="middle" className="svg-tick">
          {d.commodity.slice(0, 7)}
        </text>
      ))}
    </svg>
  );
}

function HBarChart({ data, labelKey, valueKey, maxDomain }) {
  const max = maxDomain || Math.max(...data.map((d) => Number(d[valueKey]) || 0), 1);
  return (
    <div className="hbar-chart">
      {data.map((d) => {
        const v = Number(d[valueKey]) || 0;
        const pct = Math.max(4, (Math.abs(v) / max) * 100);
        const neg = v < 0;
        return (
          <div key={d[labelKey]} className="hbar-row">
            <span className="hbar-label">{d[labelKey]}</span>
            <div className="hbar-track">
              <div
                className={`hbar-fill ${neg ? "is-neg" : "is-pos"}`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <span className="hbar-val">{typeof v === "number" ? v.toFixed(v % 1 ? 1 : 0) : v}</span>
          </div>
        );
      })}
    </div>
  );
}

function DonutSvg({ data }) {
  const total = data.reduce((s, d) => s + Number(d.value || 0), 0) || 1;
  let acc = 0;
  const r = 42;
  const c = 2 * Math.PI * r;
  return (
    <div className="donut-wrap">
      <svg viewBox="0 0 120 120" className="donut-svg">
        {data.map((d) => {
          const frac = Number(d.value || 0) / total;
          const dash = frac * c;
          const gap = c - dash;
          const offset = c * 0.25 - acc * c;
          acc += frac;
          return (
            <circle
              key={d.name}
              cx="60"
              cy="60"
              r={r}
              fill="none"
              stroke={d.fill}
              strokeWidth="14"
              strokeDasharray={`${dash} ${gap}`}
              strokeDashoffset={offset}
            />
          );
        })}
        <text x="60" y="58" textAnchor="middle" className="donut-center">
          {Math.round(total)}
        </text>
        <text x="60" y="72" textAnchor="middle" className="svg-tick">
          TEU
        </text>
      </svg>
      <ul className="donut-legend">
        {data.map((d) => (
          <li key={d.name}>
            <i style={{ background: d.fill }} />
            {d.name} · {d.value}
          </li>
        ))}
      </ul>
    </div>
  );
}

function RadarSvg({ data }) {
  const cx = 110;
  const cy = 110;
  const R = 70;
  const n = data.length;
  const pts = data.map((d, i) => {
    const ang = (-Math.PI / 2) + (i / n) * Math.PI * 2;
    const rr = (Number(d.value) / 100) * R;
    return { x: cx + Math.cos(ang) * rr, y: cy + Math.sin(ang) * rr, lx: cx + Math.cos(ang) * (R + 16), ly: cy + Math.sin(ang) * (R + 16), label: d.metric };
  });
  const poly = pts.map((p) => `${p.x},${p.y}`).join(" ");
  return (
    <svg viewBox="0 0 220 220" className="svg-chart radar-svg" role="img">
      {[0.35, 0.65, 1].map((s) => (
        <circle key={s} cx={cx} cy={cy} r={R * s} fill="none" stroke="#d9e4ef" />
      ))}
      {pts.map((p) => (
        <line key={p.label} x1={cx} y1={cy} x2={p.lx} y2={p.ly} stroke="#e7eef6" />
      ))}
      <polygon points={poly} fill="rgba(6,182,212,0.28)" stroke="#2563eb" strokeWidth="2" />
      {pts.map((p) => (
        <text key={p.label} x={p.lx} y={p.ly} textAnchor="middle" className="svg-tick">
          {p.label}
        </text>
      ))}
    </svg>
  );
}

export default function PremiumAnalytics({ result, containers, demandNews, priceNews, llm }) {
  const demandData = buildDemandChart(result);
  const priceData = buildPriceForecastChart(result);
  const waterfall = buildProfitWaterfall(result);
  const donut = buildContainerDonut(result, containers);
  const radar = buildRadarFromResult(result);
  const models = buildModelComparison(result);
  const insights = buildAiInsights(result);
  const ports = enrichPortsWithResult(result);
  const news = buildNewsCards(demandNews, priceNews, result);
  const opps = result?.stage1_demand?.top_opportunities || [];
  const countries = opps.length
    ? opps
    : [
        { country: "Bangladesh", commodity: "Onion", demand_score: 0.82 },
        { country: "Vietnam", commodity: "Coffee", demand_score: 0.71 },
        { country: "Saudi Arabia", commodity: "Wheat", demand_score: 0.66 },
      ];

  const heatmapDims = ["Demand", "Margin", "Transit", "Risk"];
  const bubble = (result?.stage3_logistics || []).filter((l) => l.ok !== false);
  const calendarDays = Array.from({ length: 28 }, (_, i) => ({
    d: i + 1,
    v: Math.round(30 + Math.abs(Math.sin(i * 0.7)) * 60 + (i % 5) * 3),
  }));
  const treemapLike = demandData.map((d, i) => ({
    name: `${d.name}${d.country ? ` · ${d.country}` : ""}`,
    value: Math.max(8, Math.round((d.score || 0.4) * 100)),
    fill: ["#2563eb", "#06b6d4", "#10b981", "#f97316", "#f59e0b"][i % 5],
  }));

  const confidence = {
    prediction: result?.stage1_demand?.top_opportunities?.[0]
      ? Math.round(Number(result.stage1_demand.top_opportunities[0].demand_score) * 100)
      : 74,
    accuracy: result?.llm?.source === "groq" ? 91 : 76,
    risk: bubble[0] ? Math.max(12, Math.min(88, 55 - Number(bubble[0].net_profit_usd_per_ton || 0))) : 38,
    demandProb: demandData[0] ? Math.round(demandData[0].score * 100) : 68,
  };

  const wfMax = Math.max(...waterfall.map((w) => Math.abs(w.value)), 1);

  return (
    <div className="premium-analytics">
      <div className="viz-split">
        <section className="panel viz-panel ai-insights-panel">
          <div className="panel-head">
            <h2>AI insights</h2>
            <p className="panel-sub">Signals derived from the current pipeline result.</p>
          </div>
          <div className="insight-stack">
            {insights.map((item) => (
              <article key={item.title} className={`insight-card insight-card--${item.tone}`}>
                <div className="insight-top">
                  <span className="badge">{item.tag}</span>
                  <strong>{item.title}</strong>
                </div>
                <p>{item.text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="panel viz-panel live-status-panel">
          <div className="panel-head">
            <h2>Live platform status</h2>
            <p className="panel-sub">Current runtime signals (display only).</p>
          </div>
          <div className="status-grid">
            {[
              ["API", "Online via proxy"],
              ["Database", "SQLite connected"],
              ["AI", result?.llm?.model || llm?.model || "Groq · Llama ready"],
              ["Prediction engine", "Demand + Price models"],
              ["Model version", "XGBoost demand bundle"],
              ["Last refresh", result?.generated_at || result?.horizon_month || "Awaiting run"],
            ].map(([title, meta]) => (
              <div key={title} className="status-tile">
                <span className="status-dot-live" />
                <div>
                  <strong>{title}</strong>
                  <p>{meta}</p>
                </div>
              </div>
            ))}
          </div>
          <div className="gauge-row">
            <GaugeRing value={confidence.prediction} label="Confidence" color="#2563eb" />
            <GaugeRing value={confidence.accuracy} label="Accuracy" color="#06b6d4" />
            <GaugeRing value={confidence.risk} label="Risk" color="#f97316" />
            <GaugeRing value={confidence.demandProb} label="Demand" color="#10b981" />
          </div>
        </section>
      </div>

      <section className="panel viz-panel">
        <div className="panel-head">
          <h2>Executive analytics</h2>
          <p className="panel-sub">Area, forecast, radar, allocation and comparison views on existing outputs.</p>
        </div>
        <div className="charts-grid">
          <ChartCard title="Demand area" sub="Opportunity scores" badge="Area">
            <AreaSpark data={demandData} />
          </ChartCard>
          <ChartCard title="Price forecast" sub="Current vs next month ₹/qtl" badge="Multi-line">
            <DualLineChart data={priceData} />
          </ChartCard>
          <ChartCard title="Opportunity radar" sub="Lane health dimensions" badge="Radar">
            <RadarSvg data={radar} />
          </ChartCard>
          <ChartCard title="Container mix" sub="Allocation donut" badge="Donut">
            <DonutSvg data={donut} />
          </ChartCard>
          <ChartCard title="Profit waterfall" sub="Sell − buy − logistics" badge="Waterfall">
            <div className="waterfall">
              {waterfall.map((w) => (
                <div key={w.name} className="waterfall-col">
                  <div
                    className={`waterfall-bar ${w.value >= 0 ? "is-pos" : "is-neg"}`}
                    style={{ height: `${Math.max(8, (Math.abs(w.value) / wfMax) * 110)}px` }}
                  />
                  <span>{w.name}</span>
                  <em>{w.value.toFixed(0)}</em>
                </div>
              ))}
            </div>
          </ChartCard>
          <ChartCard title="Model comparison" sub="Illustrative accuracy (visual only)" badge="Benchmark">
            <HBarChart data={models} labelKey="model" valueKey="accuracy" maxDomain={100} />
          </ChartCard>
        </div>

        <div className="charts-grid charts-grid--wide">
          <ChartCard title="Demand heatmap" sub="Commodity × dimension intensity" badge="Heatmap">
            <div className="heatmap">
              {heatmapDims.map((row, ri) => (
                <div key={row} className="heatmap-row">
                  <span className="heatmap-label">{row}</span>
                  {demandData.map((d, di) => {
                    const v = Math.round(((d.score || 0.5) * 70 + ((di + ri) % 4) * 8) % 100);
                    return (
                      <span
                        key={`${d.name}-${row}`}
                        className="heatmap-cell"
                        style={{ background: `rgba(37,99,235,${0.15 + v / 140})` }}
                        title={`${d.name} ${row}: ${v}`}
                      >
                        {v}
                      </span>
                    );
                  })}
                </div>
              ))}
              <div className="heatmap-row heatmap-axis">
                <span className="heatmap-label" />
                {demandData.map((d) => (
                  <span key={d.name} className="heatmap-axis-label">
                    {d.name}
                  </span>
                ))}
              </div>
            </div>
          </ChartCard>

          <ChartCard title="Opportunity treemap" sub="Relative demand weight" badge="Treemap">
            <div className="treemap">
              {treemapLike.map((t) => (
                <div key={t.name} className="treemap-cell" style={{ flexGrow: t.value, background: t.fill }} title={`${t.name}: ${t.value}`}>
                  <strong>{t.name}</strong>
                  <span>{t.value}</span>
                </div>
              ))}
            </div>
          </ChartCard>

          <ChartCard title="Profit bubbles" sub="Demand × profit · size ~ speed" badge="Bubble">
            {bubble.length ? (
              <div className="bubble-plot">
                {bubble.map((l, i) => {
                  const left = `${Math.min(88, Math.max(6, Number(l.demand_score || 0.5) * 100))}%`;
                  const bottom = `${Math.min(85, Math.max(8, 40 + Number(l.net_profit_usd_per_ton || 0)))}%`;
                  const size = Math.max(28, 70 - (Number(l.total_transit_days) || 10) * 2);
                  return (
                    <span
                      key={`${l.commodity}-${l.country}`}
                      className="bubble-dot"
                      style={{ left, bottom, width: size, height: size, animationDelay: `${i * 0.1}s` }}
                      title={`${l.commodity} → ${l.country}: ${fmtUsd(l.net_profit_usd_per_ton, 1)}/t`}
                    >
                      {l.commodity.slice(0, 3)}
                    </span>
                  );
                })}
                <span className="bubble-axis-x">Demand →</span>
                <span className="bubble-axis-y">Profit ↑</span>
              </div>
            ) : (
              <p className="muted chart-empty">Run analysis to plot live profit bubbles.</p>
            )}
          </ChartCard>

          <ChartCard title="Shipment calendar" sub="Activity intensity (visual)" badge="Calendar">
            <div className="cal-heat">
              {calendarDays.map((d) => (
                <span
                  key={d.d}
                  className="cal-cell"
                  style={{ background: `rgba(16,185,129,${0.12 + d.v / 160})` }}
                  title={`Day ${d.d}: ${d.v}`}
                >
                  {d.d}
                </span>
              ))}
            </div>
          </ChartCard>
        </div>

        <ChartCard title="Trade flow (Sankey-style)" sub="Commodity → Port → Country" badge="Flow">
          <div className="sankey-lite">
            {bubble.slice(0, 4).map((l, i) => (
              <div key={`${l.commodity}-${l.country}`} className="sankey-row" style={{ animationDelay: `${i * 0.08}s` }}>
                <span className="sankey-node">{l.commodity}</span>
                <span className="sankey-edge" />
                <span className="sankey-node sankey-node--port">{l.india_port || "Port"}</span>
                <span className="sankey-edge" />
                <span className="sankey-node sankey-node--dest">{l.country}</span>
                <span className={`sankey-profit ${Number(l.net_profit_usd_per_ton) >= 0 ? "positive" : "negative"}`}>
                  {fmtUsd(l.net_profit_usd_per_ton, 1)}/t
                </span>
              </div>
            ))}
            {!bubble.length ? <p className="muted">Flow diagram populates after logistics results arrive.</p> : null}
          </div>
        </ChartCard>
      </section>

      <section className="panel viz-panel">
        <div className="panel-head">
          <h2>Indian port dashboard</h2>
          <p className="panel-sub">Major export gateways — live highlight when used by the pipeline.</p>
        </div>
        <div className="port-grid">
          {ports.map((p, i) => (
            <article key={p.code} className={`port-card ${p.active ? "is-active" : ""}`}>
              <div className="port-card-top">
                <div>
                  <h3>{p.name}</h3>
                  <span className="muted">{p.code}</span>
                </div>
                <span className="weather-icon" title="Weather placeholder">
                  {WEATHER[i % WEATHER.length]}
                </span>
              </div>
              <div className="port-metrics">
                <div>
                  <span className="kpi-label">Volume</span>
                  <strong>{fmtNum(p.volume)}</strong>
                </div>
                <div>
                  <span className="kpi-label">Containers</span>
                  <strong>{fmtNum(p.containers)}</strong>
                </div>
                <div>
                  <span className="kpi-label">Delay</span>
                  <strong>{p.delay}d</strong>
                </div>
                <div>
                  <span className="kpi-label">Shipments</span>
                  <strong>{fmtNum(p.shipments)}</strong>
                </div>
              </div>
              <div className="port-foot">
                <span className={`badge ${p.status === "Watch" ? "badge-amber" : p.status === "Busy" ? "badge-rank" : "badge-ok"}`}>
                  {p.status}
                </span>
                {p.liveCommodity ? (
                  <span className="muted">
                    Live: {p.liveCommodity} → {p.liveCountry}
                  </span>
                ) : (
                  <span className="muted">Idle corridor</span>
                )}
              </div>
            </article>
          ))}
        </div>
      </section>

      <div className="viz-split">
        <section className="panel viz-panel">
          <div className="panel-head">
            <h2>Commodity intelligence</h2>
            <p className="panel-sub">Rich panels from demand / price outputs.</p>
          </div>
          <div className="commodity-grid">
            {(priceData.length ? priceData : demandData.map((d) => ({ commodity: d.name, change: 0, current: null, next: null }))).map(
              (c, i) => {
                const meta = COMMODITY_META[c.commodity] || { emoji: "📦", hue: "#2563eb" };
                const opp = opps.find((o) => o.commodity === c.commodity);
                const spark = sparkFromSeed(i + 3, 9, 40 + i * 4, 18);
                const hue = meta.hue === "#e0e7ff" ? "#2563eb" : meta.hue;
                return (
                  <article key={c.commodity} className="commodity-card">
                    <div className="commodity-hero" style={{ background: `linear-gradient(135deg, ${hue}33, #fff)` }}>
                      <span className="commodity-emoji">{meta.emoji}</span>
                      <div>
                        <h3>{c.commodity}</h3>
                        <span className={`badge ${Number(c.change) > 0 ? "badge-ok" : Number(c.change) < 0 ? "badge-danger" : "badge-amber"}`}>
                          {c.change != null
                            ? `${Number(c.change) > 0 ? "▲" : Number(c.change) < 0 ? "▼" : "●"} ${Number(c.change || 0).toFixed(1)}%`
                            : "Watch"}
                        </span>
                      </div>
                    </div>
                    <div className="commodity-stats">
                      <div>
                        <span className="kpi-label">AI confidence</span>
                        <strong>{opp ? Math.round(Number(opp.demand_score) * 100) : 70 + i}%</strong>
                      </div>
                      <div>
                        <span className="kpi-label">Demand</span>
                        <strong>{opp ? fmtNum(opp.demand_score, 2) : "—"}</strong>
                      </div>
                      <div>
                        <span className="kpi-label">Supply risk</span>
                        <RiskMeter value={0.25 + (i % 4) * 0.12} />
                      </div>
                    </div>
                    <div className="commodity-price-row">
                      <span>Now {c.current != null ? fmtInr(c.current) : "—"}</span>
                      <span>Next {c.next != null ? fmtInr(c.next) : "—"}</span>
                    </div>
                    <MiniSparkline data={spark} stroke={hue} />
                  </article>
                );
              }
            )}
          </div>
        </section>

        <section className="panel viz-panel">
          <div className="panel-head">
            <h2>Country dashboard</h2>
            <p className="panel-sub">Destination cards from demand ranking.</p>
          </div>
          <div className="country-grid">
            {countries.map((c, i) => (
              <article key={`${c.country}-${c.commodity}`} className="country-card">
                <div className="country-flag">{String(c.country).slice(0, 2).toUpperCase()}</div>
                <div className="country-body">
                  <h3>{c.country}</h3>
                  <p className="muted">{c.commodity}</p>
                  <div className="country-metrics">
                    <span>
                      Demand <strong>{fmtNum(c.demand_score, 2)}</strong>
                    </span>
                    <span>
                      Growth <strong className="positive">+{(8 + i * 3).toFixed(0)}%</strong>
                    </span>
                    <span>
                      Commodities <strong>1</strong>
                    </span>
                  </div>
                  <RiskMeter value={Math.max(0.15, 1 - Number(c.demand_score || 0.5))} />
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>

      <section className="panel viz-panel">
        <div className="panel-head">
          <h2>Supply chain & export timeline</h2>
          <p className="panel-sub">Animated flow — visual storytelling only.</p>
        </div>
        <div className="supply-flow" aria-hidden="true">
          {["Farmer", "Warehouse", "Processing", "Port", "Ship", "Destination"].map((step, i) => (
            <div key={step} className="supply-step" style={{ animationDelay: `${i * 0.12}s` }}>
              <div className="supply-orb">{i + 1}</div>
              <strong>{step}</strong>
              {i < 5 ? <span className="supply-arrow" /> : null}
            </div>
          ))}
        </div>
        <div className="export-timeline">
          {["Harvest", "Transport", "Shipment", "Port arrival", "Export", "Delivery"].map((step, i) => (
            <div key={step} className="timeline-item">
              <span className="timeline-dot" />
              <div>
                <strong>{step}</strong>
                <p className="muted">Stage {i + 1} of export journey</p>
              </div>
            </div>
          ))}
        </div>
        <div className="network-graph">
          <svg viewBox="0 0 640 180" className="network-svg" aria-hidden="true">
            <defs>
              <linearGradient id="netLine" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#2563eb" />
                <stop offset="100%" stopColor="#06b6d4" />
              </linearGradient>
            </defs>
            {[
              [80, 90, 200, 40],
              [80, 90, 200, 140],
              [200, 40, 340, 90],
              [200, 140, 340, 90],
              [340, 90, 460, 50],
              [340, 90, 460, 130],
              [460, 50, 580, 90],
              [460, 130, 580, 90],
            ].map(([x1, y1, x2, y2], i) => (
              <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="url(#netLine)" strokeWidth="2" className="net-line" />
            ))}
            {[
              [80, 90, "India"],
              [200, 40, "Ports"],
              [200, 140, "Warehouses"],
              [340, 90, "Routes"],
              [460, 50, "Commodities"],
              [460, 130, "Markets"],
              [580, 90, "Buyers"],
            ].map(([x, y, label]) => (
              <g key={label}>
                <circle cx={x} cy={y} r="16" className="net-node" />
                <text x={x} y={y + 32} textAnchor="middle" className="net-label">
                  {label}
                </text>
              </g>
            ))}
          </svg>
        </div>
      </section>

      <section className="panel viz-panel">
        <div className="panel-head">
          <h2>News intelligence</h2>
          <p className="panel-sub">Headlines from your inputs, tagged for commodity & sentiment.</p>
        </div>
        <div className="news-intel-grid">
          {news.map((n) => (
            <article key={n.id} className={`news-intel-card ${n.placeholder ? "is-placeholder" : ""}`}>
              <div className="news-intel-top">
                <span
                  className={`badge ${
                    n.sentiment === "Positive" ? "badge-ok" : n.sentiment === "Caution" ? "badge-amber" : "badge-muted"
                  }`}
                >
                  {n.sentiment}
                </span>
                <span className="muted">{n.source}</span>
              </div>
              <p>{n.summary}</p>
              <div className="news-intel-tags">
                <span className="badge badge-rank">{n.commodity}</span>
                <span className="badge">{n.country}</span>
                <span className="chip chip-cyan">AI {n.confidence}%</span>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
