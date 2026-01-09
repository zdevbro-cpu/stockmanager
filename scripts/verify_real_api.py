import os
import requests
import json
import time
from datetime import date
from sqlalchemy import create_engine, text

# Load env manually to avoid dependency issues
def load_env():
    env_vars = {}
    try:
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    key, val = line.strip().split("=", 1)
                    env_vars[key] = val
    except Exception as e:
        print(f"Warning: Could not read .env file: {e}")
    return env_vars

ENV = load_env()
DB_URL = f"postgresql+psycopg://{ENV.get('DB_USER', 'postgres')}:{ENV.get('DB_PASSWORD', 'Kevin0371_')}@{ENV.get('DB_HOST', 'localhost')}:{ENV.get('DB_PORT', '5432')}/{ENV.get('DB_NAME', 'stockmanager')}"

KIS_APP_KEY = ENV.get("KIS_API_KEY")
KIS_APP_SECRET = ENV.get("KIS_API_SECRET_KEY")
KIS_BASE_URL = "https://openapi.koreainvestment.com:9443" # Prod URL

def get_kis_token():
    url = f"{KIS_BASE_URL}/oauth2/tokenP"
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": KIS_APP_KEY,
        "appsecret": KIS_APP_SECRET
    }
    
    print(f"Requesting KIS Token... (Key ends with: {KIS_APP_KEY[-4:] if KIS_APP_KEY else 'None'})")
    res = requests.post(url, headers=headers, data=json.dumps(body))
    
    if res.status_code != 200:
        print(f"Failed to get token: {res.text}")
        return None
    
    return res.json().get("access_token")

def get_current_price(token, ticker="005930"): # Samsung Elec
    url = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price"
    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {token}",
        "appkey": KIS_APP_KEY,
        "appsecret": KIS_APP_SECRET,
        "tr_id": "FHKST01010100"
    }
    params = {
        "fid_cond_mrkt_div_code": "J",
        "fid_input_iscd": ticker
    }
    
    print(f"Fetching price for {ticker}...")
    res = requests.get(url, headers=headers, params=params)
    
    if res.status_code != 200:
        print(f"Failed to fetch price: {res.text}")
        return None
    
    return res.json().get("output")

def save_to_db(data, ticker):
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            # 1. Insert Company (if not exists)
            # returning company_id if inserted, or finding it if exists
            # For simplicity in this verifiction, we try insert and ignore conflict, 
            # then select it.
            conn.execute(text("INSERT INTO company (name_ko, company_type) VALUES ('Samsung Electronics', 'LISTED') ON CONFLICT DO NOTHING"))
            
            # Get company_id (assuming it exists now)
            cid_res = conn.execute(text("SELECT company_id FROM company WHERE name_ko = 'Samsung Electronics'"))
            company_id = cid_res.scalar()

            # 2. Upsert Security
            conn.execute(text("""
                INSERT INTO security (ticker, market, company_id) 
                VALUES (:t, 'KRX_KOSPI', :cid) 
                ON CONFLICT (ticker) DO NOTHING
            """), {"t": ticker, "cid": company_id})
            
            # 3. Insert Price
            # output keys: stck_prpr (close), stck_oprc (open), stck_hgpr (high), stck_lwpr (low), acml_vol (vol), acml_tr_pbmn (val)
            stmt = text("""
                INSERT INTO price_daily (ticker, trade_date, open, high, low, close, volume, turnover_krw, source, created_at)
                VALUES (:t, :d, :o, :h, :l, :c, :v, :val, 'KIS_REAL', NOW())
                ON CONFLICT (ticker, trade_date) 
                DO UPDATE SET close = EXCLUDED.close, volume = EXCLUDED.volume, turnover_krw = EXCLUDED.turnover_krw
            """)
            
            price_data = {
                "t": ticker,
                "d": date.today(),
                "o": int(data['stck_oprc']),
                "h": int(data['stck_hgpr']),
                "l": int(data['stck_lwpr']),
                "c": int(data['stck_prpr']),
                "v": int(data['acml_vol']),
                "val": int(data['acml_tr_pbmn'])
            }
            
            conn.execute(stmt, price_data)
            conn.commit()
            print(f"Successfully saved real data to DB: {price_data}")
            
    except Exception as e:
        print(f"DB Error: {e}")

def run():
    if not KIS_APP_KEY or not KIS_APP_SECRET:
        print("ERROR: KIS_APP_KEY or KIS_APP_SECRET is missing in .env")
        return

    token = get_kis_token()
    if token:
        data = get_current_price(token)
        if data:
            save_to_db(data, "005930")

if __name__ == "__main__":
    run()
