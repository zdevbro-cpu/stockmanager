from __future__ import annotations

import os
import json
from dataclasses import dataclass
from datetime import date, datetime, timezone

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import sessionmaker

from apps.api.app.orm import (
    Security,
    PriceDaily,
    RecommendationRow,
    TimingSignalRow,
    SecurityClassification,
    ClassificationNode,
)

DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    raise RuntimeError("DATABASE_URL env var is required")

ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
RUN_STATUS_PATH = os.path.join(ROOT_PATH, "artifacts", "recommendation_last_run.json")


@dataclass
class StrategyParams:
    strategy_id: str = "prod_v1"
    strategy_version: str = "1.0"
    top_n: int = 5
    max_weight_per_name: float = 0.20
    max_weight_per_sector: float = 0.45
    sector_taxonomy: str = "KIS_INDUSTRY"
    min_avg_turnover_krw_20d: float = 5e10
    min_price_krw: float = 2000.0


def zscore(s: pd.Series) -> pd.Series:
    std = float(s.std(ddof=0))
    if std == 0.0 or np.isnan(std):
        return s * 0.0
    return (s - s.mean()) / (std + 1e-12)


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["ticker", "trade_date"]).copy()
    df["ret_1"] = df.groupby("ticker")["close"].pct_change(1)
    df["ret_5"] = df.groupby("ticker")["close"].pct_change(5)
    df["ret_20"] = df.groupby("ticker")["close"].pct_change(20)
    df["vol_20"] = (
        df.groupby("ticker")["close"]
        .pct_change()
        .groupby(df["ticker"])
        .rolling(20, min_periods=2)
        .std()
        .reset_index(level=0, drop=True)
    )
    df["turnover_20d"] = (
        df.groupby("ticker")["turnover_krw"]
        .rolling(20, min_periods=1)
        .mean()
        .reset_index(level=0, drop=True)
    )
    return df


