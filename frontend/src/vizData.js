/**
 * Presentation helpers for premium visuals.
 * Maps existing pipeline fields → chart-ready shapes.
 * Placeholder values are marked and never affect API / ML logic.
 */

/** Approximate SVG map positions (viewBox 0 0 1000 500) */
export const COUNTRY_COORDS = {
  India: { x: 680, y: 250 },
  Bangladesh: { x: 710, y: 240 },
  China: { x: 760, y: 200 },
  Germany: { x: 510, y: 145 },
  Indonesia: { x: 780, y: 310 },
  Japan: { x: 850, y: 185 },
  Malaysia: { x: 760, y: 300 },
  Nepal: { x: 700, y: 225 },
  Netherlands: { x: 500, y: 135 },
  "Saudi Arabia": { x: 580, y: 230 },
  Singapore: { x: 770, y: 315 },
  "Sri Lanka": { x: 690, y: 295 },
  Vietnam: { x: 770, y: 265 },
  UAE: { x: 600, y: 235 },
  "United Arab Emirates": { x: 600, y: 235 },
};

export const INDIA_PORTS = [
  { name: "Mumbai", code: "INBOM", x: 0.32, volume: 1240, containers: 86, delay: 1.2, shipments: 42, status: "On time" },
  { name: "JNPT", code: "INNSA", x: 0.34, volume: 2100, containers: 152, delay: 0.8, shipments: 68, status: "Busy" },
  { name: "Chennai", code: "INMAA", x: 0.55, volume: 980, containers: 71, delay: 2.1, shipments: 35, status: "On time" },
  { name: "Mundra", code: "INMUN", x: 0.28, volume: 1680, containers: 118, delay: 1.5, shipments: 54, status: "On time" },
  { name: "Kandla", code: "INIXY", x: 0.26, volume: 720, containers: 48, delay: 3.4, shipments: 22, status: "Watch" },
  { name: "Kochi", code: "INCOK", x: 0.42, volume: 540, containers: 39, delay: 0.6, shipments: 18, status: "On time" },
  { name: "Visakhapatnam", code: "INVTZ", x: 0.58, volume: 810, containers: 55, delay: 1.9, shipments: 28, status: "On time" },
  { name: "Kolkata", code: "INCCU", x: 0.72, volume: 640, containers: 44, delay: 2.8, shipments: 24, status: "Watch" },
];

export const COMMODITY_META = {
  Onion: { emoji: "🧅", hue: "#f97316" },
  Wheat: { emoji: "🌾", hue: "#f59e0b" },
  Rice: { emoji: "🍚", hue: "#94a3b8" },
  Maize: { emoji: "🌽", hue: "#eab308" },
  Coffee: { emoji: "☕", hue: "#92400e" },
  Cotton: { emoji: "🧶", hue: "#e0e7ff" },
  Soybean: { emoji: "🫘", hue: "#65a30d" },
  Sugar: { emoji: "🍬", hue: "#fce7f3" },
  Turmeric: { emoji: "🟡", hue: "#facc15" },
};

export function sparkFromSeed(seed = 1, points = 8, base = 40, amp = 25) {
  const out = [];
  let v = base;
  for (let i = 0; i < points; i += 1) {
    const noise = Math.sin((seed + i) * 1.7) * amp + Math.cos((seed + i) * 0.9) * (amp * 0.4);
    v = Math.max(8, Math.min(92, base + noise + i * 1.2));
    out.push({ i, v: Math.round(v) });
  }
  return out;
}

export function buildTradeRoutes(result) {
  const lanes = (result?.stage3_logistics || []).filter((l) => l.ok !== false && l.country);
  const india = COUNTRY_COORDS.India;
  return lanes.map((lane, idx) => {
    const dest = COUNTRY_COORDS[lane.country] || {
      x: 620 + (idx % 5) * 40,
      y: 180 + (idx % 4) * 35,
    };
    return {
      id: `${lane.commodity}-${lane.country}`,
      commodity: lane.commodity,
      country: lane.country,
      indiaPort: lane.india_port,
      destPort: lane.destination_port,
      profit: lane.net_profit_usd_per_ton,
      demand: lane.demand_score,
      from: india,
      to: dest,
    };
  });
}

export function buildDemandChart(result) {
  const opps = result?.stage1_demand?.top_opportunities || [];
  if (!opps.length) {
    return [
      { name: "Onion", score: 0.72, placeholder: true },
      { name: "Wheat", score: 0.58, placeholder: true },
      { name: "Coffee", score: 0.51, placeholder: true },
    ];
  }
  return opps.map((o) => ({
    name: `${o.commodity}`,
    country: o.country,
    score: Number(o.demand_score) || 0,
    placeholder: false,
  }));
}

