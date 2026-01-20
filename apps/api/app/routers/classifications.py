from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..auth import get_current_user
from ..db import get_db
from ..orm import ClassificationTaxonomy, ClassificationNode, SecurityClassification

router = APIRouter(tags=["Universe"])


@router.get("/classifications/taxonomies")
def list_taxonomies(_user=Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(select(ClassificationTaxonomy).order_by(ClassificationTaxonomy.taxonomy_id.asc())).scalars().all()
    return {"items": [{"taxonomy_id": r.taxonomy_id, "name": r.name, "kind": r.kind} for r in rows]}


@router.get("/classifications/nodes")
def list_nodes(
    taxonomy_id: str,
    parent_code: str | None = None,
    level: int | None = None,
    q: str | None = None,
    _user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(ClassificationNode).where(ClassificationNode.taxonomy_id == taxonomy_id)
    if parent_code is not None:
        stmt = stmt.where(ClassificationNode.parent_code == parent_code)
    if level is not None:
        stmt = stmt.where(ClassificationNode.level == level)
    if q:
        stmt = stmt.where(ClassificationNode.name.ilike(f"%{q}%"))
    rows = db.execute(stmt.order_by(ClassificationNode.code.asc())).scalars().all()
    return {"items": [
        {
            "taxonomy_id": r.taxonomy_id,
            "code": r.code,
            "name": r.name,
            "level": r.level,
            "parent_code": r.parent_code,
        } for r in rows
    ]}


@router.get("/classifications/securities/{ticker}")
def get_security_classifications(ticker: str, _user=Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(select(SecurityClassification).where(SecurityClassification.ticker == ticker)).scalars().all()
    industry = [r for r in rows if r.taxonomy_id == "KIS_INDUSTRY"]
    themes = [r for r in rows if r.taxonomy_id == "THEME"]
    primary = next((r for r in industry if r.is_primary), None)
    return {
        "ticker": ticker,
        "industry": {
            "taxonomy_id": "KIS_INDUSTRY",
            "primary": {"code": primary.code} if primary else None,
            "path": [{"code": primary.code}] if primary else [],
        },
        "themes": [{"code": t.code, "confidence": t.confidence} for t in themes],
    }
