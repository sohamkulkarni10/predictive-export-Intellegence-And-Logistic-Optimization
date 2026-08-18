export default function PageContainer({ eyebrow, title, subtitle, actions, children, className = "" }) {
  return (
    <div className={`page-container ${className}`}>
      <header className="page-heading">
        <div>
          {eyebrow ? <p>{eyebrow}</p> : null}
          <h2>{title}</h2>
          {subtitle ? <span>{subtitle}</span> : null}
        </div>
        {actions ? <div className="page-heading__actions">{actions}</div> : null}
      </header>
      {children}
    </div>
  );
}
