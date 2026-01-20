from __future__ import annotations

from datetime import date as dt_date
import os
import pandas as pd
import numpy as np
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, text

from ..auth import get_current_user
from ..db import get_db
from ..orm import TimingSignalRow, SignalConfigRow

router = APIRouter(tags=["Signals"])

SIGNAL_ENGINE_DEFAULT = os.environ.get("SIGNAL_ENGINE", "simple_ma_v2_gate3").lower()

DEFAULT_SIGNAL_WEIGHTS = {
    "ma_gap": 0.45,
    "trend_strength": 0.35,
    "vol_strength": 0.20,
    "vol_penalty": -0.40,
}

HORIZON_RULES = {
    "1D": dict(short=5, long=20, mom=5, slope_lb=10,
               vol_n=20, vol_mult=1.20, atr_n=14,
               vol_q_window=200, vol_q=0.90, confirm=2),
    "3D": dict(short=10, long=30, mom=10, slope_lb=15,
               vol_n=20, vol_mult=1.15, atr_n=14,
               vol_q_window=200, vol_q=0.85, confirm=2),
    "1W": dict(short=20, long=60, mom=20, slope_lb=20,
               vol_n=20, vol_mult=1.10, atr_n=14,
               vol_q_window=200, vol_q=0.80, confirm=1),
}

_RULE_FLOAT_KEYS = {"vol_mult", "vol_q"}
_ALLOWED_ENGINES = {"simple_ma_v1", "simple_ma_v2_gate3"}


class SignalConfigPayload(BaseModel):
    mode: str
    config: dict | None = None


def _default_signal_config() -> dict:
    return {
        "engine": SIGNAL_ENGINE_DEFAULT if SIGNAL_ENGINE_DEFAULT in _ALLOWED_ENGINES else "simple_ma_v2_gate3",
        "horizons": {key: value.copy() for key, value in HORIZON_RULES.items()},
        "weights": DEFAULT_SIGNAL_WEIGHTS.copy(),
    }


def _normalize_rule(rule: dict, defaults: dict) -> dict:
    normalized = {}
    for key, default_val in defaults.items():
        raw_val = rule.get(key, default_val)
        try:
            if key in _RULE_FLOAT_KEYS:
                normalized[key] = float(raw_val)
            else:
                normalized[key] = int(raw_val)
        except (TypeError, ValueError):
            normalized[key] = default_val
    return normalized


def _normalize_config(config: dict) -> dict:
    defaults = _default_signal_config()
    engine = str(config.get("engine", defaults["engine"])).lower()
    if engine not in _ALLOWED_ENGINES:
        engine = defaults["engine"]

    horizons_raw = config.get("horizons", {})
    horizons = {}
    for key, default_rule in defaults["horizons"].items():
        rule_raw = horizons_raw.get(key, {}) if isinstance(horizons_raw, dict) else {}
        horizons[key] = _normalize_rule(rule_raw, default_rule)

    weights_raw = config.get("weights", {})
    weights = {}
    for key, default_val in defaults["weights"].items():
        raw_val = weights_raw.get(key, default_val) if isinstance(weights_raw, dict) else default_val
        try:
            weights[key] = float(raw_val)
        except (TypeError, ValueError):
            weights[key] = default_val

    return {"engine": engine, "horizons": horizons, "weights": weights}


def _get_signal_config(db: Session) -> tuple[dict, str, dict]:
    defaults = _default_signal_config()
    row = db.execute(select(SignalConfigRow).where(SignalConfigRow.id == 1)).scalar_one_or_none()
    if not row:
        return defaults, "default", defaults
    config = _normalize_config({
        "engine": row.engine,
        "horizons": row.horizons,
        "weights": row.weights,
    })
    return config, "custom", defaults


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

def _sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n, min_periods=n).mean()

def _atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        (high - low).abs(),
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(n, min_periods=n).mean()

def _rolling_quantile(s: pd.Series, window: int, q: float) -> pd.Series:
    return s.rolling(window, min_periods=window).quantile(q)

def _apply_confirm_bars(cond: pd.Series, confirm: int) -> pd.Series:
    if confirm <= 1:
        return cond.fillna(False)
    c = cond.fillna(False).astype(int)
    return c.rolling(confirm, min_periods=confirm).sum().eq(confirm)

def _build_price_df(rows: list[tuple]) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "volume"])
    df = df.sort_values("date")
    return df

