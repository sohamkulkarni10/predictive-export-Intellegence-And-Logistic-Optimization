/**
 * Price forecast — black editorial price modules.
 */
import KpiValue from "./KpiValue";
import { fmtInr, fmtPct } from "../utils";

const TONES = ["brown", "cream", "yellow"];

export default function EditorialPrices({ data, horizon }) {
  const preds = (data?.predictions || []).filter((p) => !p.error);
  const asOf = data?.current_month_used || "2026-06";
  const maxPrice = Math.max(
    ...preds.flatMap((p) => [Number(p.current_price_inr) || 0, Number(p.predicted_next_month_price_inr) || 0]),
    1
  );

  return (
    <section className="ed-section ed-section--black" id="prices">
      <div className="ed-wrap">
        <div className="ed-section-head">
          <span className="ed-num ed-num--light">02</span>
          <div>
            <p className="ed-label ed-label--muted">PRICE FORECAST</p>
            <h2 className="ed-h2 ed-h2--light">What will commodities cost next month?</h2>
            <p className="ed-lead ed-lead--muted">
              INR per quintal · current from dataset {asOf}
              {horizon ? ` · predict ${horizon}` : ""}.
            </p>
          </div>
        </div>

        {!preds.length ? (
          <p className="ed-empty ed-empty--dark">Price modules appear after the pipeline returns forecasts.</p>
        ) : (
          <>
            <div className="ed-price-modules">
              {preds.map((p, i) => {
                const up = Number(p.predicted_change_pct) > 0;
                const down = Number(p.predicted_change_pct) < 0;
                return (
                  <article key={p.commodity} className={`ed-price-mod ed-price-mod--${TONES[i % 3]}`}>
                    <p className="ed-label">{p.commodity}</p>
                    <p className="ed-price-now">
                      Current {fmtInr(p.current_price_inr)}
                    </p>
                    <p className="ed-metric-label">NEXT MONTH</p>
                    <p className="ed-metric-xl">
                      <KpiValue value={p.predicted_next_month_price_inr} format={fmtInr} />
                    </p>
                    <p className={`ed-delta ${up ? "is-up" : down ? "is-down" : "is-flat"}`}>
                      {up ? "↑" : down ? "↓" : "→"} {fmtPct(p.predicted_change_pct)}
                      {horizon ? ` · ${horizon}` : ""}
                    </p>
                  </article>
                );
              })}
            </div>

            <div className="ed-price-compare">
              <p className="ed-label ed-label--muted">CURRENT VS PREDICTED</p>
              {preds.map((p) => (
                <div key={`${p.commodity}-cmp`} className="ed-cmp-row">
                  <span>{p.commodity}</span>
                  <div className="ed-cmp-bars">
                    <div
                      className="ed-cmp-bar is-current"
                      style={{ width: `${(Number(p.current_price_inr) / maxPrice) * 100}%` }}
                      title={fmtInr(p.current_price_inr)}
                    />
                    <div
                      className="ed-cmp-bar is-next"
                      style={{ width: `${(Number(p.predicted_next_month_price_inr) / maxPrice) * 100}%` }}
                      title={fmtInr(p.predicted_next_month_price_inr)}
                    />
                  </div>
                  <strong>{fmtInr(p.predicted_next_month_price_inr)}</strong>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </section>
  );
}
