/**
 * Frontend-only adapter: pipeline API → dashboard view model.
 * Logistics money values are shown in INR (FX ₹96.3 / USD).
 */
import { directionFromPct, isPresent, USD_TO_INR } from "../utils";

const HISTORY_KEY = "exportintel_session_history";

function toInr(value, alreadyInr = null) {
  if (isPresent(alreadyInr)) return Number(alreadyInr);
  if (!isPresent(value) || Number.isNaN(Number(value))) return null;
  return Number(value) * USD_TO_INR;
}
export function mapDemandResults(stage1) {
  const list = stage1?.top_opportunities || [];
  // Always sort by demand score so Top Demand card matches Demand page
  const mapped = list.map((row, i) => ({
    rank: row.rank ?? i + 1,
    country: row.country ?? null,
    commodity: row.commodity ?? null,
    demandScore: isPresent(row.demand_score) ? Number(row.demand_score) : null,
    mentions: isPresent(row.mentions) ? Number(row.mentions) : null,
    note: row.note || row.reason || row.news_reason || null,
  }));
  mapped.sort((a, b) => (b.demandScore || 0) - (a.demandScore || 0));
  return mapped.map((row, i) => ({ ...row, rank: i + 1 }));
}

export function mapPriceResults(stage2) {
  const list = stage2?.predictions || [];
  return list.map((row) => ({
    commodity: row.commodity ?? null,
    currentPriceInr: isPresent(row.current_price_inr) ? Number(row.current_price_inr) : null,
    predictedPriceInr: isPresent(row.predicted_next_month_price_inr)
      ? Number(row.predicted_next_month_price_inr)
      : null,
    changePct: isPresent(row.predicted_change_pct) ? Number(row.predicted_change_pct) : null,
    direction: directionFromPct(row.predicted_change_pct),
    priceDiff:
      isPresent(row.predicted_next_month_price_inr) && isPresent(row.current_price_inr)
        ? Number(row.predicted_next_month_price_inr) - Number(row.current_price_inr)
        : null,
  }));
}

export function mapLogisticsResults(stage3) {
  const list = Array.isArray(stage3) ? stage3 : [];
  return list.map((row) => {
    const profitUsd =
      row?.profit?.net_profit_usd_per_ton ??
      row?.net_profit_usd_per_ton ??
      null;
    const profitInr =
      row?.profit?.net_profit_inr_per_ton ??
      row?.net_profit_inr_per_ton ??
      null;
    const netProfitPerTon = toInr(profitUsd, profitInr);
    const costPerTon = toInr(row.cost_per_ton_usd, row.cost_per_ton_inr);
    const costPerContainer = toInr(row.cost_per_container_usd, row.cost_per_container_inr);
    const laneProfit = toInr(
      row?.profit?.net_profit_usd_for_allocation ?? row.net_profit_usd_for_allocation,
      row?.profit?.net_profit_inr_for_allocation ?? row.net_profit_inr_for_allocation ?? row.net_profit_inr
    );
    const profitPerContainer = toInr(
      row?.profit?.net_profit_usd_per_container,
      row?.profit?.net_profit_inr_per_container
    );
    return {
      commodity: row.commodity ?? null,
      country: row.country ?? null,
      demandScore: isPresent(row.demand_score) ? Number(row.demand_score) : null,
      predictedIndiaPriceInr: isPresent(row.predicted_india_price_inr)
        ? Number(row.predicted_india_price_inr)
        : null,
      origin: row.origin ?? null,
      indiaPort: row.india_port ?? null,
      destinationPort: row.destination_port ?? null,
      costPerTonUsd: costPerTon, // displayed as INR
      costPerContainerUsd: costPerContainer, // displayed as INR
      costPerTonInr: costPerTon,
      costPerContainerInr: costPerContainer,
      transitDays: isPresent(row.total_transit_days) ? Number(row.total_transit_days) : null,
      distance: isPresent(row.distance_km) ? Number(row.distance_km) : null,
      serviceType: row.service_type ?? null,
      decisionSummary: row.decision_summary ?? null,
      netProfitPerTon,
      netProfitPerContainer: profitPerContainer,
      totalLaneProfit: laneProfit,
      currency: "INR",
      fxInrPerUsd: USD_TO_INR,
      ok: row.ok !== false && !row.error,
      error: row.error || null,
      profitable: isPresent(netProfitPerTon) ? Number(netProfitPerTon) > 0 : null,
    };
  });
}
export function mapContainerResults(stage4, inputs) {
  const allocations = stage4?.allocations || [];
  const available = isPresent(inputs?.available_containers)
    ? Number(inputs.available_containers)
    : null;
  const allocated = allocations.reduce(
    (sum, a) => sum + (Number(a.containers_allocated) || 0),
    0
  );
  const blocks = [];
  allocations.forEach((a) => {
    const n = Number(a.containers_allocated) || 0;
    for (let i = 0; i < n; i += 1) {
      blocks.push({
        commodity: a.commodity,
        country: a.country,
        priority: a.priority_rank,
      });
    }
  });

  return {
    summary: stage4?.summary || null,
    exportFirst: stage4?.export_first
      ? {
          commodity: stage4.export_first.commodity ?? null,
          country: stage4.export_first.country ?? null,
          containers: isPresent(stage4.export_first.containers)
            ? Number(stage4.export_first.containers)
            : null,
          indiaPort: stage4.export_first.india_port ?? null,
          destinationPort: stage4.export_first.destination_port ?? null,
          netProfitPerTon: toInr(
            stage4.export_first.net_profit_usd_per_ton,
            stage4.export_first.net_profit_inr_per_ton
          ),
        }
      : null,
    available,
    allocated,
    remaining: available != null ? Math.max(0, available - allocated) : null,
    containerType: inputs?.container_type || null,
    blocks,
    allocations: allocations.map((a) => ({
      priority: a.priority_rank ?? null,
      commodity: a.commodity ?? null,
      country: a.country ?? null,
      containers: isPresent(a.containers_allocated) ? Number(a.containers_allocated) : null,
      opportunityScore: isPresent(a.priority_score) ? Number(a.priority_score) : null,
      indiaPort: a.india_port ?? null,
      destinationPort: a.destination_port ?? null,
      netProfitPerTon: toInr(a.net_profit_usd_per_ton, a.net_profit_inr_per_ton),
      exportFirst: Boolean(a.export_first),
      profitable: isPresent(a.net_profit_usd_per_ton) || isPresent(a.net_profit_inr_per_ton)
        ? Number(toInr(a.net_profit_usd_per_ton, a.net_profit_inr_per_ton)) > 0
        : null,
    })),
  };
}

