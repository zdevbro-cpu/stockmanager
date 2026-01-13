from app.db import SessionLocal
from sqlalchemy import text

db = SessionLocal()
result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='financial_statement' ORDER BY ordinal_position")).fetchall()

print("financial_statement columns:")
for r in result:
    print(f"  - {r[0]}")

db.close()
