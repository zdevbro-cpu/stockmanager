type ChartPlaceholderProps = {
  title: string;
  height?: string;
};

export const ChartPlaceholder = ({
  title,
  height = "h-40",
}: ChartPlaceholderProps) => {
  return (
    <div
      className={`flex ${height} items-center justify-center rounded-xl border border-dashed border-[var(--border)] bg-[var(--surface-muted)] text-xs text-[var(--muted)]`}
    >
      {title} (차트 준비 중)
    </div>
  );
};
