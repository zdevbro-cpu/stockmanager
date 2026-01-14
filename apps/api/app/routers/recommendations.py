from __future__ import annotations

from datetime import date as dt_date
import importlib
import json
import os
import sys
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, text

from ..auth import get_current_user
from ..config import settings
from ..db import get_db
from ..orm import RecommendationRow

ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if ROOT_PATH not in sys.path:
    sys.path.append(ROOT_PATH)
WORKER_PATH = os.path.join(ROOT_PATH, "services", "worker")
if WORKER_PATH not in sys.path:
    sys.path.append(WORKER_PATH)

router = APIRouter(tags=["Recommendations"])


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

class RecommendationTrigger(BaseModel):
    as_of_date: str | None = None
    strategy_id: str = "prod_v1"
    strategy_version: str = "1.0"
    top_n: int = 5
    params_override: dict[str, object] | None = None

class StrategyInfo(BaseModel):
    strategy_id: str
    strategy_version: str
    name: str
    summary: str
    params: dict[str, object]


STRATEGY_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../../docs/strategies.json")
)
RUN_STATUS_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../../artifacts/recommendation_last_run.json")
)


def load_strategies() -> list[StrategyInfo]:
    if os.path.exists(STRATEGY_PATH):
        with open(STRATEGY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [StrategyInfo(**item) for item in data]
    return [
        StrategyInfo(
            strategy_id="prod_v1",
            strategy_version="1.0",
            name="Momentum + Volatility",
            summary=(
                "Ranks by 20d/5d returns and penalizes 20d volatility. "
                "Applies price/liquidity filters and weight caps."
            ),
            params={
                "top_n_default": 5,
                "min_price_krw": 2000,
                "min_avg_turnover_krw_20d": 5e10,
                "max_weight_per_name": 0.20,
                "max_weight_per_sector": 0.45,
                "sector_taxonomy": "KIS_INDUSTRY",
            },
        )
    ]


def save_strategies(strategies: list[StrategyInfo]) -> None:
    payload = [s.model_dump() for s in strategies]
    os.makedirs(os.path.dirname(STRATEGY_PATH), exist_ok=True)
    with open(STRATEGY_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=True, indent=2)


@router.get("/strategies")
def list_strategies():
    return {"items": [s.model_dump() for s in load_strategies()]}


@router.get("/recommendations/run-status")
def get_recommendation_run_status():
    if not os.path.exists(RUN_STATUS_PATH):
        return {"status": "EMPTY"}
    with open(RUN_STATUS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@router.post("/strategies")
def create_strategy(strategy: StrategyInfo, overwrite: bool = False):
    strategies = load_strategies()
    exists = next(
        (s for s in strategies if s.strategy_id == strategy.strategy_id and s.strategy_version == strategy.strategy_version),
        None,
    )
    if exists and not overwrite:
        raise HTTPException(status_code=409, detail="Strategy already exists.")
    if exists:
        strategies = [s for s in strategies if not (s.strategy_id == strategy.strategy_id and s.strategy_version == strategy.strategy_version)]
    strategies.append(strategy)
    save_strategies(strategies)
    return {"status": "ok"}


@router.get("/recommendations")
def get_recommendations(
    as_of_date: str | None = None,
    strategy_id: str | None = None,
    strategy_version: str | None = None,
    # _user=Depends(get_current_user), # Temporarily disabled for dev
    db: Session = Depends(get_db),
):
    asof = dt_date.fromisoformat(as_of_date) if as_of_date else None
    where_clauses = []
    params: dict[str, object] = {}
    if asof:
        where_clauses.append("r.as_of_date = :as_of_date")
        params["as_of_date"] = asof
    if strategy_id:
        where_clauses.append("r.strategy_id = :strategy_id")
        params["strategy_id"] = strategy_id
    if strategy_version:
        where_clauses.append("r.strategy_version = :strategy_version")
        params["strategy_version"] = strategy_version

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    sql = text(f"""
        SELECT r.as_of_date,
               r.strategy_id,
               r.strategy_version,
               r.ticker,
               r.rank,
               r.score,
               r.target_weight,
               r.rationale,
               r.created_at,
               c.name_ko,
               s.company_id
        FROM recommendation r
        LEFT JOIN security s ON s.ticker = r.ticker
        LEFT JOIN company c ON c.company_id = s.company_id
        {where_sql}
        ORDER BY r.rank ASC
        LIMIT 50
    """)

    try:
        rows = db.execute(sql, params).all()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    tickers = [r.ticker for r in rows]
    company_ids = [r.company_id for r in rows if r.company_id is not None]

    price_map: dict[str, list[tuple]] = {}
    if tickers:
        price_rows = db.execute(
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
            {"tickers": tickers, "lookback": 60},
        ).fetchall()
        for row in price_rows:
            price_map.setdefault(row.ticker, []).append(
                (row.trade_date, row.open, row.high, row.low, row.close)
            )

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

    items = []
    try:
        for r in rows:
            roe = None
            debt_ratio = None
            if r.company_id is not None and r.company_id in ratio_map:
                roe_raw, debt_raw = ratio_map[r.company_id]
                roe = _to_float(roe_raw)
                debt_ratio = _to_float(debt_raw)
            low, high, basis = _compute_target_range(price_map.get(r.ticker, []), roe, debt_ratio)
            items.append(
                {
                    "as_of_date": r.as_of_date.isoformat(),
                    "strategy_id": r.strategy_id,
                    "strategy_version": r.strategy_version,
                    "ticker": r.ticker,
                    "name_ko": r.name_ko,
                    "rank": r.rank,
                    "score": r.score,
                    "target_weight": r.target_weight,
                    "rationale": r.rationale,
                    "target_price_low": low,
                    "target_price_high": high,
                    "target_price_basis": basis,
                }
            )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Target range compute failed: {exc}")

    return {"items": items}


@router.post("/recommendations/trigger")
def trigger_recommendations(
    payload: RecommendationTrigger,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if settings.DATABASE_URL:
        os.environ.setdefault("DATABASE_URL", settings.DATABASE_URL)
    try:
        module = importlib.import_module("worker.jobs.daily_close")
        importlib.reload(module)
        StrategyParams = module.StrategyParams
        run_daily_close = module.run
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Worker import failed: {exc}")

    if not os.getenv("DATABASE_URL"):
        raise HTTPException(status_code=500, detail="DATABASE_URL is not set.")

    as_of = dt_date.today() if payload.as_of_date is None else dt_date.fromisoformat(payload.as_of_date)
    strategies = load_strategies()
    selected = next(
        (s for s in strategies if s.strategy_id == payload.strategy_id and s.strategy_version == payload.strategy_version),
        None,
    )
    if selected:
        exists = db.execute(
            text("SELECT 1 FROM strategy_def WHERE strategy_id = :strategy_id AND version = :version"),
            {"strategy_id": selected.strategy_id, "version": selected.strategy_version},
        ).scalar()
        if not exists:
            db.execute(
                text(
                    "INSERT INTO strategy_def (strategy_id, version, name, json_def) "
                    "VALUES (:strategy_id, :version, :name, :json_def)"
                ),
                {
                    "strategy_id": selected.strategy_id,
                    "version": selected.strategy_version,
                    "name": selected.name,
                    "json_def": json.dumps(selected.model_dump(), ensure_ascii=True),
                },
            )
            db.commit()
    params_kwargs: dict[str, object] = {
        "strategy_id": payload.strategy_id,
        "strategy_version": payload.strategy_version,
        "top_n": payload.top_n,
    }
    if selected:
        params_kwargs.update({
            "top_n": int(selected.params.get("top_n_default", payload.top_n)),
            "min_price_krw": float(selected.params.get("min_price_krw", 2000)),
            "min_avg_turnover_krw_20d": float(selected.params.get("min_avg_turnover_krw_20d", 5e10)),
            "max_weight_per_name": float(selected.params.get("max_weight_per_name", 0.20)),
            "max_weight_per_sector": float(selected.params.get("max_weight_per_sector", 0.45)),
            "sector_taxonomy": str(selected.params.get("sector_taxonomy", "KIS_INDUSTRY")),
        })
    if payload.params_override:
        params_kwargs.update(payload.params_override)
    params = StrategyParams(**params_kwargs)
    def run_with_status():
        try:
            run_daily_close(as_of, params)
        except Exception as exc:
            os.makedirs(os.path.dirname(RUN_STATUS_PATH), exist_ok=True)
            payload_data = {}
            if os.path.exists(RUN_STATUS_PATH):
                try:
                    with open(RUN_STATUS_PATH, "r", encoding="utf-8") as f:
                        payload_data = json.load(f)
                except Exception:
                    payload_data = {}
            payload_data.update({
                "status": "FAILED",
                "reason": str(exc),
                "as_of_date": as_of.isoformat(),
                "strategy_id": payload.strategy_id,
                "strategy_version": payload.strategy_version,
            })
            with open(RUN_STATUS_PATH, "w", encoding="utf-8") as f:
                json.dump(payload_data, f, ensure_ascii=True, indent=2)
            raise

    background_tasks.add_task(run_with_status)
    return {
        "status": "accepted",
        "as_of_date": as_of.isoformat(),
        "strategy_id": payload.strategy_id,
        "strategy_version": payload.strategy_version,
        "top_n": payload.top_n,
    }
