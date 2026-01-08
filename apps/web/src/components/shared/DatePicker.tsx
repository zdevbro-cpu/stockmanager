type DatePickerProps = {
  value: string;
  onChange: (value: string) => void;
};

export const DatePicker = ({ value, onChange }: DatePickerProps) => {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2 text-xs text-[var(--muted)]">
      <span>기준일</span>
      <input
        type="date"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="bg-transparent text-xs font-semibold text-[var(--text)] outline-none"
      />
    </div>
  );
};
