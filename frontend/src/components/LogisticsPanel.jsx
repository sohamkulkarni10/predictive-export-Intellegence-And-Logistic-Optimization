/**
 * Stage 3 — logistics route cards + comparison table.
 */
import KpiValue from "./KpiValue";
import { fmtNum, fmtUsd, profitClass } from "../utils";
import { IconPin, IconShip, IconWarn } from "./Icons";

function fmtInr(n) {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return "—";
  return `₹${Number(n).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

export default function LogisticsPanel({ lanes }) {
  const list = lanes || [];

  return (
    <section className="panel stage-panel reveal">
      <div className="panel-head">
        <h2>Logistics &amp; net profit</h2>
        <p className="panel-sub">
          Best India port → destination. Profit = trade sell price − predicted buy price − logistics.
        </p>
      </div>

      {list.length === 0 ? (
        <p className="muted">No logistics lanes returned.</p>
      ) : (
        <div className="lane-stack">
          {list.map((lane) => {
            const key = `${lane.commodity}-${lane.country}`;
            if (lane.ok === false) {
              return (
                <article key={key} className="glass-card lane-card lane-card--error">
                  <div className="card-top">
                    <span className="badge">{lane.commodity}</span>
                    <span className="badge">{lane.country}</span>
                  </div>
                  <p className="error-text">
                    Route unavailable: {lane.error || "logistics failed for this lane"}
                  </p>
                </article>
              );
            }

            const profitTon =
              lane.net_profit_usd_per_ton ?? lane.profit?.net_profit_usd_per_ton;
            const profitInr = lane.net_profit_inr ?? lane.profit?.net_profit_inr;
            const pClass = profitClass(profitTon);
            const profitable = Number(profitTon) > 0;
            const paths = lane.all_paths || [];

            return (
              <article key={key} className={`glass-card lane-card ${profitable ? "lane-card--profit" : "lane-card--loss"}`}>
                <div className="card-top">
                  <span className="badge">{lane.commodity}</span>
                  <span className="badge">{lane.country}</span>
                  {lane.service_type ? (
                    <span className="badge badge-muted">{lane.service_type}</span>
                  ) : null}
                  <span className={`badge ${profitable ? "badge-ok" : "badge-danger"}`}>
                    {profitable ? "Profitable route" : "Loss-making route"}
                  </span>
                </div>

                <div className="route-journey" aria-label="Export route">
                  <div className="route-stop">
                    <IconPin />
                    <span>{lane.origin || "India origin"}</span>
                  </div>
                  <span className="route-line" />
                  <div className="route-stop">
                    <IconShip />
                    <span>{lane.india_port || "India port"}</span>
                  </div>
                  <span className="route-line" />
                  <div className="route-stop">
                    <IconPin />
                    <span>{lane.destination_port || "Dest port"}</span>
                  </div>
                  <span className="route-line" />
                  <div className="route-stop">
                    <IconPin />
                    <span>{lane.country || "Country"}</span>
                  </div>
                </div>

                {!profitable ? (
                  <p className="warn-line">
                    <IconWarn /> High interest lane may still lose money after logistics.
                  </p>
                ) : null}

                {lane.decision_summary ? (
                  <p className="muted lane-summary">{lane.decision_summary}</p>
                ) : null}

                <div className="kpi-row kpi-row--six">
                  <div className="kpi-block">
                    <span className="kpi-label">Cost / ton</span>
                    <KpiValue
                      value={lane.cost_per_ton_usd}
                      format={(n) => fmtUsd(n, 1)}
                      className="kpi-mid"
                    />
                  </div>
                  <div className="kpi-block">
                    <span className="kpi-label">Transit</span>
                    <KpiValue
                      value={lane.total_transit_days}
                      format={(n) => `${fmtNum(n, 0)}d`}
                      className="kpi-mid"
                    />
                  </div>
                  <div className="kpi-block">
                    <span className="kpi-label">Total logistics</span>
                    <KpiValue
                      value={lane.total_logistics_cost_usd}
                      format={(n) => fmtUsd(n, 0)}
                      className="kpi-mid"
                    />
                  </div>
                  <div className="kpi-block">
                    <span className="kpi-label">Containers needed</span>
                    <KpiValue
                      value={lane.containers_required ?? lane.required_containers}
                      format={(n) => fmtNum(n, 0)}
                      className="kpi-mid"
                    />
                  </div>
                  <div className={`kpi-block profit-hero ${pClass}`}>
                    <span className="kpi-label">Net profit / ton</span>
                    <KpiValue
                      value={profitTon}
                      format={(n) => fmtUsd(n, 1)}
                      className="kpi-hero"
                    />
                  </div>
                  <div className={`kpi-block profit-hero ${pClass}`}>
                    <span className="kpi-label">Net profit (lane)</span>
                    <KpiValue value={profitInr} format={fmtInr} className="kpi-hero" />
                  </div>
                </div>

                {paths.length > 0 ? (
                  <div className="table-wrap" style={{ marginTop: "0.85rem" }}>
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>India port</th>
                          <th>Dest port</th>
                          <th className="num">Logistics $</th>
                          <th className="num">Days</th>
                          <th className="num">Net profit ₹</th>
                        </tr>
                      </thead>
                      <tbody>
                        {paths.slice(0, 5).map((p, i) => (
                          <tr key={`${p.india_port}-${p.destination_port}-${i}`}>
                            <td>{p.india_port}</td>
                            <td>{p.destination_port}</td>
                            <td className="num">{fmtUsd(p.total_logistics_cost_usd, 0)}</td>
                            <td className="num">{fmtNum(p.total_transit_days, 0)}</td>
                            <td className={`num ${profitClass(p.net_profit_inr)}`}>
                              {fmtInr(p.net_profit_inr)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : null}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
