from fastapi import APIRouter, Depends, Response, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db import get_db
from ..schemas import WatchlistCreate, WatchlistItemAdd, WatchlistItemNoteUpdate

router = APIRouter(tags=["Watchlists"])


def _ensure_watchlist_tables(db: Session):
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS watchlist (
            watchlist_id SERIAL PRIMARY KEY,
            owner_user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """))
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS watchlist_item (
            watchlist_id INTEGER NOT NULL REFERENCES watchlist(watchlist_id) ON DELETE CASCADE,
            ticker TEXT NOT NULL,
            added_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            name TEXT,
            note TEXT,
            PRIMARY KEY (watchlist_id, ticker)
        )
    """))
    db.execute(text("ALTER TABLE watchlist_item ADD COLUMN IF NOT EXISTS name TEXT"))
    db.execute(text("ALTER TABLE watchlist_item ADD COLUMN IF NOT EXISTS note TEXT"))
    db.execute(text("ALTER TABLE watchlist ADD COLUMN IF NOT EXISTS owner_user_id TEXT"))
    db.commit()


def _get_user_id(user: dict) -> str:
    return user.get("uid") or "local-dev"


def _ensure_watchlist_owned(db: Session, watchlist_id: int, user_id: str):
    row = db.execute(
        text("SELECT 1 FROM watchlist WHERE watchlist_id = :wid AND owner_user_id = :uid"),
        {"wid": watchlist_id, "uid": user_id}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Watchlist not found")


@router.post("/watchlists", status_code=201)
def create_watchlist(req: WatchlistCreate, _user=Depends(get_current_user), _db: Session = Depends(get_db)):
    _ensure_watchlist_tables(_db)
    user_id = _get_user_id(_user)
    row = _db.execute(
        text("""
            INSERT INTO watchlist (owner_user_id, name)
            VALUES (:uid, :name)
            RETURNING watchlist_id
        """),
        {"uid": user_id, "name": req.name}
    ).fetchone()
    _db.commit()
    return {"watchlist_id": row[0], "name": req.name}


@router.get("/watchlists")
def list_watchlists(_user=Depends(get_current_user), _db: Session = Depends(get_db)):
    _ensure_watchlist_tables(_db)
    user_id = _get_user_id(_user)
    rows = _db.execute(
        text("""
            SELECT watchlist_id, name
            FROM watchlist
            WHERE owner_user_id = :uid
            ORDER BY watchlist_id ASC
        """),
        {"uid": user_id}
    ).fetchall()
    if not rows:
        row = _db.execute(
            text("""
                INSERT INTO watchlist (owner_user_id, name)
                VALUES (:uid, :name)
                RETURNING watchlist_id, name
            """),
            {"uid": user_id, "name": "관심종목"}
        ).fetchone()
        _db.commit()
        rows = [row]
    return {"items": [{"watchlist_id": r[0], "name": r[1]} for r in rows]}


@router.post("/watchlists/{watchlist_id}/items", status_code=204)
def add_item(watchlist_id: int, req: WatchlistItemAdd, _user=Depends(get_current_user), _db: Session = Depends(get_db)):
    _ensure_watchlist_tables(_db)
    user_id = _get_user_id(_user)
    _ensure_watchlist_owned(_db, watchlist_id, user_id)
    _db.execute(
        text("""
            INSERT INTO watchlist_item (watchlist_id, ticker, name, note)
            VALUES (:wid, :ticker, :name, '')
            ON CONFLICT (watchlist_id, ticker) DO NOTHING
        """),
        {"wid": watchlist_id, "ticker": req.ticker, "name": req.name}
    )
    _db.commit()
    return Response(status_code=204)


@router.get("/watchlists/{watchlist_id}/items")
def list_items(watchlist_id: int, _user=Depends(get_current_user), _db: Session = Depends(get_db)):
    _ensure_watchlist_tables(_db)
    user_id = _get_user_id(_user)
    _ensure_watchlist_owned(_db, watchlist_id, user_id)
    _db.execute(
        text("""
            UPDATE watchlist_item wi
            SET name = c.name_ko
            FROM company c
            WHERE wi.watchlist_id = :wid
              AND (wi.name IS NULL OR wi.name = '' OR TRIM(wi.name) = TRIM(wi.ticker))
              AND LPAD(TRIM(wi.ticker), 6, '0') = LPAD(TRIM(c.stock_code), 6, '0')
        """),
        {"wid": watchlist_id}
    )
    _db.commit()
    rows = _db.execute(
        text("""
            SELECT
                wi.ticker,
                COALESCE(NULLIF(NULLIF(wi.name, ''), wi.ticker), c.name_ko, '') AS name,
                wi.note,
                wi.added_at
            FROM watchlist_item wi
            LEFT JOIN company c
              ON LPAD(TRIM(c.stock_code), 6, '0') = LPAD(TRIM(wi.ticker), 6, '0')
            WHERE wi.watchlist_id = :wid
            ORDER BY wi.added_at DESC
        """),
        {"wid": watchlist_id}
    ).fetchall()
    return {
        "items": [
            {
                "ticker": r[0],
                "name": r[1] or "",
                "note": r[2] or "",
                "added_at": r[3].isoformat() if r[3] else None
            }
            for r in rows
        ]
    }


@router.delete("/watchlists/{watchlist_id}/items/{ticker}", status_code=204)
def delete_item(watchlist_id: int, ticker: str, _user=Depends(get_current_user), _db: Session = Depends(get_db)):
    _ensure_watchlist_tables(_db)
    user_id = _get_user_id(_user)
    _ensure_watchlist_owned(_db, watchlist_id, user_id)
    _db.execute(
        text("DELETE FROM watchlist_item WHERE watchlist_id = :wid AND ticker = :ticker"),
        {"wid": watchlist_id, "ticker": ticker}
    )
    _db.commit()
    return Response(status_code=204)


@router.put("/watchlists/{watchlist_id}/items/{ticker}", status_code=204)
def update_item_note(
    watchlist_id: int,
    ticker: str,
    req: WatchlistItemNoteUpdate,
    _user=Depends(get_current_user),
    _db: Session = Depends(get_db),
):
    _ensure_watchlist_tables(_db)
    user_id = _get_user_id(_user)
    _ensure_watchlist_owned(_db, watchlist_id, user_id)
    _db.execute(
        text("""
            UPDATE watchlist_item
            SET note = :note
            WHERE watchlist_id = :wid AND ticker = :ticker
        """),
        {"note": req.note, "wid": watchlist_id, "ticker": ticker}
    )
    _db.commit()
    return Response(status_code=204)


@router.post("/watchlists/{watchlist_id}/simulate", status_code=202)
def simulate_watchlist(watchlist_id: int, payload: dict, _user=Depends(get_current_user), _db: Session = Depends(get_db)):
    return {"sim_id": 1, "status": "PENDING"}
