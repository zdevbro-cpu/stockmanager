from datetime import date as dt_date
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func, text

from ..auth import get_current_user
from ..db import get_db
from ..orm import PriceDaily
from app.services import scrapers

router = APIRouter(tags=["Universe"])


@router.get("/universe")
def get_universe(
    include_etf_reit: bool = False,
    min_price_krw: float | None = None,
    min_avg_turnover_krw_20d: float | None = None,
    min_listing_days: int | None = None,
    as_of_date: str | None = None,
    include_industry_codes: str | None = None,
    include_industry_names: str | None = None,
    exclude_industry_codes: str | None = None,
    include_theme_ids: str | None = None,
    exclude_theme_ids: str | None = None,
    _user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.execute(text("""
        SELECT c.stock_code,
               c.name_ko,
               COALESCE(c.market, s.market) AS market,
               c.sector_name,
               c.sector_code
        FROM company c
        LEFT JOIN security s ON s.ticker = c.stock_code
        WHERE c.stock_code IS NOT NULL
        ORDER BY c.stock_code ASC
    """)).fetchall()
    securities = [
        {
            "ticker": r.stock_code,
            "name_ko": r.name_ko,
            "market": r.market,
            "sector_name": r.sector_name,
            "sector_code": r.sector_code,
        }
        for r in rows
    ]

    asof = dt_date.fromisoformat(as_of_date) if as_of_date else None
    latest_prices = db.execute(text("""
        SELECT DISTINCT ON (ticker)
               ticker,
               trade_date,
               open,
               close,
               turnover_krw
        FROM price_daily
        ORDER BY ticker, trade_date DESC
    """)).fetchall()
    latest_map = {
        row.ticker: {
            "trade_date": row.trade_date,
            "open": row.open,
            "close": row.close,
            "turnover_krw": row.turnover_krw,
        }
        for row in latest_prices
    }
    avg_turnover_rows = db.execute(text("""
        SELECT ticker, AVG(turnover_krw) AS avg_turnover_krw_20d
        FROM (
            SELECT ticker,
                   turnover_krw,
                   ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY trade_date DESC) AS rn
            FROM price_daily
            WHERE turnover_krw IS NOT NULL
        ) t
        WHERE rn <= 20
        GROUP BY ticker
    """)).fetchall()
    avg_turnover_map = {row.ticker: row.avg_turnover_krw_20d for row in avg_turnover_rows}

    def split_csv(value: str | None) -> List[str]:
        if not value:
            return []
        return [v.strip() for v in value.split(",") if v.strip()]

    industry_name_map: dict[str, str] = {}
    # filters
    include_industry_name_list = split_csv(include_industry_names)
    if include_industry_name_list:
        tickers_by_industry: set[str] = set()
        for name in include_industry_name_list:
            link = scrapers.get_industry_link_by_name(name)
            if not link:
                continue
            members = scrapers.get_naver_industry_members(link)
            tickers_by_industry.update(members)
            for ticker in members:
                industry_name_map.setdefault(ticker, name)
        if tickers_by_industry:
            securities = [s for s in securities if s["ticker"] in tickers_by_industry]
    include_industry_code_list = split_csv(include_industry_codes)
    if include_industry_code_list:
        securities = [s for s in securities if s.get("sector_code") in include_industry_code_list]
    exclude_industry_code_list = split_csv(exclude_industry_codes)
    if exclude_industry_code_list:
        securities = [s for s in securities if s.get("sector_code") not in exclude_industry_code_list]

    items = []
    for s in securities:
        ticker = s["ticker"]
        last_price = None
        avg_turnover = None
        latest = latest_map.get(ticker)
        if asof:
            last_price = db.execute(
                select(PriceDaily.close)
                .where(PriceDaily.ticker == ticker, PriceDaily.trade_date <= asof)
                .order_by(PriceDaily.trade_date.desc())
                .limit(1)
            ).scalar_one_or_none()
            avg_turnover = db.execute(
                select(func.avg(PriceDaily.turnover_krw))
                .where(PriceDaily.ticker == ticker, PriceDaily.trade_date <= asof)
            ).scalar_one_or_none()
        else:
            last_price = latest.get("close") if latest else None
            avg_turnover = avg_turnover_map.get(ticker)

        sector_code = s.get("sector_code")
        sector_name = s.get("sector_name")
        if not sector_name and ticker in industry_name_map:
            sector_name = industry_name_map[ticker]

        if min_price_krw is not None and (last_price is None or last_price < min_price_krw):
            continue
        if min_avg_turnover_krw_20d is not None and (avg_turnover is None or avg_turnover < min_avg_turnover_krw_20d):
            continue

        signal = None
        if latest:
            open_price = latest.get("open")
            close_price = latest.get("close")
            if open_price is not None and close_price is not None:
                if close_price > open_price:
                    signal = "BUY"
                elif close_price < open_price:
                    signal = "SELL"
                else:
                    signal = "WAIT"

        items.append({
            "ticker": ticker,
            "name_ko": s["name_ko"],
            "market": s["market"],
            "sector_name": sector_name,
            "sector_code": sector_code,
            "avg_turnover_krw_20d": float(avg_turnover) if avg_turnover is not None else None,
            "last_price_krw": float(last_price) if last_price is not None else None,
            "signal": signal,
        })

    return {"items": items}
@router.get("/companies/search")
def search_company(q: str, db: Session = Depends(get_db)):
    # Search in company table by name_ko or stock_code
    rows = db.execute(text("""
        SELECT company_id, name_ko, stock_code, sector_name, market
        FROM company
        WHERE name_ko ILIKE :q OR stock_code ILIKE :q
        ORDER BY stock_code ASC
        LIMIT 10
    """), {"q": f"%{q}%"}).fetchall()
    return [
        {
            "id": r.company_id,
            "name": r.name_ko,
            "ticker": r.stock_code,
            "sector": r.sector_name,
            "market": r.market
        }
        for r in rows
    ]
