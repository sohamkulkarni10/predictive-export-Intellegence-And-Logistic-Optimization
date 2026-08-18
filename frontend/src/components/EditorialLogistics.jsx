/**
 * Logistics — route journey + profit panel + comparison table.
 */
import KpiValue from "./KpiValue";
import { fmtNum, fmtUsd, profitClass } from "../utils";

function fmtInr(n) {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return "—";
  return `₹${Number(n).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

export default function EditorialLogistics({ lanes }) {
  const list = lanes || [];
  const primary = list.find((l) => l.ok !== false) || null;
  const profitTon = primary
    ? primary.net_profit_usd_per_ton ?? primary.profit?.net_profit_usd_per_ton
    : null;
  const profitInr = primary ? primary.net_profit_inr ?? primary.profit?.net_profit_inr : null;
  const profitable = Number(profitTon) > 0;
  const paths = primary?.all_paths || [];

  return (
    <section className="ed-section ed-section--cream" id="logistics">
      <div className="ed-wrap">
        <div className="ed-section-head">
          <span className="ed-num">03</span>
          <div>
            <p className="ed-label">ROUTE INTELLIGENCE</p>
            <h2 className="ed-h2">From Indian origin to global destination.</h2>
            <p className="ed-lead">
              Best India port → destination. Profit = trade sell price − predicted buy price − logistics.
            </p>
          </div>
        </div>

        {!primary ? (
          <p className="ed-empty">Logistics routes appear after a successful pipeline run.</p>
        ) : (
          <>
            <div className="ed-route-split">
              <div className="ed-journey">
                <div className="ed-node">
                  <span className="ed-node-label">ORIGIN</span>
                  <strong>{primary.origin || "India origin"}</strong>
                </div>
                <div className="ed-route-line">
                  <span className="ed-moving-dot" />
                </div>
                <div className="ed-node">
                  <span className="ed-node-label">INDIAN PORT</span>
                  <strong>{primary.india_port || "—"}</strong>
                </div>
                <div className="ed-route-line ed-route-line--sea">
                  <span className="ed-ship">SHIP ROUTE</span>
                  <span className="ed-moving-dot" />
                </div>
                <div className="ed-node">
                  <span className="ed-node-label">DESTINATION PORT</span>
                  <strong>{primary.destination_port || "—"}</strong>
                </div>
                <div className="ed-route-line">
                  <span className="ed-moving-dot" />
                </div>
                <div className="ed-node">
                  <span className="ed-node-label">COUNTRY</span>
                  <strong>
                    {primary.country} · {primary.commodity}
                  </strong>
                </div>
                {primary.total_transit_days != null ? (
                  <p className="ed-transit">TRANSIT {fmtNum(primary.total_transit_days, 0)} DAYS</p>
                ) : null}
              </div>

              <aside className={`ed-profit-panel ${profitable ? "is-profit" : "is-loss"}`}>
                <p className="ed-label">
                  {profitable ? "PROFITABLE ROUTE ↑" : "LOSS-MAKING ROUTE ⚠"}
                </p>
                <p className="ed-metric-label">NET PROFIT / TON</p>
                <p className="ed-metric-xl">
                  <KpiValue value={profitTon} format={(n) => fmtUsd(n, 1)} />
                </p>
                <p className="ed-profit-total">
                  Lane total <KpiValue value={profitInr} format={fmtInr} />
                </p>
                <div className="ed-profit-grid">
                  <div>
                    <span>Cost / ton</span>
                    <strong>{fmtUsd(primary.cost_per_ton_usd, 1)}</strong>
                  </div>
                  <div>
                    <span>Transit</span>
                    <strong>{fmtNum(primary.total_transit_days, 0)}d</strong>
                  </div>
                  <div>
                    <span>Logistics</span>
                    <strong>{fmtUsd(primary.total_logistics_cost_usd, 0)}</strong>
                  </div>
                  <div>
                    <span>Containers</span>
                    <strong>
                      {fmtNum(primary.containers_required ?? primary.required_containers, 0)}
                    </strong>
                  </div>
                </div>
                {!profitable ? (
                  <p className="ed-warn-copy">
                    High interest lane may still lose money after logistics. Not recommended as a lead shipment.
                  </p>
                ) : null}
              </aside>
            </div>

            {paths.length > 0 ? (
              <div className="ed-table-panel">
                <p className="ed-label ed-label--muted">ROUTE COMPARISON</p>
                <div className="ed-table-scroll">
                  <table className="ed-table">
                    <thead>
                      <tr>
                        <th>India port</th>
                        <th>Dest port</th>
                        <th>Logistics $</th>
                        <th>Days</th>
                        <th>Net profit ₹</th>
                      </tr>
                    </thead>
                    <tbody>
                      {paths.slice(0, 8).map((p, i) => (
                        <tr key={`${p.india_port}-${p.destination_port}-${i}`} className={i === 0 ? "is-recommended" : ""}>
                          <td>{p.india_port}</td>
                          <td>{p.destination_port}</td>
                          <td>{fmtUsd(p.total_logistics_cost_usd, 0)}</td>
                          <td>{fmtNum(p.total_transit_days, 0)}</td>
                          <td className={profitClass(p.net_profit_inr)}>{fmtInr(p.net_profit_inr)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : null}

            {list.length > 1 ? (
              <div className="ed-lane-list">
                {list.slice(1).map((lane) => {
                  if (lane.ok === false) {
                    return (
                      <div key={`${lane.commodity}-${lane.country}`} className="ed-lane-mini">
                        <strong>
                          {lane.commodity} → {lane.country}
                        </strong>
                        <span className="negative">Route unavailable</span>
                      </div>
                    );
                  }
                  const ton = lane.net_profit_usd_per_ton ?? lane.profit?.net_profit_usd_per_ton;
                  return (
                    <div key={`${lane.commodity}-${lane.country}`} className="ed-lane-mini">
                      <strong>
                        {lane.commodity} → {lane.country}
                      </strong>
                      <span>
                        {lane.india_port} → {lane.destination_port}
                      </span>
                      <span className={profitClass(ton)}>{fmtUsd(ton, 1)} / ton</span>
                    </div>
                  );
                })}
              </div>
            ) : null}
          </>
        )}
      </div>
    </section>
  );
}
