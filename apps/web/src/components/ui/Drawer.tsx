import { useEffect } from "react";
import { cn } from "../../lib/utils";

type DrawerProps = {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  placement?: "right" | "bottom";
};

export const Drawer = ({
  open,
  onClose,
  title,
  children,
  placement = "right",
}: DrawerProps) => {
  if (!open) return null;

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  return (
    <div
      className={cn(
        "fixed inset-0 z-40 transition",
        open ? "pointer-events-auto" : "pointer-events-none"
      )}
      aria-hidden={!open}
    >
      <div
        className={cn(
          "absolute inset-0 bg-slate-900/30 backdrop-blur-sm transition",
          open ? "opacity-100" : "opacity-0"
        )}
        onClick={onClose}
      />
      <div
        className={cn(
          "absolute bg-[var(--surface)] shadow-2xl transition",
          placement === "right" &&
            "right-0 top-0 h-full w-full max-w-lg sm:w-[420px]",
          placement === "bottom" &&
            "bottom-0 left-0 right-0 max-h-[80vh] rounded-t-2xl",
          open
            ? "translate-x-0 translate-y-0"
            : placement === "right"
              ? "translate-x-full"
              : "translate-y-full"
        )}
      >
        <div className="flex items-center justify-between border-b border-[var(--border)] px-5 py-4">
          <div className="text-sm font-semibold text-[var(--text)]">
            {title ?? "상세 보기"}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-[var(--border)] px-2 py-1 text-xs text-[var(--muted)] hover:border-[var(--accent)]"
          >
            닫기
          </button>
        </div>
        <div className="h-[calc(100%-60px)] overflow-y-auto px-5 py-4">
          {children}
        </div>
      </div>
    </div>
  );
};
