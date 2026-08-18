import {
  Bot,
  Boxes,
  BrainCircuit,
  ChevronLeft,
  ChevronRight,
  Gauge,
  LayoutDashboard,
  LogOut,
  Map,
  Ship,
  TrendingUp,
  X,
} from "lucide-react";
import { NavLink } from "react-router-dom";

const ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/demand", label: "Demand Prediction", icon: TrendingUp },
  { to: "/price", label: "Price Prediction", icon: Gauge },
  { to: "/logistics", label: "Logistics Optimisation", icon: Map },
  { to: "/containers", label: "Container Priority", icon: Boxes },
  { to: "/global-trade", label: "Global Trade Overview", icon: Ship },
  { to: "/assistant", label: "AI Assistant", icon: Bot },
  { to: "/agents", label: "Agent Reasoning", icon: BrainCircuit },
];

export default function DashboardSidebar({
  collapsed,
  mobileOpen,
  onCloseMobile,
  onToggleCollapse,
  horizon,
  modelOnline,
  onLogout,
}) {
  return (
    <>
      <button
        className={`dash-sidebar-backdrop ${mobileOpen ? "is-open" : ""}`}
        onClick={onCloseMobile}
        aria-label="Close navigation"
        type="button"
      />
      <aside className={`dash-sidebar ${collapsed ? "is-collapsed" : ""} ${mobileOpen ? "is-open" : ""}`}>
        <div className="dash-sidebar__brand">
          <span><Ship size={19} /></span>
          {!collapsed && (
            <div>
              <strong>EXPORTINTEL AI</strong>
              <small><i /> AI ONLINE</small>
            </div>
          )}
          <button className="xi-icon-btn dash-sidebar__mobile-close" type="button" onClick={onCloseMobile} aria-label="Close sidebar">
            <X size={17} />
          </button>
        </div>

        <nav className="dash-sidebar__nav" aria-label="Dashboard navigation">
          <p className="dash-sidebar__group">{collapsed ? "•••" : "INTELLIGENCE PLATFORM"}</p>
          {ITEMS.map(({ to, label, icon: Icon, end }, index) => (
            <NavLink
              key={`${label}-${index}`}
              to={to}
              end={end}
              className={({ isActive }) => `dash-sidebar__item ${isActive ? "is-active" : ""}`}
              title={collapsed ? label : undefined}
              onClick={onCloseMobile}
            >
              <Icon size={17} />
              {!collapsed && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>

        <div className="dash-sidebar__footer">
          {!collapsed && (
            <div className="dash-sidebar__status">
              <div><span>Forecast horizon</span><strong>{horizon || "Not available"}</strong></div>
              <div><span>Model status</span><strong className={modelOnline ? "is-online" : ""}>{modelOnline ? "Ready" : "Awaiting run"}</strong></div>
            </div>
          )}
          <button className="dash-sidebar__item" type="button" onClick={onLogout} title={collapsed ? "Logout" : undefined}>
            <LogOut size={17} />
            {!collapsed && <span>Logout</span>}
          </button>
          <button className="dash-sidebar__collapse" type="button" onClick={onToggleCollapse} aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}>
            {collapsed ? <ChevronRight size={16} /> : <><ChevronLeft size={16} /><span>Collapse sidebar</span></>}
          </button>
        </div>
      </aside>
    </>
  );
}
