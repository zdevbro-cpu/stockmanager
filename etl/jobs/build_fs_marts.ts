/**
 * build_fs_marts.ts
 * - fs_fact + account_mapping -> fs_mart_annual / fs_mart_quarter
 * - then fs_ratio_mart + chart_cache 생성(기본 차트 payload)
 *
 * 실행:
 *   DATABASE_URL=... ts-node etl/jobs/build_fs_marts.ts --company_id=<uuid>
 *
 * NOTE:
 * - 실제 환경에서는 Cloud Run Job 또는 Scheduler 트리거로 실행 권장
 */
import { makePool } from "../lib/db";

type Args = { company_id?: string };
function parseArgs(): Args {
  const out: Args = {};
  for (const a of process.argv.slice(2)) {
    const [k, v] = a.split("=");
    if (k === "--company_id") out.company_id = v;
  }
  return out;
}

const STD_KEYS = [
  "revenue","gross_profit","op_income","net_income",
  "assets","liabilities","equity",
  "op_cf","inv_cf","fin_cf"
] as const;

function safeDiv(a: number | null, b: number | null): number | null {
  if (a === null || b === null) return null;
  if (b === 0) return null;
  return a / b;
}
function safePct(a: number | null, b: number | null): number | null {
  const d = safeDiv(a, b);
  if (d === null) return null;
  return d;
}

