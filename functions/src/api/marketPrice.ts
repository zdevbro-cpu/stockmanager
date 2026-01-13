import type { Request, Response } from "express";
import { query } from "../lib/db";

/**
 * GET /api/market/price?security_id=...&from=YYYY-MM-DD&to=YYYY-MM-DD
 */
export async function price(req: Request, res: Response) {
  const securityId = String(req.query.security_id || "");
  const from = String(req.query.from || "");
  const to = String(req.query.to || "");
  if (!securityId || !from || !to) return res.status(400).json({ error: "security_id, from, to are required" });

  return query(
    req, res,
    `
    SELECT trade_date, open, high, low, close, volume, value, adj_close
    FROM price_ohlcv_d
    WHERE security_id=$1 AND trade_date BETWEEN $2 AND $3
    ORDER BY trade_date ASC
    `,
    [securityId, from, to]
  );
}

/**
 * GET /api/market/returns?security_id=...
 */
export async function returns(req: Request, res: Response) {
  const securityId = String(req.query.security_id || "");
  if (!securityId) return res.status(400).json({ error: "security_id is required" });

  return query(
    req, res,
    `
    SELECT as_of_date, return_1m, return_3m, return_6m, return_1y, volatility_1y, max_drawdown_1y, updated_at
    FROM price_return_mart
    WHERE security_id=$1
    ORDER BY as_of_date DESC
    LIMIT 30
    `,
    [securityId]
  );
}