def compute_signal_simple_ma_v1(price_daily: pd.DataFrame, horizon: str, rules: dict) -> dict:
    r = rules
    df = price_daily.copy().sort_values("date")
    if df.empty:
        return {"signal": "WAIT", "confidence": 0.0, "triggers": [], "debug": {"reason": "no_data"}}
    close = df["close"].astype(float)
    ma_s = _sma(close, r["short"])
    ma_l = _sma(close, r["long"])
    mom = close / close.shift(r["mom"]) - 1.0
    last = df.index[-1]
    buy_base = (ma_s > ma_l) & (mom > 0)
    sell_base = (ma_s < ma_l) & (mom < 0)
    signal = "WAIT"
    triggers: list[str] = []
    if bool(buy_base.loc[last]) and not bool(sell_base.loc[last]):
        signal = "BUY"
        triggers = [f"MA{r['short']} > MA{r['long']}", f"Mom{r['mom']}d > 0"]
    elif bool(sell_base.loc[last]) and not bool(buy_base.loc[last]):
        signal = "SELL"
        triggers = [f"MA{r['short']} < MA{r['long']}", f"Mom{r['mom']}d < 0"]
    else:
        triggers = [f"MA{r['short']} ~ MA{r['long']}", f"Mom{r['mom']}d mixed"]
    spread = abs(ma_s - ma_l) / ma_l.replace({0: np.nan})
    confidence = float(spread.loc[last]) if not pd.isna(spread.loc[last]) else 0.0
    confidence = max(0.0, min(confidence, 1.0))
    return {
        "signal": signal,
        "confidence": confidence,
        "triggers": triggers,
        "debug": {
            "buy_base": bool(buy_base.loc[last]) if not pd.isna(buy_base.loc[last]) else False,
            "sell_base": bool(sell_base.loc[last]) if not pd.isna(sell_base.loc[last]) else False,
        },
    }

