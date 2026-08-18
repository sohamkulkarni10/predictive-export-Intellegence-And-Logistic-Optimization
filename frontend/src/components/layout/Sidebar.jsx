import {
  Activity,
  Boxes,
  Brain,
  ChevronLeft,
  ChevronRight,
  Database,
  FileText,
  History,
  LayoutDashboard,
  MapPinned,
  Menu,
  MessageSquareText,
  Play,
  Settings,
  TrendingUp,
  X,
} from "lucide-react";

const NAV = [
  {
    group: "COMMAND CENTRE",
    items: [
      { id: "overview", label: "Overview", icon: LayoutDashboard },
      { id: "run", label: "Run Analysis", icon: Play },
      { id: "history", label: "Analysis History", icon: History },
    ],
  },
  {
    group: "INTELLIGENCE",
    items: [
      { id: "demand", label: "Demand Opportunities", icon: TrendingUp },
      { id: "price", label: "Price Forecast", icon: Activity },
      { id: "logistics", label: "Route Optimisation", icon: MapPinned },
      { id: "containers", label: "Container Priority", icon: Boxes },
    ],
  },
  {
    group: "AI SYSTEM",
    items: [
      { id: "agents", label: "Agent Reasoning", icon: Brain },
      { id: "rag", label: "Trade Assistant", icon: MessageSquareText },
      { id: "sources", label: "Data Sources", icon: Database },
    ],
  },
];

export default function Sidebar({
  activeView,
  onNavigate,
  collapsed,
  onToggleCollapse,
  mobileOpen,
  onCloseMobile,
  horizon,
  llmOnline,
}) {
  return (
    <>
      <div
        className={`xi-sidebar-backdrop ${mobileOpen ? "is-open" : ""}`}
        onClick={onCloseMobile}
        aria-hidden={!mobileOpen}
      />
      <aside
        className={`xi-sidebar ${collapsed ? "is-collapsed" : ""} ${mobileOpen ? "is-open" : ""}`}
        aria-label="Main navigation"
      >
        <div className="xi-brand">
          <div className="xi-brand__mark" aria-hidden="true">
            <FileText size={18} />
          </div>
          {!collapsed && (
            <div className="xi-brand__text">
              <strong>EXPORTINTEL AI</strong>
              <span className="xi-brand__status">
                <i className="xi-dot xi-dot--live" /> SYSTEM ONLINE
              </span>
            </div>
          )}
          <button
            type="button"
            className="xi-icon-btn xi-sidebar__close"
            onClick={onCloseMobile}
            aria-label="Close menu"
          >
            <X size={18} />
          </button>
        </div>

        <nav className="xi-nav">
          {NAV.map((group) => (
            <div key={group.group} className="xi-nav__group">
              {!collapsed && <p className="xi-nav__label">{group.group}</p>}
              <ul>
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const active = activeView === item.id;
                  return (
                    <li key={item.id}>
                      <button
                        type="button"
                        className={`xi-nav__item ${active ? "is-active" : ""}`}
                        onClick={() => onNavigate(item.id)}
                        title={collapsed ? item.label : undefined}
                        aria-current={active ? "page" : undefined}
                      >
                        <Icon size={18} aria-hidden="true" />
                        {!collapsed && <span>{item.label}</span>}
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>

        <div className="xi-sidebar__foot">
          {!collapsed && (
            <div className="xi-sidebar__meta">
              <div>
                <span>Forecast horizon</span>
                <strong>{horizon || "—"}</strong>
              </div>
              <div>
                <span>LLM status</span>
                <strong className={llmOnline ? "ok" : "warn"}>
                  {llmOnline ? "Groq online" : "Offline / unknown"}
                </strong>
              </div>
            </div>
          )}
          <div className="xi-sidebar__tools">
            <button type="button" className="xi-icon-btn" aria-label="Settings" title="Settings">
              <Settings size={16} />
            </button>
            <button
              type="button"
              className="xi-icon-btn xi-collapse-btn"
              onClick={onToggleCollapse}
              aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
              title={collapsed ? "Expand" : "Collapse"}
            >
              {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}

export function MobileMenuButton({ onClick }) {
  return (
    <button type="button" className="xi-icon-btn xi-mobile-menu" onClick={onClick} aria-label="Open menu">
      <Menu size={18} />
    </button>
  );
}
