import sqlalchemy
from sqlalchemy import create_engine, text

DB_URL = "postgresql+psycopg://postgres:Kevin0371_@localhost:5432/stockmanager"

def check_tables():
    engine = create_engine(DB_URL)
    tables = [
        "company", "security", "price_daily", "dart_filing", "macro_series"
    ]
    
    with engine.connect() as conn:
        print("--- Table Status ---")
        for table in tables:
            try:
                res = conn.execute(text(f"SELECT count(*) FROM {table}"))
                count = res.scalar()
                print(f"Table '{table}': {count} rows")
            except Exception as e:
                print(f"Table '{table}': FAILED/MISSING ({e})")

if __name__ == "__main__":
    check_tables()
