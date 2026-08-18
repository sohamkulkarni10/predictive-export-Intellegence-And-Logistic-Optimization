import { useEffect, useState } from "react";
import { Brain, ChevronDown, ChevronUp, Copy } from "lucide-react";
import { llmBadge } from "../../utils";
import { EmptyState, LoadingSkeleton, Panel, StatusBadge } from "../common/Primitives";

export default function AgentReasoningPanel({ agents, llm, ready, isRunning, onRun }) {
  // Agent Reasoning page shows only Demand + Price agents
  const list = (agents || []).filter(
    (a) => a.key === "demand_agent" || a.key === "price_agent"
  );
  const [open, setOpen] = useState({});

  useEffect(() => {
    if (ready) {
      setOpen((prev) => ({ ...prev, demand_agent: true }));
    }
  }, [ready]);

  return (
    <Panel
      id="panel-agents"
      title="Agent Reasoning"
      subtitle="Collapsible explanations from each pipeline stage"
      actions={<StatusBadge tone="info">{llmBadge(llm)}</StatusBadge>}
    >
      {!ready && isRunning ? <LoadingSkeleton rows={5} /> : null}
      {!ready && !isRunning ? (
        <EmptyState
          title="No agent explanations yet"
          description="Run analysis to generate Demand → Supervisor reasoning."
          action={
            <button type="button" className="xi-btn xi-btn--primary" onClick={onRun}>
              Run Analysis
            </button>
          }
        />
      ) : null}

      {ready ? (
        <ul className="xi-accordion">
          {list.map((agent) => {
            const isOpen = Boolean(open[agent.key]);
            const summary = agent.text
              ? String(agent.text).slice(0, 120) + (agent.text.length > 120 ? "…" : "")
              : "No explanation returned for this agent.";
            return (
              <li key={agent.key} className={`xi-accordion__item ${isOpen ? "is-open" : ""}`}>
                <button
                  type="button"
                  className="xi-accordion__trigger"
                  aria-expanded={isOpen}
                  onClick={() => setOpen((p) => ({ ...p, [agent.key]: !p[agent.key] }))}
                >
                  <span className="xi-accordion__icon"><Brain size={16} /></span>
                  <span className="xi-accordion__title">
                    <strong>{agent.label}</strong>
                    <em>{summary}</em>
                  </span>
                  <StatusBadge tone={agent.text ? "success" : "neutral"}>
                    {agent.text ? "Ready" : "Empty"}
                  </StatusBadge>
                  {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>
                {isOpen ? (
                  <div className="xi-accordion__panel">
                    <p>{agent.text || "Not available"}</p>
                    {agent.text ? (
                      <button
                        type="button"
                        className="xi-btn xi-btn--ghost xi-btn--sm"
                        onClick={() => navigator.clipboard?.writeText(agent.text)}
                      >
                        <Copy size={14} /> Copy
                      </button>
                    ) : null}
                  </div>
                ) : null}
              </li>
            );
          })}
        </ul>
      ) : null}
    </Panel>
  );
}
