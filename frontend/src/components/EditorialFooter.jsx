/**
 * Large black editorial footer.
 */
export default function EditorialFooter({ onScrollTo }) {
  const links = [
    { id: "opportunities", label: "Demand" },
    { id: "prices", label: "Prices" },
    { id: "logistics", label: "Logistics" },
    { id: "containers", label: "Containers" },
    { id: "agents", label: "AI Agents" },
    { id: "assistant", label: "Trade Assistant" },
  ];

  return (
    <footer className="ed-footer">
      <div className="ed-wrap ed-footer-grid">
        <div>
          <div className="ed-brand ed-brand--footer">
            <span className="ed-logo" aria-hidden="true">
              <span />
              <span />
            </span>
            <span className="ed-brand-text">EXPORTINTEL AI</span>
          </div>
          <p className="ed-footer-copy">
            AI-powered export intelligence for demand, pricing, logistics and trade decisions.
          </p>
        </div>
        <nav className="ed-footer-nav">
          {links.map((l) => (
            <button key={l.id} type="button" onClick={() => onScrollTo(l.id)}>
              {l.label}
            </button>
          ))}
        </nav>
      </div>
      <div className="ed-footer-bottom">
        <p>Predictive Export Intelligence &amp; Logistics Optimisation Platform</p>
      </div>
    </footer>
  );
}
