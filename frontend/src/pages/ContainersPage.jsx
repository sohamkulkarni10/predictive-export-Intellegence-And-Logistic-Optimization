import { useNavigate } from "react-router-dom";
import { ArrowRight, Boxes } from "lucide-react";
import { useApp } from "../context/AppContext";
import PageContainer from "../components/layout/PageContainer";
import ContainerPanel from "../components/containers/ContainerPanel";
import { EmptyState, StatusBadge } from "../components/common/Primitives";
import { fmtInr, fmtScore, formatRoute } from "../utils";

const LEVELS = [
  { key: "high", title: "High Priority", tone: "success", test: (rank) => rank === 1 },
  { key: "medium", title: "Medium Priority", tone: "warning", test: (rank) => rank === 2 },
  { key: "low", title: "Lower Priority", tone: "danger", test: (rank) => rank > 2 },
];

export default function ContainersPage() {
  const navigate = useNavigate();
  const { analysis } = useApp();
  const plan = analysis.dashboard?.containerPlan;
  const allocations = plan?.allocations || [];

  return (
    <PageContainer
      eyebrow="CAPACITY PLANNING"
      title="Container Priority"
      subtitle="Ranking presentation based on the original container-priority order returned by the API."
      actions={
        <button className="xi-btn xi-btn--primary" type="button" onClick={() => navigate("/demand")}>
          Run new analysis <ArrowRight size={15} />
        </button>
      }
    >
      {analysis.revealed.container && allocations.length ? (
        <div className="priority-board">
          {LEVELS.map((level) => {
            const rows = allocations.filter((item) => level.test(Number(item.priority)));
            return (
              <section className={`priority-column priority-column--${level.key}`} key={level.key}>
                <header><span><Boxes size={16} /></span><h3>{level.title}</h3><em>{rows.length}</em></header>
                {rows.length ? rows.map((row) => (
                  <article key={`${row.priority}-${row.commodity}-${row.country}`}>
                    <div><strong>{row.commodity || "Not available"}</strong><StatusBadge tone={level.tone}>Rank {row.priority}</StatusBadge></div>
                    <p>{row.country || "Not available"}</p>
                    <dl>
                      <div><dt>Containers</dt><dd>{row.containers ?? "Not available"}</dd></div>
                      <div><dt>Demand score</dt><dd>{fmtScore(row.opportunityScore)}</dd></div>
                      <div><dt>Profit / ton</dt><dd className={row.profitable === false ? "neg" : "pos"}>{fmtInr(row.netProfitPerTon)}</dd></div>
                      <div><dt>Route</dt><dd title={`${row.indiaPort || ""} → ${row.destinationPort || ""}`.trim()}>{formatRoute(row.indiaPort, row.destinationPort)}</dd></div>
                    </dl>
                    {row.profitable === false && Number(row.opportunityScore) >= 0.6 ? (
                      <StatusBadge tone="warning">HIGH DEMAND · LOSS-MAKING</StatusBadge>
                    ) : null}
                  </article>
                )) : <p className="xi-muted">No allocation in this rank band.</p>}
              </section>
            );
          })}
        </div>
      ) : !analysis.isRunning ? (
        <EmptyState title="No container ranking yet" description="Run analysis to populate the priority board." />
      ) : null}

      <ContainerPanel
        plan={plan}
        ready={analysis.revealed.container}
        isRunning={analysis.isRunning}
        onRun={() => navigate("/demand")}
      />
    </PageContainer>
  );
}
