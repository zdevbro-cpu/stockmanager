import { DatePicker } from "../shared/DatePicker";
import { SearchBox } from "../shared/SearchBox";
import { useAppSettings } from "../../store/appStore";

export const TopBar = () => {
  const { asOfDate, setAsOfDate, searchQuery, setSearchQuery, demoMode } =
    useAppSettings();

  return (
    <header className="sticky top-0 z-20 flex flex-wrap items-center gap-3 border-b border-[var(--border)] bg-[var(--surface)] px-4 py-3 backdrop-blur">
      <div className="min-w-[140px] text-sm font-semibold text-[var(--text)]">
        StockManager
      </div>
      <div className="flex flex-1 flex-wrap items-center gap-3">
        <SearchBox value={searchQuery} onChange={setSearchQuery} />
        <DatePicker value={asOfDate} onChange={setAsOfDate} />
      </div>
      <div className="rounded-full border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-1 text-xs text-[var(--muted)]">
        {demoMode ? "데모 모드" : "실시간"}
      </div>
    </header>
  );
};
