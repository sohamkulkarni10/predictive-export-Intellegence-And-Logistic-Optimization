import { Play, RefreshCw, Settings, Sparkles } from "lucide-react";
import { MobileMenuButton } from "./Sidebar";
import { fmtDate } from "../../utils";
import { StatusBadge } from "../common/Primitives";

function statusTone(status) {
  if (status === "completed") return "success";
  if (status === "failed") return "danger";
  if (status === "idle") return "neutral";
  return "info";
}

function statusLabel(status, isRunning) {
  if (isRunning) return "Analysis running";
  if (status === "completed") return "Completed";
  if (status === "failed") return "Failed";
  return "Idle";
}

export default function TopHeader({
  horizon,
  generatedAt,
  analysisStatus,
  isRunning,
  activeAgent,
  onOpenMenu,
  onRun,
  onRefresh,
  onNavigateRun,
}) {
  return (
    <header className="xi-header">
      <div className="xi-header__left">
        <MobileMenuButton onClick={onOpenMenu} />
        <div>
          <h1 className="xi-header__title">Export Intelligence Command Centre</h1>
          <p className="xi-header__sub">
            Demand, pricing, logistics and AI decision support
          </p>
          <div className="xi-header__meta">
            <span>Horizon {horizon || "—"}</span>
            <span>{generatedAt ? fmtDate(generatedAt) : "Not generated"}</span>
            <StatusBadge tone={statusTone(analysisStatus)}>
              {statusLabel(analysisStatus, isRunning)}
            </StatusBadge>
            {isRunning && activeAgent ? (
              <span className="xi-header__agent" aria-live="polite">
                {activeAgent}
              </span>
            ) : null}
          </div>
        </div>
      </div>
      <div className="xi-header__right">
        <button
          type="button"
          className="xi-btn xi-btn--ghost"
          onClick={onRefresh}
          aria-label="Refresh data"
        >
          <RefreshCw size={16} />
          <span className="xi-hide-sm">Refresh</span>
        </button>
        <button type="button" className="xi-icon-btn" aria-label="Settings">
          <Settings size={16} />
        </button>
        <button
          type="button"
          className="xi-btn xi-btn--primary"
          onClick={isRunning ? undefined : onRun || onNavigateRun}
          disabled={isRunning}
        >
          {isRunning ? (
            <>
              <span className="xi-spinner" aria-hidden="true" />
              Analysis Running
            </>
          ) : (
            <>
              <Sparkles size={16} />
              Run Analysis
            </>
          )}
        </button>
      </div>
    </header>
  );
}

export function RunAnalysisButton({ isRunning, onClick, className = "" }) {
  return (
    <button
      type="button"
      className={`xi-btn xi-btn--primary ${className}`}
      onClick={onClick}
      disabled={isRunning}
    >
      {isRunning ? (
        <>
          <span className="xi-spinner" aria-hidden="true" />
          Analysis Running
        </>
      ) : (
        <>
          <Play size={16} />
          Run Analysis
        </>
      )}
    </button>
  );
}