def compute_signal_simple_ma_v2_gate3(price_daily: pd.DataFrame, horizon: str, rules: dict, weights: dict) -> dict:
    r = rules
    df = price_daily.copy().sort_values("date")
    if df.empty:
        return {"signal": "WAIT", "confidence": 0.0, "triggers": [], "debug": {"reason": "no_data"}}
    for col in ("open", "high", "low", "close", "volume"):
        if col not in df.columns:
            return {"signal": "WAIT", "confidence": 0.0, "debug": {"reason": f"missing:{col}"}}

    close = df["close"].astype(float)
    vol = df["volume"].astype(float)

    ma_s = _sma(close, r["short"])
    ma_l = _sma(close, r["long"])
    mom = close / close.shift(r["mom"]) - 1.0
    slope = (ma_l - ma_l.shift(r["slope_lb"])) / float(r["slope_lb"])

    vol_ma = _sma(vol, r["vol_n"])
    vol_ratio = vol / vol_ma.replace({0: np.nan})

    atr = _atr(df, r["atr_n"])
    atr_pct = atr / close.replace({0: np.nan})
    atr_pct_q = _rolling_quantile(atr_pct, r["vol_q_window"], r["vol_q"])
    atr_pct_fallback = _sma(atr_pct, 60)
    atr_gate = (atr_pct <= atr_pct_q)
    atr_gate = atr_gate.where(~atr_pct_q.isna(), atr_pct <= atr_pct_fallback)
    atr_gate = atr_gate.fillna(False)

    buy_base = (ma_s > ma_l) & (mom > 0)
    sell_base = (ma_s < ma_l) & (mom < 0)
    buy_trend = (close > ma_l) & (slope > 0)
    sell_trend = (close < ma_l) & (slope < 0)

    buy_event = (close > ma_s) & (close.shift(1) <= ma_s.shift(1))
    sell_event = (close < ma_s) & (close.shift(1) >= ma_s.shift(1))
    vol_gate_relaxed = (vol_ratio >= 1.0)
    buy_vol_gate = np.where(buy_event.fillna(False), (vol_ratio >= r["vol_mult"]), vol_gate_relaxed)
    sell_vol_gate = np.where(sell_event.fillna(False), (vol_ratio >= r["vol_mult"]), vol_gate_relaxed)
    buy_vol_gate = pd.Series(buy_vol_gate, index=df.index).fillna(False)
    sell_vol_gate = pd.Series(sell_vol_gate, index=df.index).fillna(False)

    buy_final_raw = buy_base & buy_trend & atr_gate & buy_vol_gate
    sell_final_raw = sell_base & sell_trend & atr_gate & sell_vol_gate
    buy_final = _apply_confirm_bars(buy_final_raw, r["confirm"])
    sell_final = _apply_confirm_bars(sell_final_raw, r["confirm"])

    last = df.index[-1]
    if bool(buy_final.loc[last]) and not bool(sell_final.loc[last]):
        signal = "BUY"
    elif bool(sell_final.loc[last]) and not bool(buy_final.loc[last]):
        signal = "SELL"
    else:
        signal = "WAIT"

    ma_gap = (ma_s - ma_l).abs() / ma_l.replace({0: np.nan})
    trend_strength = (slope.abs() / ma_l.replace({0: np.nan}))
    vol_strength = ((vol_ratio - 1.0) / max(r["vol_mult"] - 1.0, 1e-9)).clip(0, 1)
    is_event = (buy_event | sell_event).fillna(False)
    vol_strength = vol_strength.where(is_event, 0.0).fillna(0.0)
    vol_penalty = ((atr_pct - atr_pct_q) / atr_pct_q.replace({0: np.nan})).clip(0, 1)
    vol_penalty = vol_penalty.fillna(0.0)
    w_gap = weights.get("ma_gap", 0.45)
    w_trend = weights.get("trend_strength", 0.35)
    w_vol = weights.get("vol_strength", 0.20)
    w_penalty = weights.get("vol_penalty", -0.40)
    conf = (w_gap * ma_gap.fillna(0.0) + w_trend * trend_strength.fillna(0.0) + w_vol * vol_strength + w_penalty * vol_penalty)
    conf = conf.clip(0, 1).fillna(0.0)

    triggers: list[str] = []
    if signal == "BUY":
        triggers = [
            f"MA{r['short']} > MA{r['long']}",
            f"Mom{r['mom']}d > 0",
            "TrendGate",
            "VolumeGate",
            "VolatilityGate",
            f"Confirm{r['confirm']}",
        ]
    elif signal == "SELL":
        triggers = [
            f"MA{r['short']} < MA{r['long']}",
            f"Mom{r['mom']}d < 0",
            "TrendGate",
            "VolumeGate",
            "VolatilityGate",
            f"Confirm{r['confirm']}",
        ]
    else:
        triggers = ["Gates not satisfied"]

    return {
        "signal": signal,
        "confidence": float(conf.loc[last]),
        "triggers": triggers,
        "debug": {
            "buy_base": bool(buy_base.loc[last]) if not pd.isna(buy_base.loc[last]) else False,
            "sell_base": bool(sell_base.loc[last]) if not pd.isna(sell_base.loc[last]) else False,
            "buy_trend": bool(buy_trend.loc[last]) if not pd.isna(buy_trend.loc[last]) else False,
            "sell_trend": bool(sell_trend.loc[last]) if not pd.isna(sell_trend.loc[last]) else False,
            "atr_gate": bool(atr_gate.loc[last]) if not pd.isna(atr_gate.loc[last]) else False,
            "vol_ratio": float(vol_ratio.loc[last]) if not pd.isna(vol_ratio.loc[last]) else None,
        }
    }


