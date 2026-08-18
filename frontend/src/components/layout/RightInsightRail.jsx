import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Circle,
  Loader2,
  XCircle,
} from "lucide-react";
import { fmtInr, fmtScore, formatRoute } from "../../utils";
import { StatusBadge } from "../common/Primitives";

const STAGES = [
  { id: "demand", label: "Demand", n: 1 },
  { id: "price", label: "Price", n: 2 },
  { id: "logistics", label: "Logistics", n: 3 },
  { id: "container", label: "Container", n: 4 },
  { id: "supervisor", label: "Supervisor", n: 5 },
];

function stageState(id, analysisStatus, revealed, activeStage) {
  if (analysisStatus === "failed" && activeStage === id) return "failed";
  if (revealed?.[id]) return "completed";
  if (activeStage === id || analysisStatus === `${id}_running`) return "running";
  if (analysisStatus === "idle") return "idle";
  // ordering for pending
  const order = ["demand", "price", "logistics", "container", "supervisor"];
  const idx = order.indexOf(id);
  const activeIdx = order.indexOf(activeStage);
  if (activeIdx >= 0 && idx < activeIdx) return "completed";
  return "pending";
}

export function AgentPipeline({ analysisStatus, revealed, activeStage, onSelect }) {
  return (
    <div className="xi-pipeline" aria-label="Agent pipeline">
      {STAGES.map((stage, i) => {
        const state = stageState(stage.id, analysisStatus, revealed, activeStage);
        return (
          <div key={stage.id} className="xi-pipeline__wrap">
            <button
              type="button"
              className={`xi-pipeline__stage is-${state}`}
              onClick={() => onSelect?.(stage.id)}
            >
              <span className="xi-pipeline__n">{stage.n}</span>
              <span className="xi-pipeline__icon">
                {state === "running" && <Loader2 size={14} className="spin" />}
                {state === "completed" && <CheckCircle2 size={14} />}
                {state === "failed" && <XCircle size={14} />}
                {(state === "idle" || state === "pending") && <Circle size={14} />}
              </span>
              <span className="xi-pipeline__name">{stage.label}</span>
              <span className="xi-pipeline__status">
                {state === "running"
                  ? "Running"
                  : state === "completed"
                    ? "Complete"
                    : state === "failed"
                      ? "Failed"
                      : "Waiting"}
              </span>
            </button>
            {i < STAGES.length - 1 ? (
              <div className={`xi-pipeline__connector ${revealed?.[stage.id] ? "is-done" : ""} ${activeStage === stage.id ? "is-active" : ""}`} />
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

export default function RightInsightRail({
  dashboard,
  revealed,
  analysisStatus,
  isRunning,
  onNavigate,
}) {
  const rec = revealed?.supervisor ? dashboard?.supervisorRecommendation : null;
  const topRoute = revealed?.logistics
    ? [...(dashboard?.logisticsRoutes || [])].sort(
        (a, b) => (b.netProfitPerTon || 0) - (a.netProfitPerTon || 0)
      )[0]
    : null;
  // Highest demand score (same as Demand page #1 / Top Demand card)
  const topDemand = revealed?.demand
    ? [...(dashboard?.demandOpportunities || [])].sort(
        (a, b) => (b.demandScore || 0) - (a.demandScore || 0)
      )[0]
    : null;
  const topPrice = revealed?.price
    ? dashboard?.priceForecasts?.find((p) => p.commodity === topDemand?.commodity) ||
      dashboard?.priceForecasts?.[0]
    : null;

  return (
    <aside className="xi-rail" aria-label="Intelligence rail">
      <div className="xi-rail__card">
        <h3>Final Recommendation</h3>
        {!rec ? (
          <p className="xi-muted">
            {isRunning ? "Waiting for supervisor…" : "Run analysis to generate a recommendation."}
          </p>
        ) : (
          <div className="xi-rail__rec">
            <p className="xi-rail__hero">
              {rec.commodity || "—"} → {rec.country || "—"}
            </p>
            <ul>
              <li>
                <span>Demand score</span>
                <strong>{fmtScore(rec.demandScore)}</strong>
              </li>
              <li>
                <span>Profit / ton</span>
                <strong className={Number(rec.profitPerTon) > 0 ? "pos" : Number(rec.profitPerTon) < 0 ? "neg" : ""}>
                  {fmtInr(rec.profitPerTon)}
                </strong>
              </li>
              <li>
                <span>Route</span>
                <strong title={`${rec.indiaPort || ""} → ${rec.destinationPort || ""}`.trim()}>
                  {formatRoute(rec.indiaPort, rec.destinationPort)}
                </strong>
              </li>
              <li>
                <span>Containers</span>
                <strong>{rec.containers ?? "Not available"}</strong>
              </li>
            </ul>
            {rec.summary ? <p className="xi-rail__summary">{rec.summary}</p> : null}
            <StatusBadge tone="success">Supervisor ready</StatusBadge>
          </div>
        )}
      </div>

      <div className="xi-rail__card">
        <h3>Risk & Profitability</h3>
        {!topRoute && !topPrice && !topDemand ? (
          <p className="xi-muted">Available after analysis stages complete.</p>
        ) : (
          <ul className="xi-rail__risk">
            {topRoute?.profitable != null && (
              <li>
                <span>Route</span>
                <StatusBadge tone={topRoute.profitable ? "success" : "danger"}>
                  {topRoute.profitable ? "Profitable" : "Loss-making"}
                </StatusBadge>
              </li>
            )}
            {topPrice?.direction && (
              <li>
                <span>Price direction</span>
                <StatusBadge
                  tone={
                    topPrice.direction === "increase"
                      ? "success"
                      : topPrice.direction === "decrease"
                        ? "danger"
                        : "warning"
                  }
                >
                  {topPrice.direction}
                </StatusBadge>
              </li>
            )}
            {topRoute?.transitDays != null && (
              <li>
                <span>Transit</span>
                <strong>{topRoute.transitDays} days</strong>
              </li>
            )}
            {topDemand?.demandScore != null && (
              <li>
                <span>Top demand</span>
                <strong>{fmtScore(topDemand.demandScore)}</strong>
              </li>
            )}
            {topPrice?.predictedPriceInr != null && (
              <li>
                <span>Forecast buy</span>
                <strong>{fmtInr(topPrice.predictedPriceInr)}</strong>
              </li>
            )}
          </ul>
        )}
      </div>

      <div className="xi-rail__card">
        <h3>Suggested Actions</h3>
        <div className="xi-rail__actions">
          <button type="button" onClick={() => onNavigate("demand")}>
            Prioritise top opportunity <ArrowRight size={14} />
          </button>
          {topRoute && topRoute.profitable === false ? (
            <button type="button" onClick={() => onNavigate("logistics")}>
              <AlertTriangle size={14} /> Review loss-making route
            </button>
          ) : (
            <button type="button" onClick={() => onNavigate("logistics")}>
              Compare destination ports <ArrowRight size={14} />
            </button>
          )}
          <button type="button" onClick={() => onNavigate("rag")}>
            Ask Trade Assistant <ArrowRight size={14} />
          </button>
        </div>
      </div>

      <div className="xi-rail__card">
        <h3>Analysis Completion</h3>
        <ul className="xi-rail__stages">
          {STAGES.map((s) => {
            const state = stageState(s.id, analysisStatus, revealed, null);
            return (
              <li key={s.id} className={`is-${state}`}>
                <span>{s.label}</span>
                <em>
                  {state === "completed" ? "Done" : state === "running" ? "Running" : "Pending"}
                </em>
              </li>
            );
          })}
        </ul>
      </div>
    </aside>
  );
}
