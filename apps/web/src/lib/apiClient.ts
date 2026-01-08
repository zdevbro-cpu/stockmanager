import {
  demoHealth,
  demoIndustryNodes,
  demoRecommendations,
  demoSecurityClassifications,
  demoSignals,
  demoTaxonomies,
  demoThemeNodes,
  demoUniverse,
} from "../data/demoData";
import type {
  Classification,
  ClassificationTaxonomy,
  RecommendationItem,
  SignalItem,
  UniverseItem,
} from "../types/api";

type ApiContext = {
  baseUrl: string;
  demoMode: boolean;
};

const fetchJson = async <T>(baseUrl: string, path: string): Promise<T> => {
  const response = await fetch(`${baseUrl}${path}`);
  if (!response.ok) {
    throw new Error(`API 요청 실패: ${response.status}`);
  }
  return (await response.json()) as T;
};

export const getHealth = async ({ baseUrl, demoMode }: ApiContext) => {
  if (demoMode) return demoHealth;
  return fetchJson<{ status: string }>(baseUrl, "/health");
};

export const getUniverse = async (
  ctx: ApiContext,
  params: {
    as_of_date: string;
    include_industry_codes?: string[];
    include_theme_ids?: string[];
    min_price?: number | null;
    min_turnover?: number | null;
  }
): Promise<UniverseItem[]> => {
  if (ctx.demoMode) return demoUniverse;
  const search = new URLSearchParams();
  search.set("as_of_date", params.as_of_date);
  if (params.include_industry_codes?.length) {
    search.set("include_industry_codes", params.include_industry_codes.join(","));
  }
  if (params.include_theme_ids?.length) {
    search.set("include_theme_ids", params.include_theme_ids.join(","));
  }
  if (params.min_price !== null && params.min_price !== undefined) {
    search.set("min_price", String(params.min_price));
  }
  if (params.min_turnover !== null && params.min_turnover !== undefined) {
    search.set("min_turnover", String(params.min_turnover));
  }
  return fetchJson<UniverseItem[]>(ctx.baseUrl, `/universe?${search.toString()}`);
};

export const getRecommendations = async (
  ctx: ApiContext,
  params: {
    as_of_date: string;
    strategy_id: string;
    strategy_version: string;
  }
): Promise<RecommendationItem[]> => {
  if (ctx.demoMode) return demoRecommendations;
  const search = new URLSearchParams();
  search.set("as_of_date", params.as_of_date);
  search.set("strategy_id", params.strategy_id);
  search.set("strategy_version", params.strategy_version);
  return fetchJson<RecommendationItem[]>(
    ctx.baseUrl,
    `/recommendations?${search.toString()}`
  );
};

export const getSignals = async (
  ctx: ApiContext,
  params: { ticker: string; horizon: string }
): Promise<SignalItem[]> => {
  if (ctx.demoMode) return demoSignals.filter((item) => item.ticker === params.ticker);
  const search = new URLSearchParams();
  search.set("ticker", params.ticker);
  search.set("horizon", params.horizon);
  return fetchJson<SignalItem[]>(ctx.baseUrl, `/signals?${search.toString()}`);
};

export const getTaxonomies = async (
  ctx: ApiContext
): Promise<ClassificationTaxonomy[]> => {
  if (ctx.demoMode) return demoTaxonomies;
  return fetchJson<ClassificationTaxonomy[]>(ctx.baseUrl, "/classifications/taxonomies");
};

export const getClassificationNodes = async (
  ctx: ApiContext,
  params: { taxonomy_id: string; level?: number }
): Promise<Classification[]> => {
  if (ctx.demoMode) {
    return params.taxonomy_id === "THEME" ? demoThemeNodes : demoIndustryNodes;
  }
  const search = new URLSearchParams();
  search.set("taxonomy_id", params.taxonomy_id);
  if (params.level !== undefined) {
    search.set("level", String(params.level));
  }
  return fetchJson<Classification[]>(
    ctx.baseUrl,
    `/classifications/nodes?${search.toString()}`
  );
};

export const getSecurityClassifications = async (
  ctx: ApiContext,
  ticker: string
): Promise<Classification[]> => {
  if (ctx.demoMode) return demoSecurityClassifications[ticker] ?? [];
  return fetchJson<Classification[]>(
    ctx.baseUrl,
    `/classifications/securities/${ticker}`
  );
};
