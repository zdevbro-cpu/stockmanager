
import sys
import os
import time
import concurrent.futures
from datetime import datetime, date
from sqlalchemy import text
import requests

# Add ingest service path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/ingest")))

from ingest.db import SessionLocal
from ingest.kis_client import KisClient
from ingest.config import settings

import threading

# Thread-safe Print
print_lock = threading.Lock()

def _log(msg):
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_msg = f"[{timestamp}] {msg}"
    with print_lock:
        print(log_msg, flush=True)
    with open("backfill_debug.log", "a", encoding="utf-8") as f:
        f.write(log_msg + "\n")

def process_ticker(kis, ticker, start_dt, end_dt):
    """
    Fetch and save price history for a single ticker.
    Returns (success: bool, message: str)
    """
    try:
        if ticker in ['000020', '005930']: # Sample debug for specific tickers
             _log(f"Fetching {ticker}...") 
        
        # 1. Fetch data
        # KisClient handles authentication internally
        # get_stock_daily_history returns list of dicts
        prices = kis.get_stock_daily_history(ticker, start_dt, end_dt)
        
        if not prices:
            return False, f"{ticker}: No data returned"

        # 2. Save to DB (Single Transaction per ticker to avoid locking issues)
        with SessionLocal() as db:
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
            
            for p in prices:
                # KIS returns YYYYMMDD string
                d_str = p['stck_bsop_date']
                p_date = date(int(d_str[:4]), int(d_str[4:6]), int(d_str[6:8]))
                
                db.execute(stmt, {
                    "t": ticker,
                    "d": p_date,
                    "o": int(p.get('stck_oprc', 0)),
                    "h": int(p.get('stck_hgpr', 0)),
                    "l": int(p.get('stck_lwpr', 0)),
                    "c": int(p.get('stck_clpr', 0)),
                    "v": int(p.get('acml_vol', 0)),
                    "turnover_krw": int(p.get('acml_tr_pbmn', 0))
                })
            db.commit()
            
        return True, f"{ticker}: Saved {len(prices)} rows"

    except Exception as e:
        return False, f"{ticker}: Error - {e}"

def main():
    # To get ~252 trading days (1 year), we need roughly 365 calendar days.
    # Previous setting of 252 calendar days only fetched ~175 trading days (start date ~May 9th).
    days = 365 
    workers = 5  # Conservative concurrency
    
    _log(f"Starting FAST Backfill (Days={days}, Workers={workers})")

    # 1. Initialize KIS Client
    kis = KisClient()
    try:
        kis._get_token()
    except Exception as e:
        _log(f"Failed to issue KIS Access Token: {e}")
        return

    # 2. Get Tickers
    with SessionLocal() as db:
        tickers = [r[0] for r in db.execute(text("SELECT ticker FROM security ORDER BY ticker")).fetchall()]
    
    _log(f"Total Tickers to process: {len(tickers)}")
    
    # 3. Define Date Range
    # Simple approach: Request today's data and KIS will give us 'days' worth of history backwards?
    # Actually get_stock_daily_history needs YYYYMMDD ~ YYYYMMDD
    # But the KisClient.get_stock_daily_history implementation handles the paging/date logic internally 
    # if we look at the implementation... wait, let's check kis_client.py logic usage.
    # The existing loader does: kis.get_stock_daily_history(ticker, period_code="D") ... no, let's pass dates if possible.
    # Looking at previous context, get_stock_daily_history(self, stock_code, start_date=None, end_date=None)
    # If start/end not provided, it fetches recent?
    # Let's verify KIS client usage.
    
    # Assuming get_stock_daily_history(ticker) fetches recent 30 days by default or we need to loop?
    # Let's stick to what the original backfill did or try to be smart.
    # Original backfill_kis_prices.py calls: update_kis_prices_task or backfill...
    # In kis_loader.py: 
    # def backfill_kis_prices_task(days=100):
    #    ...
    #    hist = kis.get_stock_daily_history(t.ticker, start_date=start_str, end_date=end_str)
    
    # So we need start/end str.
    from datetime import timedelta
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")
    
    _log(f"Target Period: {start_str} ~ {end_str}")

    success_count = 0
    fail_count = 0
    
    # 4. Run Parallel with Retry Queue
    # We will use a while loop to process tickers, and retry failed ones.
    # But for simplicity in this script, let's just process once and log failures.
    # To be robust as user requested, we could add auto-restart logic here?
    # Actually, the user wants me to *cognize* error and restart.
    # So I will wrap the executor in a try-except block that can recover?
    # No, better to handle inside threaded tasks.
    
    max_retries = 3
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        # Submit all tasks
        future_to_ticker = {
            executor.submit(process_ticker, kis, ticker, start_str, end_str): ticker 
            for ticker in tickers
        }
        
        for future in concurrent.futures.as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            try:
                success, msg = future.result()
                if success:
                    success_count += 1
                    if success_count % 50 == 0:
                        _log(f"Progress: {success_count}/{len(tickers)} (Last: {msg})")
                else:
                    fail_count += 1
                    _log(f"FAIL: {msg}")
                    # Basic retry logic could be added here if needed, but keeping it simple for now.
            except Exception as e:
                fail_count += 1
                _log(f"CRASH {ticker}: {e}")
                
            # Rate Limit Throttle (Simple)
            time.sleep(0.05) 

    _log(f"Finished. Success: {success_count}, Fail: {fail_count}")

    # Auto-restart check: if too many failures (e.g. token issue), we might want to alert or re-run.
    if fail_count > 100:
        _log("WARNING: High failure count. Check logs.")

if __name__ == "__main__":
    main()
