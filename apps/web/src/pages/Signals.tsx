import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getSignals } from "../lib/apiClient";
import { useAppSettings } from "../store/appStore";
import { useWatchlist } from "../store/watchlistStore";
import { Panel } from "../components/shared/Panel";
import { Tabs } from "../components/ui/Tabs";
import { Badge } from "../components/ui/Badge";
import { Drawer } from "../components/ui/Drawer";
import { ChartPlaceholder } from "../components/shared/ChartPlaceholder";
import { ErrorState } from "../components/ui/ErrorState";
import { formatDateLabel } from "../lib/utils";
import type { SignalItem } from "../types/api";
import { useErrorToast } from "../lib/useErrorToast";

const horizonOptions = [
  { value: "1d", label: "1일" },
  { value: "3d", label: "3일" },
  { value: "1w", label: "1주" },
];

const SignalsPage = () => {
  const { apiBaseUrl, demoMode } = useAppSettings();
  const { items } = useWatchlist();
  const [horizon, setHorizon] = useState("1d");
  const [manualTicker, setManualTicker] = useState("");
  const [selected, setSelected] = useState<SignalItem | null>(null);

  const tickers = manualTicker
    ? [manualTicker.trim()]
    : items.map((item) => item.ticker);

  const signalsQuery = useQuery({
    queryKey: ["signals", tickers, horizon, apiBaseUrl, demoMode],
    queryFn: async () => {
      if (tickers.length === 0) return [];
      const results = await Promise.all(
        tickers.map((ticker) =>
          getSignals({ baseUrl: apiBaseUrl, demoMode }, { ticker, horizon })
        )
      );
      return results.flat();
    },
  });

  useErrorToast(signalsQuery.isError, "시그널 데이터를 불러오지 못했습니다.");

  const rows = useMemo(() => {
    const list = signalsQuery.data ?? [];
    return list.sort((a, b) => b.ts.localeCompare(a.ts));
  }, [signalsQuery.data]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="text-lg font-semibold text-[var(--text)]">시그널</div>
          <div className="text-xs text-[var(--muted)]">
            관심종목 기준 최신 타이밍 신호를 확인합니다.
          </div>
        </div>
        <Tabs items={horizonOptions} value={horizon} onChange={setHorizon} />
      </div>

      <Panel
        title="티커 입력"
        action={
          <input
            value={manualTicker}
            onChange={(event) => setManualTicker(event.target.value)}
            placeholder="예: 005930"
            className="w-[140px] rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2 text-xs"
          />
        }
      >
        {signalsQuery.isError ? (
          <ErrorState />
        ) : (
          <div className="space-y-3 text-sm">
            {rows.length === 0 && !signalsQuery.isLoading && (
              <div className="text-sm text-[var(--muted)]">
                조회할 티커를 선택하거나 입력하세요.
              </div>
            )}
            {rows.map((signal) => (
              <button
                key={`${signal.ticker}-${signal.ts}`}
                type="button"
                onClick={() => setSelected(signal)}
                className="flex w-full items-center justify-between rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-3 text-left shadow-card"
              >
                <div>
                  <div className="text-sm font-semibold text-[var(--text)]">
                    {signal.ticker}
                  </div>
                  <div className="text-xs text-[var(--muted)]">
                    {signal.triggers.join(", ") || "트리거 없음"}
                  </div>
                </div>
                <div className="text-right">
                  <Badge label={signal.signal} variant="info" />
                  <div className="mt-1 text-xs text-[var(--muted)]">
                    업데이트 {formatDateLabel(signal.ts.slice(0, 10))}
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </Panel>

      <Drawer
        open={!!selected}
        onClose={() => setSelected(null)}
        title={selected ? `${selected.ticker} 시그널 상세` : "시그널 상세"}
      >
        {selected && (
          <div className="space-y-4 text-sm">
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] p-4">
              <div className="text-xs text-[var(--muted)]">신호</div>
              <div className="text-lg font-semibold">{selected.signal}</div>
              <div className="mt-1 text-xs text-[var(--muted)]">
                신뢰도 {selected.confidence ?? "-"} · 모델 {selected.model_version ?? "-"}
              </div>
            </div>
            <div>
              <div className="mb-2 text-xs font-semibold text-[var(--muted)]">
                트리거
              </div>
              <div className="flex flex-wrap gap-2">
                {selected.triggers.map((trigger) => (
                  <Badge key={trigger} label={trigger} variant="default" />
                ))}
                {selected.triggers.length === 0 && (
                  <span className="text-xs text-[var(--muted)]">
                    트리거 없음
                  </span>
                )}
              </div>
            </div>
            <ChartPlaceholder title="Mini Chart" height="h-48" />
            <div className="text-xs text-[var(--muted)]">
              히스토리 정보는 추후 제공됩니다.
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default SignalsPage;
