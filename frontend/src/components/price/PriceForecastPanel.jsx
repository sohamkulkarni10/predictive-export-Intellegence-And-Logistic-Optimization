import { useMemo, useState } from "react";
import { ArrowDownRight, ArrowRight, ArrowUpRight } from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fmtInr, fmtPct } from "../../utils";
import { EmptyState, LoadingSkeleton, Panel, StatusBadge } from "../common/Primitives";

export default function PriceForecastPanel({ data, horizon, ready, isRunning, onRun }) {
  const rows = data || [];
  const [selected, setSelected] = useState(null);
  const activeCommodity = selected || rows[0]?.commodity || null;
  const active = rows.find((r) => r.commodity === activeCommodity) || rows[0];

  const chartData = useMemo(() => {
    if (!active) return [];
    return [
      { label: "Current", price: active.currentPriceInr },
      { label: "Forecast", price: active.predictedPriceInr },
    ].filter((d) => d.price != null);
  }, [active]);

  const DirIcon =
    active?.direction === "increase"
      ? ArrowUpRight
      : active?.direction === "decrease"
        ? ArrowDownRight
        : ArrowRight;

  return (
    <Panel
      id="panel-price"
      accent="purple"
      title="India Price Forecast"
      subtitle={`Predicted next-month mandi prices${horizon ? ` · horizon ${horizon}` : ""}`}
    >
      {!ready && isRunning ? <LoadingSkeleton rows={4} /> : null}
      {!ready && !isRunning ? (
        <EmptyState
          title="No price forecasts yet"
          description="Run analysis to compare current vs next-month India prices."
          action={
            <button type="button" className="xi-btn xi-btn--primary" onClick={onRun}>
              Run Analysis
            </button>
          }
        />
      ) : null}

      {ready && rows.length === 0 ? (
        <EmptyState title="No price predictions returned" description="The price stage completed without forecast rows." />
      ) : null}

      {ready && rows.length > 0 ? (
        <>
          <div className="xi-pills" role="tablist" aria-label="Commodities">
            {rows.map((r) => (
              <button
                key={r.commodity}
                type="button"
                role="tab"
                aria-selected={r.commodity === active?.commodity}
                className={`xi-pill ${r.commodity === active?.commodity ? "is-active" : ""}`}
                onClick={() => setSelected(r.commodity)}
              >
                {r.commodity}
              </button>
            ))}
          </div>

          {active ? (
            <div className="xi-price-layout">
              <div className="xi-price-metrics">
                <div>
                  <span className="xi-metric__label">Current price</span>
                  <strong className="xi-metric__value">{fmtInr(active.currentPriceInr)}</strong>
                </div>
                <div>
                  <span className="xi-metric__label">Predicted next month</span>
                  <strong className="xi-metric__value">{fmtInr(active.predictedPriceInr)}</strong>
                </div>
                <div>
                  <span className="xi-metric__label">Change</span>
                  <strong className="xi-metric__value">
                    <StatusBadge
                      tone={
                        active.direction === "increase"
                          ? "success"
                          : active.direction === "decrease"
                            ? "danger"
                            : "warning"
                      }
                    >
                      <DirIcon size={14} /> {fmtPct(active.changePct)}
                    </StatusBadge>
                  </strong>
                </div>
                <div>
                  <span className="xi-metric__label">Price difference</span>
                  <strong className={`xi-metric__value ${active.priceDiff > 0 ? "pos" : active.priceDiff < 0 ? "neg" : ""}`}>
                    {active.priceDiff == null
                      ? "Not available"
                      : `${active.priceDiff >= 0 ? "+" : "−"}${fmtInr(Math.abs(active.priceDiff))}`}
                  </strong>
                  <span className="xi-metric__hint">INR / quintal · horizon {horizon || "—"}</span>
                </div>
              </div>

              <div className="xi-chart-block" aria-label="Current versus forecast price">
                {chartData.length >= 2 ? (
                  <ResponsiveContainer width="100%" height={220}>
                    <LineChart data={chartData}>
                      <CartesianGrid stroke="#202936" strokeDasharray="3 3" />
                      <XAxis dataKey="label" tick={{ fill: "#9AA7B7", fontSize: 12 }} axisLine={false} />
                      <YAxis tick={{ fill: "#667385", fontSize: 11 }} axisLine={false} tickLine={false} />
                      <Tooltip
                        formatter={(v) => fmtInr(v)}
                        contentStyle={{ background: "#151C26", border: "1px solid #293443", borderRadius: 8 }}
                      />
                      <Line
                        type="monotone"
                        dataKey="price"
                        stroke="#A78BFA"
                        strokeWidth={3}
                        dot={{ r: 5, fill: "#A78BFA" }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="xi-muted">Not enough price points for a comparison chart.</p>
                )}
                <p className="xi-chart-caption">Two-point comparison only — Current vs Forecast. No synthetic history.</p>
              </div>
            </div>
          ) : null}
        </>
      ) : null}
    </Panel>
  );
}
