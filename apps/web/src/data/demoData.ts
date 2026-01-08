import type {
  Classification,
  ClassificationTaxonomy,
  RecommendationItem,
  SignalItem,
  UniverseItem,
} from "../types/api";

export const demoHealth = { status: "ok" };

export const demoUniverse: UniverseItem[] = [
  {
    ticker: "005930",
    name_ko: "삼성전자",
    market: "KOSPI",
    sector_name: "반도체",
    avg_turnover_krw_20d: 124000000000,
    last_price_krw: 74200,
  },
  {
    ticker: "000660",
    name_ko: "SK하이닉스",
    market: "KOSPI",
    sector_name: "반도체",
    avg_turnover_krw_20d: 98200000000,
    last_price_krw: 176000,
  },
  {
    ticker: "035420",
    name_ko: "NAVER",
    market: "KOSPI",
    sector_name: "인터넷",
    avg_turnover_krw_20d: 31200000000,
    last_price_krw: 201000,
  },
  {
    ticker: "051910",
    name_ko: "LG화학",
    market: "KOSPI",
    sector_name: "화학",
    avg_turnover_krw_20d: 22100000000,
    last_price_krw: 352000,
  },
  {
    ticker: "068270",
    name_ko: "셀트리온",
    market: "KOSPI",
    sector_name: "바이오",
    avg_turnover_krw_20d: 18900000000,
    last_price_krw: 167500,
  },
];

export const demoRecommendations: RecommendationItem[] = [
  {
    as_of_date: "2026-01-08",
    strategy_id: "prod_v1",
    strategy_version: "1.0",
    ticker: "005930",
    rank: 1,
    score: 0.82,
    target_weight: 0.12,
    rationale: {
      summary: {
        total_score: 0.82,
        target_weight: 0.12,
        industry: "반도체",
        themes: ["AI 인프라", "메모리 업사이드"],
      },
      filters: [
        { name: "유동성", pass: true },
        { name: "밸류에이션", pass: true },
        { name: "모멘텀", pass: true },
      ],
      factors: [
        { name: "ROE 개선", weight: 0.25, contribution: 0.18 },
        { name: "수요 가시성", weight: 0.2, contribution: 0.16 },
        { name: "수급", weight: 0.15, contribution: 0.12 },
      ],
      constraints: ["산업 비중 상한 20%"],
      risk_flags: [],
    },
  },
  {
    as_of_date: "2026-01-08",
    strategy_id: "prod_v1",
    strategy_version: "1.0",
    ticker: "000660",
    rank: 2,
    score: 0.78,
    target_weight: 0.1,
    rationale: {
      summary: {
        total_score: 0.78,
        target_weight: 0.1,
        industry: "반도체",
        themes: ["HBM", "서버 투자"],
      },
      filters: [
        { name: "유동성", pass: true },
        { name: "밸류에이션", pass: true },
        { name: "모멘텀", pass: false },
      ],
      factors: [
        { name: "가격 모멘텀", weight: 0.2, contribution: 0.05 },
        { name: "이익 모멘텀", weight: 0.25, contribution: 0.2 },
      ],
      constraints: ["동일 산업 내 종목 수 제한"],
      risk_flags: ["단기 변동성 확대"],
    },
  },
];

export const demoSignals: SignalItem[] = [
  {
    ts: "2026-01-08T09:00:00+09:00",
    ticker: "005930",
    horizon: "1d",
    signal: "BUY",
    confidence: 0.66,
    triggers: ["가격 상향 돌파", "거래대금 증가"],
    risk_flags: [],
    model_version: "v3.2",
  },
  {
    ts: "2026-01-08T09:00:00+09:00",
    ticker: "035420",
    horizon: "1d",
    signal: "WAIT",
    confidence: 0.4,
    triggers: ["수급 약화"],
    risk_flags: ["실적 발표 임박"],
    model_version: "v3.2",
  },
];

export const demoTaxonomies: ClassificationTaxonomy[] = [
  { taxonomy_id: "KIS_INDUSTRY", name: "산업(KIS)" },
  { taxonomy_id: "THEME", name: "테마" },
];

export const demoIndustryNodes: Classification[] = [
  {
    taxonomy_id: "KIS_INDUSTRY",
    code: "KIS_L1_10",
    name: "반도체",
    level: 1,
    parent_code: null,
  },
  {
    taxonomy_id: "KIS_INDUSTRY",
    code: "KIS_L1_20",
    name: "인터넷",
    level: 1,
    parent_code: null,
  },
  {
    taxonomy_id: "KIS_INDUSTRY",
    code: "KIS_L1_30",
    name: "바이오",
    level: 1,
    parent_code: null,
  },
];

export const demoThemeNodes: Classification[] = [
  {
    taxonomy_id: "THEME",
    code: "KIS_T_AI",
    name: "AI 인프라",
    level: 1,
    parent_code: null,
  },
  {
    taxonomy_id: "THEME",
    code: "KIS_T_GREEN",
    name: "친환경 전환",
    level: 1,
    parent_code: null,
  },
  {
    taxonomy_id: "THEME",
    code: "KIS_T_HEALTH",
    name: "헬스케어",
    level: 1,
    parent_code: null,
  },
];

export const demoSecurityClassifications: Record<string, Classification[]> = {
  "005930": [
    {
      taxonomy_id: "KIS_INDUSTRY",
      code: "KIS_L1_10",
      name: "반도체",
      level: 1,
      parent_code: null,
    },
    {
      taxonomy_id: "THEME",
      code: "KIS_T_AI",
      name: "AI 인프라",
      level: 1,
      parent_code: null,
    },
  ],
  "000660": [
    {
      taxonomy_id: "KIS_INDUSTRY",
      code: "KIS_L1_10",
      name: "반도체",
      level: 1,
      parent_code: null,
    },
  ],
  "035420": [
    {
      taxonomy_id: "KIS_INDUSTRY",
      code: "KIS_L1_20",
      name: "인터넷",
      level: 1,
      parent_code: null,
    },
  ],
};
