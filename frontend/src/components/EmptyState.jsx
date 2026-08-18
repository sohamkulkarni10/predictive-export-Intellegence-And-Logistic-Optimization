/**
 * Empty / loading placeholders shown before the first successful run.
 */
export default function EmptyState({ loading }) {
  if (loading) {
    return (
      <section className="panel empty-state empty-state--loading" aria-busy="true">
        <div className="empty-orb" aria-hidden="true" />
        <h2>Running the pipeline</h2>
        <p className="muted">
          Scoring demand, forecasting prices, optimizing routes, and allocating containers…
        </p>
        <div className="pipeline-progress">
          <div className="pipeline-progress-bar" />
        </div>
      </section>
    );
  }

  return (
    <section className="panel empty-state">
      <div className="empty-orb empty-orb--idle" aria-hidden="true" />
      <h2>Ready when you are</h2>
      <p className="muted">
        Load sample news or paste your own headlines, set how many containers you have,
        then run Export AI to see demand, prices, profit lanes, and decisions.
      </p>
      <ul className="empty-steps">
        <li>01 Demand ranking</li>
        <li>02 Price forecast</li>
        <li>03 Logistics + profit</li>
        <li>04 Container priority</li>
        <li>05 Final decisions</li>
      </ul>
    </section>
  );
}
