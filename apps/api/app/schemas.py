from pydantic import BaseModel, Field
from typing import Any, Literal


class UniverseItem(BaseModel):
    ticker: str
    name_ko: str
    market: Literal["KRX_KOSPI", "KRX_KOSDAQ", "KRX_ETF", "KRX_REIT"]
    sector_name: str | None = None
    avg_turnover_krw_20d: float | None = None
    last_price_krw: float | None = None


class Recommendation(BaseModel):
    as_of_date: str
    strategy_id: str
    strategy_version: str
    ticker: str
    rank: int
    score: float | None = None
    target_weight: float = Field(ge=0, le=1)
    rationale: dict[str, Any] | None = None


class TimingSignal(BaseModel):
    ts: str
    ticker: str
    horizon: Literal["1d", "3d", "1w"]
    signal: Literal["BUY", "WAIT", "REDUCE", "SELL"]
    confidence: float | None = Field(default=None, ge=0, le=1)
    triggers: list[str] = []
    risk_flags: list[str] = []
    model_version: str | None = None


class ReportRequestCreate(BaseModel):
    company_id: int
    template: Literal["investment_memo_v1", "investment_memo_vc_v1", "short_brief_v1"]
    as_of_date: str | None = None
    params: dict[str, Any] | None = None


class WatchlistCreate(BaseModel):
    name: str


class WatchlistItemAdd(BaseModel):
    ticker: str
