type ErrorStateProps = {
  title?: string;
  description?: string;
};

export const ErrorState = ({
  title = "데이터를 불러오지 못했습니다.",
  description = "잠시 후 다시 시도해 주세요.",
}: ErrorStateProps) => {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-[var(--border)] bg-[var(--surface)] px-6 py-10 text-center text-sm text-[var(--muted)]">
      <div className="text-base font-semibold text-[var(--text)]">{title}</div>
      <p className="mt-2 max-w-sm">{description}</p>
    </div>
  );
};
