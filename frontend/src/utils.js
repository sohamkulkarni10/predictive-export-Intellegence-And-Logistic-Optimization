/**
 * Safe formatting helpers — never emit undefined / NaN / [object Object].
 */

const NA = "Not available";

export function isPresent(value) {
  return value !== null && value !== undefined && value !== "";
}

export function fmtNum(value, digits = 0) {
  if (!isPresent(value) || Number.isNaN(Number(value))) return NA;
  return Number(value).toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export function fmtUsd(value, digits = 2) {
  if (!isPresent(value) || Number.isNaN(Number(value))) return NA;
  const n = Number(value);
  const sign = n < 0 ? "-" : "";
  return `${sign}$${Math.abs(n).toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })}`;
}

/** Fixed FX used for logistics / profit display (1 USD = ₹96.3) */
export const USD_TO_INR = 96.3;

export function usdToInr(value) {
  if (!isPresent(value) || Number.isNaN(Number(value))) return null;
  return Number(value) * USD_TO_INR;
}

export function fmtInr(value, digits = 0) {
  if (!isPresent(value) || Number.isNaN(Number(value))) return NA;
  const n = Number(value);
  const sign = n < 0 ? "-" : "";
  const abs = Math.abs(n);
  if (digits > 0) {
    return `${sign}₹${abs.toLocaleString("en-IN", {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    })}`;
  }
  return `${sign}₹${Math.round(abs).toLocaleString("en-IN")}`;
}

export function fmtPct(value, digits = 2) {
  if (!isPresent(value) || Number.isNaN(Number(value))) return NA;
  const n = Number(value);
  const sign = n > 0 ? "+" : "";
  return `${sign}${n.toFixed(digits)}%`;
}

export function fmtScore(value, digits = 2) {
  if (!isPresent(value) || Number.isNaN(Number(value))) return NA;
  return Number(value).toFixed(digits);
}

export function fmtDate(value) {
  if (!isPresent(value)) return NA;
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function profitClass(value) {
  const n = Number(value);
  if (!isPresent(value) || Number.isNaN(n) || n === 0) return "neutral";
  return n > 0 ? "positive" : "negative";
}

export function directionFromPct(pct) {
  if (!isPresent(pct) || Number.isNaN(Number(pct))) return null;
  const n = Number(pct);
  if (n > 0.15) return "increase";
  if (n < -0.15) return "decrease";
  return "stable";
}

export function agentLabel(key) {
  return String(key || "")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function llmBadge(llm) {
  if (!llm || typeof llm !== "object") return "LLM · OFFLINE";
  const source = String(llm.source || "groq").toUpperCase();
  const model = String(llm.model || "LLAMA 3.3 70B")
    .replace(/llama-/i, "LLAMA ")
    .replace(/-/g, " ")
    .toUpperCase();
  return `${source} · ${model}`;
}

export function countryInitials(name) {
  if (!isPresent(name)) return "?";
  return String(name)
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() || "")
    .join("");
}

/** Short labels for long official port names (dashboard / cards). */
export function shortPortName(name) {
  if (!isPresent(name)) return "—";
  let s = String(name).trim();

  // Prefer city in parentheses: "V.O. Chidambaranar Port (Tuticorin)" → Tuticorin
  const paren = s.match(/\(([^)]+)\)\s*$/);
  if (paren?.[1]) {
    s = paren[1].trim();
  } else {
    s = s
      .replace(/^Port\s+of\s+/i, "")
      .replace(/\s+Port(?:\s+Trust)?$/i, "")
      .replace(/\s+Harbour$/i, "")
      .replace(/\s+Harbor$/i, "")
      .replace(/^Jawaharlal\s+Nehru(?:\s+Port)?(?:\s+Trust)?/i, "JNPT")
      .replace(/^V\.?\s*O\.?\s*Chidambaranar(?:\s+Port)?/i, "Tuticorin")
      .replace(/^Nhava\s+Sheva.*/i, "Nhava Sheva")
      .trim();
  }

  // Keep it card-friendly
  if (s.length > 18) s = `${s.slice(0, 16)}…`;
  return s || "—";
}

/** Compact corridor label: Tuticorin → Colombo */
export function formatRoute(indiaPort, destinationPort, fallback = "—") {
  if (!isPresent(indiaPort) && !isPresent(destinationPort)) return fallback;
  return `${shortPortName(indiaPort)} → ${shortPortName(destinationPort)}`;
}

export function commodityAccent(commodity) {
  const key = String(commodity || "").toLowerCase();
  if (key.includes("onion") || key.includes("coffee")) return "blue";
  if (key.includes("rice") || key.includes("sugar")) return "purple";
  if (key.includes("wheat") || key.includes("maize")) return "orange";
  if (key.includes("tea")) return "cyan";
  return "cyan";
}
