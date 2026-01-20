-- PostgreSQL Schema (ERD/DDL) v2.1
-- Generated: 2026-01-08 (KST)
-- 목적: 코스피/코스닥 단기 추천(TopN+비중) + 타이밍 신호 + 상장/비상장 VC 리포트 + 문서 인제스트/RAG + 백테스트/버전관리

BEGIN;

DO $$ BEGIN
  CREATE TYPE market_scope AS ENUM ('KRX_KOSPI','KRX_KOSDAQ','KRX_ETF','KRX_REIT');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE signal_type AS ENUM ('BUY','WAIT','REDUCE','SELL');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE report_status AS ENUM ('PENDING','RUNNING','DONE','FAILED','CANCELED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE company_type AS ENUM ('LISTED','PRIVATE');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS company (
  company_id        BIGSERIAL PRIMARY KEY,
  company_type      company_type NOT NULL,
  name_ko           TEXT NOT NULL,
  name_en           TEXT,
  -- listed
  corp_code         TEXT UNIQUE,
  stock_code        TEXT UNIQUE,
  market            market_scope,
  sector_code       TEXT,
  sector_name       TEXT,
  listing_date      DATE,
  delisting_date    DATE,
  status            TEXT,
  -- private (민감정보는 해시/암호화 권장)
  external_id_hash  TEXT UNIQUE,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_company_type ON company(company_type);
CREATE INDEX IF NOT EXISTS idx_company_market ON company(market);

CREATE TABLE IF NOT EXISTS security (
  security_id   BIGSERIAL PRIMARY KEY,
  ticker        TEXT NOT NULL UNIQUE,
  isin          TEXT,
  market        market_scope,
  currency      TEXT DEFAULT 'KRW',
  lot_size      INTEGER DEFAULT 1,
  tick_size     NUMERIC,
  company_id    BIGINT REFERENCES company(company_id) ON DELETE SET NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_security_company_id ON security(company_id);

CREATE TABLE IF NOT EXISTS price_daily (
  ticker        TEXT NOT NULL,
  trade_date    DATE NOT NULL,
  open          NUMERIC,
  high          NUMERIC,
  low           NUMERIC,
  close         NUMERIC,
  volume        NUMERIC,
  turnover_krw  NUMERIC,
  adj_factor    NUMERIC,
  source        TEXT DEFAULT 'KIS',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (ticker, trade_date)
);
CREATE INDEX IF NOT EXISTS idx_price_daily_date ON price_daily(trade_date);

CREATE TABLE IF NOT EXISTS market_index_daily (
  index_code    TEXT NOT NULL,
  trade_date    DATE NOT NULL,
  close         NUMERIC,
  ret_1d        NUMERIC,
  vol_20d       NUMERIC,
  source        TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (index_code, trade_date)
);

CREATE TABLE IF NOT EXISTS dart_filing (
  rcp_no        TEXT PRIMARY KEY,
  corp_code     TEXT NOT NULL,
  filing_date   DATE NOT NULL,
  filing_time   TIME,
  filing_type   TEXT,
  title         TEXT,
  url           TEXT,
  is_last_report BOOLEAN DEFAULT FALSE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_dart_filing_corp_date ON dart_filing(corp_code, filing_date);

CREATE TABLE IF NOT EXISTS financial_statement (
  corp_code        TEXT NOT NULL,
  period_end       DATE NOT NULL,
  announced_at     TIMESTAMPTZ NOT NULL,
  item_code        TEXT NOT NULL,
  item_name        TEXT,
  value            NUMERIC,
  unit             TEXT,
  consolidated_flag BOOLEAN DEFAULT TRUE,
  source_rcp_no    TEXT REFERENCES dart_filing(rcp_no) ON DELETE SET NULL,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (corp_code, period_end, item_code, announced_at)
);
CREATE INDEX IF NOT EXISTS idx_fs_announced_at ON financial_statement(announced_at);
CREATE INDEX IF NOT EXISTS idx_fs_corp_period ON financial_statement(corp_code, period_end);

CREATE TABLE IF NOT EXISTS document (
  document_id    BIGSERIAL PRIMARY KEY,
  company_id     BIGINT REFERENCES company(company_id) ON DELETE CASCADE,
  source_type    TEXT NOT NULL, -- DART, UPLOAD, EXTERNAL
  source_ref     TEXT,          -- rcp_no 등
  file_path      TEXT NOT NULL, -- storage path
  file_type      TEXT,          -- pdf/pptx/xlsx/docx
  sha256         TEXT,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_document_company ON document(company_id);
CREATE INDEX IF NOT EXISTS idx_document_source ON document(source_type, source_ref);

CREATE TABLE IF NOT EXISTS document_chunk (
  chunk_id       BIGSERIAL PRIMARY KEY,
  document_id    BIGINT NOT NULL REFERENCES document(document_id) ON DELETE CASCADE,
  chunk_no       INTEGER NOT NULL,
  text_path      TEXT,
  content_text   TEXT,
  token_count    INTEGER,
  embedding_id   TEXT,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(document_id, chunk_no)
);
CREATE INDEX IF NOT EXISTS idx_document_chunk_doc ON document_chunk(document_id);

CREATE TABLE IF NOT EXISTS macro_series (
  series_code   TEXT NOT NULL,
  obs_date      DATE NOT NULL,
  value         NUMERIC,
  unit          TEXT,
  source        TEXT DEFAULT 'ECOS',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (series_code, obs_date)
);

CREATE TABLE IF NOT EXISTS ingest_run_log (
  run_id      BIGSERIAL PRIMARY KEY,
  job_id      TEXT NOT NULL,
  status      TEXT NOT NULL,
  started_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at TIMESTAMPTZ,
  row_count   INTEGER,
  message     TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_ingest_run_log_job_started ON ingest_run_log(job_id, started_at DESC);

CREATE TABLE IF NOT EXISTS feature_snapshot (
  as_of_date     DATE NOT NULL,
  ticker         TEXT NOT NULL,
  feature_name   TEXT NOT NULL,
  value          NUMERIC,
  effective_from TIMESTAMPTZ,
  data_version   TEXT NOT NULL DEFAULT 'v1',
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (as_of_date, ticker, feature_name, data_version)
);
CREATE INDEX IF NOT EXISTS idx_feature_snapshot_ticker_date ON feature_snapshot(ticker, as_of_date);

CREATE TABLE IF NOT EXISTS factor_score (
  as_of_date      DATE NOT NULL,
  ticker          TEXT NOT NULL,
  model_version   TEXT NOT NULL,
  total_score     NUMERIC,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (as_of_date, ticker, model_version)
);

CREATE TABLE IF NOT EXISTS strategy_def (
  strategy_id    TEXT NOT NULL,
  version        TEXT NOT NULL,
  schema_version TEXT NOT NULL DEFAULT '2.1.0',
  name           TEXT,
  json_def       JSONB NOT NULL,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY(strategy_id, version)
);

CREATE TABLE IF NOT EXISTS backtest_run (
  run_id           BIGSERIAL PRIMARY KEY,
  strategy_id      TEXT NOT NULL,
  strategy_version TEXT NOT NULL,
  start_date       DATE NOT NULL,
  end_date         DATE NOT NULL,
  cost_model       JSONB NOT NULL,
  metrics          JSONB,
  artifacts_path   TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  FOREIGN KEY(strategy_id, strategy_version) REFERENCES strategy_def(strategy_id, version) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS recommendation (
  as_of_date       DATE NOT NULL,
  strategy_id      TEXT NOT NULL,
  strategy_version TEXT NOT NULL,
  ticker           TEXT NOT NULL,
  rank             INTEGER NOT NULL,
  score            NUMERIC,
  target_weight    NUMERIC,
  rationale        JSONB,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY(as_of_date, strategy_id, strategy_version, ticker),
  FOREIGN KEY(strategy_id, strategy_version) REFERENCES strategy_def(strategy_id, version) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS idx_reco_asof_rank ON recommendation(as_of_date, rank);

CREATE TABLE IF NOT EXISTS timing_signal (
  ts            TIMESTAMPTZ NOT NULL,
  ticker        TEXT NOT NULL,
  horizon       TEXT NOT NULL,
  signal        signal_type NOT NULL,
  confidence    NUMERIC,
  triggers      JSONB,
  risk_flags    JSONB,
  model_version TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY(ts, ticker, horizon)
);
CREATE INDEX IF NOT EXISTS idx_signal_ticker_ts ON timing_signal(ticker, ts DESC);

CREATE TABLE IF NOT EXISTS watchlist (
  watchlist_id  BIGSERIAL PRIMARY KEY,
  owner_user_id TEXT NOT NULL,
  name          TEXT NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS watchlist_item (
  watchlist_id  BIGINT NOT NULL REFERENCES watchlist(watchlist_id) ON DELETE CASCADE,
  ticker        TEXT NOT NULL,
  added_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY(watchlist_id, ticker)
);

CREATE TABLE IF NOT EXISTS report_request (
  report_id     BIGSERIAL PRIMARY KEY,
  company_id    BIGINT NOT NULL REFERENCES company(company_id) ON DELETE CASCADE,
  template      TEXT NOT NULL,
  as_of_date    DATE,
  status        report_status NOT NULL DEFAULT 'PENDING',
  requested_by  TEXT,
  params        JSONB,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_report_company ON report_request(company_id, created_at DESC);

CREATE TABLE IF NOT EXISTS report_artifact (
  artifact_id   BIGSERIAL PRIMARY KEY,
  report_id     BIGINT NOT NULL REFERENCES report_request(report_id) ON DELETE CASCADE,
  format        TEXT NOT NULL, -- pdf/html
  file_path     TEXT NOT NULL,
  citations     JSONB,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMIT;


-- === Classification (Industry/Theme) v2.2 ===
DO $$ BEGIN
  CREATE TYPE taxonomy_kind AS ENUM ('INDUSTRY','THEME');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS classification_taxonomy (
  taxonomy_id   TEXT PRIMARY KEY,  -- e.g., KIS_INDUSTRY, THEME
  kind          taxonomy_kind NOT NULL,
  name          TEXT NOT NULL,
  provider      TEXT,              -- e.g., KIS, INTERNAL
  version       TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS classification_node (
  taxonomy_id   TEXT NOT NULL REFERENCES classification_taxonomy(taxonomy_id) ON DELETE CASCADE,
  code          TEXT NOT NULL,      -- industry code or theme id/slug
  name          TEXT NOT NULL,
  level         INTEGER,            -- industry tree level (theme can be NULL/1)
  parent_code   TEXT,               -- nullable
  extra         JSONB,              -- provider-specific fields
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (taxonomy_id, code)
);
CREATE INDEX IF NOT EXISTS idx_class_node_tax_parent ON classification_node(taxonomy_id, parent_code);
CREATE INDEX IF NOT EXISTS idx_class_node_tax_level ON classification_node(taxonomy_id, level);

-- M:N mapping: security ↔ classification (industry/theme)
CREATE TABLE IF NOT EXISTS security_classification (
  ticker         TEXT NOT NULL,
  taxonomy_id    TEXT NOT NULL,
  code           TEXT NOT NULL,
  is_primary     BOOLEAN NOT NULL DEFAULT FALSE,  -- industry primary classification
  effective_from DATE,
  effective_to   DATE,
  confidence     NUMERIC,                         -- for theme inference later
  source         TEXT,                            -- KIS / INTERNAL / MANUAL
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (ticker, taxonomy_id, code, effective_from),
  FOREIGN KEY (taxonomy_id, code) REFERENCES classification_node(taxonomy_id, code) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS idx_sec_class_ticker ON security_classification(ticker);
CREATE INDEX IF NOT EXISTS idx_sec_class_tax_code ON security_classification(taxonomy_id, code);
