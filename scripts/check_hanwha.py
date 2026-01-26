import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from apps.api.app.db import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    res = db.execute(text("SELECT company_id, name_ko, corp_code FROM company WHERE name_ko LIKE '%한화에어로스페이스%'")).fetchall()
    print(f"Result: {res}")
finally:
    db.close()
