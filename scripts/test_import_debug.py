
import sys
import os

# Add ingest service path
INGEST_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/ingest"))
if INGEST_PATH not in sys.path:
    sys.path.append(INGEST_PATH)

print(f"Testing import of ingest.dart_loader from {INGEST_PATH}")

try:
    from ingest.dart_loader import fetch_and_save_dart_filings
    print("Successfully imported fetch_and_save_dart_filings from dart_loader")
except Exception as e:
    print(f"FAILED to import dart_loader: {e}")
    import traceback
    traceback.print_exc()

print("-" * 20)

try:
    from ingest.dart_financials_loader import fetch_and_save_company_financials
    print("Successfully imported fetch_and_save_company_financials from dart_financials_loader")
except Exception as e:
    print(f"FAILED to import dart_financials_loader: {e}")
    import traceback
    traceback.print_exc()
