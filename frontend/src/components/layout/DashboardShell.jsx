import { useState } from "react";
import { Outlet } from "react-router-dom";
import { useApp } from "../../context/AppContext";
import DashboardHeader from "./DashboardHeader";
import DashboardSidebar from "./DashboardSidebar";

export default function DashboardShell() {
  const { signOut, analysis } = useApp();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className={`dash-app ${collapsed ? "is-collapsed" : ""}`}>
      <DashboardSidebar
        collapsed={collapsed}
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
        onToggleCollapse={() => setCollapsed((value) => !value)}
        horizon={analysis.dashboard?.horizon}
        modelOnline={Boolean(analysis.dashboard?.llm?.enabled)}
        onLogout={signOut}
      />
      <div className="dash-main">
        <DashboardHeader onOpenMenu={() => setMobileOpen(true)} />
        <main className="dash-content">
          <Outlet />
        </main>
      </div>
      {analysis.toast ? (
        <div className={`xi-toast xi-toast--${analysis.toast.type}`} role="status">
          <span>{analysis.toast.message}</span>
          <button type="button" onClick={() => analysis.setToast(null)} aria-label="Dismiss notification">×</button>
        </div>
      ) : null}
    </div>
  );
}
