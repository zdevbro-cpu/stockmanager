import pandas as pd
import numpy as np

HORIZON_RULES = {
    "1D": dict(short=5, long=20, mom=5, slope_lb=10,
               vol_n=20, vol_mult=1.20, atr_n=14,
               vol_q_window=252, vol_q=0.90, confirm=2),
    "3D": dict(short=10, long=30, mom=10, slope_lb=15,
               vol_n=20, vol_mult=1.15, atr_n=14,
               vol_q_window=252, vol_q=0.85, confirm=2),
    "1W": dict(short=20, long=60, mom=20, slope_lb=20,
               vol_n=20, vol_mult=1.10, atr_n=14,
               vol_q_window=252, vol_q=0.80, confirm=1),
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
    # pandas rolling quantile
    return s.rolling(window, min_periods=window).quantile(q)

def _apply_confirm_bars(cond: pd.Series, confirm: int) -> pd.Series:
    """
    cond가 True를 confirm일 연속 만족할 때 True.
    예) confirm=2 -> 오늘/어제 모두 True인 시점부터 True
    """
    if confirm <= 1:
        return cond.fillna(False)
    # 연속 True 체크: 최근 confirm개가 모두 True
    # rolling sum == confirm 이면 연속 True
    c = cond.fillna(False).astype(int)
    return c.rolling(confirm, min_periods=confirm).sum().eq(confirm)

def compute_signal_simple_ma_v2_gate3(price_daily: pd.DataFrame, horizon: str) -> dict:
    """
    반환 형식(dict)은 프로젝트 기존 signals.py의 포맷에 맞춰 조정하십시오.
    여기서는 예시로 {signal, confidence, debug} 형태를 반환합니다.
    """
    r = HORIZON_RULES[horizon]
    df = price_daily.copy().sort_values("date")

    # 필수 컬럼 체크
    for col in ("open", "high", "low", "close", "volume"):
        if col not in df.columns:
            return {"signal": "WAIT", "confidence": 0.0, "debug": {"reason": f"missing:{col}"}}

    close = df["close"].astype(float)
    vol = df["volume"].astype(float)

    ma_s = _sma(close, r["short"])
    ma_l = _sma(close, r["long"])

    # momentum: 기존 구현이 다르면 이 부분을 "기존 방식"으로 교체
    mom = close / close.shift(r["mom"]) - 1.0

    slope = (ma_l - ma_l.shift(r["slope_lb"])) / float(r["slope_lb"])

    vol_ma = _sma(vol, r["vol_n"])
    vol_ratio = vol / vol_ma.replace({0: np.nan})

    atr = _atr(df, r["atr_n"])
    atr_pct = atr / close.replace({0: np.nan})

    atr_pct_q = _rolling_quantile(atr_pct, r["vol_q_window"], r["vol_q"])

    # 초기 구간 처리(quantile이 NaN이면 임시 기준 사용)
    # 1) 1D/3D는 안전하게 WAIT 유도: 임시 기준을 SMA(ATR_pct, 60)
    atr_pct_fallback = _sma(atr_pct, 60)
    atr_gate = (atr_pct <= atr_pct_q)
    atr_gate = atr_gate.where(~atr_pct_q.isna(), atr_pct <= atr_pct_fallback)
    atr_gate = atr_gate.fillna(False)

    # Base condition
    buy_base = (ma_s > ma_l) & (mom > 0)
    sell_base = (ma_s < ma_l) & (mom < 0)

    # Trend Gate
    buy_trend = (close > ma_l) & (slope > 0)
    sell_trend = (close < ma_l) & (slope < 0)

    # Volume Gate (event day strict, otherwise relaxed to >=1.0)
    buy_event = (close > ma_s) & (close.shift(1) <= ma_s.shift(1))
    sell_event = (close < ma_s) & (close.shift(1) >= ma_s.shift(1))

    vol_gate_relaxed = (vol_ratio >= 1.0)
    buy_vol_gate = np.where(buy_event.fillna(False), (vol_ratio >= r["vol_mult"]), vol_gate_relaxed)
    sell_vol_gate = np.where(sell_event.fillna(False), (vol_ratio >= r["vol_mult"]), vol_gate_relaxed)

    buy_vol_gate = pd.Series(buy_vol_gate, index=df.index).fillna(False)
    sell_vol_gate = pd.Series(sell_vol_gate, index=df.index).fillna(False)

    # Final condition + confirm
    buy_final_raw = buy_base & buy_trend & atr_gate & buy_vol_gate
    sell_final_raw = sell_base & sell_trend & atr_gate & sell_vol_gate

    buy_final = _apply_confirm_bars(buy_final_raw, r["confirm"])
    sell_final = _apply_confirm_bars(sell_final_raw, r["confirm"])

    # 오늘 신호
    last = df.index[-1]
    if bool(buy_final.loc[last]) and not bool(sell_final.loc[last]):
        signal = "BUY"
    elif bool(sell_final.loc[last]) and not bool(buy_final.loc[last]):
        signal = "SELL"
    else:
        signal = "WAIT"

    # confidence (0~1) - 기본: MA gap + slope + volume, volatility penalty
    ma_gap = (ma_s - ma_l).abs() / ma_l.replace({0: np.nan})
    trend_strength = (slope.abs() / ma_l.replace({0: np.nan}))
    # volume_strength는 이벤트일 때만 반영
    vol_strength = ((vol_ratio - 1.0) / max(r["vol_mult"] - 1.0, 1e-9)).clip(0, 1)
    is_event = (buy_event | sell_event).fillna(False)
    vol_strength = vol_strength.where(is_event, 0.0).fillna(0.0)

    vol_penalty = ((atr_pct - atr_pct_q) / atr_pct_q.replace({0: np.nan})).clip(0, 1)
    vol_penalty = vol_penalty.fillna(0.0)

    conf = (0.45 * ma_gap.fillna(0.0) + 0.35 * trend_strength.fillna(0.0) + 0.20 * vol_strength - 0.40 * vol_penalty)
    conf = conf.clip(0, 1).fillna(0.0)

    return {
        "signal": signal,
        "confidence": float(conf.loc[last]),
        "debug": {
            "horizon": horizon,
            "buy_base": bool(buy_base.loc[last]) if not pd.isna(buy_base.loc[last]) else False,
            "sell_base": bool(sell_base.loc[last]) if not pd.isna(sell_base.loc[last]) else False,
            "buy_trend": bool(buy_trend.loc[last]) if not pd.isna(buy_trend.loc[last]) else False,
            "sell_trend": bool(sell_trend.loc[last]) if not pd.isna(sell_trend.loc[last]) else False,
            "atr_gate": bool(atr_gate.loc[last]) if not pd.isna(atr_gate.loc[last]) else False,
            "vol_ratio": float(vol_ratio.loc[last]) if not pd.isna(vol_ratio.loc[last]) else None,
        }
    }
