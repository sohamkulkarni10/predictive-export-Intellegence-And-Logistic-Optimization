import { Boxes, MapPinned, Sparkles, TrendingUp } from "lucide-react";
import { fmtInr, fmtScore, formatRoute } from "../../utils";
import { LoadingSkeleton, StatusBadge, TiltPanel } from "../common/Primitives";

export function DecisionSummaryCards({ dashboard, revealed, isRunning }) {
  // Highest demand score = top demand card (must match Demand page #1)
  const top = revealed.demand
    ? [...(dashboard?.demandOpportunities || [])].sort(
        (a, b) => (b.demandScore || 0) - (a.demandScore || 0)
      )[0]
    : null;
  const price = revealed.price
    ? dashboard?.priceForecasts?.find((p) => p.commodity === top?.commodity) ||
      dashboard?.priceForecasts?.[0]
    : null;
  // Most profitable route = highest net profit (separate from demand rank)
  const route = revealed.logistics
    ? [...(dashboard?.logisticsRoutes || [])].sort(
        (a, b) => (b.netProfitPerTon || 0) - (a.netProfitPerTon || 0)
      )[0]
    : null;
  // Container recommendation = export-first allocation (priority blend)
  const container = revealed.container ? dashboard?.containerPlan?.exportFirst : null;

  const cards = [
    {
      id: "demand",
      label: "Top Demand Opportunity",
      icon: TrendingUp,
      accent: "blue",
      ready: revealed.demand,
      value: top ? `${top.commodity} → ${top.country}` : null,
      meta: top ? `Demand score ${fmtScore(top.demandScore)}` : null,
      badge: top ? "Highest demand" : null,
      title: null,
    },
    {
      id: "price",
      label: "Best Price Outlook",
      icon: Sparkles,
      accent: "purple",
      ready: revealed.price,
      value: price ? fmtInr(price.predictedPriceInr) : null,
      meta: price
        ? `${price.commodity} · ${price.changePct != null ? (price.changePct > 0 ? "+" : "") + price.changePct.toFixed(2) + "%" : "—"}`
        : null,
      badge: price?.direction || null,
      tone:
        price?.direction === "increase"
          ? "success"
          : price?.direction === "decrease"
            ? "danger"
            : "warning",
      title: null,
    },
    {
      id: "logistics",
      label: "Most Profitable Route",
      icon: MapPinned,
      accent: "orange",
      ready: revealed.logistics,
      // Short city/port labels only — full official names on hover
      value: route ? formatRoute(route.indiaPort, route.destinationPort) : null,
      meta: route
        ? `${fmtInr(route.netProfitPerTon)}/ton · ${route.transitDays ?? "—"} days`
        : null,
      badge: route?.profitable === true ? "Profitable" : route?.profitable === false ? "Loss-making" : null,
      tone: route?.profitable === true ? "success" : route?.profitable === false ? "danger" : "neutral",
      title: route
        ? `${route.indiaPort || ""} → ${route.destinationPort || ""}`.trim()
        : null,
    },
    {
      id: "container",
      label: "Container Recommendation",
      icon: Boxes,
      accent: "cyan",
      ready: revealed.container,
      value: container
        ? `${container.containers ?? "—"} × ${container.commodity || "—"}`
        : null,
      meta: container ? `${container.country || "—"} · ${fmtInr(container.netProfitPerTon)}/ton` : null,
      badge: container ? "Export first" : null,
      title: null,
    },
  ];

  return (
    <div className="xi-decision-grid">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <TiltPanel key={card.id}>
            <article className={`xi-decision-card xi-decision-card--${card.accent}`}>
              <div className="xi-decision-card__top">
                <span className="xi-decision-card__icon">
                  <Icon size={16} />
                </span>
                <span className="xi-decision-card__label">{card.label}</span>
                {card.badge ? <StatusBadge tone={card.tone || "info"}>{card.badge}</StatusBadge> : null}
              </div>
              {!card.ready ? (
                isRunning ? (
                  <LoadingSkeleton rows={2} />
                ) : (
                  <p className="xi-muted">Awaiting analysis</p>
                )
              ) : (
                <>
                  <p className="xi-decision-card__value" title={card.title || undefined}>
                    {card.value || "Not available"}
                  </p>
                  <p className="xi-decision-card__meta">{card.meta}</p>
                </>
              )}
            </article>
          </TiltPanel>
        );
      })}
    </div>
  );
}
