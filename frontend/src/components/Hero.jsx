/**
 * Brand hero — Export Intelligence Dashboard.
 */
export default function Hero({ horizon, recommendation, onRunClick }) {
  return (
    <header className="hero">
      <div className="hero-pattern" aria-hidden="true" />
      <div className="hero-content">
        <p className="hero-eyebrow">Predictive Export Intelligence &amp; Logistics Optimisation</p>
        <h1 className="brand">Export Intelligence Dashboard</h1>
        <p className="tagline">
          Combine demand signals, mandi price forecasts, port routing and container allocation —
          with Groq llama explanations for Indian exporters.
        </p>
        <div className="hero-meta">
          {horizon ? <span className="chip chip-light">Horizon {horizon}</span> : null}
          {recommendation ? (
            <span className="chip chip-light">Lead: {recommendation}</span>
          ) : (
            <span className="chip chip-light">Paste news and run analysis</span>
          )}
          {onRunClick ? (
            <button type="button" className="btn-primary hero-cta" onClick={onRunClick}>
              Jump to analysis inputs
            </button>
          ) : null}
        </div>
      </div>
    </header>
  );
}
