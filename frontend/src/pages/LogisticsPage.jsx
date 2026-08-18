import { useNavigate } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { useApp } from "../context/AppContext";
import PageContainer from "../components/layout/PageContainer";
import LogisticsPanel from "../components/logistics/LogisticsPanel";

export default function LogisticsPage() {
  const navigate = useNavigate();
  const { analysis } = useApp();

  return (
    <PageContainer
      eyebrow="LANE INTELLIGENCE"
      title="Logistics Optimisation"
      subtitle="Compare origin, port corridor, cost, transit time and net profit for returned routes."
      actions={
        <button className="xi-btn xi-btn--primary" type="button" onClick={() => navigate("/demand")}>
          Run new analysis <ArrowRight size={15} />
        </button>
      }
    >
      <LogisticsPanel
        routes={analysis.dashboard?.logisticsRoutes}
        ready={analysis.revealed.logistics}
        isRunning={analysis.isRunning}
        onRun={() => navigate("/demand")}
      />
    </PageContainer>
  );
}
