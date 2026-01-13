-- VC Memo v1.1 Core Tables Migration
-- Feature: Financials (3Y/12Q), Ratios, KIND Market Actions, Chart Cache

-- 1. Financial Fact Table (Standardized DART Data)
CREATE TABLE IF NOT EXISTS fs_fact (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES company(company_id), -- Corrected FK
    period_type VARCHAR(10) NOT NULL, -- 'ANNUAL', 'QUARTER'
    fiscal_year INTEGER NOT NULL,
    fiscal_quarter INTEGER, -- 1, 2, 3, 4 (Nullable for Annual)
    statement_type VARCHAR(20) NOT NULL, -- 'IS', 'BS', 'CF'
    is_consolidated BOOLEAN DEFAULT TRUE,
    account_code VARCHAR(50) NOT NULL,
    account_name VARCHAR(100),
    amount NUMERIC(20, 2),
    currency VARCHAR(10) DEFAULT 'KRW',
    as_of_date DATE,
    disclosure_id VARCHAR(50), -- Link to DART rcp_no
    revision_no INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT uq_fs_fact UNIQUE (company_id, period_type, fiscal_year, fiscal_quarter, statement_type, account_code, is_consolidated, revision_no)
);

-- 2. Financial Mart - Annual 3Y Summary (Pivot)
CREATE TABLE IF NOT EXISTS fs_mart_annual (
    company_id INTEGER NOT NULL,
    fiscal_year INTEGER NOT NULL,
    
    -- Income Statement
    revenue NUMERIC(20, 2),
    gross_profit NUMERIC(20, 2),
    op_income NUMERIC(20, 2),
    net_income NUMERIC(20, 2),
    
    -- Balance Sheet
    assets NUMERIC(20, 2),
    liabilities NUMERIC(20, 2),
    equity NUMERIC(20, 2),
    
    -- Cash Flow
    op_cf NUMERIC(20, 2),
    inv_cf NUMERIC(20, 2),
    fin_cf NUMERIC(20, 2),
    fcf NUMERIC(20, 2),
    
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (company_id, fiscal_year)
);

-- 3. Financial Mart - Quarterly (Pivot)
CREATE TABLE IF NOT EXISTS fs_mart_quarter (
    company_id INTEGER NOT NULL,
    fiscal_year INTEGER NOT NULL,
    fiscal_quarter INTEGER NOT NULL,
    
    revenue NUMERIC(20, 2),
    op_income NUMERIC(20, 2),
    net_income NUMERIC(20, 2),
    
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (company_id, fiscal_year, fiscal_quarter)
);

-- 4. Financial Ratios Mart
CREATE TABLE IF NOT EXISTS fs_ratio_mart (
    company_id INTEGER NOT NULL,
    period_type VARCHAR(10) NOT NULL, -- ANNUAL, QUARTER
    fiscal_year INTEGER NOT NULL,
    fiscal_quarter INTEGER NOT NULL DEFAULT 4, -- For annual, default to 4 or 0
    
    -- Profitability
    gross_margin NUMERIC(10, 4), -- 0.1234 = 12.34%
    op_margin NUMERIC(10, 4),
    net_margin NUMERIC(10, 4),
    roe NUMERIC(10, 4),
    
    -- Stability
    debt_ratio NUMERIC(10, 4), -- Liabilities / Equity
    current_ratio NUMERIC(10, 4),
    interest_coverage NUMERIC(10, 4),
    
    -- Growth (YoY)
    revenue_growth_yoy NUMERIC(10, 4),
    op_income_growth_yoy NUMERIC(10, 4),
    
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (company_id, period_type, fiscal_year, fiscal_quarter)
);

-- 5. KIND Market Actions (Risks)
CREATE TABLE IF NOT EXISTS kind_market_action (
    id SERIAL PRIMARY KEY,
    security_id INTEGER NOT NULL, -- Link to security_master if exists, else match by code
    stock_code VARCHAR(10), -- Fallback link
    
    action_type VARCHAR(50) NOT NULL, -- 'STOP_TRADING', 'MANAGEMENT_ITEM', 'UNFAITHFUL_DISCLOSURE'
    reason TEXT,
    start_date DATE,
    end_date DATE,
    severity VARCHAR(10) DEFAULT 'MED', -- LOW, MED, HIGH
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_kind_action_code ON kind_market_action(stock_code);

-- 6. Chart Cache (For Frontend Rendering)
CREATE TABLE IF NOT EXISTS chart_cache (
    company_id INTEGER NOT NULL,
    chart_key VARCHAR(50) NOT NULL, -- 'FIN_IS_ANNUAL_3Y', 'PRICE_OHLCV_1Y'
    payload JSONB NOT NULL, -- Recharts compatible data array
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    PRIMARY KEY (company_id, chart_key)
);
