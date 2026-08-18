/**
 * Left sidebar navigation — visual only, drives view selection.
 */
import {
  IconBot,
  IconBox,
  IconClose,
  IconDoc,
  IconGlobe,
  IconLayout,
  IconRoute,
  IconShip,
  IconSpark,
  IconTrendUp,
} from "./Icons";

const NAV = [
  { id: "overview", label: "Overview", Icon: IconLayout },
  { id: "demand", label: "Demand Opportunities", Icon: IconGlobe, stage: 0 },
  { id: "prices", label: "Price Forecast", Icon: IconTrendUp, stage: 1 },
  { id: "logistics", label: "Logistics", Icon: IconRoute, stage: 2 },
  { id: "containers", label: "Container Priority", Icon: IconBox, stage: 3 },
  { id: "decisions", label: "Final Decisions", Icon: IconShip, stage: 4 },
  { id: "agents", label: "AI Explanations", Icon: IconBot },
  { id: "rag", label: "Trade Document Assistant", Icon: IconDoc },
];

export default function Sidebar({ activeView, onNavigate, open, onClose }) {
  return (
    <>
      <div
        className={`sidebar-backdrop ${open ? "is-open" : ""}`}
        onClick={onClose}
        aria-hidden={!open}
      />
      <aside className={`sidebar ${open ? "is-open" : ""}`} aria-label="Main navigation">
        <div className="sidebar-brand">
          <div className="sidebar-logo" aria-hidden="true">
            <IconSpark />
          </div>
          <div>
            <p className="sidebar-eyebrow">Predictive Export</p>
            <h1 className="sidebar-title">ExportIntel AI</h1>
          </div>
          <button type="button" className="sidebar-close" onClick={onClose} aria-label="Close menu">
            <IconClose />
          </button>
        </div>

        <nav className="sidebar-nav">
          {NAV.map((item) => {
            const active = activeView === item.id;
            return (
              <button
                key={item.id}
                type="button"
                className={`sidebar-link ${active ? "is-active" : ""}`}
                onClick={() => onNavigate(item.id, item.stage)}
              >
                <span className="sidebar-link-icon">
                  <item.Icon />
                </span>
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="sidebar-foot">
          <span className="status-pill status-pill--live">
            <span className="status-dot-live" />
            AI Active
          </span>
          <p>Demand · Price · Logistics · Containers</p>
        </div>
      </aside>
    </>
  );
}

export { NAV };
