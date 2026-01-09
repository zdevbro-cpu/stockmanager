import requests
from sqlalchemy import text
from ingest.config import settings
from ingest.db import SessionLocal
from datetime import date

def fetch_and_save_ecos_series(limit: int = 10):
    """
    Fetch economic indicators from BOK ECOS. 
    REAL API ONLY.
    """
    api_key = settings.ECOS_API_KEY
    print(f"Starting REAL ECOS Ingest (Key: {api_key})...", flush=True)
    
    with SessionLocal() as db:
        try:
            # StatCode: 722Y001 (Interest Rates), ItemCode1: 0101000 (Base Rate)
            # URL: StatCode/Cycle/Start/End/ItemCode1
            url = f"http://ecos.bok.or.kr/api/StatisticSearch/{api_key}/json/kr/1/{limit}/722Y001/D/20230101/20241231/0101000"
            
            resp = requests.get(url, timeout=10)
            data = resp.json()
            
            if resp.status_code == 200 and "StatisticSearch" in data:
                rows = data["StatisticSearch"]["row"]
                count = 0
                for row in rows:
                    if not row.get('DATA_VALUE'): continue
                    obs_date_str = row['TIME']
                    obs_date = date(int(obs_date_str[:4]), int(obs_date_str[4:6]), int(obs_date_str[6:8]))
                    db.execute(text("""
                        INSERT INTO macro_series (series_code, obs_date, value, created_at)
                        VALUES (:sc, :od, :v, NOW())
                        ON CONFLICT (series_code, obs_date) DO UPDATE SET value = EXCLUDED.value
                    """), {"sc": row['ITEM_CODE1'], "od": obs_date, "v": float(row['DATA_VALUE'])})
                    count += 1
                db.commit()
                print(f"Successfully saved {count} records from ECOS.")
            else:
                error_msg = data.get("RESULT", {}).get("MESSAGE") or data
                print(f"ECOS API Error: {error_msg}")
                
        except Exception as e:
            print(f"ECOS Ingest Failed: {e}")
            db.rollback()
        finally:
            db.close()
