/**
 * AI explanations as accordion cards (display only).
 */
import { useState } from "react";
import { IconBot, IconChevron, IconSpark } from "./Icons";

const AGENTS = [
  { key: "demand_agent", label: "Demand Agent", stage: 0 },
  { key: "price_agent", label: "Price Agent", stage: 1 },
  { key: "logistics_agent", label: "Logistics Agent", stage: 2 },
  { key: "container_agent", label: "Container Agent", stage: 3 },
  { key: "supervisor_agent", label: "Supervisor Agent", stage: 4 },
];

export default function AgentPanel({ explanations, llm, activeStage }) {
  const source = llm?.source || "fallback";
  const isGroq = String(source).toLowerCase() === "groq";

  const rows = AGENTS.map((a) => ({
    ...a,
    text: explanations?.[a.key] || "",
  }));

  const [openKey, setOpenKey] = useState(() => {
    const focus = AGENTS.find((a) => a.stage === activeStage)?.key;
    if (focus && explanations?.[focus]) return focus;
    const firstWithText = rows.find((r) => r.text)?.key;
    return firstWithText || rows[0]?.key;
  });

  return (
    <section className="panel agent-panel reveal">
      <div className="panel-head panel-head-row">
        <div>
          <h2>AI explanations</h2>
          <p className="panel-sub">Expand each agent card to read the full rationale.</p>
        </div>
        <div className="llm-badges">
          <span className={`llm-badge ${isGroq ? "llm-badge--groq" : "llm-badge--fallback"}`}>
            {isGroq ? "Powered by Groq · Llama 3.3 70B" : "Offline numbers"}
          </span>
          {llm?.model ? <span className="llm-badge llm-badge--model">{llm.model}</span> : null}
        </div>
      </div>

      <div className="agent-flow" aria-hidden="true">
        {AGENTS.map((row, i) => (
          <span key={row.key} className="agent-flow-item">
            {row.label.replace(" Agent", "")}
            {i < AGENTS.length - 1 ? <span className="agent-flow-arrow">→</span> : null}
          </span>
        ))}
      </div>

      <div className="agent-stack">
        {rows.map((row) => {
          const open = openKey === row.key;
          const hasText = Boolean(row.text);
          const summary = hasText
            ? String(row.text).split(/(?<=[.!?])\s+/)[0] || row.text
            : "No AI explanation returned for this agent in the current run.";
          return (
            <article
              key={row.key}
              className={`agent-box accordion ${open ? "is-open" : ""} ${
                activeStage === row.stage ? "is-focus" : ""
              }`}
            >
              <button
                type="button"
                className="agent-box-head accordion-trigger"
                onClick={() => setOpenKey(open ? null : row.key)}
                aria-expanded={open}
              >
                <span className="agent-head-left">
                  <span className="agent-icon">
                    {row.key.includes("demand") || row.key.includes("price") ? (
                      <IconSpark />
                    ) : (
                      <IconBot />
                    )}
                  </span>
                  <strong>{row.label}</strong>
                  <span className={`badge ${hasText ? "badge-ok" : "badge-muted"}`}>
                    {hasText ? "Ready" : "No text"}
                  </span>
                  {activeStage === row.stage ? (
                    <span className="badge badge-rank">This stage</span>
                  ) : null}
                </span>
                <IconChevron className={`chevron ${open ? "is-open" : ""}`} />
              </button>
              <p className="agent-summary">{summary}</p>
              {open && hasText ? <p className="agent-text">{row.text}</p> : null}
            </article>
          );
        })}
      </div>
    </section>
  );
}
