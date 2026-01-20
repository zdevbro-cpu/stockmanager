
import sys
import os
from sqlalchemy import text

# Add ingest service path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/ingest")))

from ingest.db import SessionLocal

def check_schema():
    with SessionLocal() as db:
        # Get columns for price_daily
        stmt = text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'price_daily'")
        rows = db.execute(stmt).fetchall()
        
        print("--- price_daily columns ---")
        for r in rows:
            print(f"{r[0]} ({r[1]})")

if __name__ == "__main__":
    check_schema()