def run(as_of: date, params: StrategyParams) -> None:
    engine = create_engine(DB_URL, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    session = Session()
    run_stats = {
        "as_of_date": as_of.isoformat(),
        "strategy_id": params.strategy_id,
        "strategy_version": params.strategy_version,
        "universe_total": 0,
        "after_min_price": 0,
        "after_min_turnover": 0,
        "after_indicators": 0,
        "final_top_n": 0,
    }

    try:
        secs = session.execute(select(Security.ticker)).scalars().all()
        tickers = [s for s in secs if s]
        run_stats["universe_total"] = len(tickers)

        prices = session.execute(
            select(PriceDaily).where(PriceDaily.ticker.in_(tickers), PriceDaily.trade_date <= as_of)
        ).scalars().all()
        if not prices:
            raise RuntimeError("price_daily is empty (seed first)")

        df = pd.DataFrame([{"ticker": p.ticker, "trade_date": p.trade_date, "close": p.close, "turnover_krw": p.turnover_krw or np.nan} for p in prices])
        df = compute_features(df)
        latest_dt = df["trade_date"].max()
        latest = df[df["trade_date"] == latest_dt].copy()
        latest["ret_5"] = latest["ret_5"].fillna(latest["ret_1"])
        latest["ret_20"] = latest["ret_20"].fillna(latest["ret_1"])
        latest["vol_20"] = latest["vol_20"].fillna(0.0)

        base_latest = latest.copy()

        def apply_filters(df: pd.DataFrame, min_price: float, min_turnover: float) -> pd.DataFrame:
            filtered = df[df["close"] >= min_price]
            run_stats["after_min_price"] = int(len(filtered))
            filtered = filtered[filtered["turnover_20d"] >= min_turnover]
            run_stats["after_min_turnover"] = int(len(filtered))
            filtered = filtered.dropna(subset=["ret_5", "ret_20", "vol_20"])
            run_stats["after_indicators"] = int(len(filtered))
            return filtered

        # universe filters (primary)
        latest = apply_filters(base_latest, params.min_price_krw, params.min_avg_turnover_krw_20d)

        # fallback: relax filters once if empty
        run_stats["fallback_used"] = False
        if latest.empty:
            relaxed_min_price = max(0.0, params.min_price_krw * 0.5)
            relaxed_min_turnover = max(0.0, params.min_avg_turnover_krw_20d * 0.2)
            run_stats["fallback_used"] = True
            run_stats["fallback_min_price_krw"] = relaxed_min_price
            run_stats["fallback_min_avg_turnover_krw_20d"] = relaxed_min_turnover
            latest = apply_filters(base_latest, relaxed_min_price, relaxed_min_turnover)

        if latest.empty:
            raise RuntimeError("universe became empty after filters")

        latest["z_ret20"] = zscore(latest["ret_20"])
        latest["z_ret5"] = zscore(latest["ret_5"])
        latest["z_vol20"] = zscore(latest["vol_20"].fillna(latest["vol_20"].median()))
        latest["score"] = 0.6 * latest["z_ret20"] + 0.4 * latest["z_ret5"] - 0.2 * latest["z_vol20"]

        top = latest.sort_values("score", ascending=False).head(params.top_n).copy()
        run_stats["final_top_n"] = int(len(top))

        ind_rows = session.execute(
            select(SecurityClassification).where(
                SecurityClassification.ticker.in_(top["ticker"].tolist()),
                SecurityClassification.taxonomy_id == params.sector_taxonomy,
            )
        ).scalars().all()
        prim_ind = {r.ticker: r.code for r in ind_rows if r.is_primary}

        nodes = session.execute(select(ClassificationNode).where(ClassificationNode.taxonomy_id == params.sector_taxonomy)).scalars().all()
        ind_name = {n.code: n.name for n in nodes}

        inv_vol = 1 / top["vol_20"].clip(lower=1e-6)
        w0 = inv_vol / inv_vol.sum()
        top["weight"] = w0.clip(upper=params.max_weight_per_name)
        top["weight"] = top["weight"] / top["weight"].sum()

        # sector cap (greedy)
        sector_weight = {}
        weights = []
        for _, r in top.iterrows():
            sec = prim_ind.get(r["ticker"], "UNKNOWN")
            cur = sector_weight.get(sec, 0.0)
            alloc = float(r["weight"])
            if cur + alloc > params.max_weight_per_sector:
                alloc = max(0.0, params.max_weight_per_sector - cur)
            sector_weight[sec] = cur + alloc
            weights.append(alloc)
        top["weight"] = weights
        if float(top["weight"].sum()) > 0:
            top["weight"] = top["weight"] / top["weight"].sum()

        # idempotent delete
        session.execute(
            delete(RecommendationRow).where(
                RecommendationRow.as_of_date == as_of,
                RecommendationRow.strategy_id == params.strategy_id,
                RecommendationRow.strategy_version == params.strategy_version,
            )
        )

        # write recommendations
        top = top.sort_values("score", ascending=False).reset_index(drop=True)
        for idx, r in top.iterrows():
            tkr = r["ticker"]
            ind_code = prim_ind.get(tkr)
            rationale = {
                "as_of_date": as_of.isoformat(),
                "classifications": {
                    "industry": {
                        "taxonomy": params.sector_taxonomy,
                        "primary": {"code": ind_code, "name": ind_name.get(ind_code), "level": 1} if ind_code else None,
                        "path": [{"code": ind_code, "name": ind_name.get(ind_code), "level": 1}] if ind_code else [],
                    },
                    "themes": [],
                },
                "filters": {
                    "passed": True,
                    "rules": [
                        {"name": "min_price_krw", "passed": True, "value": float(r["close"]), "threshold": params.min_price_krw},
                        {"name": "min_avg_turnover_krw_20d", "passed": True, "value": float(r["turnover_20d"]), "threshold": params.min_avg_turnover_krw_20d},
                    ],
                },
                "factors": {
                    "total_score": float(r["score"]),
                    "contrib": [
                        {"factor": "ret_20", "value": float(r["ret_20"]), "weight": 0.6, "contribution": float(0.6 * r["z_ret20"])},
                        {"factor": "ret_5", "value": float(r["ret_5"]), "weight": 0.4, "contribution": float(0.4 * r["z_ret5"])},
                        {"factor": "vol_20", "value": float(r["vol_20"]), "weight": -0.2, "contribution": float(-0.2 * r["z_vol20"])},
                    ],
                },
                "portfolio": {
                    "target_weight": float(r["weight"]),
                    "constraints": [
                        {"name": "max_weight_per_name", "passed": True, "limit": params.max_weight_per_name},
                        {"name": "max_weight_per_sector", "passed": True, "limit": params.max_weight_per_sector, "sector_taxonomy": params.sector_taxonomy, "sector_level": 1},
                    ],
                },
                "event_risk": {"window_days": 2, "policy": "block_entry", "flags": []},
            }

            session.add(
                RecommendationRow(
                    as_of_date=as_of,
                    strategy_id=params.strategy_id,
                    strategy_version=params.strategy_version,
                    ticker=tkr,
                    rank=int(idx + 1),
                    score=float(r["score"]),
                    target_weight=float(r["weight"]),
                    rationale=rationale,
                )
            )

        # signals: MA5 vs MA20
        df2 = df.sort_values(["ticker", "trade_date"]).copy()
        df2["ma_5"] = df2.groupby("ticker")["close"].rolling(5).mean().reset_index(level=0, drop=True)
        df2["ma_20"] = df2.groupby("ticker")["close"].rolling(20).mean().reset_index(level=0, drop=True)
        latest2 = df2[df2["trade_date"] == latest_dt].copy()

        now_ts = datetime(as_of.year, as_of.month, as_of.day, 15, 30, tzinfo=timezone.utc)
        top_tickers = set(top["ticker"].tolist())

        for _, r in latest2[latest2["ticker"].isin(top_tickers)].iterrows():
            if np.isnan(r["ma_5"]) or np.isnan(r["ma_20"]):
                continue
            if r["ma_5"] > r["ma_20"]:
                signal, conf, triggers = "BUY", 0.65, ["ma5_gt_ma20"]
            else:
                signal, conf, triggers = "WAIT", 0.55, ["ma5_le_ma20"]
            session.add(
                TimingSignalRow(
                    ts=now_ts,
                    ticker=r["ticker"],
                    horizon="1d",
                    signal=signal,
                    confidence=conf,
                    triggers=triggers,
                    risk_flags=[],
                    model_version="rules_v1",
                )
            )

        session.commit()
        os.makedirs(os.path.dirname(RUN_STATUS_PATH), exist_ok=True)
        with open(RUN_STATUS_PATH, "w", encoding="utf-8") as f:
            json.dump({**run_stats, "status": "SUCCESS"}, f, ensure_ascii=True, indent=2)
    except Exception as exc:
        session.rollback()
        os.makedirs(os.path.dirname(RUN_STATUS_PATH), exist_ok=True)
        with open(RUN_STATUS_PATH, "w", encoding="utf-8") as f:
            json.dump({**run_stats, "status": "FAILED", "reason": str(exc)}, f, ensure_ascii=True, indent=2)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    run(date.today(), StrategyParams())
