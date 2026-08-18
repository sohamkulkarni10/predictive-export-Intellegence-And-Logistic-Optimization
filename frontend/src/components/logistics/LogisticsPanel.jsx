import { useState } from "react";
import { Anchor, MapPin, Ship, TrainFront, Warehouse } from "lucide-react";
import { fmtInr, shortPortName } from "../../utils";
import { EmptyState, LoadingSkeleton, Panel, StatusBadge } from "../common/Primitives";

function RouteVisual({ route }) {
  if (!route) return null;
  const nodes = [
    { label: route.origin || "Origin", icon: MapPin },
    { label: "Inland", icon: TrainFront },
    { label: shortPortName(route.indiaPort) || "India port", icon: Warehouse },
    { label: "Sea", icon: Ship },
    { label: shortPortName(route.destinationPort) || "Dest. port", icon: Anchor },
    { label: route.country || "Country", icon: MapPin },
  ];
  return (
    <div className={`xi-route-canvas ${route.profitable === false ? "is-loss" : route.profitable ? "is-profit" : ""}`}>
      <div className="xi-route-flow">
        {nodes.map((n, i) => {
          const Icon = n.icon;
          return (
            <div key={`${n.label}-${i}`} className="xi-route-node">
              <span className="xi-route-node__icon"><Icon size={14} /></span>
              <span>{n.label}</span>
              {i < nodes.length - 1 ? <i className="xi-route-line" aria-hidden="true" /> : null}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function LogisticsPanel({ routes, ready, isRunning, onRun }) {
  const list = routes || [];
  const [selectedIdx, setSelectedIdx] = useState(0);
  const route = list[selectedIdx] || list[0];

  return (
    <Panel
      id="panel-logistics"
      accent="orange"
      title="Route Optimisation"
      subtitle="India port corridors ranked by logistics cost and net profit"
    >
      {!ready && isRunning ? <LoadingSkeleton rows={5} /> : null}
      {!ready && !isRunning ? (
        <EmptyState
          title="No logistics routes yet"
          description="Run analysis to evaluate port pairs and lane profitability."
          action={
            <button type="button" className="xi-btn xi-btn--primary" onClick={onRun}>
              Run Analysis
            </button>
          }
        />
      ) : null}

      {ready && list.length === 0 ? (
        <EmptyState title="No routes returned" description="The logistics stage completed without lane results." />
      ) : null}

      {ready && route ? (
        <div className="xi-logistics-layout">
          <RouteVisual route={route} />
          <div className={`xi-route-metrics ${route.profitable === false ? "is-loss" : route.profitable ? "is-profit" : ""}`}>
            <div className="xi-route-metrics__head">
              <strong>
                {route.commodity} → {route.country}
              </strong>
              {route.profitable === true ? (
                <StatusBadge tone="success">Profitable Route</StatusBadge>
              ) : route.profitable === false ? (
                <StatusBadge tone="danger">Loss-Making Route</StatusBadge>
              ) : null}
            </div>
            <div className="xi-metric-grid">
              <div><span>Cost / ton</span><strong>{fmtInr(route.costPerTonInr ?? route.costPerTonUsd)}</strong></div>
              <div><span>Cost / container</span><strong>{fmtInr(route.costPerContainerInr ?? route.costPerContainerUsd)}</strong></div>
              <div><span>Transit</span><strong>{route.transitDays != null ? `${route.transitDays} days` : "Not available"}</strong></div>
              <div><span>Net profit / ton</span><strong className={route.profitable === false ? "neg" : route.profitable ? "pos" : ""}>{fmtInr(route.netProfitPerTon)}</strong></div>
            </div>
            {route.decisionSummary ? <p className="xi-muted">{route.decisionSummary}</p> : null}
            {route.profitable === false ? (
              <p className="xi-warn">This lane shows negative net profit per ton. Review before allocating containers.</p>
            ) : null}
          </div>

          <div className="xi-table-wrap">
            <table className="xi-table">
              <thead>
                <tr>
                  <th>Commodity</th>
                  <th>India port</th>
                  <th>Destination</th>
                  <th>Cost / ton</th>
                  <th>Transit</th>
                  <th>Profit / ton</th>
                  <th>Status</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {list.map((r, i) => (
                  <tr key={`${r.commodity}-${r.country}-${i}`} className={i === selectedIdx ? "is-selected" : ""}>
                    <td>{r.commodity}</td>
                    <td title={r.indiaPort || undefined}>{shortPortName(r.indiaPort)}</td>
                    <td title={r.destinationPort || undefined}>{shortPortName(r.destinationPort)}</td>
                    <td>{fmtInr(r.costPerTonInr ?? r.costPerTonUsd)}</td>
                    <td>{r.transitDays != null ? `${r.transitDays}d` : "—"}</td>
                    <td className={r.profitable === false ? "neg" : r.profitable ? "pos" : ""}>{fmtInr(r.netProfitPerTon)}</td>
                    <td>
                      {r.profitable === true ? (
                        <StatusBadge tone="success">Profit</StatusBadge>
                      ) : r.profitable === false ? (
                        <StatusBadge tone="danger">Loss</StatusBadge>
                      ) : (
                        <StatusBadge>Unknown</StatusBadge>
                      )}
                    </td>
                    <td>
                      <button type="button" className="xi-btn xi-btn--ghost xi-btn--sm" onClick={() => setSelectedIdx(i)}>
                        View route
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </Panel>
  );
}
