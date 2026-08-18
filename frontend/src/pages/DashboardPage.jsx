import { useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext";
import PageContainer from "../components/layout/PageContainer";
import RightInsightRail from "../components/layout/RightInsightRail";
import {
  AnalysisActivityFeed,
  OverviewDashboard,
  RunAnalysisWorkspace,
} from "../components/dashboard/OverviewDashboard";

const ROUTES = {
  demand: "/demand",
  price: "/price",
  logistics: "/logistics",
  container: "/containers",
  containers: "/containers",
  supervisor: "/agents",
  agents: "/agents",
  rag: "/assistant",
};

export default function DashboardPage() {
  const navigate = useNavigate();
  const { analysis } = useApp();
  const dashboard = analysis.dashboard;

  function go(target) {
    navigate(ROUTES[target] || "/dashboard");
  }

  function focusAnalysis() {
    document.getElementById("panel-run")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <PageContainer
      eyebrow="COMMAND CENTRE"
      title="Dashboard"
      subtitle="Here is what is happening with your export analysis."
    >
      <div className="overview-layout">
        <div className="overview-layout__main">
          <OverviewDashboard
            dashboard={dashboard}
            revealed={analysis.revealed}
            isRunning={analysis.isRunning}
            analysisStatus={analysis.analysisStatus}
            activeStage={analysis.activeStage}
            progress={analysis.progress}
            activeAgent={analysis.activeAgent}
            onRun={focusAnalysis}
            onNavigate={go}
            sessionMeta={analysis.sessionMeta}
            onClear={analysis.clearDashboard}
            onRestore={analysis.restoreSession}
          />

          <RunAnalysisWorkspace
            demandNews={analysis.demandNews}
            priceNews={analysis.priceNews}
            containers={analysis.containers}
            containerType={analysis.containerType}
            onDemandChange={analysis.setDemandNews}
            onPriceChange={analysis.setPriceNews}
            onContainersChange={analysis.setContainers}
            onContainerTypeChange={analysis.setContainerType}
            onLoadSamples={analysis.loadSamples}
            onFetchLiveNews={analysis.loadLiveNews}
            onRun={analysis.runAnalysis}
            isRunning={analysis.isRunning}
            newsLoading={analysis.newsLoading}
            error={analysis.error}
            progress={analysis.progress}
            activeAgent={analysis.activeAgent}
          />

          <AnalysisActivityFeed activity={analysis.activity} />
        </div>
        <RightInsightRail
          dashboard={dashboard}
          revealed={analysis.revealed}
          analysisStatus={analysis.analysisStatus}
          isRunning={analysis.isRunning}
          onNavigate={go}
        />
      </div>
    </PageContainer>
  );
}
