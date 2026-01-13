from app.db import SessionLocal
from sqlalchemy import text

db = SessionLocal()
result = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='report_request' ORDER BY ordinal_position")).fetchall()

print("report_request table columns:")
for r in result:
    print(f"  {r[0]}: {r[1]}")

db.close()
