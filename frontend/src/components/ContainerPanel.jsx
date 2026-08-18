/**
 * Stage 4 — container allocation dashboard.
 */
import KpiValue from "./KpiValue";
import { fmtNum, fmtUsd, profitClass } from "../utils";
import { IconWarn } from "./Icons";

export default function ContainerPanel({ data }) {
  const allocations = data?.allocations || [];
  const first = data?.export_first || {};
  const available = Number(data?.available_containers || 0);
  const allocated = allocations.reduce((s, a) => s + Number(a.containers_allocated || 0), 0);
  const remaining = Math.max(0, available - allocated);
  const expectedProfit = allocations.reduce(
    (s, a) => s + Number(a.net_profit_usd_for_allocation || 0),
    0
  );

  return (
    <section className="panel stage-panel reveal">
      <div className="panel-head">
        <h2>Container priority</h2>
        <p className="panel-sub">If only N containers are available — who ships first.</p>
      </div>

      <div className="container-summary-grid container-summary-grid--five">
        <article className="mini-stat">
          <span className="kpi-label">Total containers</span>
          <strong>{available || "—"}</strong>
        </article>
        <article className="mini-stat">
          <span className="kpi-label">Allocated</span>
          <strong>{allocated}</strong>
        </article>
        <article className="mini-stat">
          <span className="kpi-label">Remaining</span>
          <strong>{remaining}</strong>
        </article>
        <article className="mini-stat mini-stat--accent">
          <span className="kpi-label">Highest priority</span>
          <strong>
            {first.commodity && first.country
              ? `${first.commodity} → ${first.country}`
              : "—"}
          </strong>
        </article>
        <article className="mini-stat">
          <span className="kpi-label">Expected profit</span>
          <strong className={profitClass(expectedProfit)}>{fmtUsd(expectedProfit, 0)}</strong>
        </article>
      </div>

      {available > 0 ? (
        <div className="alloc-bar" aria-hidden="true">
          <div className="alloc-bar-fill" style={{ width: `${Math.min(100, (allocated / available) * 100)}%` }} />
        </div>
      ) : null}

      {data?.summary ? (
        <div className="banner banner-amber">
          <span className="banner-kicker">Export first</span>
          <h3>
            {first.commodity && first.country
              ? `${first.commodity} → ${first.country}`
              : "Top allocation"}
          </h3>
          <p>{data.summary}</p>
        </div>
      ) : null}

      {allocations.length === 0 ? (
        <p className="muted">No allocations returned.</p>
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Priority</th>
                <th>Commodity</th>
                <th>Country</th>
                <th className="num">Containers</th>
                <th className="num">Score</th>
                <th>Route</th>
                <th className="num">Net profit / ton</th>
                <th>Note</th>
              </tr>
            </thead>
            <tbody>
              {allocations.map((a) => {
                const zero = !a.containers_allocated;
                const loss = Number(a.net_profit_usd_per_ton) < 0;
                return (
                  <tr
                    key={`${a.commodity}-${a.country}`}
                    className={`${a.export_first ? "row-first" : ""} ${zero ? "row-zero" : ""}`}
                  >
                    <td>
                      <span className={`badge ${a.export_first ? "badge-amber" : ""}`}>
                        #{a.priority_rank}
                        {a.export_first ? " ★" : ""}
                      </span>
                    </td>
                    <td>{a.commodity}</td>
                    <td>{a.country}</td>
                    <td className="num">
                      <KpiValue
                        value={a.containers_allocated ?? 0}
                        format={(n) => fmtNum(n, 0)}
                        className="kpi-inline"
                      />
                      {zero ? <span className="zero-tag">none</span> : null}
                    </td>
                    <td className="num">{fmtNum(a.priority_score, 2)}</td>
                    <td className="route-cell">
                      {a.india_port && a.destination_port
                        ? `${a.india_port} → ${a.destination_port}`
                        : "—"}
                    </td>
                    <td className={`num ${profitClass(a.net_profit_usd_per_ton)}`}>
                      {fmtUsd(a.net_profit_usd_per_ton, 1)}
                    </td>
                    <td>
                      {loss ? (
                        <span className="badge badge-amber">
                          <IconWarn /> High demand, loss-making
                        </span>
                      ) : (
                        <span className="badge badge-ok">Viable</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
