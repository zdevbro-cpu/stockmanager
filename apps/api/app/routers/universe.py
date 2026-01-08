from __future__ import annotations

from datetime import date as dt_date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ..auth import get_current_user
from ..db import get_db
from ..orm import Security, PriceDaily, SecurityClassification, ClassificationNode

router = APIRouter(tags=["Universe"])


@router.get("/universe")
def get_universe(
    include_etf_reit: bool = False,
    min_price_krw: float | None = None,
    min_avg_turnover_krw_20d: float | None = None,
    min_listing_days: int | None = None,
    as_of_date: str | None = None,
    include_industry_codes: list[str] | None = None,
    exclude_industry_codes: list[str] | None = None,
    include_theme_ids: list[str] | None = None,
    exclude_theme_ids: list[str] | None = None,
    _user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = select(Security).where(Security.is_active.is_(True))
    securities = db.execute(q).scalars().all()

    asof = dt_date.fromisoformat(as_of_date) if as_of_date else None

    # preload classification rows
    tickers = [s.ticker for s in securities]
    ind_map: dict[str, list[SecurityClassification]] = {}
    theme_map: dict[str, list[SecurityClassification]] = {}

    if tickers:
        rows = db.execute(select(SecurityClassification).where(SecurityClassification.ticker.in_(tickers))).scalars().all()
        for r in rows:
            if r.taxonomy_id == "KIS_INDUSTRY":
                ind_map.setdefault(r.ticker, []).append(r)
            elif r.taxonomy_id == "THEME":
                theme_map.setdefault(r.ticker, []).append(r)

    # filters
    if include_industry_codes:
        securities = [s for s in securities if any(r.code in include_industry_codes for r in ind_map.get(s.ticker, []))]
    if exclude_industry_codes:
        securities = [s for s in securities if not any(r.code in exclude_industry_codes for r in ind_map.get(s.ticker, []))]
    if include_theme_ids:
        securities = [s for s in securities if any(r.code in include_theme_ids for r in theme_map.get(s.ticker, []))]
    if exclude_theme_ids:
        securities = [s for s in securities if not any(r.code in exclude_theme_ids for r in theme_map.get(s.ticker, []))]

    # industry names (primary)
    node_name = {n.code: n.name for n in db.execute(select(ClassificationNode).where(ClassificationNode.taxonomy_id == "KIS_INDUSTRY")).scalars().all()}

    items = []
    for s in securities:
        last_price = None
        avg_turnover = None
        if asof:
            last_price = db.execute(
                select(PriceDaily.close)
                .where(PriceDaily.ticker == s.ticker, PriceDaily.trade_date <= asof)
                .order_by(PriceDaily.trade_date.desc())
                .limit(1)
            ).scalar_one_or_none()

            avg_turnover = db.execute(
                select(func.avg(PriceDaily.turnover_krw))
                .where(PriceDaily.ticker == s.ticker, PriceDaily.trade_date <= asof)
            ).scalar_one_or_none()

        primary_ind = next((r for r in ind_map.get(s.ticker, []) if r.is_primary), None)
        sector_name = node_name.get(primary_ind.code) if primary_ind else None

        if min_price_krw is not None and (last_price is None or last_price < min_price_krw):
            continue
        if min_avg_turnover_krw_20d is not None and (avg_turnover is None or avg_turnover < min_avg_turnover_krw_20d):
            continue

        items.append({
            "ticker": s.ticker,
            "name_ko": s.name_ko,
            "market": s.market,
            "sector_name": sector_name,
            "avg_turnover_krw_20d": float(avg_turnover) if avg_turnover is not None else None,
            "last_price_krw": float(last_price) if last_price is not None else None,
        })

    return {"items": items}
