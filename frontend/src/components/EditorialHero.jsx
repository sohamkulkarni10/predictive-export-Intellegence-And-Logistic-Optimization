/**
 * Full-viewport editorial hero.
 */
export default function EditorialHero({
  horizon,
  generatedAt,
  llm,
  loading,
  onRun,
  onExplore,
}) {
  return (
    <section className="ed-hero" id="hero">
      <div className="ed-hero-grid" aria-hidden="true">
        <svg className="ed-hero-svg" viewBox="0 0 1200 700" preserveAspectRatio="xMidYMid slice">
          <defs>
            <linearGradient id="routeStroke" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#DFFF4F" stopOpacity="0" />
              <stop offset="50%" stopColor="#DFFF4F" stopOpacity="0.55" />
              <stop offset="100%" stopColor="#FF6B2C" stopOpacity="0" />
            </linearGradient>
          </defs>
          {Array.from({ length: 12 }).map((_, i) => (
            <line key={`h${i}`} x1="0" y1={40 + i * 55} x2="1200" y2={40 + i * 55} className="ed-lat" />
          ))}
          {Array.from({ length: 18 }).map((_, i) => (
            <line key={`v${i}`} x1={30 + i * 65} y1="0" x2={30 + i * 65} y2="700" className="ed-lng" />
          ))}
          <path
            d="M180 420 C 340 300, 520 280, 680 340 S 980 420, 1080 300"
            fill="none"
            stroke="url(#routeStroke)"
            strokeWidth="1.5"
            className="ed-route-path"
          />
          <path
            d="M140 500 C 380 460, 560 520, 760 480 S 1000 380, 1120 420"
            fill="none"
            stroke="rgba(120,148,255,0.45)"
            strokeWidth="1.2"
            className="ed-route-path ed-route-path--alt"
          />
          <circle cx="180" cy="420" r="3.5" className="ed-port-dot" />
          <circle cx="680" cy="340" r="3.5" className="ed-port-dot" />
          <circle cx="1080" cy="300" r="3.5" className="ed-port-dot" />
          <circle r="3" className="ed-ship-dot">
            <animateMotion dur="14s" repeatCount="indefinite" path="M180 420 C 340 300, 520 280, 680 340 S 980 420, 1080 300" />
          </circle>
        </svg>
      </div>

      <div className="ed-hero-inner">
        <p className="ed-kicker">PREDICTIVE EXPORT INTELLIGENCE</p>
        <h1 className="ed-hero-title">
          EXPORT SMARTER.
          <br />
          DECIDE WITH <span className="ed-accent">AI</span>.
        </h1>
        <p className="ed-hero-sub">
          Demand prediction, price forecasting, route optimisation and AI-powered trade
          intelligence—combined in one export decision system.
        </p>

        <div className="ed-hero-actions">
          <button type="button" className="ed-cta ed-cta--lime" onClick={onRun} disabled={loading}>
            {loading ? "RUNNING PIPELINE…" : "RUN EXPORT ANALYSIS"}
            <span className="ed-arrow" aria-hidden="true">→</span>
          </button>
          <button type="button" className="ed-cta ed-cta--ghost" onClick={onExplore}>
            EXPLORE OPPORTUNITIES
          </button>
        </div>

        <div className="ed-hero-meta">
          <div>
            <span className="ed-meta-label">HORIZON</span>
            <strong>{horizon || "Awaiting run"}</strong>
          </div>
          <div>
            <span className="ed-meta-label">AI AGENTS</span>
            <strong>{llm?.source === "groq" ? "Groq online" : "Ready"}</strong>
          </div>
          <div>
            <span className="ed-meta-label">DATA</span>
            <strong>Models + trade costs</strong>
          </div>
          <div>
            <span className="ed-meta-label">LAST RUN</span>
            <strong>{generatedAt ? String(generatedAt).slice(0, 16) : "—"}</strong>
          </div>
        </div>
      </div>

      <div className="ed-hero-peek" aria-hidden="true" />
    </section>
  );
}
