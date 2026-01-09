import os
from datetime import date, timedelta
import sqlalchemy
from sqlalchemy import create_engine, text
import random

# DB credentials
DB_URL = "postgresql+psycopg://postgres:Kevin0371_@localhost:5432/stockmanager"

SAM_ELEC = {"ticker": "005930", "name": "삼성전자", "isin": "KR7005930003", "market": "KRX_KOSPI"}
SK_HYNIX = {"ticker": "000660", "name": "SK하이닉스", "isin": "KR7000660001", "market": "KRX_KOSPI"}
ECOPRO = {"ticker": "086520", "name": "에코프로", "isin": "KR7086520004", "market": "KRX_KOSDAQ"}

def seed_data():
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            print("Connected to DB.")
            
            # 1. Insert Company & Security
            print("Seeding 'company' & 'security' tables...")
            for stock in [SAM_ELEC, SK_HYNIX, ECOPRO]:
                # Insert Company
                # check if company exists
                # For simplicity, we assume 1:1 mapping for this seed script
                res = conn.execute(text("INSERT INTO company (name_ko, company_type) VALUES (:name, 'LISTED') RETURNING company_id"), {"name": stock["name"]})
                company_id = res.scalar()
                
                # Insert Security
                stmt = text("""
                    INSERT INTO security (ticker, isin, market, company_id)
                    VALUES (:ticker, :isin, :market, :cid)
                    ON CONFLICT (ticker) DO NOTHING
                """)
                conn.execute(stmt, {
                    "ticker": stock["ticker"], 
                    "isin": stock["isin"], 
                    "market": stock["market"],
                    "cid": company_id
                })

            
            # 2. Insert Price History (Last 30 days)
            print("Seeding 'price_daily' table (30 days)...")
            today = date.today()
            
            for stock, base_price in [(SAM_ELEC, 72000), (SK_HYNIX, 130000), (ECOPRO, 800000)]:
                current_price = base_price
                for i in range(30):
                    trade_date = today - timedelta(days=29-i)
                    if trade_date.weekday() >= 5: continue # Skip weekend
                    
                    change = random.uniform(-0.03, 0.03)
                    current_price = current_price * (1 + change)
                    
                    stmt = text("""
                        INSERT INTO price_daily (ticker, trade_date, open, high, low, close, volume, turnover_krw)
                        VALUES (:ticker, :date, :open, :high, :low, :close, :vol, :val)
                        ON CONFLICT (ticker, trade_date) DO NOTHING
                    """)
                    
                    conn.execute(stmt, {
                        "ticker": stock["ticker"],
                        "date": trade_date,
                        "open": int(current_price * 0.99),
                        "high": int(current_price * 1.02),
                        "low": int(current_price * 0.98),
                        "close": int(current_price),
                        "vol": random.randint(100000, 1000000),
                        "val": random.randint(1000000000, 10000000000)
                    })
            
            conn.commit()
            print("Seeding completed successfully.")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    seed_data()
