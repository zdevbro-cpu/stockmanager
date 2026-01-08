from __future__ import annotations

from datetime import date as dt_date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..auth import get_current_user
from ..db import get_db
from ..orm import RecommendationRow

router = APIRouter(tags=["Recommendations"])


@router.get("/recommendations")
def get_recommendations(
    as_of_date: str,
    strategy_id: str,
    strategy_version: str,
    _user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asof = dt_date.fromisoformat(as_of_date)
    rows = db.execute(
        select(RecommendationRow)
        .where(
            RecommendationRow.as_of_date == asof,
            RecommendationRow.strategy_id == strategy_id,
            RecommendationRow.strategy_version == strategy_version,
        )
        .order_by(RecommendationRow.rank.asc())
    ).scalars().all()

    return {"items": [
        {
            "as_of_date": r.as_of_date.isoformat(),
            "strategy_id": r.strategy_id,
            "strategy_version": r.strategy_version,
            "ticker": r.ticker,
            "rank": r.rank,
            "score": r.score,
            "target_weight": r.target_weight,
            "rationale": r.rationale,
        } for r in rows
    ]}
