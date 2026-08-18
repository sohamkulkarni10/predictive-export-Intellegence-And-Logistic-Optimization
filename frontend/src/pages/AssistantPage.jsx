import { AlertTriangle, MapPinned, Sparkles, TrendingUp } from "lucide-react";
import { useApp } from "../context/AppContext";
import PageContainer from "../components/layout/PageContainer";
import TradeAssistant from "../components/rag/TradeAssistant";
import { fmtInr, fmtScore, formatRoute } from "../utils";

export default function AssistantPage() {
  const { analysis } = useApp();
  const dashboard = analysis.dashboard;
  const recommendation = dashboard?.supervisorRecommendation;
  const topDemand = dashboard?.demandOpportunities?.[0];
  const topRoute = dashboard?.logisticsRoutes?.[0];

  return (
    <PageContainer
      eyebrow="AI TRADE DESK"
      title="AI Assistant"
      subtitle="Ask the existing RAG service about trade documents, tariffs, routes and export rules."
    >
      <div className="assistant-page-grid">
        <TradeAssistant
          question={analysis.question}
          onQuestionChange={analysis.setQuestion}
          onAsk={analysis.onAsk}
          loading={analysis.ragLoading}
          rag={analysis.rag}
          lastAsked={analysis.lastAsked}
          error={analysis.ragError}
          messages={analysis.ragMessages}
          onClear={analysis.clearRag}
        />

        <aside className="assistant-insights">
          <h3>Today’s AI Recommendations</h3>
          <article><TrendingUp size={17} /><div><span>Top opportunity</span><strong>{topDemand ? `${topDemand.commodity} → ${topDemand.country}` : "Not available"}</strong><small>Demand score {fmtScore(topDemand?.demandScore)}</small></div></article>
          <article><MapPinned size={17} /><div><span>Most profitable route</span><strong title={topRoute ? `${topRoute.indiaPort} → ${topRoute.destinationPort}` : undefined}>{topRoute ? formatRoute(topRoute.indiaPort, topRoute.destinationPort) : "Not available"}</strong><small>{fmtInr(topRoute?.netProfitPerTon)} / ton</small></div></article>
          <article><AlertTriangle size={17} /><div><span>Main warning</span><strong>{topRoute?.profitable === false ? "Loss-making route detected" : "No returned loss warning"}</strong></div></article>
          <article><Sparkles size={17} /><div><span>Supervisor insight</span><p>{recommendation?.summary || "Not available"}</p></div></article>
        </aside>
      </div>
    </PageContainer>
  );
}
