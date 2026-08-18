/**
 * SVG primitives for premium dashboard visuals (no chart lib required).
 */
export function MiniSparkline({ data = [], stroke = "#2563eb", fill = "rgba(37,99,235,0.15)", height = 36, width = 96 }) {
  if (!data.length) return null;
  const max = Math.max(...data.map((d) => d.v), 1);
  const min = Math.min(...data.map((d) => d.v), 0);
  const span = Math.max(1, max - min);
  const pts = data
    .map((d, i) => {
      const x = (i / Math.max(1, data.length - 1)) * width;
      const y = height - ((d.v - min) / span) * (height - 4) - 2;
      return `${x},${y}`;
    })
    .join(" ");
  const area = `0,${height} ${pts} ${width},${height}`;
  return (
    <svg className="mini-sparkline" width={width} height={height} viewBox={`0 0 ${width} ${height}`} aria-hidden="true">
      <polygon points={area} fill={fill} />
      <polyline points={pts} fill="none" stroke={stroke} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

export function GaugeRing({ value = 0, label = "", size = 108, color = "#2563eb", track = "#e7eef6" }) {
  const v = Math.max(0, Math.min(100, Number(value) || 0));
  const r = 40;
  const c = 2 * Math.PI * r;
  const offset = c - (v / 100) * c;
  return (
    <div className="gauge-ring" style={{ width: size, height: size }}>
      <svg viewBox="0 0 100 100" width={size} height={size}>
        <circle cx="50" cy="50" r={r} fill="none" stroke={track} strokeWidth="8" />
        <circle
          cx="50"
          cy="50"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
          transform="rotate(-90 50 50)"
          className="gauge-progress"
        />
        <text x="50" y="48" textAnchor="middle" className="gauge-value-text">
          {Math.round(v)}%
        </text>
        <text x="50" y="62" textAnchor="middle" className="gauge-label-text">
          {label}
        </text>
      </svg>
    </div>
  );
}

export function RiskMeter({ value = 0.4 }) {
  const pct = Math.max(0, Math.min(100, Number(value) * 100));
  return (
    <div className="risk-meter" aria-label={`Risk ${Math.round(pct)}%`}>
      <div className="risk-meter-track">
        <div className="risk-meter-fill" style={{ width: `${pct}%` }} />
      </div>
      <span className="risk-meter-label">{Math.round(pct)}% risk</span>
    </div>
  );
}

export function ProgressBarAnimated({ value = 0, max = 1, tone = "blue" }) {
  const pct = Math.max(0, Math.min(100, (Number(value) / Math.max(max, 0.0001)) * 100));
  return (
    <div className={`progress-anim progress-anim--${tone}`}>
      <div className="progress-anim-fill" style={{ width: `${pct}%` }} />
    </div>
  );
}
