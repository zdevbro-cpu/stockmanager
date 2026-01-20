
import sys
import os
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/ingest")))

from ingest.db import SessionLocal

def check_corp_codes():
    print("--- Checking Company Corp Codes ---")
    with SessionLocal() as db:
        total = db.execute(text("SELECT COUNT(*) FROM company")).scalar()
        null_codes = db.execute(text("SELECT COUNT(*) FROM company WHERE corp_code IS NULL")).scalar()
        filled_codes = db.execute(text("SELECT COUNT(*) FROM company WHERE corp_code IS NOT NULL")).scalar()
        
        print(f"Total Companies: {total}")
        print(f"With Corp Code: {filled_codes}")
        print(f"Without Corp Code: {null_codes}")
        
        if null_codes > 0:
            print("\nSample companies without corp_code:")
            rows = db.execute(text("SELECT company_id, name_ko FROM company WHERE corp_code IS NULL LIMIT 5")).fetchall()
            for r in rows:
                print(f" - {r.company_id}: {r.name_ko}")

if __name__ == "__main__":
    check_corp_codes()
