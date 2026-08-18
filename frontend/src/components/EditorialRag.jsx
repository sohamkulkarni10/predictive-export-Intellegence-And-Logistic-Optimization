/**
 * Trade Document Assistant — same RAG props, editorial AI search UI.
 */
const CHIPS = [
  "Onion export documents",
  "IEC registration",
  "CIF vs FOB",
  "Phytosanitary certificate",
  "Wheat HS code",
  "Vietnam tariff",
];

export default function EditorialRag({
  question,
  onQuestionChange,
  onAsk,
  loading,
  rag,
  lastAsked,
  error,
}) {
  return (
    <section className="ed-section ed-section--lime" id="assistant">
      <div className="ed-wrap">
        <div className="ed-section-head">
          <span className="ed-num">06</span>
          <div>
            <p className="ed-label">TRADE DOCUMENT INTELLIGENCE</p>
            <h2 className="ed-h2">Ask before you export.</h2>
            <p className="ed-lead">
              IEC, HS codes, CIF/FOB, phytosanitary certificates, destination tariffs, and container rules.
            </p>
          </div>
        </div>

        <form
          className="ed-ask"
          onSubmit={(e) => {
            e.preventDefault();
            onAsk();
          }}
        >
          <input
            value={question}
            onChange={(e) => onQuestionChange(e.target.value)}
            placeholder="What documents are needed to export onions from India?"
            disabled={loading}
            aria-label="Trade document question"
          />
          <button type="submit" className="ed-ask-btn" disabled={loading || !question.trim()}>
            {loading ? "…" : "ASK AI"}
          </button>
        </form>

        <div className="ed-chips">
          {CHIPS.map((chip) => (
            <button key={chip} type="button" onClick={() => onQuestionChange(chip)}>
              {chip.toUpperCase()}
            </button>
          ))}
        </div>

        {!lastAsked && !rag?.answer && !error ? (
          <p className="ed-empty">Ask a question to search the trade-document knowledge base.</p>
        ) : null}

        {lastAsked ? (
          <div className="ed-answer-block">
            <p className="ed-label">YOU ASKED</p>
            <p className="ed-q">{lastAsked}</p>
          </div>
        ) : null}

        {loading ? <div className="ed-skeleton" aria-busy="true" /> : null}

        {rag?.answer ? (
          <div className="ed-answer-block ed-answer-block--out">
            <p className="ed-label">EXPORTINTEL AI</p>
            <p className="ed-a">{rag.answer}</p>
            {(rag.sources || []).length > 0 ? (
              <div className="ed-sources">
                {(rag.sources || []).map((s) => (
                  <span key={`${s.title}-${s.score}`}>
                    {s.title}
                    {typeof s.score === "number" ? ` · ${s.score.toFixed(2)}` : ""}
                  </span>
                ))}
              </div>
            ) : null}
          </div>
        ) : null}

        {error ? (
          <div className="ed-error" role="alert">
            <strong>Request failed</strong>
            <p>{error}</p>
            <button type="button" className="ed-cta ed-cta--ghost" onClick={onAsk}>
              RETRY
            </button>
          </div>
        ) : null}
      </div>
    </section>
  );
}
