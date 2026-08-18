/**
 * Backend health badges: models, Groq, Databricks.
 */
export default function StatusBar({ health, healthError }) {
  if (healthError) {
    return (
      <div className="status-bar status-bar--down" role="status">
        <span className="status-dot status-dot--down" />
        <span className="status-label">API offline</span>
        <span className="status-meta">{healthError}</span>
      </div>
    );
  }

  if (!health) {
    return (
      <div className="status-bar status-bar--loading" role="status">
        <span className="status-dot status-dot--pulse" />
        <span className="status-label">Checking backend…</span>
      </div>
    );
  }

  const demandOk = Boolean(health.demand_model);
  const priceOk = Boolean(health.price_model);
  const modelsOk = demandOk && priceOk;
  const groqOn = Boolean(health.groq_enabled);
  const dbxOn = Boolean(health.databricks_enabled);

  return (
    <div className="status-bar" role="status">
      <span className={`status-dot ${health.status === "ok" ? "status-dot--ok" : "status-dot--warn"}`} />
      <span className="status-label">Backend</span>

      <span className={`status-badge ${modelsOk ? "is-ok" : "is-warn"}`}>
        Models {modelsOk ? "loaded" : "partial"}
      </span>
      <span className={`status-badge ${groqOn ? "is-ok" : "is-muted"}`}>
        {groqOn ? `Groq · ${health.groq_model || "on"}` : "Groq off · fallback"}
      </span>
      <span className={`status-badge ${dbxOn ? "is-ok" : "is-muted"}`}>
        {dbxOn ? "Databricks connected" : "Databricks local"}
      </span>
    </div>
  );
}
