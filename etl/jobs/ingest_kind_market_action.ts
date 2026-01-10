/**
 * ingest_kind_market_action.ts (stub)
 * - KIND에서 가져온 시장조치/투자유의 데이터를 kind_market_action 테이블에 적재하는 작업 스켈레톤입니다.
 * - 실제 KIND 수집 방식(API/크롤링/수동 업로드)에 맞춰 fetch 부분을 구현하세요.
 *
 * 실행 예:
 *   DATABASE_URL=... ts-node etl/jobs/ingest_kind_market_action.ts --payload_file=./kind.json
 */
import fs from "fs";
import { makePool } from "../lib/db";

type Args = { payload_file?: string };
function parseArgs(): Args {
  const out: Args = {};
  for (const a of process.argv.slice(2)) {
    const [k, v] = a.split("=");
    if (k === "--payload_file") out.payload_file = v;
  }
  return out;
}

function mapSeverity(actionType: string): "low" | "med" | "high" {
  const t = actionType.toLowerCase();
  if (t.includes("거래정지") || t.includes("관리") || t.includes("실질") || t.includes("상장폐지")) return "high";
  if (t.includes("투자경고") || t.includes("불성실")) return "med";
  return "low";
}

async function main() {
  const { payload_file } = parseArgs();
  if (!payload_file) throw new Error("--payload_file is required");

  const payload = JSON.parse(fs.readFileSync(payload_file, "utf-8"));
  // payload 예시(권장):
  // [{ stock_code, action_type, start_at, end_at, reason, source_ref, raw_payload }]

  const pool = makePool();
  try {
    for (const item of payload) {
      const stockCode = String(item.stock_code || "");
      if (!stockCode) continue;

      const secRes = await pool.query(
        "SELECT security_id FROM security_master WHERE stock_code=$1 LIMIT 1",
        [stockCode]
      );
      const securityId = secRes.rows[0]?.security_id;
      if (!securityId) continue;

      const actionType = String(item.action_type || "UNKNOWN");
      const severity = mapSeverity(actionType);

      await pool.query(
        `
        INSERT INTO kind_market_action (
          security_id, action_type, start_at, end_at, reason, severity, source_ref, raw_payload, loaded_at
        ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8::jsonb, now())
        `,
        [
          securityId,
          actionType,
          item.start_at || null,
          item.end_at || null,
          item.reason || null,
          severity,
          item.source_ref || null,
          JSON.stringify(item.raw_payload || item)
        ]
      );
    }
  } finally {
    await pool.end();
  }

  console.log("[OK] ingest_kind_market_action done");
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
