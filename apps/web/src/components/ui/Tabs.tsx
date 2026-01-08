import { cn } from "../../lib/utils";

type TabItem = {
  value: string;
  label: string;
};

type TabsProps = {
  items: TabItem[];
  value: string;
  onChange: (value: string) => void;
};

export const Tabs = ({ items, value, onChange }: TabsProps) => {
  return (
    <div className="flex flex-wrap gap-2 rounded-full border border-[var(--border)] bg-[var(--surface)] p-1">
      {items.map((item) => (
        <button
          key={item.value}
          type="button"
          onClick={() => onChange(item.value)}
          className={cn(
            "rounded-full px-3 py-1 text-xs font-semibold transition",
            value === item.value
              ? "bg-[var(--accent)] text-white"
              : "text-[var(--muted)] hover:bg-[var(--surface-muted)]"
          )}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
};
