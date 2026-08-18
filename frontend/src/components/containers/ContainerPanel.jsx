import { commodityAccent, fmtInr, fmtScore, formatRoute } from "../../utils";
import { EmptyState, LoadingSkeleton, Panel, StatusBadge } from "../common/Primitives";

export default function ContainerPanel({ plan, ready, isRunning, onRun }) {
  if (!ready && isRunning) {
    return (
      <Panel id="panel-containers" accent="cyan" title="Container Allocation" subtitle="Priority plan across available boxes">
        <LoadingSkeleton rows={4} />
      </Panel>
    );
  }

  if (!ready) {
    return (
      <Panel id="panel-containers" accent="cyan" title="Container Allocation" subtitle="Priority plan across available boxes">
        <EmptyState
          title="No container plan yet"
          description="Run analysis to allocate containers by opportunity score and profit."
          action={
            <button type="button" className="xi-btn xi-btn--primary" onClick={onRun}>
              Run Analysis
            </button>
          }
        />
      </Panel>
    );
  }

  if (!plan) {
    return (
      <Panel id="panel-containers" accent="cyan" title="Container Allocation">
        <EmptyState title="No allocation returned" description="Container stage completed without a plan." />
      </Panel>
    );
  }

  return (
    <Panel
      id="panel-containers"
      accent="cyan"
      title="Container Allocation"
      subtitle={plan.summary || "Visual allocation from the container priority agent"}
    >
      <div className="xi-metric-grid xi-metric-grid--4">
        <div><span>Available</span><strong>{plan.available ?? "Not available"}</strong></div>
        <div><span>Allocated</span><strong>{plan.allocated ?? "Not available"}</strong></div>
        <div><span>Remaining</span><strong>{plan.remaining ?? "Not available"}</strong></div>
        <div><span>Expected combined profit</span><strong>{fmtInr(plan.expectedCombinedProfit)}</strong></div>
      </div>

      <div className="xi-container-blocks" aria-label="Container blocks">
        {(plan.blocks || []).length === 0 ? (
          <p className="xi-muted">No containers were allocated in the response.</p>
        ) : (
          plan.blocks.map((b, i) => (
            <div
              key={`${b.commodity}-${i}`}
              className={`xi-container-block accent-${commodityAccent(b.commodity)}`}
              title={`${b.commodity} → ${b.country}`}
            >
              {b.commodity}
            </div>
          ))
        )}
      </div>

      <div className="xi-table-wrap">
        <table className="xi-table">
          <thead>
            <tr>
              <th>Priority</th>
              <th>Commodity</th>
              <th>Country</th>
              <th>Containers</th>
              <th>Opportunity</th>
              <th>Route</th>
              <th>Net profit / ton</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {(plan.allocations || []).map((a, i) => {
              const lossHighDemand =
                a.profitable === false && a.opportunityScore != null && a.opportunityScore >= 0.6;
              return (
                <tr key={`${a.priority}-${a.commodity}-${i}`} className={i === 0 ? "is-highlight" : ""}>
                  <td>#{a.priority ?? i + 1}</td>
                  <td>{a.commodity || "—"}</td>
                  <td>{a.country || "—"}</td>
                  <td>{a.containers ?? "—"}</td>
                  <td>{fmtScore(a.opportunityScore)}</td>
                  <td>
                    {(a.indiaPort || a.destinationPort)
                      ? formatRoute(a.indiaPort, a.destinationPort)
                      : "—"}
                  </td>
                  <td className={a.profitable === false ? "neg" : a.profitable ? "pos" : ""}>
                    {fmtInr(a.netProfitPerTon)}
                  </td>
                  <td>
                    {lossHighDemand ? (
                      <StatusBadge tone="warning">HIGH DEMAND · LOSS-MAKING</StatusBadge>
                    ) : a.profitable === true ? (
                      <StatusBadge tone="success">Profitable</StatusBadge>
                    ) : a.profitable === false ? (
                      <StatusBadge tone="danger">Loss-making</StatusBadge>
                    ) : (
                      <StatusBadge>Not available</StatusBadge>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}
