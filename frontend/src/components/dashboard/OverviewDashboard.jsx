import { CheckCircle2, CircleAlert, History, Play, Radio } from "lucide-react";
import { fmtDate } from "../../utils";
import { EmptyState, Panel, ProgressBar } from "../common/Primitives";
import { AgentPipeline } from "../layout/RightInsightRail";
import { DecisionSummaryCards } from "../dashboard/DecisionSummaryCards";
import { RunAnalysisButton } from "../layout/TopHeader";

const FLOW = ["Demand", "Price", "Logistics", "Container", "Supervisor"];

export function AnalysisActivityFeed({ activity }) {
  if (!activity?.length) {
    return (
      <Panel title="Analysis Activity" subtitle="Live session log for this browser run">
        <p className="xi-muted">Activity items appear as each frontend stage completes.</p>
      </Panel>
    );
  }
  return (
    <Panel title="Analysis Activity" subtitle="Generated from the current frontend analysis session">
      <ul className="xi-activity-list">
        {activity.map((item) => (
          <li key={item.id} className="xi-activity-row">
            <div className="xi-activity-row__main static">
              <span className="xi-avatar xi-avatar--sm">
                {item.status === "error" ? <CircleAlert size={14} /> : <CheckCircle2 size={14} />}
              </span>
              <span className="xi-activity-row__body">
                <strong>{item.title}</strong>
                <em>{item.description}</em>
              </span>
              <span className="xi-activity-row__score">
                <small>{fmtDate(item.at)}</small>
              </span>
            </div>
          </li>
        ))}
      </ul>
    </Panel>
  );
}

export function RunAnalysisWorkspace({
  demandNews,
  priceNews,
  containers,
  containerType,
  onDemandChange,
  onPriceChange,
  onContainersChange,
  onContainerTypeChange,
  onLoadSamples,
  onFetchLiveNews,
  onRun,
  isRunning,
  newsLoading,
  error,
  progress,
  activeAgent,
}) {
  return (
    <Panel
      id="panel-run"
      title="Run Analysis"
      subtitle="Click Fetch Live News to refresh headlines, or Run Analysis (auto-fetches too)"
    >
      <div className="xi-analysis-grid">
        <label className="xi-field">
          <span>Demand news (auto-filled from live APIs)</span>
          <textarea
            value={demandNews}
            onChange={(e) => onDemandChange(e.target.value)}
            placeholder="Will auto-fetch country + commodity demand news…"
            disabled={isRunning || newsLoading}
          />
        </label>
        <label className="xi-field">
          <span>India commodity price news (auto-filled)</span>
          <textarea
            value={priceNews}
            onChange={(e) => onPriceChange(e.target.value)}
            placeholder="Will auto-fetch India mandi / commodity price news…"
            disabled={isRunning || newsLoading}
          />
        </label>
      </div>
      <div className="xi-analysis-controls">
        <label className="xi-inline">
          <span>Containers</span>
          <input
            type="number"
            min={1}
            max={50}
            value={containers}
            onChange={(e) => onContainersChange(e.target.value)}
            disabled={isRunning || newsLoading}
          />
        </label>
        <label className="xi-inline">
          <span>Type</span>
          <select
            value={containerType}
            onChange={(e) => onContainerTypeChange(e.target.value)}
            disabled={isRunning || newsLoading}
          >
            <option value="20FT">20FT</option>
            <option value="40FT">40FT</option>
          </select>
        </label>
        <button
          type="button"
          className="xi-btn xi-btn--ghost"
          onClick={onFetchLiveNews}
          disabled={isRunning || newsLoading || !onFetchLiveNews}
        >
          {newsLoading ? (
            <>
              <span className="xi-spinner" aria-hidden="true" />
              Fetching news…
            </>
          ) : (
            "Fetch Live News"
          )}
        </button>
        <button type="button" className="xi-btn xi-btn--ghost" onClick={onLoadSamples} disabled={isRunning || newsLoading}>
          Load sample news
        </button>
        <RunAnalysisButton isRunning={isRunning || newsLoading} onClick={onRun} />
      </div>

      {newsLoading ? (
        <div className="xi-live-progress" role="status" aria-live="polite">
          <ProgressBar value={35} label="News Agent fetching live headlines…" />
          <p className="xi-muted">Pulling demand + India price news from GDELT / Google News…</p>
        </div>
      ) : null}

      {isRunning ? (
        <div className="xi-live-progress" role="status" aria-live="polite">
          <ProgressBar value={progress} label={activeAgent || "Pipeline running"} />
          <p className="xi-muted">News Agent → Demand → Price → Logistics → Containers → Groq Explain</p>
        </div>
      ) : null}

      {error ? (
        <div className="xi-error" role="alert">
          <strong>Analysis failed</strong>
          <p>{error}</p>
          <button type="button" className="xi-btn xi-btn--ghost" onClick={onRun}>
            Retry
          </button>
        </div>
      ) : null}
    </Panel>
  );
}

