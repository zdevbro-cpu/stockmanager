import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getRecommendations } from "../lib/apiClient";
import { useAppSettings } from "../store/appStore";
import { DataTable } from "../components/ui/DataTable";
import { Drawer } from "../components/ui/Drawer";
import { Button } from "../components/ui/Button";
import { Panel } from "../components/shared/Panel";
import { ErrorState } from "../components/ui/ErrorState";
import { RationalePanel } from "../components/shared/RationalePanel";
import { formatPercent } from "../lib/utils";
import type { RecommendationItem } from "../types/api";
import { useErrorToast } from "../lib/useErrorToast";

const RecommendationsPage = () => {
  const { asOfDate, apiBaseUrl, demoMode, searchQuery } = useAppSettings();
  const [strategyId, setStrategyId] = useState("prod_v1");
  const [strategyVersion, setStrategyVersion] = useState("1.0");
  const [selected, setSelected] = useState<RecommendationItem | null>(null);

  const recommendationsQuery = useQuery({
    queryKey: [
      "recommendations",
      asOfDate,
      strategyId,
      strategyVersion,
      apiBaseUrl,
      demoMode,
    ],
    queryFn: () =>
      getRecommendations(
        { baseUrl: apiBaseUrl, demoMode },
        { as_of_date: asOfDate, strategy_id: strategyId, strategy_version: strategyVersion }
      ),
  });

  useErrorToast(
    recommendationsQuery.isError,
    "추천 데이터를 불러오지 못했습니다."
  );

  const rows = useMemo(() => {
    const list = recommendationsQuery.data ?? [];
    if (!searchQuery) return list;
    return list.filter((item) => item.ticker.includes(searchQuery.trim()));
  }, [recommendationsQuery.data, searchQuery]);

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
      header: "근거",
      key: "rationale",
      render: (row: RecommendationItem) => (
        <Button label="Explain" size="sm" variant="outline" onClick={() => setSelected(row)} />
      ),
      align: "right",
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="text-lg font-semibold text-[var(--text)]">추천 TopN</div>
          <div className="text-xs text-[var(--muted)]">
            전략별 추천 종목과 근거를 확인합니다.
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={strategyId}
            onChange={(event) => setStrategyId(event.target.value)}
            className="rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2 text-xs"
          >
            <option value="prod_v1">prod_v1</option>
            <option value="alpha_v1">alpha_v1</option>
          </select>
          <select
            value={strategyVersion}
            onChange={(event) => setStrategyVersion(event.target.value)}
            className="rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2 text-xs"
          >
            <option value="1.0">1.0</option>
            <option value="0.9">0.9</option>
          </select>
          <Button label="Export" variant="outline" />
        </div>
      </div>

      <Panel title="추천 리스트">
        {recommendationsQuery.isError ? (
          <ErrorState />
        ) : (
          <DataTable
            columns={columns}
            rows={rows}
            loading={recommendationsQuery.isLoading}
            emptyMessage="추천 데이터가 없습니다."
          />
        )}
      </Panel>

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

export default RecommendationsPage;
