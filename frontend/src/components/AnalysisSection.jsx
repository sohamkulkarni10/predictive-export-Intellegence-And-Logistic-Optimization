/**
 * Analysis inputs — same props / handlers as NewsInputs, editorial skin.
 */
export default function AnalysisSection({
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
    <section className="ed-section ed-section--black" id="analysis-inputs">
      <div className="ed-wrap">
        <div className="ed-section-head">
          <span className="ed-num">00</span>
          <div>
            <p className="ed-label">PIPELINE INPUT</p>
            <h2 className="ed-h2">Feed the intelligence engine.</h2>
            <p className="ed-lead">
              Paste demand and mandi headlines, set container capacity, then run the five-stage
              export pipeline.
            </p>
          </div>
        </div>

        <div className="ed-analysis-grid">
          <label className="ed-field">
            <span>Demand news</span>
            <textarea
              value={demandNews}
              onChange={(e) => onDemandChange(e.target.value)}
              placeholder="International demand, shortage, or import news…"
              disabled={loading}
            />
          </label>
          <label className="ed-field">
            <span>India market news (optional)</span>
            <textarea
              value={priceNews}
              onChange={(e) => onPriceChange(e.target.value)}
              placeholder="Mandi, auction, or stock news…"
              disabled={loading}
            />
          </label>
        </div>

        <div className="ed-analysis-controls">
          <label className="ed-inline">
            <span>Containers</span>
            <input
              type="number"
              min={1}
              max={50}
              value={containers}
              onChange={(e) => onContainersChange(e.target.value)}
              disabled={loading}
            />
          </label>
          <label className="ed-inline">
            <span>Type</span>
            <select
              value={containerType}
              onChange={(e) => onContainerTypeChange(e.target.value)}
              disabled={loading}
            >
              <option value="20FT">20FT</option>
              <option value="40FT">40FT</option>
            </select>
          </label>
          <button type="button" className="ed-cta ed-cta--ghost" onClick={onLoadSamples} disabled={loading}>
            LOAD SAMPLES
          </button>
          <button type="button" className="ed-cta ed-cta--lime" onClick={onRun} disabled={loading}>
            {loading ? "RUNNING…" : "RUN ANALYSIS"}
            <span className="ed-arrow">→</span>
          </button>
        </div>

        {loading ? (
          <div className="ed-loading-bar" role="status">
            <div />
            <p>Demand → Prices → Logistics → Containers → Decisions</p>
          </div>
        ) : null}

        {error ? (
          <div className="ed-error" role="alert">
            <strong>Something went wrong</strong>
            <p>{error}</p>
          </div>
        ) : null}
      </div>
    </section>
  );
}
