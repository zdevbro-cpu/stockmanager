
import sys
import os
from sqlalchemy import text

# Add ingest service path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/ingest")))

from ingest.db import SessionLocal

def analyze_mapping_data():
    with SessionLocal() as db:
        # 1. Total Securities
        total_securities = db.execute(text("SELECT COUNT(*) FROM security")).scalar()
        
        # 2. Total Price Daily Rows
        total_prices = db.execute(text("SELECT COUNT(*) FROM price_daily")).scalar()
        
        # 3. Average prices per security
        avg_days = 0
        if total_securities > 0:
            avg_days = total_prices / total_securities
            
        print(f"--- Data Analysis ---")
        print(f"Total Securities (Jongmok): {total_securities}")
        print(f"Total Price Data Rows (280k?): {total_prices}")
        print(f"Average Data Days per Security: {avg_days:.1f} days")
        
        print("\n--- Why 280,000? ---")
        print(f"{total_securities} (tickers) x {avg_days:.1f} (days) = {total_prices}")

if __name__ == "__main__":
    analyze_mapping_data()
