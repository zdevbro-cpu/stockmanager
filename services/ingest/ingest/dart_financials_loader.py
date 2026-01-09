import requests
from sqlalchemy import text
from ingest.config import settings
from ingest.db import SessionLocal
from datetime import date

def fetch_and_save_company_financials(limit_companies: int = 10):
    """
    Fetch major financial indicators (Revenue, Operating Profit, etc.) 
    for companies from OpenDART and save to 'financial_statement' table.
    Uses 'fnlttSinglAcnt' API (Major Accounts).
    """
    api_key = settings.DART_API_KEY
    if not api_key:
        print("DART_API_KEY is missing.", flush=True)
        return

    print(f"Starting DART Financials Ingest (Limit: {limit_companies} companies)...", flush=True)
    
    with SessionLocal() as db:
        try:
            # 1. Get companies with corp_code
            stmt = text("SELECT corp_code, name_ko FROM company WHERE corp_code IS NOT NULL LIMIT :l")
            companies = db.execute(stmt, {"l": limit_companies}).fetchall()
            
            # Reprt codes: 11011(Annual), 11012(Half), 11013(Q1), 11014(Q3)
            # For now, let's fetch 2023 Annual Report (11011) as a base.
            bsns_year = "2023"
            reprt_code = "11011"
            
            count = 0
            for corp_code, name in companies:
                print(f"Fetching financials for {name} ({corp_code})...", flush=True)
                
                url = "https://opendart.fss.or.kr/api/fnlttSinglAcnt.json"
                params = {
                    "crtfc_key": api_key,
                    "corp_code": corp_code,
                    "bsns_year": bsns_year,
                    "reprt_code": reprt_code
                }
                
                resp = requests.get(url, params=params, timeout=10)
                data = resp.json()
                
                if resp.status_code == 200 and data.get("status") == "000":
                    list_data = data.get("list", [])
                    for item in list_data:
                        # item keys: account_nm, thstrm_amount, fs_div, fs_nm, etc.
                        # value is usually a string with commas
                        val_str = item.get('thstrm_amount', '0').replace(',', '')
                        try:
                            val = float(val_str) if val_str and val_str != '-' else 0
                        except ValueError:
                            val = 0
                            
                        # fs_div: CFS (Consolidated), OFS (Separate)
                        is_consolidated = (item.get('fs_div') == 'CFS')
                        
                        stmt_upsert = text("""
                            INSERT INTO financial_statement 
                            (corp_code, period_end, announced_at, item_code, item_name, value, unit, consolidated_flag, created_at)
                            VALUES (:cc, :pe, NOW(), :icode, :iname, :v, :u, :cf, NOW())
                            ON CONFLICT (corp_code, period_end, item_code, announced_at) 
                            DO UPDATE SET value = EXCLUDED.value, item_name = EXCLUDED.item_name
                        """)
                        
                        # period_end is approximate for 2023 annual report
                        p_end = date(int(bsns_year), 12, 31)
                        
                        db.execute(stmt_upsert, {
                            "cc": corp_code,
                            "pe": p_end,
                            "icode": item.get('account_id', item.get('account_nm')),
                            "iname": item.get('account_nm'),
                            "v": val,
                            "u": "KRW",
                            "cf": is_consolidated
                        })
                    
                    count += 1
                    db.commit()
                    print(f"Saved financials for {name}", flush=True)
                else:
                    print(f"Skipping {name}: {data.get('message')}", flush=True)
                
            print(f"Finished. Processed {count} companies.", flush=True)
            
        except Exception as e:
            print(f"DART Financials Ingest Failed: {e}", flush=True)
            db.rollback()
        finally:
            db.close()
