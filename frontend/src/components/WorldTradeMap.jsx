/**
 * Interactive world map + animated India → destination shipping routes.
 * Presentation only — uses pipeline countries when available.
 */
import { useMemo, useState } from "react";
import { buildTradeRoutes, COUNTRY_COORDS } from "../vizData";

function curvePath(from, to) {
  const mx = (from.x + to.x) / 2;
  const my = Math.min(from.y, to.y) - 40 - Math.abs(to.x - from.x) * 0.08;
  return `M ${from.x} ${from.y} Q ${mx} ${my} ${to.x} ${to.y}`;
}

export default function WorldTradeMap({ result }) {
  const routes = useMemo(() => buildTradeRoutes(result), [result]);
  const [hover, setHover] = useState(null);

  const displayRoutes =
    routes.length > 0
      ? routes
      : [
          {
            id: "ph-bd",
            commodity: "Onion",
            country: "Bangladesh",
            indiaPort: "Kolkata",
            destPort: "Chittagong",
            profit: null,
            from: COUNTRY_COORDS.India,
            to: COUNTRY_COORDS.Bangladesh,
            placeholder: true,
          },
          {
            id: "ph-sa",
            commodity: "Wheat",
            country: "Saudi Arabia",
            indiaPort: "Mundra",
            destPort: "Jeddah",
            profit: null,
            from: COUNTRY_COORDS.India,
            to: COUNTRY_COORDS["Saudi Arabia"],
            placeholder: true,
          },
          {
            id: "ph-vn",
            commodity: "Coffee",
            country: "Vietnam",
            indiaPort: "Chennai",
            destPort: "Ho Chi Minh",
            profit: null,
            from: COUNTRY_COORDS.India,
            to: COUNTRY_COORDS.Vietnam,
            placeholder: true,
          },
        ];

  return (
    <section className="panel viz-panel world-map-panel">
      <div className="panel-head panel-head-row">
        <div>
          <h2>Global trade map</h2>
          <p className="panel-sub">
            India export corridors with animated shipping lanes
            {routes.length === 0 ? " · placeholder routes until analysis runs" : ""}.
          </p>
        </div>
        <span className="chip chip-cyan">{displayRoutes.length} lanes</span>
      </div>

      <div className="world-map-wrap">
        <svg className="world-map-svg" viewBox="0 0 1000 500" role="img" aria-label="World trade map">
          <defs>
            <linearGradient id="oceanGrad" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#0b3c5d" />
              <stop offset="100%" stopColor="#071a2b" />
            </linearGradient>
            <linearGradient id="routeGlow" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#06b6d4" />
              <stop offset="100%" stopColor="#2563eb" />
            </linearGradient>
            <filter id="softGlow">
              <feGaussianBlur stdDeviation="2.5" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          <rect width="1000" height="500" rx="18" fill="url(#oceanGrad)" />

          {/* Grid / digital texture */}
          <g opacity="0.18" stroke="#67e8f9" strokeWidth="0.6">
            {Array.from({ length: 10 }).map((_, i) => (
              <line key={`h${i}`} x1="0" y1={50 * i} x2="1000" y2={50 * i} />
            ))}
            {Array.from({ length: 20 }).map((_, i) => (
              <line key={`v${i}`} x1={50 * i} y1="0" x2={50 * i} y2="500" />
            ))}
          </g>

          {/* Simplified continent blobs */}
          <g fill="rgba(148,163,184,0.22)" stroke="rgba(226,232,240,0.25)" strokeWidth="1">
            <ellipse cx="280" cy="180" rx="120" ry="70" />
            <ellipse cx="480" cy="160" rx="90" ry="55" />
            <ellipse cx="520" cy="260" rx="55" ry="70" />
            <ellipse cx="720" cy="210" rx="140" ry="90" />
            <ellipse cx="780" cy="320" rx="80" ry="45" />
            <ellipse cx="180" cy="280" rx="70" ry="100" />
            <ellipse cx="850" cy="380" rx="60" ry="35" />
          </g>

          {displayRoutes.map((r, i) => (
            <g key={r.id}>
              <path
                d={curvePath(r.from, r.to)}
                fill="none"
                stroke="url(#routeGlow)"
                strokeWidth="2.5"
                strokeDasharray="8 10"
                className="ship-route-line"
                style={{ animationDelay: `${i * 0.4}s` }}
                filter="url(#softGlow)"
                onMouseEnter={() => setHover(r)}
                onMouseLeave={() => setHover(null)}
              />
              <circle cx={r.to.x} cy={r.to.y} r="7" className="dest-pulse" fill="#06b6d4" />
              <text x={r.to.x + 10} y={r.to.y - 8} className="map-label">
                {r.country}
              </text>
              {/* moving ship marker along path via CSS offset-path fallback: animate circle */}
              <circle r="4" fill="#f8fafc" className="ship-dot">
                <animateMotion dur={`${4 + i}s`} repeatCount="indefinite" path={curvePath(r.from, r.to)} />
              </circle>
            </g>
          ))}

          <g>
            <circle cx={COUNTRY_COORDS.India.x} cy={COUNTRY_COORDS.India.y} r="10" fill="#f97316" filter="url(#softGlow)" />
            <circle cx={COUNTRY_COORDS.India.x} cy={COUNTRY_COORDS.India.y} r="18" fill="none" stroke="#f97316" className="india-ring" />
            <text x={COUNTRY_COORDS.India.x - 18} y={COUNTRY_COORDS.India.y + 28} className="map-label map-label--india">
              India
            </text>
          </g>
        </svg>

        {hover ? (
          <div className="map-tooltip">
            <strong>
              {hover.commodity} → {hover.country}
            </strong>
            <span>
              {hover.indiaPort || "India"} → {hover.destPort || "Destination"}
            </span>
            {hover.profit != null ? <span>Net / ton: ${Number(hover.profit).toFixed(1)}</span> : <span>Preview lane</span>}
          </div>
        ) : null}
      </div>
    </section>
  );
}
