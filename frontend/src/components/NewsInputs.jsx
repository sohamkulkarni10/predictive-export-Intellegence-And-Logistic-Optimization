/**
 * News paste area + container controls + run / sample actions.
 */
export default function NewsInputs({
  demandNews,
  priceNews,
  containers,
  containerType,
  loading,
  error,
  onDemandChange,
  onPriceChange,
  onContainersChange,
  onContainerTypeChange,
  onLoadSamples,
  onRun,
}) {
  return (
    <section className="panel panel-inputs" id="analysis-inputs">
      <div className="panel-head">
        <h2>Run analysis</h2>
        <p className="panel-sub">Paste headlines or load samples, then run the five-stage pipeline.</p>
      </div>

      <div className="grid-2">
        <div className="field-block">
          <label htmlFor="demand-news">Demand news</label>
          <textarea
            id="demand-news"
            value={demandNews}
            onChange={(e) => onDemandChange(e.target.value)}
            placeholder="International demand, shortage, or import news…"
            disabled={loading}
          />
        </div>
        <div className="field-block">
          <label htmlFor="price-news">India market news (optional — uses demand news if empty)</label>
          <textarea
            id="price-news"
            value={priceNews}
            onChange={(e) => onPriceChange(e.target.value)}
            placeholder="Mandi, auction, or stock news…"
            disabled={loading}
          />
        </div>
      </div>

      <div className="controls">
        <div className="field">
          <label htmlFor="containers">Containers available</label>
          <input
            id="containers"
            type="number"
            min={1}
            max={50}
            value={containers}
            onChange={(e) => onContainersChange(e.target.value)}
            disabled={loading}
          />
        </div>
        <div className="field">
          <label htmlFor="container-type">Container type</label>
          <select
            id="container-type"
            value={containerType}
            onChange={(e) => onContainerTypeChange(e.target.value)}
            disabled={loading}
          >
            <option value="20FT">20FT</option>
            <option value="40FT">40FT</option>
          </select>
        </div>
        <button className="btn-ghost" type="button" onClick={onLoadSamples} disabled={loading}>
          Load sample news
        </button>
        <button className="btn-primary" type="button" onClick={onRun} disabled={loading}>
          {loading ? (
            <>
              <span className="btn-spinner" aria-hidden="true" />
              Running pipeline…
            </>
          ) : (
            "Run Analysis"
          )}
        </button>
      </div>

      {loading ? (
        <div className="pipeline-progress" role="status" aria-live="polite">
          <div className="pipeline-progress-bar" />
          <p className="muted">Demand → Prices → Logistics → Containers → Decisions</p>
        </div>
      ) : null}

      {error ? (
        <div className="state-banner state-banner--error" role="alert">
          <strong>Something went wrong</strong>
          <p>{error}</p>
        </div>
      ) : null}
    </section>
  );
}
