import { useReducedMotion } from "../../hooks/useReducedMotion";

export function Panel({
  children,
  className = "",
  accent,
  title,
  subtitle,
  actions,
  id,
}) {
  return (
    <section
      id={id}
      className={`xi-panel ${accent ? `xi-panel--${accent}` : ""} ${className}`}
    >
      {(title || actions) && (
        <header className="xi-panel__head">
          <div>
            {title ? <h2 className="xi-panel__title">{title}</h2> : null}
            {subtitle ? <p className="xi-panel__sub">{subtitle}</p> : null}
          </div>
          {actions ? <div className="xi-panel__actions">{actions}</div> : null}
        </header>
      )}
      {children}
    </section>
  );
}

export function TiltPanel({ children, className = "", disabled = false }) {
  const reduced = useReducedMotion();
  const enable = !disabled && !reduced;

  function onMove(e) {
    if (!enable) return;
    const el = e.currentTarget;
    const rect = el.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    const rx = Math.max(-1.5, Math.min(1.5, -y * 3));
    const ry = Math.max(-1.5, Math.min(1.5, x * 3));
    el.style.transform = `perspective(1000px) translateY(-2px) rotateX(${rx}deg) rotateY(${ry}deg)`;
  }

  function onLeave(e) {
    e.currentTarget.style.transform = "";
  }

  return (
    <div
      className={`xi-tilt ${className}`}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
    >
      {children}
    </div>
  );
}

export function Metric({ label, value, hint, tone }) {
  return (
    <div className={`xi-metric ${tone ? `xi-metric--${tone}` : ""}`}>
      <span className="xi-metric__label">{label}</span>
      <strong className="xi-metric__value">{value}</strong>
      {hint ? <span className="xi-metric__hint">{hint}</span> : null}
    </div>
  );
}

export function StatusBadge({ children, tone = "neutral" }) {
  return <span className={`xi-badge xi-badge--${tone}`}>{children}</span>;
}

export function ProgressBar({ value = 0, label }) {
  const pct = Math.max(0, Math.min(100, Number(value) || 0));
  return (
    <div className="xi-progress" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
      {label ? <div className="xi-progress__label">{label}</div> : null}
      <div className="xi-progress__track">
        <div className="xi-progress__fill" style={{ width: `${pct}%` }} />
      </div>
      <span className="xi-progress__pct">{pct}%</span>
    </div>
  );
}

export function LoadingSkeleton({ rows = 3, className = "" }) {
  return (
    <div className={`xi-skeleton ${className}`} aria-hidden="true">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="xi-skeleton__row" style={{ width: `${88 - i * 12}%` }} />
      ))}
    </div>
  );
}

export function EmptyState({ title, description, action }) {
  return (
    <div className="xi-empty">
      <h3>{title}</h3>
      {description ? <p>{description}</p> : null}
      {action || null}
    </div>
  );
}

export function ErrorState({ title = "Something went wrong", message, onRetry }) {
  return (
    <div className="xi-error" role="alert">
      <strong>{title}</strong>
      {message ? <p>{message}</p> : null}
      {onRetry ? (
        <button type="button" className="xi-btn xi-btn--ghost" onClick={onRetry}>
          Retry
        </button>
      ) : null}
    </div>
  );
}

export function AnimatedNumber({ value, formatter, className = "" }) {
  const display = typeof formatter === "function" ? formatter(value) : value;
  return <span className={`xi-anim-num ${className}`}>{display}</span>;
}