async function main() {
  const { company_id } = parseArgs();
  const pool = makePool();

  try {
    // 1) 대상 회사 목록
    const companies = company_id
      ? [{ company_id }]
      : (await pool.query("SELECT company_id FROM company")).rows;

    for (const c of companies) {
      const cid = c.company_id as string;

      // 2) 최근 데이터 범위(연간 5년, 분기 16개 정도 확보 후 3Y/12Q로 사용)
      // 연간: 회사별 최대 연도부터 5개년
      const maxYearRes = await pool.query(
        "SELECT MAX(fiscal_year) AS y FROM fs_fact WHERE company_id=$1 AND period_type='ANNUAL'",
        [cid]
      );
      const maxY = maxYearRes.rows[0]?.y as number | null;
      if (!maxY) continue;
      const minY = maxY - 5;

      // 3) account_mapping 로 표준 키별 금액 집계(연간)
      // 우선순위(priority) 기준으로 계정명 매칭이 복수일 수 있어,
      // 현실 운영에서는 (회사별 커스텀 매핑) 또는 (정규화된 계정코드) 활용 권장.
      const annual = await pool.query(
        `
        WITH m AS (
          SELECT statement_type, source_account_name, standard_key, priority
          FROM account_mapping WHERE is_active=true
        ),
        f AS (
          SELECT company_id, fiscal_year, statement_type, account_name, amount, revision_no
          FROM fs_fact
          WHERE company_id=$1 AND period_type='ANNUAL' AND fiscal_year >= $2
        ),
        j AS (
          SELECT f.company_id, f.fiscal_year, m.standard_key, f.amount, f.revision_no,
                 ROW_NUMBER() OVER (PARTITION BY f.company_id, f.fiscal_year, m.standard_key ORDER BY m.priority ASC) AS rn
          FROM f
          JOIN m ON m.statement_type = f.statement_type AND m.source_account_name = f.account_name
        )
        SELECT company_id, fiscal_year, standard_key, amount, revision_no
        FROM j WHERE rn=1
        ORDER BY fiscal_year ASC
        `,
        [cid, minY]
      );

      // pivot
      const byYear = new Map<number, any>();
      for (const r of annual.rows) {
        const y = Number(r.fiscal_year);
        if (!byYear.has(y)) byYear.set(y, { company_id: cid, fiscal_year: y, revision_no: Number(r.revision_no || 0) });
        byYear.get(y)[String(r.standard_key)] = Number(r.amount);
      }

      // upsert annual mart + fcf
      for (const [y, row] of byYear.entries()) {
        const op_cf = row.op_cf ?? null;
        const inv_cf = row.inv_cf ?? null;
        const fcf = (op_cf !== null && inv_cf !== null) ? (op_cf - inv_cf) : null;

        await pool.query(
          `
          INSERT INTO fs_mart_annual (
            company_id, fiscal_year, revenue, gross_profit, op_income, net_income,
            assets, liabilities, equity, op_cf, inv_cf, fin_cf, fcf, revision_no, updated_at
          ) VALUES (
            $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14, now()
          )
          ON CONFLICT (company_id, fiscal_year) DO UPDATE SET
            revenue=EXCLUDED.revenue,
            gross_profit=EXCLUDED.gross_profit,
            op_income=EXCLUDED.op_income,
            net_income=EXCLUDED.net_income,
            assets=EXCLUDED.assets,
            liabilities=EXCLUDED.liabilities,
            equity=EXCLUDED.equity,
            op_cf=EXCLUDED.op_cf,
            inv_cf=EXCLUDED.inv_cf,
            fin_cf=EXCLUDED.fin_cf,
            fcf=EXCLUDED.fcf,
            revision_no=EXCLUDED.revision_no,
            updated_at=now()
          `,
          [
            cid, y,
            row.revenue ?? null, row.gross_profit ?? null, row.op_income ?? null, row.net_income ?? null,
            row.assets ?? null, row.liabilities ?? null, row.equity ?? null,
            row.op_cf ?? null, row.inv_cf ?? null, row.fin_cf ?? null, fcf,
            row.revision_no ?? 0
          ]
        );
      }

      // 4) ratio mart(연간) 생성: margin, debt_ratio 등
      // debt_ratio = liabilities / equity (or liabilities/assets) 정책 선택 가능. 여기서는 liabilities/equity
      const annualRows = (await pool.query(
        "SELECT * FROM fs_mart_annual WHERE company_id=$1 AND fiscal_year >= $2 ORDER BY fiscal_year ASC",
        [cid, maxY - 3]  // 3년치만
      )).rows;

      // YoY + CAGR(가능 시)
      const revByYear = new Map<number, number>();
      for (const r of annualRows) revByYear.set(Number(r.fiscal_year), r.revenue ? Number(r.revenue) : NaN);

      const ySorted = annualRows.map(r => Number(r.fiscal_year)).sort((a,b)=>a-b);
      const lastY = ySorted[ySorted.length-1];
      const firstY = ySorted.length >= 4 ? ySorted[ySorted.length-4] : null;

      const cagr3y = (firstY !== null && isFinite(revByYear.get(firstY)!) && isFinite(revByYear.get(lastY)!))
        ? (Math.pow(revByYear.get(lastY)! / revByYear.get(firstY)!, 1/3) - 1)
        : null;

      for (const r of annualRows) {
        const y = Number(r.fiscal_year);
        const revenue = r.revenue ? Number(r.revenue) : null;
        const gp = r.gross_profit ? Number(r.gross_profit) : null;
        const op = r.op_income ? Number(r.op_income) : null;
        const ni = r.net_income ? Number(r.net_income) : null;
        const liab = r.liabilities ? Number(r.liabilities) : null;
        const eq = r.equity ? Number(r.equity) : null;

        const gross_margin = safeDiv(gp, revenue);
        const op_margin = safeDiv(op, revenue);
        const net_margin = safeDiv(ni, revenue);
        const debt_ratio = safeDiv(liab, eq);

        const prevRev = revByYear.get(y-1);
        const revenue_yoy = (revenue !== null && prevRev && isFinite(prevRev)) ? (revenue / prevRev - 1) : null;
        const prevOp = annualRows.find(x => Number(x.fiscal_year) === y-1)?.op_income;
        const op_income_yoy = (op !== null && prevOp) ? (op / Number(prevOp) - 1) : null;

        await pool.query(
          `
          INSERT INTO fs_ratio_mart (
            company_id, period_type, fiscal_year, fiscal_quarter,
            gross_margin, op_margin, net_margin, debt_ratio,
            revenue_yoy, op_income_yoy, cagr_3y, updated_at
          ) VALUES (
            $1,'ANNUAL',$2,NULL,$3,$4,$5,$6,$7,$8,$9, now()
          )
          ON CONFLICT (company_id, period_type, fiscal_year, fiscal_quarter) DO UPDATE SET
            gross_margin=EXCLUDED.gross_margin,
            op_margin=EXCLUDED.op_margin,
            net_margin=EXCLUDED.net_margin,
            debt_ratio=EXCLUDED.debt_ratio,
            revenue_yoy=EXCLUDED.revenue_yoy,
            op_income_yoy=EXCLUDED.op_income_yoy,
            cagr_3y=EXCLUDED.cagr_3y,
            updated_at=now()
          `,
          [cid, y, gross_margin, op_margin, net_margin, debt_ratio, revenue_yoy, op_income_yoy, cagr3y]
        );
      }

      // 5) chart_cache payload 생성(연간 손익 + 마진)
      const chartPayload = {
        company_id: cid,
        annual: annualRows.map(r => ({
          year: Number(r.fiscal_year),
          revenue: r.revenue ? Number(r.revenue) : null,
          op_income: r.op_income ? Number(r.op_income) : null,
          net_income: r.net_income ? Number(r.net_income) : null,
          fcf: r.fcf ? Number(r.fcf) : null,
        })),
        ratios: annualRows.map(r => ({
          year: Number(r.fiscal_year),
          gross_margin: null, // 별도 조회로 합쳐도 됨
          op_margin: null,
          net_margin: null
        }))
      };

      await pool.query(
        `
        INSERT INTO chart_cache(company_id, chart_key, payload, generated_at)
        VALUES ($1, 'FIN_IS_ANNUAL_3Y', $2::jsonb, now())
        ON CONFLICT (company_id, chart_key) DO UPDATE SET
          payload=EXCLUDED.payload,
          generated_at=now()
        `,
        [cid, JSON.stringify(chartPayload)]
      );

      console.log(`[OK] built marts/ratios/charts for company ${cid}`);
    }
  } finally {
    await pool.end();
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
