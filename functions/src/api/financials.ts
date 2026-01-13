import type { Request, Response } from "express";
import { query } from "../lib/db";

/**
 * GET /api/financials/annual3y?company_id=...
 */
export async function annual3y(req: Request, res: Response) {
  const companyId = String(req.query.company_id || "");
  if (!companyId) return res.status(400).json({ error: "company_id is required" });

  return query(
    req, res,
    `
    SELECT fiscal_year, revenue, gross_profit, op_income, net_income, assets, liabilities, equity, op_cf, inv_cf, fin_cf, fcf, revision_no, updated_at
    FROM fs_mart_annual
    WHERE company_id=$1
    ORDER BY fiscal_year DESC
    LIMIT 3
    `,
    [companyId]
  );
}

/**
 * GET /api/financials/quarter12q?company_id=...
 */
export async function quarter12q(req: Request, res: Response) {
  const companyId = String(req.query.company_id || "");
  if (!companyId) return res.status(400).json({ error: "company_id is required" });

  return query(
    req, res,
    `
    SELECT fiscal_year, fiscal_quarter, revenue, op_income, net_income, fcf, revenue_yoy, revenue_qoq, op_income_yoy, op_income_qoq, revision_no, updated_at
    FROM fs_mart_quarter
    WHERE company_id=$1
    ORDER BY fiscal_year DESC, fiscal_quarter DESC
    LIMIT 12
    `,
    [companyId]
  );
}

/**
 * GET /api/financials/ratios?company_id=...&period_type=ANNUAL|QUARTER
 */
export async function ratios(req: Request, res: Response) {
  const companyId = String(req.query.company_id || "");
  const periodType = String(req.query.period_type || "ANNUAL");
  if (!companyId) return res.status(400).json({ error: "company_id is required" });

  return query(
    req, res,
    `
    SELECT period_type, fiscal_year, fiscal_quarter, gross_margin, op_margin, net_margin, debt_ratio, current_ratio, interest_coverage, revenue_yoy, op_income_yoy, cagr_3y, updated_at
    FROM fs_ratio_mart
    WHERE company_id=$1 AND period_type=$2
    ORDER BY fiscal_year DESC, fiscal_quarter DESC NULLS LAST
    LIMIT 12
    `,
    [companyId, periodType]
  );
}

/**
 * GET /api/financials/chart?company_id=...&chart_key=...
 */
export async function chart(req: Request, res: Response) {
  const companyId = String(req.query.company_id || "");
  const chartKey = String(req.query.chart_key || "");
  if (!companyId || !chartKey) return res.status(400).json({ error: "company_id and chart_key are required" });

  return query(
    req, res,
    `SELECT chart_key, payload, generated_at FROM chart_cache WHERE company_id=$1 AND chart_key=$2`,
    [companyId, chartKey]
  );
}
