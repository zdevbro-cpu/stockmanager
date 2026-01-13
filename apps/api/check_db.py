import os
from sqlalchemy import text
from dotenv import load_dotenv
import sys

# Add the app directory to sys.path
sys.path.append(os.getcwd())
from app.db import SessionLocal

def list_db_reports():
    load_dotenv("../../.env")
    db = SessionLocal()
    try:
        stmt = text("SELECT report_id, company_id, status FROM report_request")
        rows = db.execute(stmt).fetchall()
        print(f"Total reports in DB: {len(rows)}")
        for r in rows:
            print(f"- ID: {r[0]}, Company: {r[1]}, Status: {r[2]}")
    finally:
        db.close()

if __name__ == "__main__":
    list_db_reports()
