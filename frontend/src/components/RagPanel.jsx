/**
 * Trade Document Assistant (RAG) — chat UI only.
 */
import { IconDoc } from "./Icons";

const CHIPS = [
  "Onion export documents",
  "IEC registration",
  "CIF vs FOB",
  "Phytosanitary certificate",
  "Wheat HS code",
  "Vietnam tariff",
];

export default function RagPanel({
  question,
  onQuestionChange,
  onAsk,
  loading,
  rag,
  lastAsked,
  error,
}) {
  const hasThread = Boolean(lastAsked || rag?.answer);

  return (
    <section className="panel rag-panel">
      <div className="panel-head panel-head-row">
        <div className="rag-title-row">
          <span className="rag-icon">
            <IconDoc />
          </span>
          <div>
            <h2>Trade Document Assistant</h2>
            <p className="panel-sub">
              Ask about IEC, HS codes, CIF/FOB, phytosanitary certificates, destination tariffs, or container rules.
            </p>
          </div>
        </div>
      </div>

      <div className="chip-row">
        {CHIPS.map((chip) => (
          <button
            key={chip}
            type="button"
            className="example-chip"
            onClick={() => onQuestionChange(chip)}
          >
            {chip}
          </button>
        ))}
      </div>

      <div className="chat">
        {!hasThread ? (
          <div className="chat-empty">
            <p className="muted">Ask a question to search the tariff and trade-document knowledge base.</p>
          </div>
        ) : null}

        {lastAsked ? (
          <div className="chat-bubble chat-bubble--user">
            <span className="chat-role">You</span>
            <p>{lastAsked}</p>
          </div>
        ) : null}

        {rag?.answer ? (
          <div className="chat-bubble chat-bubble--answer reveal">
            <span className="chat-role">ExportIntel AI</span>
            <p>{rag.answer}</p>
            {(rag.sources || []).length > 0 ? (
              <div className="source-chips">
                {(rag.sources || []).map((s) => (
                  <span key={`${s.title}-${s.score}`} className="source-chip" title={`score ${s.score}`}>
                    {s.title}
                    {s.score !== undefined ? (
                      <em>{typeof s.score === "number" ? s.score.toFixed(2) : s.score}</em>
                    ) : null}
                  </span>
                ))}
              </div>
            ) : null}
            {rag.used_llm !== undefined ? (
              <span className="chat-meta">
                {rag.used_llm ? "Answered with LLM" : "Retrieved from docs"}
              </span>
            ) : null}
          </div>
        ) : null}

        <form
          className="chat-compose"
          onSubmit={(e) => {
            e.preventDefault();
            onAsk();
          }}
        >
          <input
            value={question}
            onChange={(e) => onQuestionChange(e.target.value)}
            placeholder="e.g. What documents are needed to export onions from India?"
            disabled={loading}
            aria-label="RAG question"
          />
          <button className="btn-primary" type="submit" disabled={loading || !question.trim()}>
            {loading ? "Searching…" : "Ask"}
          </button>
        </form>

        {error ? (
          <div className="state-banner state-banner--error" role="alert">
            <p>{error}</p>
          </div>
        ) : null}
      </div>
    </section>
  );
}