export function OverviewDashboard({
  dashboard,
  revealed,
  isRunning,
  analysisStatus,
  activeStage,
  progress,
  activeAgent,
  onRun,
  onNavigate,
  sessionMeta,
  onClear,
  onRestore,
}) {
  const hasData = Boolean(dashboard);

  return (
    <div className="xi-overview">
      <AgentPipeline
        analysisStatus={analysisStatus}
        revealed={revealed}
        activeStage={activeStage}
        onSelect={onNavigate}
      />

      {isRunning ? (
        <div className="xi-live-progress" role="status" aria-live="polite">
          <ProgressBar value={progress} label={activeAgent || "Analysis running"} />
        </div>
      ) : null}

      {!hasData && !isRunning ? (
        <div className="xi-empty-hero">
          <EmptyState
            title="No export analysis has been generated yet."
            description="Paste demand and mandi news, set container capacity, then run the five-agent pipeline. Charts and recommendations populate automatically from the API response."
            action={<RunAnalysisButton isRunning={false} onClick={onRun} />}
          />
          <div className="xi-flow-preview">
            {FLOW.map((step, i) => (
              <div key={step} className="xi-flow-preview__step">
                <Play size={14} />
                <span>{step}</span>
                {i < FLOW.length - 1 ? <span className="xi-flow-preview__arrow">→</span> : null}
              </div>
            ))}
          </div>
          {sessionMeta ? (
            <button type="button" className="xi-btn xi-btn--ghost" onClick={onRestore}>
              <History size={14} /> Restore recent browser session
            </button>
          ) : null}
        </div>
      ) : null}

      {(hasData || isRunning) && (
        <DecisionSummaryCards dashboard={dashboard} revealed={revealed} isRunning={isRunning} />
      )}

      {hasData && revealed.supervisor ? (
        <Panel title="Supervisor Recommendation" className="xi-flash">
          <p className="xi-rec-text">
            {dashboard.supervisorRecommendation?.summary || "Not available"}
          </p>
          <div className="xi-metric-grid">
            <div>
              <span>Commodity</span>
              <strong>{dashboard.supervisorRecommendation?.commodity || "Not available"}</strong>
            </div>
            <div>
              <span>Country</span>
              <strong>{dashboard.supervisorRecommendation?.country || "Not available"}</strong>
            </div>
            <div>
              <span>Containers</span>
              <strong>{dashboard.supervisorRecommendation?.containers ?? "Not available"}</strong>
            </div>
            <div>
              <span>Generated</span>
              <strong>{fmtDate(dashboard.generatedAt)}</strong>
            </div>
          </div>
        </Panel>
      ) : null}

      {sessionMeta && hasData ? (
        <div className="xi-session-bar">
          <span>
            <Radio size={14} /> {sessionMeta.label} · {fmtDate(sessionMeta.savedAt)}
          </span>
          <button type="button" className="xi-btn xi-btn--ghost xi-btn--sm" onClick={onClear}>
            Clear dashboard
          </button>
        </div>
      ) : null}
    </div>
  );
}

export function HistoryPanel({ sessionMeta, onRestore, onClear, onRun }) {
  return (
    <Panel id="panel-history" title="Analysis History" subtitle="Frontend-only recent browser session">
      {!sessionMeta ? (
        <EmptyState
          title="No saved session"
          description="Completed analyses can be restored from this browser after refresh."
          action={<RunAnalysisButton isRunning={false} onClick={onRun} />}
        />
      ) : (
        <div className="xi-history-card">
          <p>
            <strong>Recent browser session</strong>
          </p>
          <p className="xi-muted">Saved {fmtDate(sessionMeta.savedAt)}</p>
          <div className="xi-analysis-controls">
            <button type="button" className="xi-btn xi-btn--primary" onClick={onRestore}>
              Restore latest
            </button>
            <button type="button" className="xi-btn xi-btn--ghost" onClick={onClear}>
              Clear
            </button>
          </div>
        </div>
      )}
    </Panel>
  );
}

export function DataSourcesPanel() {
  return (
    <Panel id="panel-sources" title="Data Sources" subtitle="Inputs consumed by the existing backend pipeline">
      <ul className="xi-sources">
        <li>Demand news headlines (paste / sample API)</li>
        <li>India mandi / price news</li>
        <li>Demand prediction model</li>
        <li>Commodity price model (INR / quintal)</li>
        <li>Logistics cost tables & port corridors</li>
        <li>Container prioritization engine</li>
        <li>Groq LLM explanations + RAG document desk</li>
      </ul>
    </Panel>
  );
}
