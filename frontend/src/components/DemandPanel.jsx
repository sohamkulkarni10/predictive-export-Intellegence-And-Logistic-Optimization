/**
 * Stage 1 — demand opportunity cards.
 */
import KpiValue from "./KpiValue";
import { demandIntensity, fmtNum } from "../utils";

function directionClass(dir) {
  const d = String(dir || "").toLowerCase();
  if (d.includes("increase") || d.includes("rising") || d.includes("strong")) return "badge-ok";
  if (d.includes("decrease") || d.includes("fall")) return "badge-danger";
  return "badge-amber";
}

function initials(country) {
  return String(country || "?")
    .split(/\s+/)
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

export default function DemandPanel({ data }) {
  const opps = data?.top_opportunities || [];

  return (
    <section className="panel stage-panel reveal">
      <div className="panel-head">
        <h2>Top demand opportunities</h2>
        <p className="panel-sub">
          {data?.note || "Countries and commodities with the strongest predicted demand."}
        </p>
      </div>

      {opps.length === 0 ? (
        <p className="muted">No demand opportunities returned.</p>
      ) : (
        <div className="grid-3">
          {opps.map((o) => (
            <article
              key={`${o.country}-${o.commodity}`}
              className={`glass-card demand-card ${demandIntensity(o.demand_score)}`}
            >
              <div className="card-top">
                <span className="badge badge-rank">#{o.rank}</span>
                {o.predicted_direction ? (
                  <span className={`badge ${directionClass(o.predicted_direction)}`}>
                    {o.predicted_direction}
                  </span>
                ) : null}
              </div>

              <div className="demand-identity">
                <span className="country-avatar" aria-hidden="true">
                  {initials(o.country)}
                </span>
                <div>
                  <h3 className="card-title">{o.country}</h3>
                  <p className="card-commodity">{o.commodity}</p>
                </div>
              </div>

              <div className="kpi-block">
                <span className="kpi-label">Demand score</span>
                <KpiValue
                  value={o.demand_score}
                  format={(n) => fmtNum(n, 2)}
                  className="kpi-hero"
                />
                <span className="kpi-sub">
                  AI confidence {Math.round((Number(o.demand_score) || 0) * 100)}%
                </span>
              </div>

              {o.news_snippet ? <p className="muted news-snip">{o.news_snippet}</p> : null}

              <div className="demand-meter" aria-hidden="true">
                <div
                  className="demand-meter-fill"
                  style={{
                    width: `${Math.min(100, Math.round((Number(o.demand_score) || 0) * 100))}%`,
                  }}
                />
              </div>

              <div className="card-actions">
                <span className="btn-ghost btn-small" role="presentation">
                  Ranked opportunity
                </span>
                <span className="badge badge-rank">Export opportunity</span>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
