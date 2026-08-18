/**
 * Stage 5 — final recommendation board with profit per allocation.
 */
import KpiValue from "./KpiValue";
import { fmtInr, fmtUsd, profitClass } from "../utils";

export default function DecisionsPanel({ data }) {
  const lanes = data?.lanes || [];
  const first = data?.export_first || {};

  return (
    <section className="panel stage-panel reveal">
      <div className="panel-head">
        <h2>Final decisions</h2>
        <p className="panel-sub">Board-ready recommendation with container allocation and net profit.</p>
      </div>

      {data?.summary ? (
        <div className="banner banner-teal">
          <span className="banner-kicker">Board recommendation</span>
          <h3>
            {first.commodity && first.country
              ? `Lead with ${first.commodity} → ${first.country}`
              : "Export plan"}
          </h3>
          <p>{data.summary}</p>
        </div>
      ) : null}

      {lanes.length === 0 ? (
        <p className="muted">No decision lanes returned.</p>
      ) : (
        <div className="lane-stack">
          {lanes.map((lane) => {
            const key = `final-${lane.commodity}-${lane.country}`;
            const ton = lane.net_profit_usd_per_ton;
            const alloc = lane.net_profit_usd_for_allocation;
            const ctrs = lane.containers_allocated ?? 0;
            const pClass = profitClass(ton);

            return (
              <article
                key={key}
                className={`glass-card decision-card ${lane.export_first ? "is-first" : ""}`}
              >
                <div className="card-top">
                  {lane.export_first ? (
                    <span className="badge badge-amber">Export first</span>
                  ) : null}
                  <span className="badge">P{lane.priority_rank ?? "—"}</span>
                  <span className={`badge ${ctrs > 0 ? "badge-ok" : "badge-muted"}`}>
                    {ctrs} containers
                  </span>
                </div>

                <h3 className="card-title">
                  {lane.commodity} → {lane.country}
                </h3>
                <p className="route">
                  {lane.india_port && lane.destination_port
                    ? `${lane.india_port} → ${lane.destination_port}`
                    : "Route pending"}
                </p>

                <div className="kpi-row">
                  <div className="kpi-block">
                    <span className="kpi-label">Buy price</span>
                    <span className="kpi-mid">{fmtInr(lane.predicted_india_price_inr)}</span>
                  </div>
                  <div className="kpi-block">
                    <span className="kpi-label">Logistics / ton</span>
                    <span className="kpi-mid">{fmtUsd(lane.cost_per_ton_usd, 1)}</span>
                  </div>
                  <div className={`kpi-block profit-hero ${pClass}`}>
                    <span className="kpi-label">Net profit / ton</span>
                    <KpiValue value={ton} format={(n) => fmtUsd(n, 1)} className="kpi-hero" />
                  </div>
                  <div className={`kpi-block profit-hero ${profitClass(alloc)}`}>
                    <span className="kpi-label">Profit for allocation</span>
                    <KpiValue
                      value={alloc}
                      format={(n) => (ctrs === 0 ? "—" : fmtUsd(n, 0))}
                      className="kpi-hero"
                    />
                    {ctrs === 0 ? (
                      <span className="kpi-sub">0 containers allocated</span>
                    ) : (
                      <span className="kpi-sub">{ctrs} × containers</span>
                    )}
                  </div>
                </div>

                {lane.decision_summary ? (
                  <p className="muted lane-summary">{lane.decision_summary}</p>
                ) : null}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
