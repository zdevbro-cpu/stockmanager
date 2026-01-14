from __future__ import annotations

from datetime import date as dt_date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, text

from ..auth import get_current_user
from ..db import get_db
from ..orm import TimingSignalRow

router = APIRouter(tags=["Signals"])


def _to_float(value: object | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _round_price(value: float) -> int:
    return int(round(value / 10.0) * 10)


def _compute_target_range(series: list[tuple], roe: float | None, debt_ratio: float | None):
    if not series:
        return None, None, None
    series_sorted = sorted(series, key=lambda x: x[0])
    closes = [_to_float(row[4]) for row in series_sorted]
    closes = [value for value in closes if value is not None]
    if not closes:
        return None, None, None
    latest_close = closes[-1]
    if latest_close <= 0:
        return None, None, None

    trs: list[float] = []
    prev_close = None
    for trade_date, open_p, high_p, low_p, close_p in series_sorted:
        close_val = _to_float(close_p)
        if close_val is None:
            continue
        high_val = _to_float(high_p) if high_p is not None else close_val
        low_val = _to_float(low_p) if low_p is not None else close_val
        if high_val is None or low_val is None:
            continue
        if prev_close is None:
            tr = high_val - low_val
        else:
            tr = max(
                high_val - low_val,
                abs(high_val - prev_close),
                abs(low_val - prev_close),
            )
        trs.append(tr)
        prev_close = close_val

    if not trs:
        return None, None, None
    lookback = min(14, len(trs))
    atr = sum(trs[-lookback:]) / lookback if lookback else 0.0
    if atr <= 0:
        return None, None, None

    tech_low = latest_close - (atr * 1.5)
    tech_high = latest_close + (atr * 2.0)

    factor = 1.0
    if roe is not None:
        if roe >= 15:
            factor += 0.1
        elif roe <= 5:
            factor -= 0.1
    if debt_ratio is not None:
        if debt_ratio >= 200:
            factor -= 0.1
        elif debt_ratio <= 100:
            factor += 0.05
    factor = max(0.7, min(1.3, factor))

    low = latest_close - (latest_close - tech_low) * factor
    high = latest_close + (tech_high - latest_close) * factor
    return _round_price(low), _round_price(high), {
        "basis": "mixed_atr_roe_debt",
        "atr": round(atr, 2),
        "factor": round(factor, 2),
    }


@router.get("/signals")
def get_signals(
    ticker: str | None = None,
    tickers: str | None = None,
    horizon: str | None = None,
    limit: int = 200,
    _user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    horizon_key = (horizon or "1D").upper()
    horizon_map = {
        "1D": {"short": 5, "long": 20, "mom": 5},
        "3D": {"short": 10, "long": 30, "mom": 10},
        "1W": {"short": 20, "long": 60, "mom": 20},
    }
    config = horizon_map.get(horizon_key, horizon_map["1D"])

    tickers_list: list[str] = []
    if tickers:
        tickers_list = [t.strip() for t in tickers.split(",") if t.strip()]
    elif ticker:
        tickers_list = [ticker]

    if tickers_list:
        rows = db.execute(
            text(
                """
                SELECT t.ticker, t.trade_date, t.open, t.high, t.low, t.close
                FROM (
                    SELECT ticker,
                           trade_date,
                           open,
                           high,
                           low,
                           close,
                           ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY trade_date DESC) AS rn
                    FROM price_daily
                    WHERE ticker = ANY(:tickers)
                ) t
                WHERE t.rn <= :lookback
                ORDER BY t.ticker, t.trade_date DESC
                """
            ),
            {"tickers": tickers_list, "lookback": config["long"]},
        ).fetchall()

        name_rows = db.execute(
            text(
                """
                SELECT stock_code, name_ko, company_id
                FROM company
                WHERE stock_code = ANY(:tickers)
                """
            ),
            {"tickers": tickers_list},
        ).fetchall()
        name_map = {row.stock_code: row.name_ko for row in name_rows}
        company_map = {row.stock_code: row.company_id for row in name_rows}
        company_ids = [row.company_id for row in name_rows if row.company_id is not None]

        ratio_map: dict[int, tuple] = {}
        if company_ids:
            ratio_rows = db.execute(
                text(
                    """
                    SELECT DISTINCT ON (company_id)
                        company_id,
                        roe,
                        debt_ratio
                    FROM fs_ratio_mart
                    WHERE company_id = ANY(:company_ids)
                    ORDER BY company_id, fiscal_year DESC, fiscal_quarter DESC
                    """
                ),
                {"company_ids": company_ids},
            ).fetchall()
            ratio_map = {row.company_id: (row.roe, row.debt_ratio) for row in ratio_rows}

        grouped: dict[str, list[tuple]] = {}
        for row in rows:
            grouped.setdefault(row.ticker, []).append(
                (row.trade_date, row.open, row.high, row.low, row.close)
            )

        items = []
        for symbol in tickers_list:
            series = grouped.get(symbol, [])
            if not series:
                items.append({
                    "ts": dt_date.today().isoformat(),
                    "ticker": symbol,
                    "name": name_map.get(symbol),
                    "horizon": horizon_key,
                    "signal": "WAIT",
                    "confidence": 0.0,
                    "triggers": ["데이터 부족"],
                    "risk_flags": ["NO_PRICE_DATA"],
                    "model_version": "simple_ma_v1",
                    "target_price_low": None,
                    "target_price_high": None,
                    "target_price_basis": None,
                })
                continue

            closes = [_to_float(value[4]) for value in series]
            closes = [value for value in closes if value is not None]
            trade_date = series[0][0]
            if len(closes) < config["long"]:
                roe = None
                debt_ratio = None
                company_id = company_map.get(symbol)
                if company_id is not None and company_id in ratio_map:
                    roe_raw, debt_raw = ratio_map[company_id]
                    roe = _to_float(roe_raw)
                    debt_ratio = _to_float(debt_raw)
                low, high, basis = _compute_target_range(series, roe, debt_ratio)
                items.append({
                    "ts": trade_date.isoformat() if trade_date else dt_date.today().isoformat(),
                    "ticker": symbol,
                    "name": name_map.get(symbol),
                    "horizon": horizon_key,
                    "signal": "WAIT",
                    "confidence": 0.0,
                    "triggers": ["데이터 부족"],
                    "risk_flags": ["INSUFFICIENT_HISTORY"],
                    "model_version": "simple_ma_v1",
                    "target_price_low": low,
                    "target_price_high": high,
                    "target_price_basis": basis,
                })
                continue

            short_window = closes[: config["short"]]
            long_window = closes[: config["long"]]
            mom_window = closes[: config["mom"]]

            ma_short = sum(short_window) / len(short_window)
            ma_long = sum(long_window) / len(long_window)
            mom_base = mom_window[-1] if len(mom_window) >= 2 else mom_window[0]
            momentum = (mom_window[0] / mom_base - 1.0) if mom_base else 0.0

            signal = "WAIT"
            triggers: list[str] = []
            if ma_short > ma_long and momentum > 0:
                signal = "BUY"
                triggers = [
                    f"MA{config['short']} > MA{config['long']}",
                    f"Mom{config['mom']}d > 0",
                ]
            elif ma_short < ma_long and momentum < 0:
                signal = "SELL"
                triggers = [
                    f"MA{config['short']} < MA{config['long']}",
                    f"Mom{config['mom']}d < 0",
                ]
            else:
                triggers = [
                    f"MA{config['short']} ~ MA{config['long']}",
                    f"Mom{config['mom']}d 혼조",
                ]

            spread = abs(ma_short - ma_long) / ma_long if ma_long else 0.0
            confidence = min(spread * 10, 1.0)

            roe = None
            debt_ratio = None
            company_id = company_map.get(symbol)
            if company_id is not None and company_id in ratio_map:
                roe_raw, debt_raw = ratio_map[company_id]
                roe = _to_float(roe_raw)
                debt_ratio = _to_float(debt_raw)
            low, high, basis = _compute_target_range(series, roe, debt_ratio)

            items.append({
                "ts": trade_date.isoformat() if trade_date else dt_date.today().isoformat(),
                "ticker": symbol,
                "name": name_map.get(symbol),
                "horizon": horizon_key,
                "signal": signal,
                "confidence": round(confidence, 3),
                "triggers": triggers,
                "risk_flags": [],
                "model_version": "simple_ma_v1",
                "target_price_low": low,
                "target_price_high": high,
                "target_price_basis": basis,
            })

        return {"items": items}

    stmt = select(TimingSignalRow)
    if ticker:
        stmt = stmt.where(TimingSignalRow.ticker == ticker)
    if horizon:
        stmt = stmt.where(TimingSignalRow.horizon == horizon)
    rows = db.execute(stmt.order_by(TimingSignalRow.ts.desc()).limit(limit)).scalars().all()

    return {"items": [
        {
            "ts": r.ts.isoformat(),
            "ticker": r.ticker,
            "horizon": r.horizon,
            "signal": r.signal,
            "confidence": r.confidence,
            "triggers": r.triggers or [],
            "risk_flags": r.risk_flags or [],
            "model_version": r.model_version,
            "target_price_low": None,
            "target_price_high": None,
            "target_price_basis": None,
        } for r in rows
    ]}
