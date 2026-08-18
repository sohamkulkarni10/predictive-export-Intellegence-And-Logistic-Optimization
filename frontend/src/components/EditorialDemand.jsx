/**
 * Demand opportunities — asymmetric editorial layout.
 */
import KpiValue from "./KpiValue";
import { fmtNum } from "../utils";

function statusOf(dir) {
  const d = String(dir || "").toLowerCase();
  if (d.includes("increase") || d.includes("rising") || d.includes("strong")) {
    return { label: "INCREASING", tone: "up" };
  }
  if (d.includes("decrease") || d.includes("fall")) {
    return { label: "DECREASING", tone: "down" };
  }
  return { label: "STABLE", tone: "flat" };
}

function initials(country) {
  return String(country || "?")
    .split(/\s+/)
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

export default function EditorialDemand({ data }) {
  const opps = data?.top_opportunities || [];
  const top = opps[0];
  const rest = opps.slice(1, 3);
  const maxScore = Math.max(...opps.map((o) => Number(o.demand_score) || 0), 0.01);

  return (
    <section className="ed-section ed-section--cream" id="opportunities">
      <div className="ed-wrap">
        <div className="ed-section-head">
          <span className="ed-num">01</span>
          <div>
            <p className="ed-label">DEMAND INTELLIGENCE</p>
            <h2 className="ed-h2">Where should India export next?</h2>
            <p className="ed-lead">
              {data?.note ||
                "Countries and commodities with the strongest predicted demand for the next planning window."}
            </p>
          </div>
        </div>

        {!opps.length ? (
          <p className="ed-empty">Run analysis to reveal ranked demand opportunities.</p>
        ) : (
          <>
            <div className="ed-demand-layout">
              {top ? (
                <article className="ed-opp ed-opp--hero">
                  <div className="ed-opp-top">
                    <span className="ed-rank">#{top.rank}</span>
                    <span className={`ed-status ed-status--${statusOf(top.predicted_direction).tone}`}>
                      <i /> {statusOf(top.predicted_direction).label}
                    </span>
                  </div>
                  <div className="ed-opp-identity">
                    <span className="ed-flag">{initials(top.country)}</span>
                    <div>
                      <h3>{top.country}</h3>
                      <p>{top.commodity}</p>
                    </div>
                  </div>
                  <p className="ed-metric-label">DEMAND SCORE</p>
                  <p className="ed-metric-xl">
                    <KpiValue value={top.demand_score} format={(n) => fmtNum(n, 2)} />
                  </p>
                  {top.news_snippet ? <p className="ed-snip">{top.news_snippet}</p> : null}
                  <div className="ed-progress">
                    <div style={{ width: `${Math.min(100, (Number(top.demand_score) || 0) * 100)}%` }} />
                  </div>
                  <a className="ed-text-link" href="#decision">
                    View opportunity →
                  </a>
                </article>
              ) : null}

              <div className="ed-opp-stack">
                {rest.map((o, i) => (
                  <article key={`${o.country}-${o.commodity}`} className={`ed-opp ed-opp--side ${i === 0 ? "is-dark" : ""}`}>
                    <div className="ed-opp-top">
                      <span className="ed-rank">#{o.rank}</span>
                      <span className={`ed-status ed-status--${statusOf(o.predicted_direction).tone}`}>
                        <i /> {statusOf(o.predicted_direction).label}
                      </span>
                    </div>
                    <h3>
                      {o.country} · {o.commodity}
                    </h3>
                    <p className="ed-metric-md">
                      <KpiValue value={o.demand_score} format={(n) => fmtNum(n, 2)} />
                    </p>
                    {o.news_snippet ? <p className="ed-snip">{o.news_snippet}</p> : null}
                  </article>
                ))}
              </div>
            </div>

            <div className="ed-bar-compare">
              <p className="ed-label">SCORE COMPARISON</p>
              {opps.map((o) => (
                <div key={`${o.country}-bar`} className="ed-bar-row">
                  <span>
                    {o.commodity} · {o.country}
                  </span>
                  <div className="ed-bar-track">
                    <div
                      className="ed-bar-fill"
                      style={{ width: `${(Number(o.demand_score) / maxScore) * 100}%` }}
                    />
                  </div>
                  <strong>{fmtNum(o.demand_score, 2)}</strong>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </section>
  );
}
