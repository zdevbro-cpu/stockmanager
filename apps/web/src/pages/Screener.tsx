import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  getClassificationNodes,
  getSecurityClassifications,
  getUniverse,
} from "../lib/apiClient";
import { useAppSettings } from "../store/appStore";
import { FilterPanel } from "../components/shared/FilterPanel";
import { Drawer } from "../components/ui/Drawer";
import { DataTable } from "../components/ui/DataTable";
import { Panel } from "../components/shared/Panel";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { ErrorState } from "../components/ui/ErrorState";
import { formatNumber } from "../lib/utils";
import type { Classification, UniverseItem } from "../types/api";
import { useWatchlist } from "../store/watchlistStore";
import { useErrorToast } from "../lib/useErrorToast";

const ScreenerPage = () => {
  const { asOfDate, apiBaseUrl, demoMode, searchQuery } = useAppSettings();
  const { addTicker } = useWatchlist();
  const [filterOpen, setFilterOpen] = useState(false);
  const [selected, setSelected] = useState<UniverseItem | null>(null);
  const [selectedIndustries, setSelectedIndustries] = useState<string[]>([]);
  const [selectedThemes, setSelectedThemes] = useState<string[]>([]);
  const [minPrice, setMinPrice] = useState("");
  const [minTurnover, setMinTurnover] = useState("");

  const industriesQuery = useQuery({
    queryKey: ["industries", apiBaseUrl, demoMode],
    queryFn: () =>
      getClassificationNodes(
        { baseUrl: apiBaseUrl, demoMode },
        { taxonomy_id: "KIS_INDUSTRY", level: 1 }
      ),
  });

  const themesQuery = useQuery({
    queryKey: ["themes", apiBaseUrl, demoMode],
    queryFn: () =>
      getClassificationNodes(
        { baseUrl: apiBaseUrl, demoMode },
        { taxonomy_id: "THEME" }
      ),
  });

  const universeQuery = useQuery({
    queryKey: [
      "universe",
      asOfDate,
      selectedIndustries,
      selectedThemes,
      minPrice,
      minTurnover,
      apiBaseUrl,
      demoMode,
    ],
    queryFn: () =>
      getUniverse(
        { baseUrl: apiBaseUrl, demoMode },
        {
          as_of_date: asOfDate,
          include_industry_codes: selectedIndustries,
          include_theme_ids: selectedThemes,
          min_price: minPrice ? Number(minPrice) : null,
          min_turnover: minTurnover ? Number(minTurnover) : null,
        }
      ),
  });

  useErrorToast(
    universeQuery.isError,
    "유니버스 데이터를 불러오지 못했습니다."
  );

  const filteredRows = useMemo(() => {
    const list = universeQuery.data ?? [];
    if (!searchQuery) return list;
    return list.filter(
      (item) =>
        item.ticker.includes(searchQuery.trim()) ||
        item.name_ko.includes(searchQuery.trim())
    );
  }, [universeQuery.data, searchQuery]);

  const detailQuery = useQuery({
    queryKey: ["security-classifications", selected?.ticker, apiBaseUrl, demoMode],
    queryFn: () =>
      selected
        ? getSecurityClassifications(
            { baseUrl: apiBaseUrl, demoMode },
            selected.ticker
          )
        : Promise.resolve([] as Classification[]),
    enabled: !!selected,
  });

  const columns = [
    { header: "티커", key: "ticker", width: "90px" },
    { header: "기업명", key: "name_ko" },
    { header: "시장", key: "market", width: "90px" },
    {
      header: "산업",
      key: "sector_name",
      render: (row: UniverseItem) => row.sector_name ?? "-",
    },
    {
      header: "가격",
      key: "last_price_krw",
      render: (row: UniverseItem) => formatNumber(row.last_price_krw),
      align: "right",
    },
    {
      header: "거래대금(20D)",
      key: "avg_turnover_krw_20d",
      render: (row: UniverseItem) => formatNumber(row.avg_turnover_krw_20d),
      align: "right",
    },
  ];

  const toggleIndustry = (code: string) => {
    setSelectedIndustries((prev) =>
      prev.includes(code) ? prev.filter((item) => item !== code) : [...prev, code]
    );
  };

  const toggleTheme = (code: string) => {
    setSelectedThemes((prev) =>
      prev.includes(code) ? prev.filter((item) => item !== code) : [...prev, code]
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-lg font-semibold text-[var(--text)]">스크리너</div>
          <div className="text-xs text-[var(--muted)]">
            유니버스 필터와 조건을 적용해 종목을 탐색합니다.
          </div>
        </div>
        <div className="lg:hidden">
          <Button
            label="필터 열기"
            variant="outline"
            onClick={() => setFilterOpen(true)}
          />
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <div className="hidden lg:block">
          <Panel title="필터">
            <FilterPanel
              industries={industriesQuery.data ?? []}
              themes={themesQuery.data ?? []}
              selectedIndustries={selectedIndustries}
              selectedThemes={selectedThemes}
              minPrice={minPrice}
              minTurnover={minTurnover}
              onToggleIndustry={toggleIndustry}
              onToggleTheme={toggleTheme}
              onMinPriceChange={setMinPrice}
              onMinTurnoverChange={setMinTurnover}
            />
          </Panel>
        </div>

        <div>
          <Panel title={`결과 (${filteredRows.length})`}>
            {universeQuery.isError ? (
              <ErrorState />
            ) : (
              <DataTable
                columns={columns}
                rows={filteredRows}
                loading={universeQuery.isLoading}
                emptyMessage="조건에 맞는 종목이 없습니다."
                onRowClick={(row) => setSelected(row)}
              />
            )}
          </Panel>
        </div>
      </div>

      <Drawer
        open={filterOpen}
        onClose={() => setFilterOpen(false)}
        title="필터"
        placement="bottom"
      >
        <FilterPanel
          industries={industriesQuery.data ?? []}
          themes={themesQuery.data ?? []}
          selectedIndustries={selectedIndustries}
          selectedThemes={selectedThemes}
          minPrice={minPrice}
          minTurnover={minTurnover}
          onToggleIndustry={toggleIndustry}
          onToggleTheme={toggleTheme}
          onMinPriceChange={setMinPrice}
          onMinTurnoverChange={setMinTurnover}
        />
      </Drawer>

      <Drawer
        open={!!selected}
        onClose={() => setSelected(null)}
        title={selected ? `${selected.name_ko} 상세` : "상세"}
      >
        {selected && (
          <div className="space-y-4 text-sm">
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] p-4">
              <div className="text-xs text-[var(--muted)]">티커</div>
              <div className="text-lg font-semibold">{selected.ticker}</div>
              <div className="mt-1 text-xs text-[var(--muted)]">
                {selected.market} · {selected.sector_name ?? "산업 미정"}
              </div>
            </div>
            <div>
              <div className="mb-2 text-xs font-semibold text-[var(--muted)]">
                분류 태그
              </div>
              <div className="flex flex-wrap gap-2">
                {(detailQuery.data ?? []).map((tag) => (
                  <Badge
                    key={tag.code}
                    label={`${tag.name} (${tag.code})`}
                    variant="info"
                  />
                ))}
                {(detailQuery.data ?? []).length === 0 && (
                  <span className="text-xs text-[var(--muted)]">
                    분류 정보 없음
                  </span>
                )}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-lg border border-[var(--border)] p-3">
                <div className="text-xs text-[var(--muted)]">현재가</div>
                <div className="text-sm font-semibold">
                  {formatNumber(selected.last_price_krw)}
                </div>
              </div>
              <div className="rounded-lg border border-[var(--border)] p-3">
                <div className="text-xs text-[var(--muted)]">거래대금</div>
                <div className="text-sm font-semibold">
                  {formatNumber(selected.avg_turnover_krw_20d)}
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              <Button label="관심 추가" onClick={() => addTicker(selected.ticker)} />
              <Button label="시그널 보기" variant="outline" />
              <Button label="추천 보기" variant="outline" />
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default ScreenerPage;
