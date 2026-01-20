
import sys
import os
from sqlalchemy import text
from datetime import datetime, date

# Add ingest service path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/ingest")))

from ingest.db import SessionLocal
from ingest.kis_client import KisClient

def test_single_insert():
    print("1. Initializing KIS Client...")
    kis = KisClient()
    try:
        kis._get_token()
        print("   - Token OK")
    except Exception as e:
        print(f"   - Token Failed: {e}")
        return

    ticker = "005930" # Samsung Electronics
    start_dt = "20250101"
    end_dt = datetime.now().strftime("%Y%m%d")
    
    print(f"2. Fetching Data for {ticker} ({start_dt}~{end_dt})...")
    prices = kis.get_stock_daily_history(ticker, start_dt, end_dt)
    
    if not prices:
        print("   - No data returned!")
        return
    
    print(f"   - Fetched {len(prices)} rows.")
    print(f"   - Sample Row: {prices[0]}")

    print("3. Attempting DB Insert...")
    
    try:
        with SessionLocal() as db:
            # Explicitly listing columns based on schema check
            stmt = text("""
                INSERT INTO price_daily (
                    ticker, trade_date, open, high, low, close, volume, 
                    turnover_krw, created_at
                ) VALUES (
                    :t, :d, :o, :h, :l, :c, :v, :turnover_krw, NOW()
                )
                ON CONFLICT (ticker, trade_date) DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume,
                    turnover_krw = EXCLUDED.turnover_krw
            """)
            
            p = prices[0]
            d_str = p['stck_bsop_date']
            p_date = date(int(d_str[:4]), int(d_str[4:6]), int(d_str[6:8]))
            
            # Param mapping
            params = {
                "t": ticker,
                "d": p_date,
                "o": int(p.get('stck_oprc', 0)),
                "h": int(p.get('stck_hgpr', 0)),
                "l": int(p.get('stck_lwpr', 0)),
                "c": int(p.get('stck_clpr', 0)),
                "v": int(p.get('acml_vol', 0)),
                "turnover_krw": int(p.get('acml_tr_pbmn', 0))
            }
            
            print(f"   - Params: {params}")
            db.execute(stmt, params)
            db.commit()
            print("   - Insert SUCCESS!")
            
    except Exception as e:
        print(f"   - Insert FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single_insert()
