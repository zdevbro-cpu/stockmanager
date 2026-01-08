import { Badge } from "../ui/Badge";

type RationalePanelProps = {
  rationale: Record<string, unknown> | null;
};

export const RationalePanel = ({ rationale }: RationalePanelProps) => {
  if (!rationale) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] p-4 text-sm text-[var(--muted)]">
        근거 데이터가 없습니다.
      </div>
    );
  }

  const summary = (rationale as any).summary as
    | { total_score?: number; target_weight?: number; industry?: string; themes?: string[] }
    | undefined;
  const filters = ((rationale as any).filters as Array<{ name: string; pass: boolean }>) ?? [];
  const factors =
    ((rationale as any).factors as Array<{ name: string; weight: number; contribution: number }>) ??
    [];
  const constraints = ((rationale as any).constraints as string[]) ?? [];
  const riskFlags = ((rationale as any).risk_flags as string[]) ?? [];

  return (
    <div className="max-w-full break-words space-y-5 text-sm">
      <section className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
        <div className="mb-3 text-xs font-semibold text-[var(--muted)]">요약</div>
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div>
            <div className="text-[var(--muted)]">총점</div>
            <div className="text-sm font-semibold text-[var(--text)]">
              {summary?.total_score ?? "-"}
            </div>
          </div>
          <div>
            <div className="text-[var(--muted)]">타겟 비중</div>
            <div className="text-sm font-semibold text-[var(--text)]">
              {summary?.target_weight ? `${summary.target_weight * 100}%` : "-"}
            </div>
          </div>
          <div>
            <div className="text-[var(--muted)]">산업</div>
            <div className="text-sm font-semibold text-[var(--text)]">
              {summary?.industry ?? "-"}
            </div>
          </div>
          <div>
            <div className="text-[var(--muted)]">테마</div>
            <div className="flex flex-wrap gap-1">
              {(summary?.themes ?? []).length === 0 && (
                <span className="text-[var(--muted)]">-</span>
              )}
              {(summary?.themes ?? []).map((theme) => (
                <Badge key={theme} label={theme} variant="info" />
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
        <div className="mb-3 text-xs font-semibold text-[var(--muted)]">필터</div>
        <div className="flex flex-wrap gap-2">
          {filters.length === 0 && (
            <span className="text-xs text-[var(--muted)]">필터 정보 없음</span>
          )}
          {filters.map((filter) => (
            <Badge
              key={filter.name}
              label={`${filter.name} ${filter.pass ? "통과" : "실패"}`}
              variant={filter.pass ? "success" : "danger"}
            />
          ))}
        </div>
      </section>

      <section className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
        <div className="mb-3 text-xs font-semibold text-[var(--muted)]">팩터 기여도</div>
        <div className="space-y-2 text-xs">
          {factors.length === 0 && (
            <span className="text-[var(--muted)]">기여도 정보 없음</span>
          )}
          {factors.map((factor) => (
            <div key={factor.name} className="flex items-center justify-between">
              <div className="text-[var(--text)]">{factor.name}</div>
              <div className="text-mono text-[var(--muted)]">
                weight {factor.weight}, contrib {factor.contribution}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
        <div className="mb-3 text-xs font-semibold text-[var(--muted)]">제약 조건</div>
        <div className="space-y-2 text-xs text-[var(--text)]">
          {constraints.length === 0 && (
            <span className="text-[var(--muted)]">제약 조건 없음</span>
          )}
          {constraints.map((constraint) => (
            <div key={constraint}>{constraint}</div>
          ))}
        </div>
      </section>

      {riskFlags.length > 0 && (
        <section className="rounded-xl border border-amber-200 bg-amber-50 p-4">
          <div className="mb-3 text-xs font-semibold text-amber-700">
            이벤트 리스크
          </div>
          <div className="space-y-2 text-xs text-amber-700">
            {riskFlags.map((flag) => (
              <div key={flag}>{flag}</div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
};
