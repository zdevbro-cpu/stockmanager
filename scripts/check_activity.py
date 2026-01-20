
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/ingest")))

from sqlalchemy import text
from ingest.db import SessionLocal
import datetime

def check_recent_activity():
    with SessionLocal() as db:
        # Check rows updated in last 5 minutes
        cnt = db.execute(text("SELECT COUNT(*) FROM price_daily WHERE created_at > NOW() - INTERVAL '10 minutes'")).scalar()
        
        # Check which tickers were updated
        tickers = db.execute(text("""
            SELECT ticker, COUNT(*) 
            FROM price_daily 
            WHERE created_at > NOW() - INTERVAL '10 minutes'
            GROUP BY ticker
            LIMIT 5
        """)).fetchall()
        
        print(f"Rows updated in last 10 mins: {cnt}")
        if tickers:
            print("Recently updated tickers (sample):")
            for t in tickers:
                print(f" - {t[0]}: {t[1]} rows")
        else:
            print("No tickers updated recently.")

if __name__ == "__main__":
    check_recent_activity()
