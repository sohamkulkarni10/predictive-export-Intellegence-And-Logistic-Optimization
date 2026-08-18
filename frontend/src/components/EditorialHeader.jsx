/**
 * Sticky editorial header + mobile full-screen menu.
 */
import { useEffect, useState } from "react";

const LINKS = [
  { id: "intelligence", label: "Intelligence" },
  { id: "opportunities", label: "Opportunities" },
  { id: "logistics", label: "Logistics" },
  { id: "agents", label: "AI Agents" },
];

export default function EditorialHeader({
  horizon,
  loading,
  user,
  onRun,
  onLogout,
  onScrollTo,
}) {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  function go(id) {
    setOpen(false);
    onScrollTo(id);
  }

  return (
    <>
      <header className={`ed-nav ${scrolled ? "is-scrolled" : ""}`}>
        <button type="button" className="ed-brand" onClick={() => go("hero")}>
          <span className="ed-logo" aria-hidden="true">
            <span />
            <span />
          </span>
          <span className="ed-brand-text">EXPORTINTEL AI</span>
        </button>

        <nav className="ed-nav-center" aria-label="Primary">
          {LINKS.map((l) => (
            <button key={l.id} type="button" className="ed-nav-link" onClick={() => go(l.id)}>
              {l.label}
            </button>
          ))}
        </nav>

        <div className="ed-nav-right">
          {horizon ? <span className="ed-pill">{horizon}</span> : null}
          <span className="ed-pill ed-pill--live">
            <i /> AI ONLINE
          </span>
          <button type="button" className="ed-cta ed-cta--nav" onClick={onRun} disabled={loading}>
            {loading ? "RUNNING…" : "RUN ANALYSIS"}
          </button>
          <button type="button" className="ed-ghost-btn desktop-only" onClick={onLogout} title={user}>
            OUT
          </button>
          <button
            type="button"
            className="ed-burger"
            aria-label="Open menu"
            onClick={() => setOpen(true)}
          >
            <span />
            <span />
          </button>
        </div>
      </header>

      <div className={`ed-mobile ${open ? "is-open" : ""}`} aria-hidden={!open}>
        <div className="ed-mobile-top">
          <span className="ed-brand-text">EXPORTINTEL AI</span>
          <button type="button" className="ed-ghost-btn" onClick={() => setOpen(false)}>
            CLOSE
          </button>
        </div>
        <nav className="ed-mobile-nav">
          {[
            ...LINKS,
            { id: "prices", label: "Prices" },
            { id: "containers", label: "Containers" },
            { id: "assistant", label: "Trade Assistant" },
            { id: "decision", label: "Final Decision" },
          ].map((l) => (
            <button key={l.id} type="button" onClick={() => go(l.id)}>
              {l.label}
            </button>
          ))}
        </nav>
        <button type="button" className="ed-cta ed-cta--block" onClick={() => { setOpen(false); onRun(); }} disabled={loading}>
          RUN EXPORT ANALYSIS
        </button>
        <button type="button" className="ed-ghost-btn" onClick={onLogout}>
          Sign out · {user}
        </button>
      </div>
    </>
  );
}
