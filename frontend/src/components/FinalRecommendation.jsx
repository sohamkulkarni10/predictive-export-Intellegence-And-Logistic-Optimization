/**
 * Final recommendation — built only from existing pipeline data.
 */
import { fmtNum, fmtUsd } from "../utils";

export default function FinalRecommendation({ result, onViewPlan }) {
  const first = result?.final_decisions?.export_first || {};
  const demand = result?.stage1_demand?.top_opportunities?.[0];
  const price = (result?.stage2_prices?.predictions || []).find(
    (p) => !p.error && (!first.commodity || p.commodity === first.commodity)
  ) || (result?.stage2_prices?.predictions || []).find((p) => !p.error);
  const lane = (result?.stage3_logistics || []).find(
    (l) =>
      l.ok !== false &&
      (!first.commodity || l.commodity === first.commodity) &&
      (!first.country || l.country === first.country)
  ) || (result?.stage3_logistics || []).find((l) => l.ok !== false);

  const has = first.commodity && first.country;
  const heading = has
    ? `EXPORT ${String(first.commodity).toUpperCase()} TO ${String(first.country).toUpperCase()}`
    : "RUN ANALYSIS TO UNLOCK YOUR EXPORT DECISION";

  return (
    <section className="ed-section ed-section--final" id="decision">
      <div className="ed-wrap">
        <p className="ed-label">FINAL EXPORT DECISION</p>
        <h2 className="ed-final-title">{heading}</h2>
        {result?.final_decisions?.summary ? (
          <p className="ed-final-summary">{result.final_decisions.summary}</p>
        ) : null}

        {has ? (
          <div className="ed-final-grid">
            <div>
              <span>Demand score</span>
              <strong>{demand ? fmtNum(demand.demand_score, 2) : "—"}</strong>
            </div>
            <div>
              <span>Price outlook</span>
              <strong>
                {price?.predicted_change_pct != null
                  ? `${Number(price.predicted_change_pct) > 0 ? "+" : ""}${Number(price.predicted_change_pct).toFixed(1)}%`
                  : "—"}
              </strong>
            </div>
            <div>
              <span>Best route</span>
              <strong>
                {lane?.india_port && lane?.destination_port
                  ? `${lane.india_port} → ${lane.destination_port}`
                  : "—"}
              </strong>
            </div>
            <div>
              <span>Containers</span>
              <strong>{first.containers ?? "—"}</strong>
            </div>
            <div>
              <span>Profit / ton</span>
              <strong>
                {lane?.net_profit_usd_per_ton != null
                  ? fmtUsd(lane.net_profit_usd_per_ton, 1)
                  : "—"}
              </strong>
            </div>
            <div>
              <span>Supervisor</span>
              <strong>{result?.agent_explanations?.supervisor_agent ? "Ready" : "—"}</strong>
            </div>
          </div>
        ) : null}

        <button type="button" className="ed-cta ed-cta--dark" onClick={onViewPlan}>
          VIEW COMPLETE EXPORT PLAN →
        </button>
      </div>
    </section>
  );
}
