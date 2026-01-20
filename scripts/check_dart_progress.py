
import sys
import os
from sqlalchemy import text

# Add ingest service path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/ingest")))

from ingest.db import SessionLocal

def check_dart_progress():
    with SessionLocal() as db:
        # 1. Total Filings
        total = db.execute(text("SELECT COUNT(*) FROM dart_filing")).scalar()
        
        # 2. Latest Created At (To see if it's still working)
        latest_created = db.execute(text("SELECT MAX(created_at) FROM dart_filing")).scalar()
        
        # 3. Filling Date Range
        min_date = db.execute(text("SELECT MIN(filing_date) FROM dart_filing")).scalar()
        max_date = db.execute(text("SELECT MAX(filing_date) FROM dart_filing")).scalar()
        
        print(f"--- DART Filing Progress ---")
        print(f"Total Rows: {total}")
        print(f"Latest Insert: {latest_created}")
        print(f"Date Range: {min_date} ~ {max_date}")
        
        # 4. Check Recent inserts count (last 10 mins)
        recent_cnt = db.execute(text("SELECT COUNT(*) FROM dart_filing WHERE created_at > NOW() - INTERVAL '10 minutes'")).scalar()
        print(f"Rows inserted in last 10 mins: {recent_cnt}")

if __name__ == "__main__":
    check_dart_progress()
