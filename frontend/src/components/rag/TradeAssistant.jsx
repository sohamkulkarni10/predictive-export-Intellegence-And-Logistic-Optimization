import { Bot, Send, Trash2, User } from "lucide-react";
import { EmptyState, Panel } from "../common/Primitives";

const CHIPS = [
  "Onion export documents",
  "IEC requirements",
  "CIF vs FOB",
  "Phytosanitary certificate",
  "Wheat HS code",
  "Vietnam import tariff",
];

export default function TradeAssistant({
  question,
  onQuestionChange,
  onAsk,
  loading,
  rag,
  lastAsked,
  error,
  messages = [],
  onClear,
}) {
  return (
    <Panel
      id="panel-rag"
      title="Trade Document Assistant"
      subtitle="Ask about IEC, HS codes, CIF/FOB, tariffs, certificates and container rules"
      actions={messages.length ? (
        <button type="button" className="xi-btn xi-btn--ghost xi-btn--sm" onClick={onClear}>
          <Trash2 size={14} /> Clear conversation
        </button>
      ) : null}
    >
      <div className="xi-chips">
        {CHIPS.map((chip) => (
          <button
            key={chip}
            type="button"
            className="xi-chip"
            onClick={() => onQuestionChange(chip)}
          >
            {chip}
          </button>
        ))}
      </div>

      <div className="assistant-chat" aria-live="polite">
        {!messages.length && !rag ? (
          <EmptyState
            title="How can I help with your export plan?"
            description="Ask a trade-document, compliance, HS-code or route question. Answers come from the existing RAG endpoint."
          />
        ) : null}
        {messages.map((message) => (
          <div className={`assistant-message is-${message.role}`} key={message.id}>
            <span>{message.role === "assistant" ? <Bot size={16} /> : <User size={16} />}</span>
            <div>
              <strong>{message.role === "assistant" ? "ExportIntel Assistant" : "You"}</strong>
              <p>{message.content || "Not available"}</p>
              {Array.isArray(message.sources) && message.sources.length ? (
                <ul className="xi-rag-sources">
                  {message.sources.map((source, index) => (
                    <li key={index}>{source.title || source.source || "Source"}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          </div>
        ))}
        {loading ? (
          <div className="assistant-message is-assistant is-typing">
            <span><Bot size={16} /></span>
            <div><strong>ExportIntel Assistant</strong><p><i /><i /><i /></p></div>
          </div>
        ) : null}
      </div>

      {error ? (
        <div className="xi-error" role="alert">
          <strong>Assistant error</strong>
          <p>{error}</p>
          <button type="button" className="xi-btn xi-btn--ghost" onClick={onAsk}>
            Retry
          </button>
        </div>
      ) : null}

      {rag && !messages.length ? (
        <div className="xi-rag-answer">
          {lastAsked ? <p className="xi-rag-q">Q: {lastAsked}</p> : null}
          <p>{rag.answer || "Not available"}</p>
          {Array.isArray(rag.sources) && rag.sources.length > 0 ? (
            <ul className="xi-rag-sources">
              {rag.sources.map((s, i) => (
                <li key={i}>
                  {s.title || s.source || "Source"}
                  {s.score != null ? ` · ${Number(s.score).toFixed(2)}` : ""}
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}

      <form
        className="xi-rag-form"
        onSubmit={(e) => {
          e.preventDefault();
          onAsk();
        }}
      >
        <label className="sr-only" htmlFor="rag-q">Question</label>
        <input
          id="rag-q"
          value={question}
          onChange={(e) => onQuestionChange(e.target.value)}
          placeholder="Ask a trade compliance or documentation question…"
          disabled={loading}
        />
        <button type="submit" className="xi-btn xi-btn--primary" disabled={loading || !question.trim()} aria-label="Send question">
          {loading ? <span className="xi-spinner" /> : <Send size={16} />}
        </button>
      </form>
    </Panel>
  );
}
