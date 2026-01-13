import os
from sqlalchemy import text
from dotenv import load_dotenv
import sys

sys.path.append(os.getcwd())
from app.db import SessionLocal

def check_fk():
    load_dotenv("../../.env")
    db = SessionLocal()
    try:
        # Check for any tables that have a foreign key to report_request
        stmt = text("""
            SELECT
                tc.table_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' AND ccu.table_name='report_request';
        """)
        rows = db.execute(stmt).fetchall()
        print(f"Foreign keys referencing report_request: {len(rows)}")
        for r in rows:
            print(f"- Table: {r[0]}, Column: {r[1]} -> {r[2]}.{r[3]}")
    finally:
        db.close()

if __name__ == "__main__":
    check_fk()
