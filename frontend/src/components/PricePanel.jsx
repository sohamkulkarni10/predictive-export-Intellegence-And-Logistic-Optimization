/**
 * Stage 2 — India price forecast cards (INR / quintal).
 */
import KpiValue from "./KpiValue";
import { fmtInr, fmtPct, profitClass } from "../utils";
import { IconTrendDown, IconTrendUp } from "./Icons";

export default function PricePanel({ data, horizon }) {
  const preds = data?.predictions || [];
  const asOf = data?.current_month_used || "2026-06";

  return (
    <section className="panel stage-panel reveal">
      <div className="panel-head">
        <h2>India price forecast</h2>
        <p className="panel-sub">
          INR per quintal · current from dataset {asOf}
          {horizon ? ` · predict ${horizon}` : ""}.
        </p>
      </div>

      {preds.length === 0 ? (
        <p className="muted">No price predictions returned.</p>
      ) : (
        <div className="grid-3">
          {preds.map((p) => {
            if (p.error) {
              return (
                <article key={p.commodity} className="glass-card price-card">
                  <h3 className="card-title">{p.commodity}</h3>
                  <p className="error-text">{p.error}</p>
                </article>
              );
            }
            const changeClass = profitClass(p.predicted_change_pct);
            const up = Number(p.predicted_change_pct) > 0;
            return (
              <article key={p.commodity} className="glass-card price-card">
                <div className="card-top">
                  <span className={`badge ${changeClass === "positive" ? "badge-ok" : changeClass === "negative" ? "badge-danger" : "badge-amber"}`}>
                    {p.direction || "Next"}
                  </span>
                  <span className="badge">₹ / quintal</span>
                </div>
                <h3 className="card-title">{p.commodity}</h3>
                <div className="kpi-block">
                  <span className="kpi-label">Predicted next month</span>
                  <KpiValue
                    value={p.predicted_next_month_price_inr}
                    format={(n) => fmtInr(n)}
                    className="kpi-hero"
                  />
                </div>
                <div className="price-meta">
                  <span>
                    Current ({p.current_as_of || asOf}){" "}
                    <strong>{fmtInr(p.current_price_inr)}</strong>
                  </span>
                  <span className={`change-pill ${changeClass}`}>
                    {up ? <IconTrendUp /> : <IconTrendDown />}
                    {fmtPct(p.predicted_change_pct)}
                  </span>
                </div>
                <div className="mini-spark" aria-hidden="true">
                  <span />
                  <span />
                  <span />
                  <span />
                  <span className={up ? "is-up" : "is-down"} />
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
