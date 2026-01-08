import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getRecommendations, getSignals } from "../lib/apiClient";
import { useAppSettings } from "../store/appStore";
import { useWatchlist } from "../store/watchlistStore";
import { Panel } from "../components/shared/Panel";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { ErrorState } from "../components/ui/ErrorState";
import { formatPercent } from "../lib/utils";
import { useErrorToast } from "../lib/useErrorToast";

const WatchlistPage = () => {
  const { asOfDate, apiBaseUrl, demoMode } = useAppSettings();
  const { items, addTicker, removeTicker, setNote } = useWatchlist();
  const [input, setInput] = useState("");

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
      if (items.length === 0) return [];
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
    recommendationsQuery.isError || signalsQuery.isError,
    "관심종목 데이터를 불러오지 못했습니다."
  );

  const recommendationMap = useMemo(() => {
    const map = new Map<string, { target_weight: number }>();
    (recommendationsQuery.data ?? []).forEach((item) => {
      map.set(item.ticker, { target_weight: item.target_weight });
    });
    return map;
  }, [recommendationsQuery.data]);

  const signalMap = useMemo(() => {
    const map = new Map<string, string>();
    (signalsQuery.data ?? []).forEach((signal) => {
      map.set(signal.ticker, signal.signal);
    });
    return map;
  }, [signalsQuery.data]);

  return (
    <div className="space-y-6">
      <div>
        <div className="text-lg font-semibold text-[var(--text)]">관심종목</div>
        <div className="text-xs text-[var(--muted)]">
          로컬에 저장된 관심종목과 메모를 관리합니다.
        </div>
      </div>

      <Panel
        title="티커 추가"
        action={
          <div className="flex items-center gap-2">
            <input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="예: 005930"
              className="w-[160px] rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2 text-xs"
            />
            <Button
              label="추가"
              size="sm"
              onClick={() => {
                addTicker(input);
                setInput("");
              }}
            />
          </div>
        }
      >
        {recommendationsQuery.isError && <ErrorState />}
        <div className="space-y-3">
          {items.length === 0 && (
            <div className="text-sm text-[var(--muted)]">
              관심종목이 없습니다. 티커를 추가하세요.
            </div>
          )}
          {items.map((item) => {
            const reco = recommendationMap.get(item.ticker);
            const signal = signalMap.get(item.ticker);
            return (
              <div
                key={item.ticker}
                className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4 shadow-card"
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold">{item.ticker}</div>
                    <div className="text-xs text-[var(--muted)]">
                      {signal ? `최신 신호: ${signal}` : "신호 없음"}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {reco && (
                      <Badge label={`추천 ${formatPercent(reco.target_weight)}`} variant="info" />
                    )}
                    <Button
                      label="삭제"
                      size="sm"
                      variant="outline"
                      onClick={() => removeTicker(item.ticker)}
                    />
                  </div>
                </div>
                <textarea
                  value={item.note ?? ""}
                  onChange={(event) => setNote(item.ticker, event.target.value)}
                  placeholder="메모를 입력하세요."
                  className="mt-3 w-full rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2 text-xs"
                  rows={2}
                />
              </div>
            );
          })}
        </div>
      </Panel>
    </div>
  );
};

export default WatchlistPage;
