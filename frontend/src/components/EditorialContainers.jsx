/**
 * Container allocation — visual TEU strip + editorial priority rows.
 */
import { fmtNum, fmtUsd } from "../utils";

const COLORS = ["#DFFF4F", "#7894FF", "#FF6B2C", "#3DDB8B", "#F5F08A", "#FFFFFF"];

export default function EditorialContainers({ data }) {
  const allocations = data?.allocations || [];
  const first = data?.export_first || {};
  const available = Number(data?.available_containers || 0);
  const allocated = allocations.reduce((s, a) => s + Number(a.containers_allocated || 0), 0);
  const remaining = Math.max(0, available - allocated);
  const expectedProfit = allocations.reduce(
    (s, a) => s + Number(a.net_profit_usd_for_allocation || 0),
    0
  );

  const boxes = [];
  allocations.forEach((a, ai) => {
    const n = Number(a.containers_allocated || 0);
    for (let i = 0; i < n; i += 1) {
      boxes.push({
        key: `${a.commodity}-${a.country}-${i}`,
        label: a.commodity,
        color: COLORS[ai % COLORS.length],
      });
    }
  });
  for (let i = 0; i < remaining; i += 1) {
    boxes.push({ key: `empty-${i}`, label: "OPEN", color: "transparent", empty: true });
  }

  return (
    <section className="ed-section ed-section--blue" id="containers">
      <div className="ed-wrap">
        <div className="ed-section-head">
          <span className="ed-num ed-num--light">04</span>
          <div>
            <p className="ed-label ed-label--on-accent">CONTAINER ALLOCATION</p>
            <h2 className="ed-h2 ed-h2--light">When capacity is limited, who ships first?</h2>
            <p className="ed-lead ed-lead--on-accent">
              {data?.summary || "Priority ranking for scarce containers."}
            </p>
          </div>
        </div>

        {!allocations.length ? (
          <p className="ed-empty ed-empty--dark">Allocation appears after the container stage completes.</p>
        ) : (
          <>
            <div className="ed-container-hero">
              <p className="ed-label ed-label--on-accent">PRIMARY RECOMMENDATION</p>
              <h3 className="ed-mega">
                {first.commodity && first.country
                  ? `${String(first.commodity).toUpperCase()} → ${String(first.country).toUpperCase()}`
                  : "—"}
              </h3>
              <p className="ed-container-count">
                {first.containers != null
                  ? `${first.containers} OF ${available} CONTAINERS`
                  : `${allocated} OF ${available} CONTAINERS`}
              </p>
            </div>

            <div className="ed-teu-strip" aria-label="Container allocation">
              {boxes.map((b) => (
                <div
                  key={b.key}
                  className={`ed-teu ${b.empty ? "is-empty" : ""}`}
                  style={{ borderColor: b.empty ? "rgba(255,255,255,0.35)" : b.color, background: b.empty ? "transparent" : `${b.color}33` }}
                >
                  {b.label}
                </div>
              ))}
            </div>

            <div className="ed-container-stats">
              <div>
                <span>Total</span>
                <strong>{available}</strong>
              </div>
              <div>
                <span>Allocated</span>
                <strong>{allocated}</strong>
              </div>
              <div>
                <span>Remaining</span>
                <strong>{remaining}</strong>
              </div>
              <div>
                <span>Expected profit</span>
                <strong>{fmtUsd(expectedProfit, 0)}</strong>
              </div>
            </div>

            <div className="ed-priority-list">
              {allocations.map((a) => {
                const loss = Number(a.net_profit_usd_per_ton) < 0;
                return (
                  <article key={`${a.commodity}-${a.country}`} className="ed-priority-row">
                    <span className="ed-priority-rank">
                      {String(a.priority_rank).padStart(2, "0")}
                    </span>
                    <div className="ed-priority-main">
                      <strong>
                        {a.commodity} — {a.country}
                      </strong>
                      <span>
                        {a.india_port && a.destination_port
                          ? `${a.india_port} → ${a.destination_port}`
                          : "Route pending"}
                      </span>
                    </div>
                    <div className="ed-priority-meta">
                      <span>{fmtNum(a.containers_allocated ?? 0, 0)} CONTAINERS</span>
                      <span>SCORE {fmtNum(a.priority_score, 2)}</span>
                      <span className={loss ? "negative" : "positive"}>
                        {fmtUsd(a.net_profit_usd_per_ton, 1)} / TON
                      </span>
                    </div>
                    {loss ? (
                      <span className="ed-loss-badge">HIGH DEMAND / CURRENTLY LOSS-MAKING</span>
                    ) : null}
                  </article>
                );
              })}
            </div>
          </>
        )}
      </div>
    </section>
  );
}
