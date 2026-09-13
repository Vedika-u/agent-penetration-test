interface StatTileProps {
  label: string;
  value: string;
  tone?: "neutral" | "good" | "critical";
  hint?: string;
}

export function StatTile({ label, value, tone = "neutral", hint }: StatTileProps) {
  return (
    <div className={`stat-tile stat-tile--${tone}`}>
      <div className="stat-tile__label">{label}</div>
      <div className="stat-tile__value">{value}</div>
      {hint ? <div className="stat-tile__hint">{hint}</div> : null}
    </div>
  );
}