@router.get("/signals")
def get_signals(
    ticker: str | None = None,
    tickers: str | None = None,
    horizon: str | None = None,
    limit: int | None = None,
    _user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    horizon_key = (horizon or "1D").upper()
    signal_config, _, _ = _get_signal_config(db)
    config = signal_config["horizons"].get(horizon_key, signal_config["horizons"]["1D"])
    engine = signal_config["engine"]
    model_version_default = "simple_ma_v1" if engine == "simple_ma_v1" else "simple_ma_v2_gate3"

    tickers_list: list[str] = []
    if tickers:
        tickers_list = [t.strip() for t in tickers.split(",") if t.strip()]
    elif ticker:
        tickers_list = [ticker]

    if tickers_list:
        rows = db.execute(
            text(
                """
                SELECT t.ticker, t.trade_date, t.open, t.high, t.low, t.close, t.volume
                FROM (
                    SELECT ticker,
                           trade_date,
                           open,
                           high,
                           low,
                           close,
                           volume,
                           ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY trade_date DESC) AS rn
                    FROM price_daily
                    WHERE ticker = ANY(:tickers)
                ) t
                WHERE t.rn <= :lookback
                ORDER BY t.ticker, t.trade_date DESC
                """
            ),
            {"tickers": tickers_list, "lookback": max(
                config["long"],
                config["mom"],
                config["slope_lb"],
                config["vol_q_window"],
                config["vol_n"],
                config["atr_n"],
                60,
            ) + 5},
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
                (row.trade_date, row.open, row.high, row.low, row.close, row.volume)
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
                    "model_version": model_version_default,
                    "target_price_low": None,
                    "target_price_high": None,
                    "target_price_basis": None,
                })
                continue

            trade_date = series[0][0]
            price_df = _build_price_df(series)
            closes = [_to_float(value[4]) for value in series]
            closes = [value for value in closes if value is not None]
            required_lookback = max(
                config["long"],
                config["mom"],
                config["slope_lb"],
                config["vol_q_window"],
                config["vol_n"],
                config["atr_n"],
                60,
            ) + 5
            if len(closes) < required_lookback:
                roe = None
                debt_ratio = None
                company_id = company_map.get(symbol)
                if company_id is not None and company_id in ratio_map:
                    roe_raw, debt_raw = ratio_map[company_id]
                    roe = _to_float(roe_raw)
                    debt_ratio = _to_float(debt_raw)
                low, high, basis = _compute_target_range(
                    [(r[0], r[1], r[2], r[3], r[4]) for r in series],
                    roe,
                    debt_ratio,
                )
                items.append({
                    "ts": trade_date.isoformat() if trade_date else dt_date.today().isoformat(),
                    "ticker": symbol,
                    "name": name_map.get(symbol),
                    "horizon": horizon_key,
                    "signal": "WAIT",
                    "confidence": 0.0,
                    "triggers": ["데이터 부족"],
                    "risk_flags": ["INSUFFICIENT_HISTORY"],
                    "model_version": model_version_default,
                    "target_price_low": low,
                    "target_price_high": high,
                    "target_price_basis": basis,
                })
                continue

            if engine == "simple_ma_v1":
                signal_payload = compute_signal_simple_ma_v1(price_df, horizon_key, config)
                model_version = "simple_ma_v1"
            else:
                signal_payload = compute_signal_simple_ma_v2_gate3(price_df, horizon_key, config, signal_config["weights"])
                model_version = "simple_ma_v2_gate3"
            signal = signal_payload.get("signal", "WAIT")
            confidence = signal_payload.get("confidence", 0.0)
            triggers = signal_payload.get("triggers", [])

            roe = None
            debt_ratio = None
            company_id = company_map.get(symbol)
            if company_id is not None and company_id in ratio_map:
                roe_raw, debt_raw = ratio_map[company_id]
                roe = _to_float(roe_raw)
                debt_ratio = _to_float(debt_raw)
            low, high, basis = _compute_target_range(
                [(r[0], r[1], r[2], r[3], r[4]) for r in series],
                roe,
                debt_ratio,
            )

            items.append({
                "ts": trade_date.isoformat() if trade_date else dt_date.today().isoformat(),
                "ticker": symbol,
                "name": name_map.get(symbol),
                "horizon": horizon_key,
                "signal": signal,
                "confidence": round(confidence, 3),
                "triggers": triggers,
                "risk_flags": [],
                "model_version": model_version,
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
    stmt = stmt.order_by(TimingSignalRow.ts.desc())
    if limit is not None:
        stmt = stmt.limit(limit)
    rows = db.execute(stmt).scalars().all()

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


@router.get("/signals/config")
def get_signal_config(
    _user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    config, mode, defaults = _get_signal_config(db)
    return {"mode": mode, "config": config, "defaults": defaults}


@router.put("/signals/config")
def update_signal_config(
    payload: SignalConfigPayload,
    _user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mode = (payload.mode or "").lower()
    if mode not in ("default", "custom"):
        return {"ok": False, "message": "mode must be default or custom"}

    if mode == "default":
        row = db.execute(select(SignalConfigRow).where(SignalConfigRow.id == 1)).scalar_one_or_none()
        if row:
            db.delete(row)
            db.commit()
        config, _, defaults = _get_signal_config(db)
        return {"ok": True, "mode": "default", "config": config, "defaults": defaults}

    normalized = _normalize_config(payload.config or {})
    row = db.execute(select(SignalConfigRow).where(SignalConfigRow.id == 1)).scalar_one_or_none()
    if row:
        row.engine = normalized["engine"]
        row.horizons = normalized["horizons"]
        row.weights = normalized["weights"]
    else:
        row = SignalConfigRow(
            id=1,
            engine=normalized["engine"],
            horizons=normalized["horizons"],
            weights=normalized["weights"],
        )
        db.add(row)
    db.commit()
    config, _, defaults = _get_signal_config(db)
    return {"ok": True, "mode": "custom", "config": config, "defaults": defaults}
