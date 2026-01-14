from datetime import date as dt_date
import os
import sys
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers.health import router as health_router
from .routers.universe import router as universe_router
from .routers.classifications import router as classifications_router
from .routers.recommendations import router as recommendations_router
from .routers.signals import router as signals_router
from .routers.watchlists import router as watchlists_router
from .routers.reports import router as reports_router


app = FastAPI(title="StockReco API", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(universe_router)
app.include_router(classifications_router)
app.include_router(recommendations_router)
app.include_router(signals_router)
app.include_router(watchlists_router)
app.include_router(reports_router)
from .routers.ingest import router as ingest_router
app.include_router(ingest_router)
from .routers.market import router as market_router
app.include_router(market_router)
from .routers.financials.main import router as financials_router
app.include_router(financials_router)

from .routers.documents import router as documents_router
app.include_router(documents_router)

# Auto-ingest prices on server startup (local PC running)
INGEST_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../services/ingest"))
if INGEST_PATH not in sys.path:
    sys.path.append(INGEST_PATH)

def _auto_ingest_prices():
    try:
        from ingest.db import SessionLocal
        from sqlalchemy import text
        from ingest.kis_loader import update_kis_prices_task

        today = dt_date.today()
        with SessionLocal() as db:
            latest = db.execute(text("SELECT MAX(trade_date) FROM price_daily")).scalar()

        if latest is None or latest < today:
            print(f"Auto-ingest: price_daily 최신일 {latest} -> {today} 갱신 시작")
            update_kis_prices_task(limit=None)
        else:
            print(f"Auto-ingest: price_daily 최신일 {latest} (스킵)")
    except Exception as exc:
        print(f"Auto-ingest failed: {exc}")

@app.on_event("startup")
def startup_tasks():
    thread = threading.Thread(target=_auto_ingest_prices, daemon=True)
    thread.start()

# Server Reload Trigger: 2026-01-10 14:18