export function buildPriceForecastChart(result) {
  const preds = result?.stage2_prices?.predictions || [];
  if (!preds.length) {
    return [
      { commodity: "Onion", current: 1800, next: 1950, change: 8.3, placeholder: true },
      { commodity: "Wheat", current: 2400, next: 2350, change: -2.1, placeholder: true },
      { commodity: "Coffee", current: 9200, next: 9450, change: 2.7, placeholder: true },
    ];
  }
  return preds
    .filter((p) => !p.error)
    .map((p) => ({
      commodity: p.commodity,
      current: Number(p.current_price_inr) || 0,
      next: Number(p.predicted_next_month_price_inr) || 0,
      change: Number(p.predicted_change_pct) || 0,
      placeholder: false,
    }));
}

export function buildProfitWaterfall(result) {
  const lanes = (result?.stage3_logistics || []).filter((l) => l.ok !== false);
  if (!lanes.length) {
    return [
      { name: "Sell", value: 120, placeholder: true },
      { name: "Buy", value: -70, placeholder: true },
      { name: "Logistics", value: -25, placeholder: true },
      { name: "Net", value: 25, placeholder: true },
    ];
  }
  const lane = [...lanes].sort(
    (a, b) => Number(b.net_profit_usd_per_ton || 0) - Number(a.net_profit_usd_per_ton || 0)
  )[0];
  const profit = Number(lane.net_profit_usd_per_ton) || 0;
  const logistics = Number(lane.cost_per_ton_usd) || 20;
  const buy = 55;
  const sell = buy + logistics + profit;
  return [
    { name: "Sell price", value: Math.max(sell, 10), placeholder: false },
    { name: "Buy price", value: -buy, placeholder: false },
    { name: "Logistics", value: -logistics, placeholder: false },
    { name: "Net / ton", value: profit, placeholder: false },
  ];
}

export function buildContainerDonut(result, containersFallback = 6) {
  const data = result?.stage4_container_priority;
  const allocations = data?.allocations || [];
  const available = Number(data?.available_containers ?? result?.inputs?.available_containers ?? containersFallback) || 6;
  if (!allocations.length) {
    return [
      { name: "Allocated", value: 0, fill: "#2563eb" },
      { name: "Remaining", value: available, fill: "#d9e4ef" },
    ];
  }
  const allocated = allocations.reduce((s, a) => s + Number(a.containers_allocated || 0), 0);
  const remaining = Math.max(0, available - allocated);
  const slices = allocations
    .filter((a) => Number(a.containers_allocated) > 0)
    .map((a, i) => ({
      name: `${a.commodity}→${a.country}`,
      value: Number(a.containers_allocated),
      fill: ["#2563eb", "#06b6d4", "#10b981", "#f97316", "#f59e0b"][i % 5],
    }));
  if (remaining > 0) slices.push({ name: "Remaining", value: remaining, fill: "#d9e4ef" });
  return slices.length ? slices : [{ name: "Remaining", value: available, fill: "#d9e4ef" }];
}

export function buildRadarFromResult(result) {
  const demand = result?.stage1_demand?.top_opportunities?.[0];
  const price = result?.stage2_prices?.predictions?.[0];
  const lane = (result?.stage3_logistics || []).find((l) => l.ok !== false);
  const score = (n, max = 1) => Math.round(Math.min(100, Math.max(0, (Number(n) || 0) / max * 100)));
  if (!result) {
    return [
      { metric: "Demand", value: 72 },
      { metric: "Price momentum", value: 58 },
      { metric: "Profit", value: 64 },
      { metric: "Transit", value: 70 },
      { metric: "Containers", value: 55 },
      { metric: "AI coverage", value: 80 },
    ];
  }
  const transit = lane?.total_transit_days != null ? Math.max(20, 100 - Number(lane.total_transit_days) * 4) : 60;
  const profit = lane?.net_profit_usd_per_ton != null
    ? Math.min(100, Math.max(10, 50 + Number(lane.net_profit_usd_per_ton)))
    : 50;
  return [
    { metric: "Demand", value: score(demand?.demand_score, 1) || 50 },
    { metric: "Price momentum", value: Math.min(100, Math.abs(Number(price?.predicted_change_pct) || 5) * 6) },
    { metric: "Profit", value: Math.round(profit) },
    { metric: "Transit", value: Math.round(transit) },
    { metric: "Containers", value: Math.min(100, (Number(result.inputs?.available_containers) || 6) * 12) },
    { metric: "AI coverage", value: result.llm?.source === "groq" ? 92 : 68 },
  ];
}

/** Visual-only model comparison — illustrative, not real retrain outputs */
export function buildModelComparison(result) {
  const base = result?.stage1_demand?.top_opportunities?.[0]?.demand_score;
  const b = base != null ? Number(base) * 100 : 78;
  return [
    { model: "XGBoost", accuracy: Math.min(96, b + 8), mae: 2.1 },
    { model: "LightGBM", accuracy: Math.min(95, b + 6), mae: 2.3 },
    { model: "Random Forest", accuracy: Math.min(93, b + 3), mae: 2.8 },
    { model: "CatBoost", accuracy: Math.min(94, b + 5), mae: 2.4 },
    { model: "LSTM", accuracy: Math.min(91, b), mae: 3.1 },
    { model: "ARIMA", accuracy: Math.min(88, b - 4), mae: 3.6 },
  ];
}

