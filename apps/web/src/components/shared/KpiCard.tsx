type KpiCardProps = {
  label: string;
  value: string;
  helper?: string;
};

export const KpiCard = ({ label, value, helper }: KpiCardProps) => {
  return (
    <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-4 shadow-card">
      <div className="text-xs font-semibold text-[var(--muted)]">{label}</div>
      <div className="mt-2 text-2xl font-semibold text-[var(--text)]">
        {value}
      </div>
      {helper && <div className="mt-1 text-xs text-[var(--muted)]">{helper}</div>}
    </div>
  );
};
