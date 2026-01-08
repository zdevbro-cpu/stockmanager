from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db import get_db
from ..schemas import WatchlistCreate, WatchlistItemAdd

router = APIRouter(tags=["Watchlists"])


@router.post("/watchlists", status_code=201)
def create_watchlist(req: WatchlistCreate, _user=Depends(get_current_user), _db: Session = Depends(get_db)):
    # TODO: DB insert
    return {"watchlist_id": 1, "name": req.name}


@router.get("/watchlists")
def list_watchlists(_user=Depends(get_current_user), _db: Session = Depends(get_db)):
    # TODO: DB select
    return {"items": [{"watchlist_id": 1, "name": "관심종목"}]}


@router.post("/watchlists/{watchlist_id}/items", status_code=204)
def add_item(watchlist_id: int, req: WatchlistItemAdd, _user=Depends(get_current_user), _db: Session = Depends(get_db)):
    # TODO: DB insert
    return Response(status_code=204)


@router.get("/watchlists/{watchlist_id}/items")
def list_items(watchlist_id: int, _user=Depends(get_current_user), _db: Session = Depends(get_db)):
    # TODO: DB select
    return {"items": [{"ticker": "005930", "added_at": "2026-01-08T10:00:00+09:00"}]}


@router.post("/watchlists/{watchlist_id}/simulate", status_code=202)
def simulate_watchlist(watchlist_id: int, payload: dict, _user=Depends(get_current_user), _db: Session = Depends(get_db)):
    # TODO: 워커에 시뮬레이션 작업 enqueue
    return {"sim_id": 1, "status": "PENDING"}
