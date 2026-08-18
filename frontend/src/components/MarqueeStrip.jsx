/** Slow editorial marquee — one use between sections. */
export default function MarqueeStrip() {
  const text =
    "DEMAND INTELLIGENCE · PRICE FORECASTING · ROUTE OPTIMISATION · CONTAINER PRIORITY · TRADE DOCUMENTS · AI AGENTS · ";
  return (
    <div className="ed-marquee" aria-hidden="true">
      <div className="ed-marquee-track">
        <span>{text}</span>
        <span>{text}</span>
      </div>
    </div>
  );
}
