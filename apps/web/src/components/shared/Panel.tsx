import { cn } from "../../lib/utils";

type PanelProps = {
  title?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
};

export const Panel = ({ title, action, children, className }: PanelProps) => {
  return (
    <section
      className={cn(
        "min-w-0 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-card",
        className
      )}
    >
      {(title || action) && (
        <div className="mb-4 flex items-center justify-between">
          {title && (
            <h3 className="text-sm font-semibold text-[var(--text)]">
              {title}
            </h3>
          )}
          {action}
        </div>
      )}
      {children}
    </section>
  );
};
