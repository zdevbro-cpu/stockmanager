
import sys
import os
import requests

# Add path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/ingest")))

from ingest.config import settings

def test_dart():
    print("--- DART API Debug ---")
    api_key = settings.DART_API_KEY
    if not api_key:
        print("ERROR: DART_API_KEY is NOT set in settings/env.")
        print("Please check .env file in project root.")
        return
    
    masked_key = api_key[:4] + "*" * (len(api_key)-8) + api_key[-4:] if len(api_key) > 8 else "****"
    print(f"Loaded DART_API_KEY: {masked_key}")
    
    # 1. Test DART list API (Public Notice)
    url = "https://opendart.fss.or.kr/api/list.json"
    params = {
        "crtfc_key": api_key,
        "bgn_de": "20240101",
        "end_de": "20240105",
        "page_count": 10
    }
    
    try:
        print("\nTesting DART Public Notice API (list.json)...")
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        status = data.get("status")
        msg = data.get("message")
        print(f"Status: {status} ({msg})")
        if status == "000":
            print(f"Success! Found {len(data.get('list', []))} items.")
        else:
            print("FAILED.")
            
    except Exception as e:
        print(f"Request Exception: {e}")

    # 2. Test DART Financials API (Sample Company: Samsung Electronics 005930)
    # Corp Code needed. Samsung Electronics corp_code is usually 00126380 (check DB or skip)
    # Just checking API access is mostly enough.
    
    print("\nTest Complete.")

if __name__ == "__main__":
    test_dart()
