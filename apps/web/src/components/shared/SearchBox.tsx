import { Search } from "lucide-react";

type SearchBoxProps = {
  value: string;
  onChange: (value: string) => void;
};

export const SearchBox = ({ value, onChange }: SearchBoxProps) => {
  return (
    <div className="flex min-w-0 flex-1 items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2 text-xs text-[var(--muted)]">
      <Search size={14} />
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="티커 또는 회사명 검색"
        className="w-full bg-transparent text-xs font-medium text-[var(--text)] outline-none placeholder:text-[var(--muted)]"
      />
    </div>
  );
};
