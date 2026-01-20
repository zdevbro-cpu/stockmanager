
from sqlalchemy import text
import sys
import os

# Add ingest service path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/ingest")))

from ingest.db import SessionLocal

def check_tickers():
    tickers = ['012200', '043260', '005930'] # Gyeyang (012200), Sungho (043260), Samsung (005930)
    with SessionLocal() as db:
        print(f"Checking data count for: {tickers}")
        stmt = text(f"SELECT ticker, COUNT(*) FROM price_daily WHERE ticker IN {tuple(tickers)} GROUP BY ticker")
        rows = db.execute(stmt).fetchall()
        for r in rows:
            print(f"Ticker: {r[0]}, Count: {r[1]}")

if __name__ == "__main__":
    check_tickers()
