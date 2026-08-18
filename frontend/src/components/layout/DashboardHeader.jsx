import { Bell, CheckCircle2, Menu, Search, Sparkles, UserCircle2 } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { useApp } from "../../context/AppContext";

const PAGE_META = {
  "/dashboard": ["Dashboard", "Overview"],
  "/demand": ["Demand Prediction", "Intelligence / Demand"],
  "/price": ["Price Prediction", "Intelligence / Price"],
  "/logistics": ["Logistics Optimisation", "Operations / Routes"],
  "/containers": ["Container Priority", "Operations / Allocation"],
  "/assistant": ["AI Assistant", "AI System / Assistant"],
  "/global-trade": ["Global Trade Overview", "Intelligence / Global Trade"],
  "/agents": ["Agent Reasoning", "AI System / Agents"],
};

export default function DashboardHeader({ onOpenMenu }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, analysis } = useApp();
  const [title, breadcrumb] = PAGE_META[location.pathname] || ["Export Intelligence", "Platform"];

  function handleRun() {
    if (analysis.isRunning) return;
    // News Agent auto-fetches live headlines — no paste required
    analysis.runAnalysis();
    navigate("/dashboard");
  }

  const buttonLabel =
    analysis.analysisStatus === "completed"
      ? "Analysis Complete"
      : analysis.analysisStatus === "failed"
        ? "Retry Analysis"
        : analysis.isRunning
          ? "Analysing…"
          : "Run Analysis";

  return (
    <header className="dash-header">
      <div className="dash-header__title">
        <button className="xi-icon-btn dash-header__menu" type="button" onClick={onOpenMenu} aria-label="Open navigation">
          <Menu size={18} />
        </button>
        <div>
          <p>{breadcrumb}</p>
          <h1>{title}</h1>
        </div>
      </div>

      <div className="dash-header__actions">
        <label className="dash-search">
          <Search size={15} />
          <input aria-label="Search dashboard" placeholder="Search intelligence…" />
        </label>
        <button className="xi-icon-btn" type="button" aria-label="Notifications"><Bell size={17} /></button>
        <span className={`dash-status dash-status--${analysis.analysisStatus}`}>
          <i />
          {analysis.isRunning ? analysis.activeAgent || "Analysing" : analysis.analysisStatus}
        </span>
        <button className="dash-user" type="button" aria-label="Open profile">
          <UserCircle2 size={22} />
          <span><strong>{user}</strong><small>Export analyst</small></span>
        </button>
        <button
          className={`xi-btn xi-btn--primary dash-run ${analysis.analysisStatus === "completed" ? "is-complete" : ""}`}
          type="button"
          onClick={handleRun}
          disabled={analysis.isRunning}
        >
          {analysis.isRunning ? <span className="xi-spinner" /> : analysis.analysisStatus === "completed" ? <CheckCircle2 size={16} /> : <Sparkles size={16} />}
          {buttonLabel}
        </button>
      </div>
    </header>
  );
}
