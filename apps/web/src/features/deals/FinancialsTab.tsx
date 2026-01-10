import React, { useEffect, useMemo, useState } from "react";

type AnnualRow = {
  fiscal_year: number;
  revenue: number | null;
  op_income: number | null;
  net_income: number | null;
  fcf: number | null;
};

type RatioRow = {
  fiscal_year: number;
  gross_margin: number | null;
  op_margin: number | null;
  net_margin: number | null;
  debt_ratio: number | null;
  revenue_yoy: number | null;
};

function fmtNum(v: number | null) {
  if (v === null || Number.isNaN(v)) return "-";
  return new Intl.NumberFormat("ko-KR").format(Math.round(v));
}
function fmtPct(v: number | null) {
  if (v === null || Number.isNaN(v)) return "-";
  return `${(v * 100).toFixed(1)}%`;
}

/**
 * FinancialsTab.tsx (skeleton)
 * - 실제 차트 라이브러리(Recharts/Chart.js 등)로 chart_cache payload를 렌더링하세요.
 */
export function FinancialsTab({ companyId }: { companyId: string }) {
  const [annual, setAnnual] = useState<AnnualRow[]>([]);
  const [ratios, setRatios] = useState<RatioRow[]>([]);

  useEffect(() => {
    (async () => {
      const a = await fetch(`/api/financials/annual3y?company_id=${companyId}`).then(r => r.json());
      setAnnual(a.data ?? []);

      const r = await fetch(`/api/financials/ratios?company_id=${companyId}&period_type=ANNUAL`).then(r => r.json());
      setRatios(r.data ?? []);
    })();
  }, [companyId]);

  const annualSorted = useMemo(() => [...annual].sort((x,y)=>x.fiscal_year - y.fiscal_year), [annual]);
  const ratioSorted = useMemo(() => [...ratios].sort((x,y)=>x.fiscal_year - y.fiscal_year), [ratios]);

  return (
    <div style={{ padding: 16 }}>
      <h2>Financials</h2>

      <section style={{ marginTop: 16 }}>
        <h3>3개년 요약</h3>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: 8 }}>연도</th>
              <th style={{ textAlign: "right", borderBottom: "1px solid #ddd", padding: 8 }}>매출</th>
              <th style={{ textAlign: "right", borderBottom: "1px solid #ddd", padding: 8 }}>영업이익</th>
              <th style={{ textAlign: "right", borderBottom: "1px solid #ddd", padding: 8 }}>순이익</th>
              <th style={{ textAlign: "right", borderBottom: "1px solid #ddd", padding: 8 }}>FCF</th>
            </tr>
          </thead>
          <tbody>
            {annualSorted.map(r => (
              <tr key={r.fiscal_year}>
                <td style={{ padding: 8, borderBottom: "1px solid #f0f0f0" }}>{r.fiscal_year}</td>
                <td style={{ padding: 8, borderBottom: "1px solid #f0f0f0", textAlign: "right" }}>{fmtNum(r.revenue)}</td>
                <td style={{ padding: 8, borderBottom: "1px solid #f0f0f0", textAlign: "right" }}>{fmtNum(r.op_income)}</td>
                <td style={{ padding: 8, borderBottom: "1px solid #f0f0f0", textAlign: "right" }}>{fmtNum(r.net_income)}</td>
                <td style={{ padding: 8, borderBottom: "1px solid #f0f0f0", textAlign: "right" }}>{fmtNum(r.fcf)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section style={{ marginTop: 16 }}>
        <h3>마진/안정성</h3>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: 8 }}>연도</th>
              <th style={{ textAlign: "right", borderBottom: "1px solid #ddd", padding: 8 }}>GPM</th>
              <th style={{ textAlign: "right", borderBottom: "1px solid #ddd", padding: 8 }}>OPM</th>
              <th style={{ textAlign: "right", borderBottom: "1px solid #ddd", padding: 8 }}>NPM</th>
              <th style={{ textAlign: "right", borderBottom: "1px solid #ddd", padding: 8 }}>부채비율</th>
              <th style={{ textAlign: "right", borderBottom: "1px solid #ddd", padding: 8 }}>매출 YoY</th>
            </tr>
          </thead>
          <tbody>
            {ratioSorted.map(r => (
              <tr key={r.fiscal_year}>
                <td style={{ padding: 8, borderBottom: "1px solid #f0f0f0" }}>{r.fiscal_year}</td>
                <td style={{ padding: 8, borderBottom: "1px solid #f0f0f0", textAlign: "right" }}>{fmtPct(r.gross_margin)}</td>
                <td style={{ padding: 8, borderBottom: "1px solid #f0f0f0", textAlign: "right" }}>{fmtPct(r.op_margin)}</td>
                <td style={{ padding: 8, borderBottom: "1px solid #f0f0f0", textAlign: "right" }}>{fmtPct(r.net_margin)}</td>
                <td style={{ padding: 8, borderBottom: "1px solid #f0f0f0", textAlign: "right" }}>{fmtPct(r.debt_ratio)}</td>
                <td style={{ padding: 8, borderBottom: "1px solid #f0f0f0", textAlign: "right" }}>{fmtPct(r.revenue_yoy)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section style={{ marginTop: 16 }}>
        <h3>추이 차트</h3>
        <p style={{ marginTop: 8 }}>
          chart_cache 기반 렌더링을 붙이세요. 권장 chart_key: <code>FIN_IS_ANNUAL_3Y</code>
        </p>
      </section>
    </div>
  );
}
