import { cn } from "../../lib/utils";

type ChipProps = {
  label: string;
  selected?: boolean;
  onClick?: () => void;
};

export const Chip = ({ label, selected, onClick }: ChipProps) => {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-full border px-3 py-1 text-xs font-medium transition",
        selected
          ? "border-[var(--accent)] bg-[var(--accent)] text-white"
          : "border-[var(--border)] bg-[var(--surface)] text-[var(--muted)] hover:border-[var(--accent)]"
      )}
    >
      {label}
    </button>
  );
};
