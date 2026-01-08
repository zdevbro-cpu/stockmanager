import { cn } from "../../lib/utils";

type BadgeProps = {
  label: string;
  variant?: "default" | "success" | "warning" | "danger" | "info";
};

const variantStyles: Record<NonNullable<BadgeProps["variant"]>, string> = {
  default: "bg-[var(--surface-muted)] text-[var(--muted)] border-[var(--border)]",
  success: "bg-emerald-50 text-emerald-700 border-emerald-200",
  warning: "bg-amber-50 text-amber-700 border-amber-200",
  danger: "bg-orange-50 text-orange-700 border-orange-200",
  info: "bg-sky-50 text-sky-700 border-sky-200",
};

export const Badge = ({ label, variant = "default" }: BadgeProps) => {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold",
        variantStyles[variant]
      )}
    >
      {label}
    </span>
  );
};
