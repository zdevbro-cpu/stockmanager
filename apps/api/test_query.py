from app.db import SessionLocal
from sqlalchemy import text
import sys
import os

def test_api_query():
    db = SessionLocal()
    try:
        stmt = text("""
            SELECT r.report_id, r.company_id, c.name_ko as company_name, r.template, r.status, r.created_at 
            FROM report_request r
            JOIN company c ON r.company_id = c.company_id
            ORDER BY r.created_at DESC
        """)
        rows = db.execute(stmt).fetchall()
        print(f"API style query results: {len(rows)}")
    finally:
        db.close()

if __name__ == "__main__":
    test_api_query()
