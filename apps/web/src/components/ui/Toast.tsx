import { createContext, useContext, useMemo, useState } from "react";
import { cn } from "../../lib/utils";

type ToastItem = {
  id: string;
  message: string;
  variant?: "error" | "info";
};

type ToastContextValue = {
  push: (message: string, variant?: ToastItem["variant"]) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

export const ToastProvider = ({ children }: { children: React.ReactNode }) => {
  const [items, setItems] = useState<ToastItem[]>([]);

  const push = (message: string, variant: ToastItem["variant"] = "info") => {
    const id = `${Date.now()}-${Math.random()}`;
    setItems((prev) => [...prev, { id, message, variant }]);
    setTimeout(() => {
      setItems((prev) => prev.filter((item) => item.id !== id));
    }, 3000);
  };

  const value = useMemo(() => ({ push }), []);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed right-6 top-6 z-50 space-y-2">
        {items.map((item) => (
          <div
            key={item.id}
            className={cn(
              "rounded-lg border px-4 py-3 text-sm shadow-soft",
              item.variant === "error"
                ? "border-orange-200 bg-orange-50 text-orange-700"
                : "border-[var(--border)] bg-[var(--surface)] text-[var(--text)]"
            )}
          >
            {item.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("ToastProvider가 필요합니다.");
  }
  return context;
};
