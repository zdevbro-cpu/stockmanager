
import sys
import os
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/ingest")))

from ingest.dart_loader import fetch_and_save_dart_filings_for_corp

# Samsung Electronics corp_code
CORP_CODE = "00126380"

print(f"--- Testing DART Filings Backfill for {CORP_CODE} ---")
try:
    count = fetch_and_save_dart_filings_for_corp(CORP_CODE, days=30)
    print(f"Success. Count: {count}")
except Exception as e:
    print(f"\nCRITICAL ERROR in filings loader: {e}")
    import traceback
    traceback.print_exc()
