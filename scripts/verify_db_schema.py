
import sys
import os
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/ingest")))

from ingest.db import SessionLocal

def check_schema():
    db = SessionLocal()
    try:
        print("--- Table: financial_statement Indexes ---")
        rows = db.execute(text("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'financial_statement'
        """)).fetchall()
        for r in rows:
            print(f"{r.indexname}: {r.indexdef}")
            
        print("\n--- Table: dart_filing Indexes ---")
        rows = db.execute(text("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'dart_filing'
        """)).fetchall()
        for r in rows:
            print(f"{r.indexname}: {r.indexdef}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_schema()
