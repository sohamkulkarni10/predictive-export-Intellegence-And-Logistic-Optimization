/**
 * Big KPI number with optional count-up animation.
 * Respects prefers-reduced-motion.
 */
import { useEffect, useState } from "react";

function prefersReducedMotion() {
  if (typeof window === "undefined") return true;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export default function KpiValue({ value, format, duration = 600, className = "" }) {
  const numeric = Number(value);
  const canAnimate = !Number.isNaN(numeric) && value !== null && value !== undefined;
  const [display, setDisplay] = useState(canAnimate ? 0 : value);

  useEffect(() => {
    if (!canAnimate || prefersReducedMotion()) {
      setDisplay(value);
      return undefined;
    }

    let frame;
    const start = performance.now();
    const from = 0;
    const to = numeric;

    function tick(now) {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(from + (to - from) * eased);
      if (t < 1) frame = requestAnimationFrame(tick);
    }

    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value, canAnimate, numeric, duration]);

  const shown = format ? format(display) : String(display);

  return <span className={`kpi-value ${className}`.trim()}>{shown}</span>;
}
