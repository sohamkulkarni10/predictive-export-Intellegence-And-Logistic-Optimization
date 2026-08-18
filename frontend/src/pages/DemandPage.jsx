import { useApp } from "../context/AppContext";
import PageContainer from "../components/layout/PageContainer";
import DemandPanel from "../components/demand/DemandPanel";
import { RunAnalysisWorkspace } from "../components/dashboard/OverviewDashboard";

export default function DemandPage() {
  const { analysis } = useApp();

  return (
    <PageContainer
      eyebrow="MARKET INTELLIGENCE"
      title="Demand Prediction"
      subtitle="Rank country–commodity opportunities from the existing demand model and supplied news."
    >
      <div className="prediction-page-grid">
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
        <DemandPanel
          data={analysis.dashboard?.demandOpportunities}
          ready={analysis.revealed.demand}
          isRunning={analysis.isRunning}
          onRun={analysis.runAnalysis}
        />
      </div>
    </PageContainer>
  );
}
