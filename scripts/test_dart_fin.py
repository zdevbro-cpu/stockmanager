
import sys
import os
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/ingest")))

from ingest.dart_financials_loader import fetch_and_save_company_financials

print("--- Testing DART Financials Loader (Limit 1) ---")
try:
    fetch_and_save_company_financials(limit_companies=1)
    print("Success.")
except Exception as e:
    print(f"\nCRITICAL ERROR in loader: {e}")
    import traceback
    traceback.print_exc()
