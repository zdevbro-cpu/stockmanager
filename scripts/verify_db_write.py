import os
import sqlalchemy
from sqlalchemy import create_engine, text

# Use the password we found in .env (Kevin0371_)
DB_URL = "postgresql+psycopg://postgres:Kevin0371_@localhost:5432/stockmanager"

def verify():
    print(f"SQLAlchemy Version: {sqlalchemy.__version__}")
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            print("Connected to DB successfully.")
            
            # 1. Clean up potential leftover
            conn.execute(text("DELETE FROM security WHERE ticker = 'TEST99999'"))
            conn.commit()

            # 2. Insert test data
            # market_scope enum: 'KRX_KOSPI' is valid
            print("Attempting to insert test data into 'security' table...")
            conn.execute(text("INSERT INTO security (ticker, isin, market) VALUES (:t, :i, :m)"), 
                         {"t": "TEST99999", "i": "KR7000000000", "m": "KRX_KOSPI"})
            conn.commit()
            print("Insert committed.")

            # 3. Read back
            print("Verifying data by reading it back...")
            result = conn.execute(text("SELECT ticker, isin, market FROM security WHERE ticker = 'TEST99999'"))
            row = result.fetchone()
            
            if row:
                print(f"SUCCESS: Read back data -> Ticker: {row[0]}, ISIN: {row[1]}, Market: {row[2]}")
            else:
                print("FAILURE: Could not find the inserted row.")
            
            # 4. Cleanup
            conn.execute(text("DELETE FROM security WHERE ticker = 'TEST99999'"))
            conn.commit()
            print("Test data cleaned up.")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    verify()
