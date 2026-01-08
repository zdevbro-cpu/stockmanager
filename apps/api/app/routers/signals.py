from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..auth import get_current_user
from ..db import get_db
from ..orm import TimingSignalRow

router = APIRouter(tags=["Signals"])


@router.get("/signals")
def get_signals(
    ticker: str,
    horizon: str | None = None,
    _user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(TimingSignalRow).where(TimingSignalRow.ticker == ticker)
    if horizon:
        stmt = stmt.where(TimingSignalRow.horizon == horizon)
    rows = db.execute(stmt.order_by(TimingSignalRow.ts.desc()).limit(200)).scalars().all()

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
        } for r in rows
    ]}
