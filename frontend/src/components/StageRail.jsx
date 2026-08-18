/**
 * Horizontal stepper for the five pipeline stages.
 */
const STAGES = [
  { id: 0, label: "Demand", short: "01" },
  { id: 1, label: "Prices", short: "02" },
  { id: 2, label: "Logistics", short: "03" },
  { id: 3, label: "Containers", short: "04" },
  { id: 4, label: "Decisions", short: "05" },
];

export default function StageRail({ active, onSelect, hasResult }) {
  return (
    <nav className="stage-rail" aria-label="Pipeline stages">
      {STAGES.map((stage, i) => {
        const isActive = hasResult && active === stage.id;
        const isDone = hasResult && stage.id < active;
        return (
          <button
            key={stage.id}
            type="button"
            className={`stage-step ${isActive ? "is-active" : ""} ${isDone ? "is-done" : ""} ${
              !hasResult ? "is-locked" : ""
            }`}
            onClick={() => hasResult && onSelect(stage.id)}
            disabled={!hasResult}
            aria-current={isActive ? "step" : undefined}
          >
            <span className="stage-num">{stage.short}</span>
            <span className="stage-label">{stage.label}</span>
            {i < STAGES.length - 1 ? <span className="stage-connector" aria-hidden="true" /> : null}
          </button>
        );
      })}
    </nav>
  );
}
