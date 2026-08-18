import { BookOpen, FileCheck2, Search } from "lucide-react";
import { useApp } from "../context/AppContext";
import PageContainer from "../components/layout/PageContainer";
import TradeAssistant from "../components/rag/TradeAssistant";
import { Panel } from "../components/common/Primitives";

const TOPICS = [
  "IEC registration",
  "HS codes",
  "CIF versus FOB",
  "Phytosanitary certificates",
  "Export documentation",
  "Destination tariffs",
  "Container rules",
];

export default function KnowledgePage() {
  const { analysis } = useApp();

  return (
    <PageContainer
      eyebrow="TRADE KNOWLEDGE"
      title="Knowledge Base"
      subtitle="Search export documentation and compliance through the existing RAG implementation."
    >
      <Panel title="Suggested Topics" subtitle="Choose a topic to populate the assistant query">
        <div className="knowledge-topics">
          {TOPICS.map((topic) => (
            <button type="button" key={topic} onClick={() => analysis.setQuestion(topic)}>
              <FileCheck2 size={16} /><span>{topic}</span><Search size={14} />
            </button>
          ))}
        </div>
      </Panel>
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
      <p className="knowledge-note"><BookOpen size={14} /> Source references are shown only when supplied by the backend.</p>
    </PageContainer>
  );
}
