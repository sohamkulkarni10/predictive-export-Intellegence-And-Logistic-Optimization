import { useMemo, useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { countryInitials, fmtScore } from "../../utils";
import { EmptyState, LoadingSkeleton, Panel, StatusBadge } from "../common/Primitives";

export default function DemandPanel({ data, ready, isRunning, onRun }) {
  const [country, setCountry] = useState("all");
  const [commodity, setCommodity] = useState("all");
  const [sort, setSort] = useState("score");
  const [expanded, setExpanded] = useState(null);

  const rows = data || [];
  const countries = useMemo(
    () => [...new Set(rows.map((r) => r.country).filter(Boolean))],
    [rows]
  );
  const commodities = useMemo(
    () => [...new Set(rows.map((r) => r.commodity).filter(Boolean))],
    [rows]
  );

  const filtered = useMemo(() => {
    let list = [...rows];
    if (country !== "all") list = list.filter((r) => r.country === country);
    if (commodity !== "all") list = list.filter((r) => r.commodity === commodity);
    list.sort((a, b) => {
      if (sort === "country") return String(a.country).localeCompare(String(b.country));
      return (b.demandScore || 0) - (a.demandScore || 0);
    });
    return list;
  }, [rows, country, commodity, sort]);

  const chartData = filtered.map((r) => ({
    name: `${r.commodity || "?"}`.slice(0, 10),
    score: r.demandScore ?? 0,
  }));

  return (
    <Panel
      id="panel-demand"
      accent="blue"
      title="Demand Opportunities"
      subtitle="Countries and commodities with the strongest next-month demand signals"
      actions={
        <div className="xi-filters">
          <select value={country} onChange={(e) => setCountry(e.target.value)} aria-label="Filter country">
            <option value="all">All countries</option>
            {countries.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <select value={commodity} onChange={(e) => setCommodity(e.target.value)} aria-label="Filter commodity">
            <option value="all">All commodities</option>
            {commodities.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <select value={sort} onChange={(e) => setSort(e.target.value)} aria-label="Sort">
            <option value="score">Sort by score</option>
            <option value="country">Sort by country</option>
          </select>
        </div>
      }
    >
      {!ready && isRunning ? <LoadingSkeleton rows={5} /> : null}
      {!ready && !isRunning ? (
        <EmptyState
          title="No demand results yet"
          description="Run analysis to rank country–commodity opportunities from news signals."
          action={
            <button type="button" className="xi-btn xi-btn--primary" onClick={onRun}>
              Run Analysis
            </button>
          }
        />
      ) : null}
      {ready && !rows.length ? (
        <EmptyState title="No opportunities returned" description="The demand stage completed without ranked rows." />
      ) : null}

      {ready && rows.length > 0 ? (
        <>
          <div className="xi-chart-block" aria-label="Demand score comparison chart">
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={chartData}>
                <XAxis dataKey="name" tick={{ fill: "#9AA7B7", fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: "#667385", fontSize: 11 }} axisLine={false} tickLine={false} domain={[0, 1]} />
                <Tooltip
                  contentStyle={{ background: "#151C26", border: "1px solid #293443", borderRadius: 8 }}
                  labelStyle={{ color: "#F4F7FB" }}
                />
                <Bar dataKey="score" fill="#6D8CFF" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <ul className="xi-activity-list">
            {filtered.map((row, idx) => {
              const open = expanded === idx;
              const top = idx === 0 && sort === "score" && country === "all" && commodity === "all";
              return (
                <li key={`${row.rank}-${row.country}-${row.commodity}`} className={`xi-activity-row ${top ? "is-highlight" : ""} ${open ? "is-open" : ""}`}>
                  <button
                    type="button"
                    className="xi-activity-row__main"
                    onClick={() => setExpanded(open ? null : idx)}
                    aria-expanded={open}
                  >
                    <span className="xi-rank">#{row.rank ?? idx + 1}</span>
                    <span className="xi-avatar" aria-hidden="true">{countryInitials(row.country)}</span>
                    <span className="xi-activity-row__body">
                      <strong>{row.country || "Not available"}</strong>
                      <em>{row.commodity || "Not available"}</em>
                    </span>
                    <span className="xi-activity-row__score">
                      <StatusBadge tone="info">{fmtScore(row.demandScore)}</StatusBadge>
                      {row.mentions != null ? <small>{row.mentions} mentions</small> : null}
                    </span>
                    {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </button>
                  {open ? (
                    <div className="xi-activity-row__detail">
                      {row.note ? <p>{row.note}</p> : <p className="xi-muted">No additional news explanation was returned for this opportunity.</p>}
                      <p>
                        Demand score <strong>{fmtScore(row.demandScore)}</strong>
                        {row.mentions != null ? <> · Mentions <strong>{row.mentions}</strong></> : null}
                      </p>
                    </div>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </>
      ) : null}
    </Panel>
  );
}
