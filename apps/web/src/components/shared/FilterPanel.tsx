import { Chip } from "../ui/Chip";
import type { Classification } from "../../types/api";

type FilterPanelProps = {
  industries: Classification[];
  themes: Classification[];
  selectedIndustries: string[];
  selectedThemes: string[];
  minPrice: string;
  minTurnover: string;
  onToggleIndustry: (code: string) => void;
  onToggleTheme: (code: string) => void;
  onMinPriceChange: (value: string) => void;
  onMinTurnoverChange: (value: string) => void;
};

export const FilterPanel = ({
  industries,
  themes,
  selectedIndustries,
  selectedThemes,
  minPrice,
  minTurnover,
  onToggleIndustry,
  onToggleTheme,
  onMinPriceChange,
  onMinTurnoverChange,
}: FilterPanelProps) => {
  return (
    <div className="space-y-5">
      <div>
        <div className="mb-2 text-xs font-semibold text-[var(--muted)]">
          산업
        </div>
        <div className="flex flex-wrap gap-2">
          {industries.map((industry) => (
            <Chip
              key={industry.code}
              label={`${industry.name} (${industry.code})`}
              selected={selectedIndustries.includes(industry.code)}
              onClick={() => onToggleIndustry(industry.code)}
            />
          ))}
          {industries.length === 0 && (
            <div className="text-xs text-[var(--muted)]">산업 데이터 없음</div>
          )}
        </div>
      </div>
      <div>
        <div className="mb-2 text-xs font-semibold text-[var(--muted)]">테마</div>
        <div className="flex flex-wrap gap-2">
          {themes.map((theme) => (
            <Chip
              key={theme.code}
              label={`${theme.name} (${theme.code})`}
              selected={selectedThemes.includes(theme.code)}
              onClick={() => onToggleTheme(theme.code)}
            />
          ))}
          {themes.length === 0 && (
            <div className="text-xs text-[var(--muted)]">
              테마 데이터 없음
            </div>
          )}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <div className="mb-2 text-xs font-semibold text-[var(--muted)]">
            최소 가격
          </div>
          <input
            value={minPrice}
            onChange={(event) => onMinPriceChange(event.target.value)}
            placeholder="예: 20000"
            className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2 text-xs outline-none"
          />
        </div>
        <div>
          <div className="mb-2 text-xs font-semibold text-[var(--muted)]">
            최소 거래대금
          </div>
          <input
            value={minTurnover}
            onChange={(event) => onMinTurnoverChange(event.target.value)}
            placeholder="예: 10000000000"
            className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2 text-xs outline-none"
          />
        </div>
      </div>
    </div>
  );
};
