from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from app.routers.signals import compute_signal_simple_ma_v1, compute_signal_simple_ma_v2_gate3


def _make_price_df(closes, volumes=None, start_date="2024-01-01"):
    if volumes is None:
        volumes = [1000] * len(closes)
    dates = [datetime.fromisoformat(start_date) + timedelta(days=i) for i in range(len(closes))]
    closes = np.array(closes, dtype=float)
    opens = closes * 0.999
    highs = closes * 1.01
    lows = closes * 0.99
    data = {
        "date": dates,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": np.array(volumes, dtype=float),
    }
    return pd.DataFrame(data)


def _walk_signals(df, func, horizon="1D"):
    results = []
    for i in range(30, len(df)):
        subset = df.iloc[: i + 1].copy()
        results.append(func(subset, horizon)["signal"])
    return results


def test_whipsaw_wait_rate_increases_for_v2():
    closes = 100 + np.sin(np.linspace(0, 20 * np.pi, 160))
    df = _make_price_df(closes)
    v1_signals = _walk_signals(df, compute_signal_simple_ma_v1)
    v2_signals = _walk_signals(df, compute_signal_simple_ma_v2_gate3)
    v1_wait = sum(1 for s in v1_signals if s == "WAIT")
    v2_wait = sum(1 for s in v2_signals if s == "WAIT")
    assert v2_wait >= v1_wait


def test_uptrend_volume_buy_signal():
    base = np.full(220, 100.0)
    ramp = np.linspace(101, 140, 40)
    closes = np.concatenate([base, ramp])
    volumes = np.concatenate([np.full(220, 1000.0), np.full(40, 1800.0)])
    df = _make_price_df(closes, volumes)
    result = compute_signal_simple_ma_v2_gate3(df, "1D")
    assert result["signal"] == "BUY"


def test_downtrend_volume_sell_signal():
    base = np.full(200, 140.0)
    t = np.linspace(0, 1, 60)
    drop = 139 - (19 * (t ** 0.5))
    closes = np.concatenate([base, drop])
    volumes = np.concatenate([np.full(200, 1000.0), np.full(60, 2000.0)])
    df = _make_price_df(closes, volumes)
    df["high"] = df["close"]
    df["low"] = df["close"]
    result = compute_signal_simple_ma_v2_gate3(df, "1D")
    assert result["signal"] == "SELL"


def test_high_volatility_blocks_entry():
    base = np.linspace(100, 160, 240)
    spike = np.linspace(161, 170, 20)
    closes = np.concatenate([base, spike])
    volumes = np.linspace(1000, 1500, len(closes))
    df = _make_price_df(closes, volumes)
    df.loc[df.index[-5:], "high"] = df.loc[df.index[-5:], "close"] * 1.4
    df.loc[df.index[-5:], "low"] = df.loc[df.index[-5:], "close"] * 0.6
    result = compute_signal_simple_ma_v2_gate3(df, "1D")
    assert result["signal"] == "WAIT"


def test_confirm_bars_required():
    base = np.full(200, 100.0)
    ramp = np.linspace(101, 120, 30)
    closes = np.concatenate([base, ramp, [121, 122]])
    volumes = np.concatenate([np.full(200, 1000.0), np.full(30, 1200.0), [500.0, 2000.0]])
    df = _make_price_df(closes, volumes)
    result = compute_signal_simple_ma_v2_gate3(df, "1D")
    assert result["signal"] == "WAIT"

    closes = np.concatenate([base, ramp, [121, 122]])
    volumes = np.concatenate([np.full(200, 1000.0), np.full(30, 1200.0), [2000.0, 2000.0]])
    df = _make_price_df(closes, volumes)
    result = compute_signal_simple_ma_v2_gate3(df, "1D")
    assert result["signal"] == "BUY"
