export type UniverseItem = {
  ticker: string;
  name_ko: string;
  market: string;
  sector_name: string | null;
  avg_turnover_krw_20d: number | null;
  last_price_krw: number | null;
};

export type RecommendationItem = {
  as_of_date: string;
  strategy_id: string;
  strategy_version: string;
  ticker: string;
  rank: number;
  score: number | null;
  target_weight: number;
  rationale: Record<string, unknown> | null;
};

export type SignalItem = {
  ts: string;
  ticker: string;
  horizon: string;
  signal: "BUY" | "WAIT" | "REDUCE" | "SELL" | string;
  confidence: number | null;
  triggers: string[];
  risk_flags: string[];
  model_version: string | null;
};

export type Classification = {
  taxonomy_id: string;
  code: string;
  name: string;
  level: number | null;
  parent_code: string | null;
};

export type ClassificationTaxonomy = {
  taxonomy_id: string;
  name: string;
};
