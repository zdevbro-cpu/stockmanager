import type { Request, Response } from "express";
import { Pool } from "pg";

let pool: Pool | null = null;
function getPool() {
  if (pool) return pool;
  const cs = process.env.DATABASE_URL;
  if (!cs) throw new Error("DATABASE_URL is required");
  pool = new Pool({ connectionString: cs, max: 5 });
  return pool;
}

export async function query(req: Request, res: Response, sql: string, params: any[]) {
  const p = getPool();
  const r = await p.query(sql, params);
  res.json({ data: r.rows });
}
