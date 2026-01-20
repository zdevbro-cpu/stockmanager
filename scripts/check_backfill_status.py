
import sys
import os
from sqlalchemy import text


# Add path to find 'ingest' package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/ingest")))

try:
    from ingest.db import SessionLocal
except ImportError as e:
    print(f"Error importing ingest.db: {e}")
    sys.exit(1)

def check_progress():
    with SessionLocal() as db:
        # 1. Total tickers to process
        total_tickers = db.execute(text("SELECT COUNT(*) FROM security")).scalar()
        print(f"Total Tickers in DB: {total_tickers}")

        # 2. Tickers with at least some price data
        processed_tickers = db.execute(text("SELECT COUNT(DISTINCT ticker) FROM price_daily")).scalar()
        print(f"Tickers with ANY price data: {processed_tickers}")

        # 3. Tickers with recent data (e.g., in last 5 days) to see active backfill
        recent_active = db.execute(text("""
            SELECT COUNT(DISTINCT ticker) 
            FROM price_daily 
            WHERE created_at > NOW() - INTERVAL '1 day'
        """)).scalar()
        print(f"Tickers updated in last 24 hours: {recent_active}")

        print("\n--- Specific Ticker Check ---")
        print(f"{'Ticker':<10} {'Row Count':<10} {'Start Date':<15} {'End Date':<15}")
        print("-" * 50)
        
        # Check specific tickers that caused confusion
        target_tickers = ('000640', '001420')
        stmt = text(f"""
            SELECT ticker, COUNT(*) as cnt, MIN(trade_date) as start_date, MAX(trade_date) as end_date
            FROM price_daily 
            WHERE ticker IN {target_tickers}
            GROUP BY ticker
        """)
        rows = db.execute(stmt).fetchall()
        
        for r in rows:
            print(f"{r[0]:<10} {r[1]:<10} {str(r[2]):<15} {str(r[3]):<15}")

        print("\n--- Overall Statistics ---")
        stats = db.execute(text("""
            SELECT MIN(cnt), MAX(cnt), AVG(cnt)::int 
            FROM (SELECT COUNT(*) as cnt FROM price_daily GROUP BY ticker) sub
        """)).fetchone()
        print(f"Min Rows: {stats[0]}")
        print(f"Max Rows: {stats[1]}")
        print(f"Avg Rows: {stats[2]}")

if __name__ == "__main__":
    check_progress()
