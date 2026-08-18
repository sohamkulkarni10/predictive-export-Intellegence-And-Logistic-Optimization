import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useApp } from "../context/AppContext";
import PageContainer from "../components/layout/PageContainer";
import { EmptyState, Panel } from "../components/common/Primitives";
import { fmtInr, fmtNum, fmtScore } from "../utils";

const COLORS = ["#2F6BFF", "#25B8FF", "#31D49B", "#F5C451", "#F29A45"];

function ChartPanel({ title, subtitle, children, empty }) {
  return (
    <Panel title={title} subtitle={subtitle}>
      {empty ? <EmptyState title="Not available" description="Run analysis to populate this chart." /> : <div className="analytics-chart">{children}</div>}
    </Panel>
  );
}

export default function AnalyticsPage() {
  const { analysis } = useApp();
  const dashboard = analysis.dashboard;
  const demand = dashboard?.demandOpportunities || [];
  const prices = dashboard?.priceForecasts || [];
  const routes = dashboard?.logisticsRoutes || [];
  const allocations = dashboard?.containerPlan?.allocations || [];
  const avgDemand = demand.length ? demand.reduce((sum, row) => sum + (row.demandScore || 0), 0) / demand.length : null;
  const profitable = routes.filter((route) => Number.isFinite(route.netProfitPerTon));
  const avgProfit = profitable.length ? profitable.reduce((sum, route) => sum + route.netProfitPerTon, 0) / profitable.length : null;
  const priceData = prices.flatMap((row) => [
    { name: row.commodity, kind: "Current", value: row.currentPriceInr },
    { name: row.commodity, kind: "Forecast", value: row.predictedPriceInr },
  ]).filter((row) => row.value != null);

  return (
    <PageContainer
      eyebrow="PERFORMANCE INTELLIGENCE"
      title="Global Trade Overview"
      subtitle="Demand, price, route profit and container allocation from the latest analysis."
    >
      <div className="analytics-metrics">
        <article><span>Total opportunities</span><strong>{demand.length || "Not available"}</strong></article>
        <article><span>Commodities analysed</span><strong>{prices.length || "Not available"}</strong></article>
        <article><span>Average demand score</span><strong>{fmtScore(avgDemand)}</strong></article>
        <article><span>Average route profit</span><strong>{fmtInr(avgProfit)}</strong></article>
        <article><span>Completed analyses</span><strong>{analysis.analysisStatus === "completed" ? "1" : "Not available"}</strong></article>
      </div>

      <div className="analytics-grid">
        <ChartPanel title="Demand Score by Commodity" subtitle="Returned opportunity scores" empty={!demand.length}>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={demand}>
              <CartesianGrid stroke="#172A45" strokeDasharray="3 3" />
              <XAxis dataKey="commodity" tick={{ fill: "#93A4BC", fontSize: 11 }} />
              <YAxis domain={[0, 1]} tick={{ fill: "#5F718B", fontSize: 11 }} />
              <Tooltip contentStyle={{ background: "#0A1628", border: "1px solid #172A45" }} />
              <Bar dataKey="demandScore" fill="#2F6BFF" radius={[5, 5, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartPanel>

        <ChartPanel title="Current vs Forecast Price" subtitle="INR per quintal" empty={!priceData.length}>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={priceData}>
              <CartesianGrid stroke="#172A45" strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fill: "#93A4BC", fontSize: 11 }} />
              <YAxis tick={{ fill: "#5F718B", fontSize: 11 }} />
              <Tooltip contentStyle={{ background: "#0A1628", border: "1px solid #172A45" }} />
              <Legend />
              <Bar dataKey="value" fill="#25B8FF" radius={[5, 5, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartPanel>

        <ChartPanel title="Profit by Export Route" subtitle="Net INR profit per ton (₹96.3/USD)" empty={!routes.length}>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={routes}>
              <CartesianGrid stroke="#172A45" strokeDasharray="3 3" />
              <XAxis dataKey="destinationPort" tick={{ fill: "#93A4BC", fontSize: 11 }} />
              <YAxis tick={{ fill: "#5F718B", fontSize: 11 }} />
              <Tooltip contentStyle={{ background: "#0A1628", border: "1px solid #172A45" }} />
              <Bar dataKey="netProfitPerTon" radius={[5, 5, 0, 0]}>
                {routes.map((route, index) => <Cell key={index} fill={route.netProfitPerTon >= 0 ? "#31D49B" : "#F25F67"} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartPanel>

        <ChartPanel title="Container Allocation" subtitle="Actual returned allocation counts" empty={!allocations.length}>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={allocations} dataKey="containers" nameKey="commodity" innerRadius={58} outerRadius={92} paddingAngle={3}>
                {allocations.map((_, index) => <Cell key={index} fill={COLORS[index % COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={{ background: "#0A1628", border: "1px solid #172A45" }} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </ChartPanel>
      </div>

      <p className="analytics-footnote">Latest analysis: {dashboard?.generatedAt || "Not available"} · Values are not supplemented with synthetic history.</p>
    </PageContainer>
  );
}
