import requests
from sqlalchemy import text
from ingest.config import settings
from ingest.db import SessionLocal
from datetime import date, timedelta

def fetch_and_save_dart_filings():
    """
    Fetch recent filings from OpenDART. 
    REAL API ONLY. Fails if credentials or network is invalid.
    """
    api_key = settings.DART_API_KEY
    if not api_key:
        print("DART_API_KEY is missing in settings/env.")
        return

    print("Starting REAL DART Filings Ingest...")
    
    with SessionLocal() as db:
        try:
            # Last 7 days
            bgn_de = (date.today() - timedelta(days=7)).strftime("%Y%m%d")
            url = "https://opendart.fss.or.kr/api/list.json"
            params = {"crtfc_key": api_key, "bgn_de": bgn_de, "page_count": 100}
            
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            
            if resp.status_code == 200 and data.get("status") == "000":
                list_data = data.get("list", [])
                if not list_data:
                    print("No filings found for the given range.")
                    return

                count = 0
                for item in list_data:
                    # Debug: print first item keys
                    if count == 0:
                        print(f"Sample item keys: {item.keys()}")

                    stmt = text("""
                        INSERT INTO dart_filing (rcp_no, corp_code, filing_date, filing_type, title, created_at)
                        VALUES (:rno, :cc, :d, :typ, :title, NOW())
                        ON CONFLICT (rcp_no) DO UPDATE SET title = EXCLUDED.title
                    """)
                    
                    # Convert YYYYMMDD to date object
                    rdt = item.get('rcept_dt')
                    f_date = date(int(rdt[:4]), int(rdt[4:6]), int(rdt[6:8])) if rdt else date.today()

                    db.execute(stmt, {
                        "rno": item.get('rcept_no'), 
                        "cc": item.get('corp_code'),
                        "d": f_date,
                        "typ": item.get('pblntf_ty', '-'), 
                        "title": item.get('report_nm')
                    })
                    count += 1
                db.commit()
                print(f"Successfully saved {count} filings from DART.")
            else:
                print(f"DART API Error: {data.get('message')} (Code: {data.get('status')})")
                
        except Exception as e:
            print(f"DART Ingest Failed: {e}")
            db.rollback()
        finally:
            db.close()
