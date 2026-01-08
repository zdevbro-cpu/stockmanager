import { useMemo, useState } from "react";
import { Panel } from "../components/shared/Panel";
import { Tabs } from "../components/ui/Tabs";
import { Button } from "../components/ui/Button";
import { loadJson, saveJson } from "../lib/storage";

type ReportDraft = {
  id: string;
  company: string;
  listed: boolean;
  business: string;
  financials: string;
  risks: string;
  memo: string;
  updatedAt: string;
};

const STORAGE_KEY = "stockmanager.reports";

const steps = [
  { value: "company", label: "Company" },
  { value: "business", label: "Business" },
  { value: "financials", label: "Financials" },
  { value: "risks", label: "Risks" },
  { value: "memo", label: "Memo" },
];

const ReportsPage = () => {
  const [segment, setSegment] = useState("library");
  const [reports, setReports] = useState<ReportDraft[]>(
    loadJson<ReportDraft[]>(STORAGE_KEY, [])
  );
  const [activeStep, setActiveStep] = useState("company");
  const [draft, setDraft] = useState<ReportDraft>({
    id: `${Date.now()}`,
    company: "",
    listed: true,
    business: "",
    financials: "",
    risks: "",
    memo: "",
    updatedAt: new Date().toISOString(),
  });

  const persist = (next: ReportDraft[]) => {
    setReports(next);
    saveJson(STORAGE_KEY, next);
  };

  const saveDraft = () => {
    const updated = { ...draft, updatedAt: new Date().toISOString() };
    setDraft(updated);
    persist([updated, ...reports.filter((item) => item.id !== draft.id)]);
  };

  const previewSections = useMemo(
    () => [
      { label: "회사 개요", value: draft.company },
      { label: "비즈니스", value: draft.business },
      { label: "재무", value: draft.financials },
      { label: "리스크", value: draft.risks },
      { label: "메모", value: draft.memo },
    ],
    [draft]
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="text-lg font-semibold text-[var(--text)]">VC 리포트</div>
          <div className="text-xs text-[var(--muted)]">
            리포트 라이브러리와 빌더/프리뷰를 관리합니다.
          </div>
        </div>
        <Tabs
          items={[
            { value: "library", label: "Library" },
            { value: "builder", label: "Builder" },
            { value: "preview", label: "Preview" },
          ]}
          value={segment}
          onChange={setSegment}
        />
      </div>

      {segment === "library" && (
        <Panel title="라이브러리">
          <div className="space-y-3 text-sm">
            {reports.length === 0 && (
              <div className="text-sm text-[var(--muted)]">
                저장된 리포트가 없습니다.
              </div>
            )}
            {reports.map((report) => (
              <button
                key={report.id}
                type="button"
                onClick={() => {
                  setDraft(report);
                  setSegment("preview");
                }}
                className="flex w-full items-center justify-between rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-3 text-left shadow-card"
              >
                <div>
                  <div className="text-sm font-semibold">
                    {report.company || "미입력"}
                  </div>
                  <div className="text-xs text-[var(--muted)]">
                    {report.listed ? "상장" : "비상장"} · 업데이트{" "}
                    {report.updatedAt.slice(0, 10)}
                  </div>
                </div>
                <Button label="보기" size="sm" variant="outline" />
              </button>
            ))}
          </div>
        </Panel>
      )}

      {segment === "builder" && (
        <Panel
          title="리포트 빌더"
          action={<Button label="저장" size="sm" onClick={saveDraft} />}
        >
          <div className="space-y-4">
            <Tabs items={steps} value={activeStep} onChange={setActiveStep} />
            {activeStep === "company" && (
              <div className="space-y-3 text-sm">
                <div>
                  <div className="mb-2 text-xs text-[var(--muted)]">회사명</div>
                  <input
                    value={draft.company}
                    onChange={(event) =>
                      setDraft((prev) => ({ ...prev, company: event.target.value }))
                    }
                    className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2 text-xs"
                    placeholder="예: SeedLabs"
                  />
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-[var(--muted)]">상장 여부</span>
                  <button
                    type="button"
                    onClick={() =>
                      setDraft((prev) => ({ ...prev, listed: !prev.listed }))
                    }
                    className="rounded-full border border-[var(--border)] px-3 py-1 text-xs"
                  >
                    {draft.listed ? "상장" : "비상장"}
                  </button>
                </div>
              </div>
            )}
            {activeStep === "business" && (
              <textarea
                value={draft.business}
                onChange={(event) =>
                  setDraft((prev) => ({ ...prev, business: event.target.value }))
                }
                className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2 text-xs"
                rows={6}
                placeholder="비즈니스 모델, 경쟁사, 성장 전략 등을 기록하세요."
              />
            )}
            {activeStep === "financials" && (
              <textarea
                value={draft.financials}
                onChange={(event) =>
                  setDraft((prev) => ({ ...prev, financials: event.target.value }))
                }
                className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2 text-xs"
                rows={6}
                placeholder="매출, 손익, 캐시플로우 요약을 기록하세요."
              />
            )}
            {activeStep === "risks" && (
              <textarea
                value={draft.risks}
                onChange={(event) =>
                  setDraft((prev) => ({ ...prev, risks: event.target.value }))
                }
                className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2 text-xs"
                rows={6}
                placeholder="규제, 기술, 시장 리스크를 기록하세요."
              />
            )}
            {activeStep === "memo" && (
              <textarea
                value={draft.memo}
                onChange={(event) =>
                  setDraft((prev) => ({ ...prev, memo: event.target.value }))
                }
                className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2 text-xs"
                rows={6}
                placeholder="투자 메모를 기록하세요."
              />
            )}
          </div>
        </Panel>
      )}

      {segment === "preview" && (
        <Panel
          title="리포트 미리보기"
          action={<Button label="PDF Export" size="sm" variant="outline" />}
        >
          <div className="space-y-4">
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] p-4">
              <div className="text-xs text-[var(--muted)]">회사명</div>
              <div className="text-lg font-semibold">
                {draft.company || "미입력"}
              </div>
              <div className="text-xs text-[var(--muted)]">
                {draft.listed ? "상장" : "비상장"} 기업
              </div>
            </div>
            {previewSections.map((section) => (
              <div key={section.label} className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
                <div className="mb-2 text-xs font-semibold text-[var(--muted)]">
                  {section.label}
                </div>
                <div className="text-sm text-[var(--text)] whitespace-pre-line">
                  {section.value || "내용이 없습니다."}
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}
    </div>
  );
};

export default ReportsPage;
