import { useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext";
import PageContainer from "../components/layout/PageContainer";
import AgentReasoningPanel from "../components/agents/AgentReasoningPanel";
import { AgentPipeline } from "../components/layout/RightInsightRail";

export default function AgentsPage() {
  const navigate = useNavigate();
  const { analysis } = useApp();

  return (
    <PageContainer
      eyebrow="MULTI-AGENT SYSTEM"
      title="Agent Reasoning"
      subtitle="Read the original explanations returned by each existing analysis agent."
    >
      <AgentPipeline
        analysisStatus={analysis.analysisStatus}
        revealed={analysis.revealed}
        activeStage={analysis.activeStage}
      />
      <AgentReasoningPanel
        agents={analysis.dashboard?.agentExplanations}
        llm={analysis.dashboard?.llm}
        ready={analysis.revealed.supervisor}
        isRunning={analysis.isRunning}
        onRun={() => navigate("/demand")}
      />
    </PageContainer>
  );
}
