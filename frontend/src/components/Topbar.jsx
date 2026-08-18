/**
 * Sticky top bar — page title + horizon + user.
 */
import { IconLogout, IconMenu } from "./Icons";

const TITLES = {
  overview: "Export Intelligence Dashboard",
  demand: "Demand Opportunities",
  prices: "Price Forecast",
  logistics: "Logistics Optimisation",
  containers: "Container Priority",
  decisions: "Final Decisions",
  agents: "AI Explanations",
  rag: "Trade Document Assistant",
};

function IconSearch(props) {
  return (
    <svg viewBox="0 0 24 24" width="1em" height="1em" fill="none" stroke="currentColor" strokeWidth="1.8" {...props}>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </svg>
  );
}

function IconBell(props) {
  return (
    <svg viewBox="0 0 24 24" width="1em" height="1em" fill="none" stroke="currentColor" strokeWidth="1.8" {...props}>
      <path d="M6 9a6 6 0 0 1 12 0c0 7 3 7 3 7H3s3 0 3-7" />
      <path d="M10 19a2 2 0 0 0 4 0" />
    </svg>
  );
}

export default function Topbar({
  activeView,
  user,
  horizon,
  llmModel,
  onMenu,
  onLogout,
}) {
  return (
    <header className="topbar">
      <div className="topbar-left">
        <button type="button" className="icon-btn mobile-only" onClick={onMenu} aria-label="Open menu">
          <IconMenu />
        </button>
        <div>
          <p className="topbar-kicker">Export Intelligence Platform</p>
          <h2 className="topbar-title">{TITLES[activeView] || "Dashboard"}</h2>
        </div>
      </div>

      <div className="topbar-right">
        {horizon ? <span className="chip chip-blue">Horizon {horizon}</span> : null}
        <span className="chip chip-green">
          <span className="status-dot-live" />
          AI Active
        </span>
        {llmModel ? <span className="chip chip-cyan">{llmModel}</span> : null}
        <button type="button" className="icon-btn desktop-only" aria-label="Search" title="Search">
          <IconSearch />
        </button>
        <button type="button" className="icon-btn desktop-only" aria-label="Notifications" title="Notifications">
          <IconBell />
        </button>
        <div className="user-pill">
          <span className="user-avatar" aria-hidden="true">
            {(user || "E").slice(0, 1).toUpperCase()}
          </span>
          <span className="user-name">{user}</span>
          <button type="button" className="icon-btn" onClick={onLogout} aria-label="Logout" title="Logout">
            <IconLogout />
          </button>
        </div>
      </div>
    </header>
  );
}
