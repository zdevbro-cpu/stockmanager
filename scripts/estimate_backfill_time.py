
import time
from sqlalchemy import text
import sys
import os

# Add ingest service path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/ingest")))

from ingest.db import SessionLocal

def estimate_time():
    with SessionLocal() as db:
        # 1. Total tickers
        total_tickers = db.execute(text("SELECT COUNT(*) FROM security")).scalar()
        if not total_tickers:
            print("No tickers found.")
            return

        # 2. Target total rows (Target Days = 252)
        target_days = 252
        total_target_rows = total_tickers * target_days
        
        print(f"Total Tickers: {total_tickers}")
        print(f"Target Total Rows ({target_days} days): {total_target_rows}")
        
        # 3. Measure current count
        count_start = db.execute(text("SELECT COUNT(*) FROM price_daily")).scalar()
        time_start = time.time()
        print(f"Current Rows (T1): {count_start}")
        print("Measuring speed for 10 seconds...")
        
        time.sleep(10)
        
        # 4. Measure count after 10s
        count_end = db.execute(text("SELECT COUNT(*) FROM price_daily")).scalar()
        time_end = time.time()
        
        # 5. Calculate Speed
        processed = count_end - count_start
        duration = time_end - time_start
        speed_per_sec = processed / duration
        
        # 6. Estimate remaining
        remaining_rows = total_target_rows - count_end
        
        print(f"Current Rows (T2): {count_end}")
        print(f"Processed {processed} rows in {duration:.2f} seconds.")
        print(f"Speed: {speed_per_sec:.2f} rows/sec")
        
        if speed_per_sec > 0:
            remaining_seconds = remaining_rows / speed_per_sec
            remaining_minutes = remaining_seconds / 60
            remaining_hours = remaining_minutes / 60
            print(f"\n--- Estimation ---")
            print(f"Remaining Rows: {remaining_rows}")
            print(f"Estimated Time Left: {remaining_minutes:.1f} minutes ({remaining_hours:.1f} hours)")
        else:
            print("\n--- Estimation ---")
            print("Speed is 0 (or very slow). Cannot estimate time.")
            print("Backfill might be finished, paused, or stuck.")

if __name__ == "__main__":
    estimate_time()