export function mapAgentResults(explanations, llm) {
  const order = [
    ["demand_agent", "Demand Agent"],
    ["price_agent", "Price Agent"],
    ["logistics_agent", "Logistics Agent"],
    ["container_agent", "Container Agent"],
    ["supervisor_agent", "Supervisor Agent"],
  ];
  return order.map(([key, label]) => ({
    key,
    label,
    text: explanations?.[key] || null,
    llm,
  }));
}

export function mapSupervisorRecommendation(result, dashboard) {
  const final = result?.final_decisions || {};
  const first =
    final.export_first ||
    dashboard?.containerPlan?.exportFirst ||
    dashboard?.demandOpportunities?.[0] ||
    null;
  const topLane =
    (final.lanes || []).find((l) => l.export_first) ||
    (final.lanes || [])[0] ||
    dashboard?.logisticsRoutes?.[0] ||
    null;
  const topPrice = dashboard?.priceForecasts?.find(
    (p) => p.commodity && first?.commodity && p.commodity === first.commodity
  );

  return {
    summary: final.summary || null,
    commodity: first?.commodity ?? null,
    country: first?.country ?? null,
    containers: isPresent(first?.containers)
      ? Number(first.containers)
      : dashboard?.containerPlan?.exportFirst?.containers ?? null,
    demandScore:
      dashboard?.demandOpportunities?.find(
        (d) => d.commodity === first?.commodity && d.country === first?.country
      )?.demandScore ?? null,
    profitPerTon:
      (isPresent(topLane?.netProfitPerTon) ? Number(topLane.netProfitPerTon) : null) ??
      toInr(topLane?.net_profit_usd_per_ton, topLane?.net_profit_inr_per_ton) ??
      dashboard?.containerPlan?.exportFirst?.netProfitPerTon ??
      null,
    indiaPort: topLane?.india_port ?? topLane?.indiaPort ?? null,
    destinationPort: topLane?.destination_port ?? topLane?.destinationPort ?? null,
    predictedPrice: topPrice?.predictedPriceInr ?? null,
    transitDays: topLane?.total_transit_days ?? topLane?.transitDays ?? null,
    logisticsCost:
      (isPresent(topLane?.costPerTonInr) ? Number(topLane.costPerTonInr) : null) ??
      (isPresent(topLane?.costPerTonUsd) ? Number(topLane.costPerTonUsd) : null) ??
      toInr(topLane?.cost_per_ton_usd, topLane?.cost_per_ton_inr),
  };
}

export function buildAnalysisDashboard(result) {
  if (!result) return null;

  const demandOpportunities = mapDemandResults(result.stage1_demand);
  const priceForecasts = mapPriceResults(result.stage2_prices);
  const logisticsRoutes = mapLogisticsResults(result.stage3_logistics);
  const containerPlan = mapContainerResults(result.stage4_container_priority, result.inputs);
  const allocationProfits = (result.final_decisions?.lanes || [])
    .map((lane) =>
      toInr(lane.net_profit_usd_for_allocation, lane.net_profit_inr_for_allocation ?? lane.net_profit_inr)
    )
    .filter((value) => isPresent(value) && !Number.isNaN(Number(value)))
    .map(Number);
  containerPlan.expectedCombinedProfit = allocationProfits.length
    ? allocationProfits.reduce((sum, value) => sum + value, 0)
    : null;
  const agentExplanations = mapAgentResults(result.agent_explanations, result.llm);
  const dashboard = {
    status: "completed",
    horizon: result.horizon_month || null,
    generatedAt: result.generated_at || null,
    llm: result.llm || null,
    inputs: result.inputs || null,
    demandOpportunities,
    priceForecasts,
    logisticsRoutes,
    containerPlan,
    agentExplanations,
    finalDecisions: result.final_decisions || null,
    raw: result,
  };
  dashboard.supervisorRecommendation = mapSupervisorRecommendation(result, dashboard);
  return dashboard;
}

export function saveSessionHistory(dashboard) {
  if (!dashboard) return;
  try {
    const entry = {
      savedAt: new Date().toISOString(),
      horizon: dashboard.horizon,
      generatedAt: dashboard.generatedAt,
      dashboard,
    };
    localStorage.setItem(HISTORY_KEY, JSON.stringify(entry));
  } catch {
    /* ignore quota / private mode */
  }
}

export function loadSessionHistory() {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function clearSessionHistory() {
  try {
    localStorage.removeItem(HISTORY_KEY);
  } catch {
    /* ignore */
  }
}