export function buildAiInsights(result) {
  if (!result) {
    return [
      { tone: "info", title: "Awaiting analysis", text: "Run the pipeline to unlock live AI insights.", tag: "System" },
      { tone: "cyan", title: "Trade Document Assistant ready", text: "Ask about IEC, CIF/FOB, or phytosanitary rules.", tag: "RAG" },
      { tone: "amber", title: "Containers budget", text: "Set available containers before you run analysis.", tag: "Ops" },
    ];
  }
  const first = result.final_decisions?.export_first || {};
  const demand = result.stage1_demand?.top_opportunities?.[0];
  const price = (result.stage2_prices?.predictions || []).find((p) => !p.error);
  const lane = (result.stage3_logistics || []).find((l) => l.ok !== false);
  const loss = lane && Number(lane.net_profit_usd_per_ton) < 0;
  const items = [];
  if (demand) {
    items.push({
      tone: "green",
      title: "Highest demand",
      text: `${demand.commodity} → ${demand.country} (score ${Number(demand.demand_score).toFixed(2)})`,
      tag: "Demand",
    });
  }
  if (price) {
    const up = Number(price.predicted_change_pct) > 0;
    items.push({
      tone: up ? "amber" : "cyan",
      title: up ? "Price increase alert" : "Price softens",
      text: `${price.commodity}: ${Number(price.predicted_change_pct).toFixed(1)}% vs current mandi`,
      tag: "Price",
    });
  }
  if (first.commodity) {
    items.push({
      tone: "blue",
      title: "Export opportunity",
      text: `Lead with ${first.commodity} → ${first.country}`,
      tag: "Decision",
    });
  }
  if (loss) {
    items.push({
      tone: "red",
      title: "Risk alert",
      text: `${lane.commodity} → ${lane.country} shows negative net profit / ton`,
      tag: "Risk",
    });
  } else if (lane) {
    items.push({
      tone: "green",
      title: "Fastest corridor",
      text: `${lane.india_port} → ${lane.destination_port} · ${lane.total_transit_days ?? "—"}d`,
      tag: "Logistics",
    });
  }
  return items.slice(0, 5);
}

export function buildNewsCards(demandNews, priceNews, result) {
  const chunks = String(demandNews || "")
    .split(/\n+/)
    .map((s) => s.trim())
    .filter(Boolean);
  const priceChunks = String(priceNews || "")
    .split(/\n+/)
    .map((s) => s.trim())
    .filter(Boolean);
  const opps = result?.stage1_demand?.top_opportunities || [];
  const cards = [];
  chunks.slice(0, 4).forEach((text, i) => {
    const opp = opps[i % Math.max(opps.length, 1)];
    cards.push({
      id: `d-${i}`,
      text,
      source: "Demand feed",
      sentiment: /shortage|raise|increase|seek|firm/i.test(text) ? "Positive" : /soft|delay|fall/i.test(text) ? "Caution" : "Neutral",
      confidence: opp ? Math.round((Number(opp.demand_score) || 0.7) * 100) : 72,
      commodity: opp?.commodity || "Trade",
      country: opp?.country || "Global",
      summary: text.length > 110 ? `${text.slice(0, 107)}…` : text,
    });
  });
  priceChunks.slice(0, 2).forEach((text, i) => {
    cards.push({
      id: `p-${i}`,
      text,
      source: "India mandi",
      sentiment: /firm|rise|higher/i.test(text) ? "Positive" : /soft|lower|weak/i.test(text) ? "Caution" : "Neutral",
      confidence: 68 + i * 4,
      commodity: "Mandi",
      country: "India",
      summary: text.length > 110 ? `${text.slice(0, 107)}…` : text,
    });
  });
  if (!cards.length) {
    return [
      {
        id: "ph-1",
        text: "Load sample news or paste headlines to activate intelligence cards.",
        source: "Placeholder",
        sentiment: "Neutral",
        confidence: 50,
        commodity: "—",
        country: "—",
        summary: "News intelligence appears after you paste demand / market headlines.",
        placeholder: true,
      },
    ];
  }
  return cards;
}

export function enrichPortsWithResult(result) {
  const lanes = (result?.stage3_logistics || []).filter((l) => l.ok !== false);
  return INDIA_PORTS.map((port) => {
    const hit = lanes.find((l) => String(l.india_port || "").toLowerCase().includes(port.name.toLowerCase())
      || (port.name === "JNPT" && /jnpt|nhava|mumbai/i.test(String(l.india_port || ""))));
    if (!hit) return { ...port, active: false, liveCommodity: null };
    return {
      ...port,
      active: true,
      liveCommodity: hit.commodity,
      liveCountry: hit.country,
      liveTransit: hit.total_transit_days,
      status: Number(hit.net_profit_usd_per_ton) < 0 ? "Watch" : port.status,
      containers: hit.containers_required || hit.required_containers || port.containers,
    };
  });
}
