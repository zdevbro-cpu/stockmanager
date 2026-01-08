import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getRecommendations, getSignals, getUniverse } from "../lib/apiClient";
import { useAppSettings } from "../store/appStore";
import { useWatchlist } from "../store/watchlistStore";
import { DataTable } from "../components/ui/DataTable";
import { Drawer } from "../components/ui/Drawer";
import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { Panel } from "../components/shared/Panel";
import { KpiCard } from "../components/shared/KpiCard";
import { ChartPlaceholder } from "../components/shared/ChartPlaceholder";
import { RationalePanel } from "../components/shared/RationalePanel";
import { formatNumber, formatPercent, formatDateLabel } from "../lib/utils";
import type { RecommendationItem, SignalItem, UniverseItem } from "../types/api";
import { useErrorToast } from "../lib/useErrorToast";

const HomePage = () => {
  const { asOfDate, apiBaseUrl, demoMode, searchQuery } = useAppSettings();
  const { items, addTicker, hasTicker } = useWatchlist();
  const [selected, setSelected] = useState<RecommendationItem | null>(null);
  const marketSnapshot = [
    { label: "KOSPI", value: "2,746.3", change: "+0.42%" },
    { label: "KOSDAQ", value: "902.1", change: "-0.18%" },
    { label: "USD/KRW", value: "1,321.5", change: "+0.06%" },
  ];

  const universeQuery = useQuery({
    queryKey: ["universe", asOfDate, apiBaseUrl, demoMode],
    queryFn: () =>
      getUniverse(
        { baseUrl: apiBaseUrl, demoMode },
        { as_of_date: asOfDate }
      ),
  });

  const recommendationsQuery = useQuery({
    queryKey: ["recommendations", asOfDate, apiBaseUrl, demoMode],
    queryFn: () =>
      getRecommendations(
        { baseUrl: apiBaseUrl, demoMode },
        { as_of_date: asOfDate, strategy_id: "prod_v1", strategy_version: "1.0" }
      ),
  });

  const signalsQuery = useQuery({
    queryKey: ["watchlist-signals", items, apiBaseUrl, demoMode],
    queryFn: async () => {
      const results = await Promise.all(
        items.map((item) =>
          getSignals(
            { baseUrl: apiBaseUrl, demoMode },
            { ticker: item.ticker, horizon: "1d" }
          )
        )
      );
      return results.flat();
    },
    enabled: items.length > 0,
  });

  useErrorToast(
    universeQuery.isError || recommendationsQuery.isError,
    "API 연결에 실패했습니다. 데모 모드를 확인하세요."
  );

  const filteredRecommendations = useMemo(() => {
    const list = recommendationsQuery.data ?? [];
    if (!searchQuery) return list;
    return list.filter((item) => item.ticker.includes(searchQuery.trim()));
  }, [recommendationsQuery.data, searchQuery]);

  const topN = filteredRecommendations.slice(0, 5);
  const lastUpdate = recommendationsQuery.data?.[0]?.as_of_date ?? asOfDate;
  const watchlistSignals = signalsQuery.data ?? [];

  const columns = [
    { header: "순위", key: "rank", width: "70px" },
    { header: "티커", key: "ticker" },
    {
      header: "타겟 비중",
      key: "target_weight",
      render: (row: RecommendationItem) => formatPercent(row.target_weight),
      align: "right",
    },
    {
      header: "점수",
      key: "score",
      render: (row: RecommendationItem) => row.score ?? "-",
      align: "right",
    },
    {
      header: "액션",
      key: "action",
      render: (row: RecommendationItem) => (
        <div className="flex flex-wrap items-center justify-end gap-2">
          <Button
            label="Explain"
            size="sm"
            variant="outline"
            onClick={() => setSelected(row)}
          />
          <Button
            label={hasTicker(row.ticker) ? "관심 등록됨" : "관심 추가"}
            size="sm"
            variant={hasTicker(row.ticker) ? "ghost" : "primary"}
            onClick={() => addTicker(row.ticker)}
            disabled={hasTicker(row.ticker)}
          />
        </div>
      ),
      align: "right",
    },
  ];

  return (
    <div className="space-y-6">
      <section className="grid gap-4 lg:grid-cols-4">
        <KpiCard
          label="유니버스 수"
          value={formatNumber(universeQuery.data?.length ?? 0)}
          helper="최신 기준"
        />
        <KpiCard label="추천 Top N" value={formatNumber(topN.length)} />
        <KpiCard label="최근 업데이트" value={formatDateLabel(lastUpdate)} />
        <KpiCard label="기준일" value={formatDateLabel(asOfDate)} />
      </section>

      <Panel title="시장 지수">
        <div className="grid gap-3 sm:grid-cols-3">
          {marketSnapshot.map((item) => (
            <div
              key={item.label}
              className="rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] px-4 py-3"
            >
              <div className="text-xs text-[var(--muted)]">{item.label}</div>
              <div className="mt-1 text-lg font-semibold text-[var(--text)]">
                {item.value}
              </div>
              <div className="text-xs text-[var(--muted)]">{item.change}</div>
            </div>
          ))}
        </div>
      </Panel>

      <section className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Panel
            title="Today’s Recommendations"
            action={<div className="text-xs text-[var(--muted)]">prod_v1 / 1.0</div>}
          >
            {recommendationsQuery.isError ? (
              <ErrorState />
            ) : (
              <DataTable
                columns={columns}
                rows={topN}
                loading={recommendationsQuery.isLoading}
                emptyMessage="추천 데이터가 없습니다."
              />
            )}
          </Panel>

          <Panel title="Watchlist Signals Summary">
            {items.length === 0 && (
              <EmptyState
                title="관심종목이 비어 있습니다."
                description="추천 또는 관심종목 화면에서 티커를 추가하세요."
              />
            )}
            {items.length > 0 && signalsQuery.isError && <ErrorState />}
            {items.length > 0 && !signalsQuery.isError && (
              <div className="space-y-3 text-sm text-[var(--text)]">
                {watchlistSignals.length === 0 && !signalsQuery.isLoading && (
                  <div className="text-sm text-[var(--muted)]">
                    최신 신호가 없습니다.
                  </div>
                )}
                {watchlistSignals.map((signal: SignalItem) => (
                  <div
                    key={`${signal.ticker}-${signal.ts}`}
                    className="flex items-center justify-between rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] px-4 py-3"
                  >
                    <div>
                      <div className="text-sm font-semibold">{signal.ticker}</div>
                      <div className="text-xs text-[var(--muted)]">
                        {signal.triggers.join(", ") || "트리거 없음"}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-semibold text-[var(--accent)]">
                        {signal.signal}
                      </div>
                      <div className="text-xs text-[var(--muted)]">
                        신뢰도 {signal.confidence ?? "-"}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Panel>
        </div>

        <div className="space-y-6">
          <Panel title="Industry Snapshot">
            <ChartPlaceholder title="Industry Map" />
          </Panel>
          <Panel title="Theme Snapshot">
            <ChartPlaceholder title="Theme Pulse" />
          </Panel>
          <Panel title="Universe Highlights">
            <div className="space-y-2 text-xs text-[var(--muted)]">
              {(universeQuery.data ?? []).slice(0, 4).map((item: UniverseItem, index) => (
                <div
                  key={item.ticker}
                  className="flex items-center justify-between rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2"
                  style={{ ["--delay" as any]: `${index * 80}ms` }}
                >
                  <div>
                    <div className="text-sm font-semibold text-[var(--text)]">
                      {item.name_ko}
                    </div>
                    <div className="text-[11px]">{item.ticker}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs font-semibold">
                      {formatNumber(item.last_price_krw)}
                    </div>
                    <div className="text-[11px]">{item.sector_name ?? "-"}</div>
                  </div>
                </div>
              ))}
            </div>
          </Panel>
        </div>
      </section>

      <Drawer
        open={!!selected}
        onClose={() => setSelected(null)}
        title={selected ? `${selected.ticker} 추천 근거` : "추천 근거"}
      >
        <RationalePanel rationale={selected?.rationale ?? null} />
        {selected?.rationale && (
          <details className="mt-6 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4 text-xs">
            <summary className="cursor-pointer font-semibold text-[var(--text)]">
              JSON 원문 보기
            </summary>
            <pre className="mt-3 max-w-full overflow-x-auto whitespace-pre-wrap break-words text-[11px] text-[var(--muted)]">
              {JSON.stringify(selected.rationale, null, 2)}
            </pre>
          </details>
        )}
      </Drawer>
    </div>
  );
};

export default HomePage;
