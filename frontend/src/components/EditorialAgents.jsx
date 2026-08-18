/**
 * Multi-agent accordion — display existing explanations only.
 */
import { useState } from "react";

const AGENTS = [
  { key: "demand_agent", label: "DEMAND AGENT", num: "01" },
  { key: "price_agent", label: "PRICE AGENT", num: "02" },
  { key: "logistics_agent", label: "LOGISTICS AGENT", num: "03" },
  { key: "container_agent", label: "CONTAINER AGENT", num: "04" },
  { key: "supervisor_agent", label: "SUPERVISOR AGENT", num: "05" },
];

export default function EditorialAgents({ explanations, llm }) {
  const isGroq = String(llm?.source || "").toLowerCase() === "groq";
  const [openKey, setOpenKey] = useState(() => {
    if (explanations?.supervisor_agent) return "supervisor_agent";
    const first = AGENTS.find((a) => explanations?.[a.key]);
    return first?.key || "supervisor_agent";
  });

  const rows = AGENTS.map((a) => ({
    ...a,
    text: explanations?.[a.key] || "",
  }));

  return (
    <section className="ed-section ed-section--black" id="agents">
      <div className="ed-wrap">
        <div className="ed-section-head">
          <span className="ed-num ed-num--light">05</span>
          <div>
            <p className="ed-label ed-label--muted">MULTI-AGENT INTELLIGENCE</p>
            <h2 className="ed-h2 ed-h2--light">Five agents. One export decision.</h2>
            <div className="ed-model-badges">
              <span>POWERED BY GROQ</span>
              <span>LLAMA 3.3 70B</span>
              {!isGroq ? <span>FALLBACK MODE</span> : null}
            </div>
          </div>
        </div>

        <div className="ed-agent-flow" aria-hidden="true">
          {["DEMAND", "PRICE", "LOGISTICS", "CONTAINER", "SUPERVISOR"].map((name, i) => (
            <div key={name} className="ed-flow-item">
              <span>{String(i + 1).padStart(2, "0")}</span>
              <strong>{name}</strong>
              {i < 4 ? <em>→</em> : null}
            </div>
          ))}
        </div>

        <div className="ed-accordion">
          {rows.map((row) => {
            const open = openKey === row.key;
            const summary = row.text
              ? String(row.text).split(/(?<=[.!?])\s+/)[0]
              : "No explanation returned for this agent in the current run.";
            return (
              <div key={row.key} className={`ed-acc-row ${open ? "is-open" : ""}`}>
                <button
                  type="button"
                  className="ed-acc-trigger"
                  onClick={() => setOpenKey(open ? null : row.key)}
                  aria-expanded={open}
                >
                  <span className="ed-acc-left">
                    <em>{row.num}</em>
                    <strong>{row.label}</strong>
                    <span className="ed-acc-status">{row.text ? "READY" : "NO TEXT"}</span>
                  </span>
                  <span className="ed-acc-toggle">{open ? "HIDE −" : "VIEW REASONING +"}</span>
                </button>
                <p className="ed-acc-summary">{summary}</p>
                {open && row.text ? <div className="ed-acc-body">{row.text}</div> : null}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
