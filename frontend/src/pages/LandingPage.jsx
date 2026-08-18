import { useEffect, useState } from "react";
import { ArrowRight, BrainCircuit, Container, Menu, Route, Ship, X } from "lucide-react";
import { Link } from "react-router-dom";
import { useApp } from "../context/AppContext";

const FEATURES = [
  {
    icon: BrainCircuit,
    title: "Predictive intelligence",
    text: "Demand and price signals are transformed into export-ready decisions.",
  },
  {
    icon: Route,
    title: "Route optimisation",
    text: "Compare port corridors, logistics cost and lane profitability.",
  },
  {
    icon: Container,
    title: "Container priority",
    text: "Allocate available capacity using the existing opportunity ranking.",
  },
];

export default function LandingPage() {
  const { user } = useApp();
  const [menuOpen, setMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div className="landing">
      <header className={`landing-nav ${scrolled ? "is-scrolled" : ""}`}>
        <Link className="landing-brand" to="/" aria-label="ExportIntel AI home">
          <span className="landing-brand__mark"><Ship size={18} /></span>
          <strong>EXPORTINTEL AI</strong>
        </Link>
        <nav className={`landing-nav__links ${menuOpen ? "is-open" : ""}`} aria-label="Landing navigation">
          <a href="#home" onClick={() => setMenuOpen(false)}>Home</a>
          <a href="#solutions" onClick={() => setMenuOpen(false)}>Solutions</a>
          <a href="#features" onClick={() => setMenuOpen(false)}>Features</a>
          <Link className="landing-mobile-login" to="/login">Login</Link>
        </nav>
        <div className="landing-nav__actions">
          <Link className="landing-login-link" to="/login">Login</Link>
          <Link className="xi-btn xi-btn--primary" to={user ? "/dashboard" : "/login"}>
            Get Started <ArrowRight size={15} />
          </Link>
          <button
            className="xi-icon-btn landing-menu"
            type="button"
            onClick={() => setMenuOpen((open) => !open)}
            aria-label={menuOpen ? "Close menu" : "Open menu"}
          >
            {menuOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </header>

      <main>
        <section className="landing-hero" id="home">
          <div className="landing-hero__map" aria-hidden="true">
            <span className="route-dot dot-a" />
            <span className="route-dot dot-b" />
            <span className="route-dot dot-c" />
            <i className="route-arc arc-a" />
            <i className="route-arc arc-b" />
          </div>
          <div className="landing-hero__image" role="img" aria-label="International cargo ship and export terminal" />
          <div className="landing-hero__overlay" />
          <div className="landing-hero__content">
            <p className="landing-eyebrow"><span /> AI-POWERED EXPORT INTELLIGENCE</p>
            <h1>
              Smart Export Decisions.
              <span>Stronger Global Future.</span>
            </h1>
            <p className="landing-hero__copy">
              Predict demand, forecast commodity prices, optimise logistics and generate
              AI-powered export recommendations from one intelligent platform.
            </p>
            <div className="landing-hero__actions">
              <Link className="xi-btn xi-btn--primary landing-cta" to={user ? "/dashboard" : "/login"}>
                Explore Dashboard <ArrowRight size={17} />
              </Link>
              <a className="xi-btn xi-btn--ghost landing-cta" href="#features">Learn More</a>
            </div>
          </div>

          <div className="landing-stats" aria-label="Platform capabilities">
            <div><strong>Not available</strong><span>Countries analysed</span></div>
            <div><strong>Not available</strong><span>Commodities analysed</span></div>
            <div><strong>5</strong><span>Active AI agents</span></div>
            <div><strong>Next month</strong><span>Forecast horizon</span></div>
            <div><strong>{user ? "Session active" : "Ready"}</strong><span>Analysis status</span></div>
          </div>
        </section>

        <section className="landing-section" id="features">
          <p className="landing-eyebrow"><span /> INTELLIGENCE WORKFLOW</p>
          <h2>From market signal to shipment decision.</h2>
          <div className="landing-feature-grid">
            {FEATURES.map(({ icon: Icon, title, text }) => (
              <article key={title}>
                <span><Icon size={20} /></span>
                <h3>{title}</h3>
                <p>{text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="landing-section landing-about" id="solutions">
          <div>
            <p className="landing-eyebrow"><span /> ONE CONNECTED PLATFORM</p>
            <h2>Demand, price, route and capacity in one decision flow.</h2>
          </div>
          <Link className="xi-btn xi-btn--primary" to={user ? "/dashboard" : "/login"}>
            Open Platform <ArrowRight size={16} />
          </Link>
        </section>
        <footer className="landing-footer">
          <span>EXPORTINTEL AI</span>
          <span>Predictive Export Intelligence & Logistics Optimisation Platform</span>
        </footer>
      </main>
    </div>
  );
}
