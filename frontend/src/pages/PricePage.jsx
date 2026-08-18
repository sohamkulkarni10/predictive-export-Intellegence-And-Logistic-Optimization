import { useNavigate } from "react-router-dom";
import { ArrowRight, CalendarDays } from "lucide-react";
import { useApp } from "../context/AppContext";
import PageContainer from "../components/layout/PageContainer";
import PriceForecastPanel from "../components/price/PriceForecastPanel";
import { Panel, StatusBadge } from "../components/common/Primitives";

export default function PricePage() {
  const navigate = useNavigate();
  const { analysis } = useApp();
  const forecasts = analysis.dashboard?.priceForecasts || [];
  const strongest = [...forecasts].sort(
    (a, b) => Math.abs(b.changePct || 0) - Math.abs(a.changePct || 0),
  )[0];

  return (
    <PageContainer
      eyebrow="INDIA MARKET SIGNALS"
      title="Price Prediction"
      subtitle="Compare current and next-month commodity prices using only returned model values."
      actions={
        <button className="xi-btn xi-btn--primary" type="button" onClick={() => navigate("/demand")}>
          Configure analysis <ArrowRight size={15} />
        </button>
      }
    >
      <div className="page-summary-strip">
        <div><CalendarDays size={17} /><span>Forecast horizon</span><strong>{analysis.dashboard?.horizon || "Not available"}</strong></div>
        <div><span>Commodities returned</span><strong>{forecasts.length || "Not available"}</strong></div>
        <div>
          <span>Strongest price signal</span>
          <strong>{strongest?.commodity || "Not available"}</strong>
          {strongest?.direction ? <StatusBadge tone={strongest.direction === "increase" ? "success" : strongest.direction === "decrease" ? "danger" : "warning"}>{strongest.direction}</StatusBadge> : null}
        </div>
      </div>

      <PriceForecastPanel
        data={forecasts}
        horizon={analysis.dashboard?.horizon}
        ready={analysis.revealed.price}
        isRunning={analysis.isRunning}
        onRun={() => navigate("/demand")}
      />

      <Panel title="Price Decision Note" subtitle="Presentation derived from the returned price direction">
        <p className="decision-note">
          {!strongest
            ? "Not available"
            : strongest.direction === "increase"
              ? `${strongest.commodity} has an increasing model signal. Review buying timing alongside route profitability.`
              : strongest.direction === "decrease"
                ? `${strongest.commodity} has a decreasing model signal. Review before committing procurement.`
                : `${strongest.commodity} is currently presented as stable. Review the full forecast values.`}
        </p>
      </Panel>
    </PageContainer>
  );
}
