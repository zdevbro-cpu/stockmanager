/**
 * build_price_return_mart.ts
 * - price_ohlcv_d -> price_return_mart (1m/3m/6m/1y, vol, max drawdown)
 *
 * 실행:
 *   DATABASE_URL=... ts-node etl/jobs/build_price_return_mart.ts --security_id=<uuid>
 */
import { makePool } from "../lib/db";

type Args = { security_id?: string };
function parseArgs(): Args {
  const out: Args = {};
  for (const a of process.argv.slice(2)) {
    const [k, v] = a.split("=");
    if (k === "--security_id") out.security_id = v;
  }
  return out;
}

function pct(a: number, b: number) {
  if (b === 0) return null;
  return a / b - 1;
}

async function main() {
  const { security_id } = parseArgs();
  const pool = makePool();

  try {
    const securities = security_id
      ? [{ security_id }]
      : (await pool.query("SELECT security_id FROM security_master")).rows;

    for (const s of securities) {
      const sid = s.security_id as string;

      // 최근 400 거래일(대략 1.5년) 확보
      const res = await pool.query(
        `SELECT trade_date, COALESCE(adj_close, close) AS px
         FROM price_ohlcv_d
         WHERE security_id=$1
         ORDER BY trade_date DESC
         LIMIT 420`,
        [sid]
      );
      const rows = res.rows.reverse(); // ascending
      if (rows.length < 30) continue;

      // helper: find closest date index for N trading days ago
      const idx = rows.length - 1;
      const pxNow = Number(rows[idx].px);
      const px1m = rows[Math.max(0, idx - 21)] ? Number(rows[Math.max(0, idx - 21)].px) : null;
      const px3m = rows[Math.max(0, idx - 63)] ? Number(rows[Math.max(0, idx - 63)].px) : null;
      const px6m = rows[Math.max(0, idx - 126)] ? Number(rows[Math.max(0, idx - 126)].px) : null;
      const px1y = rows[Math.max(0, idx - 252)] ? Number(rows[Math.max(0, idx - 252)].px) : null;

      const r1m = px1m ? pct(pxNow, px1m) : null;
      const r3m = px3m ? pct(pxNow, px3m) : null;
      const r6m = px6m ? pct(pxNow, px6m) : null;
      const r1y = px1y ? pct(pxNow, px1y) : null;

      // volatility (daily returns stddev * sqrt(252))
      const rets: number[] = [];
      for (let i = 1; i < rows.length; i++) {
        const p0 = Number(rows[i - 1].px);
        const p1 = Number(rows[i].px);
        if (p0 > 0 && p1 > 0) rets.push(Math.log(p1 / p0));
      }
      const mean = rets.reduce((a, b) => a + b, 0) / Math.max(1, rets.length);
      const varr = rets.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / Math.max(1, rets.length - 1);
      const vol = Math.sqrt(varr) * Math.sqrt(252);

      // max drawdown
      let peak = -Infinity;
      let mdd = 0;
      for (const r of rows) {
        const p = Number(r.px);
        if (p > peak) peak = p;
        const dd = peak > 0 ? (p / peak - 1) : 0;
        if (dd < mdd) mdd = dd;
      }

      const asOf = rows[idx].trade_date;

      await pool.query(
        `
        INSERT INTO price_return_mart (
          security_id, as_of_date, return_1m, return_3m, return_6m, return_1y,
          volatility_1y, max_drawdown_1y, updated_at
        ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8, now())
        ON CONFLICT (security_id, as_of_date) DO UPDATE SET
          return_1m=EXCLUDED.return_1m,
          return_3m=EXCLUDED.return_3m,
          return_6m=EXCLUDED.return_6m,
          return_1y=EXCLUDED.return_1y,
          volatility_1y=EXCLUDED.volatility_1y,
          max_drawdown_1y=EXCLUDED.max_drawdown_1y,
          updated_at=now()
        `,
        [sid, asOf, r1m, r3m, r6m, r1y, vol, mdd]
      );

      console.log(`[OK] built price_return_mart for security ${sid} @ ${asOf}`);
    }
  } finally {
    await pool.end();
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
