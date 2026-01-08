import { cn } from "../../lib/utils";

type ButtonProps = {
  label: string;
  onClick?: () => void;
  variant?: "primary" | "ghost" | "outline";
  size?: "sm" | "md";
  disabled?: boolean;
  type?: "button" | "submit";
};

const variantClasses: Record<NonNullable<ButtonProps["variant"]>, string> = {
  primary:
    "bg-[var(--accent)] text-white border-transparent hover:bg-[var(--accent-2)]",
  ghost: "bg-transparent text-[var(--text)] hover:bg-[var(--surface-muted)]",
  outline:
    "bg-[var(--surface)] text-[var(--text)] border-[var(--border)] hover:border-[var(--accent)]",
};

const sizeClasses: Record<NonNullable<ButtonProps["size"]>, string> = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-4 py-2 text-sm",
};

export const Button = ({
  label,
  onClick,
  variant = "primary",
  size = "md",
  disabled,
  type = "button",
}: ButtonProps) => {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "inline-flex items-center justify-center rounded-md border font-semibold transition",
        variantClasses[variant],
        sizeClasses[size],
        disabled && "cursor-not-allowed opacity-60"
      )}
    >
      {label}
    </button>
  );
};
