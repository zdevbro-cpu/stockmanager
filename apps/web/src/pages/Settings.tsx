import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getHealth } from "../lib/apiClient";
import { useAppSettings } from "../store/appStore";
import { Panel } from "../components/shared/Panel";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { ErrorState } from "../components/ui/ErrorState";
import { useErrorToast } from "../lib/useErrorToast";
import { loadJson, saveJson } from "../lib/storage";

type EtlLog = {
  id: string;
  source: "KRX" | "DART" | "ECOS" | "FX";
  status: "SUCCESS" | "FAIL" | "WARN" | "RUNNING";
  message: string;
  runAt: string;
};

const STORAGE_KEY = "stockmanager.etlLogs";

const SettingsPage = () => {
  const { apiBaseUrl, setApiBaseUrl, demoMode, setDemoMode } = useAppSettings();
  const healthQuery = useQuery({
    queryKey: ["health", apiBaseUrl, demoMode],
    queryFn: () => getHealth({ baseUrl: apiBaseUrl, demoMode }),
  });

  useErrorToast(healthQuery.isError, "API 상태 확인에 실패했습니다.");

  const [logs, setLogs] = useState<EtlLog[]>(
    loadJson<EtlLog[]>(STORAGE_KEY, [])
  );
  const etlSteps = [
    {
      order: 1,
      source: "KRX" as const,
      title: "KRX 적재",
      message: "KRX 종목/가격 적재 완료",
      mappings: [
        "KRX 상장종목 → security",
        "KRX 일봉 → price_daily",
        "KIS 산업코드 → classification_node",
      ],
    },
    {
      order: 2,
      source: "DART" as const,
      title: "DART 적재",
      message: "DART 공시/기업정보 적재 완료",
      mappings: [
        "기업 코드/정보 → company",
        "공시 메타 → filing",
        "기업-종목 연결 → instrument_company_map",
      ],
    },
    {
      order: 3,
      source: "ECOS" as const,
      title: "ECOS 적재",
      message: "ECOS 거시지표 적재 완료",
      mappings: [
        "시리즈 메타 → macro_series",
        "시계열 값 → macro_value",
      ],
    },
    {
      order: 4,
      source: "FX" as const,
      title: "환율 적재",
      message: "환율 시계열 적재 완료",
      mappings: ["USD/KRW 시계열 → macro_value"],
    },
  ];

  const persist = (next: EtlLog[]) => {
    setLogs(next);
    saveJson(STORAGE_KEY, next);
  };

  const addLog = (source: EtlLog["source"], message: string) => {
    const next: EtlLog = {
      id: `${Date.now()}-${Math.random()}`,
      source,
      status: "SUCCESS",
      message,
      runAt: new Date().toISOString(),
    };
    persist([next, ...logs]);
  };

  const statusBadge = useMemo(() => {
    if (healthQuery.isFetching) return { label: "확인 중", variant: "warning" } as const;
    return { label: "연결됨", variant: "success" } as const;
  }, [healthQuery.isFetching]);

  return (
    <div className="space-y-6">
      <div>
        <div className="text-lg font-semibold text-[var(--text)]">설정</div>
        <div className="text-xs text-[var(--muted)]">
          API 환경과 데모 모드를 관리하고 ETL 로그를 기록합니다.
        </div>
      </div>

      <Panel title="API 연결">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-3">
            <input
              value={apiBaseUrl}
              onChange={(event) => setApiBaseUrl(event.target.value)}
              className="min-w-[240px] flex-1 rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2 text-xs"
            />
            <Button
              label="테스트"
              size="sm"
              variant="outline"
              onClick={() => healthQuery.refetch()}
            />
          </div>
          {healthQuery.isError && <ErrorState />}
          {!healthQuery.isError && (
            <div className="flex items-center gap-2 text-xs text-[var(--muted)]">
              <Badge label={statusBadge.label} variant={statusBadge.variant} />
              <span>
                {demoMode
                  ? "데모 모드에서는 로컬 데이터를 사용합니다."
                  : "실제 API 호출 중"}
              </span>
            </div>
          )}
        </div>
      </Panel>

      <Panel title="데모 모드">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-semibold text-[var(--text)]">
              오프라인 데모
            </div>
            <div className="text-xs text-[var(--muted)]">
              백엔드가 꺼져 있어도 UI 데모가 가능하도록 합니다.
            </div>
          </div>
          <button
            type="button"
            onClick={() => setDemoMode(!demoMode)}
            className="rounded-full border border-[var(--border)] px-4 py-2 text-xs font-semibold"
          >
            {demoMode ? "ON" : "OFF"}
          </button>
        </div>
      </Panel>

      <Panel
        title="ETL 적재"
        action={
          <Button
            label="전체 삭제"
            size="sm"
            variant="outline"
            onClick={() => persist([])}
          />
        }
      >
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-3 text-xs text-[var(--muted)]">
            적재 순서:
            {etlSteps.map((step) => (
              <span key={step.source} className="font-semibold text-[var(--text)]">
                {step.order}. {step.source}
              </span>
            ))}
          </div>
          <div className="grid gap-3 grid-cols-2">
            {etlSteps.map((step) => (
              <Button
                key={step.source}
                label={`${step.order}. ${step.title} 실행`}
                variant="primary"
                onClick={() => addLog(step.source, step.message)}
              />
            ))}
          </div>

          <div className="space-y-3">
            <div className="text-xs font-semibold text-[var(--muted)]">
              데이터 매핑
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              {etlSteps.map((step) => (
                <div
                  key={step.source}
                  className="rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] px-4 py-3 text-xs"
                >
                  <div className="mb-2 text-sm font-semibold text-[var(--text)]">
                    {step.order}. {step.title}
                  </div>
                  <ul className="list-disc space-y-1 pl-4 text-[var(--muted)]">
                    {step.mappings.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>

          {logs.length === 0 && (
            <div className="text-xs text-[var(--muted)]">
              수동 로그가 없습니다.
            </div>
          )}
          <div className="space-y-2">
            {logs.map((log) => (
              <div
                key={log.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] px-4 py-3 text-xs"
              >
                <div>
                  <div className="font-semibold text-[var(--text)]">
                    {log.source} · {log.status}
                  </div>
                  <div className="text-[var(--muted)]">{log.message}</div>
                </div>
                <div className="text-[var(--muted)]">
                  {new Date(log.runAt).toLocaleString("ko-KR")}
                </div>
              </div>
            ))}
          </div>
        </div>
      </Panel>
    </div>
  );
};

export default SettingsPage;
