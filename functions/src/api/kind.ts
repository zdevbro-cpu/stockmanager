import type { Request, Response } from "express";
import { query } from "../lib/db";

/**
 * GET /api/kind/actions?security_id=...
 */
export async function actions(req: Request, res: Response) {
  const securityId = String(req.query.security_id || "");
  if (!securityId) return res.status(400).json({ error: "security_id is required" });

  return query(
    req, res,
    `
    SELECT action_type, start_at, end_at, reason, severity, source_ref, loaded_at
    FROM kind_market_action
    WHERE security_id=$1
    ORDER BY loaded_at DESC
    LIMIT 100
    `,
    [securityId]
  );
}
