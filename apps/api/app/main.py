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
    allow_origins=["*"],  # TODO: production에서 도메인 제한
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
