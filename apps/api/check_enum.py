from app.db import SessionLocal
from sqlalchemy import text

db = SessionLocal()
result = db.execute(text("SELECT e.enumlabel FROM pg_enum e JOIN pg_type t ON e.enumtypid = t.oid WHERE t.typname = 'report_status'")).fetchall()

print("Valid report_status values:")
for r in result:
    print(f"  - {r[0]}")

db.close()
