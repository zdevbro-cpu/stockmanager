type EmptyStateProps = {
  title: string;
  description?: string;
};

export const EmptyState = ({ title, description }: EmptyStateProps) => {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-[var(--border)] bg-[var(--surface)] px-6 py-10 text-center text-sm text-[var(--muted)]">
      <div className="text-base font-semibold text-[var(--text)]">{title}</div>
      {description && <p className="mt-2 max-w-sm">{description}</p>}
    </div>
  );
};
