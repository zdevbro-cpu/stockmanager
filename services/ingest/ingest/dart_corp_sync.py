import os
import zipfile
import io
import requests
import xml.etree.ElementTree as ET
from sqlalchemy import text
from ingest.config import settings
from ingest.db import SessionLocal

def sync_dart_corp_codes():
    """
    Download ALL corp_codes from OpenDART and update 'company' table.
    Matches by 'stock_code' (ticker) for listed companies.
    """
    api_key = settings.DART_API_KEY
    if not api_key:
        print("DART_API_KEY is missing.", flush=True)
        return

    print("Downloading Corp Codes from OpenDART...", flush=True)
    url = "https://opendart.fss.or.kr/api/corpCode.xml"
    params = {"crtfc_key": api_key}
    
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        print(f"Failed to download: {resp.status_code}", flush=True)
        return

    # Response is a ZIP file containing corpCode.xml
    try:
        with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
            xml_data = z.read("CORPCODE.xml")
            
        tree = ET.fromstring(xml_data)
        count = 0
        
        with SessionLocal() as db:
            print("Syncing corp_codes to DB...", flush=True)
            for list_node in tree.findall("list"):
                corp_code = list_node.findtext("corp_code")
                stock_code = list_node.findtext("stock_code").strip()
                
                if stock_code: # Only for listed companies that have stock_code
                    # Update company table where stock_code matches
                    stmt = text("""
                        UPDATE company 
                        SET corp_code = :cc 
                        WHERE stock_code = :sc AND corp_code IS NULL
                    """)
                    res = db.execute(stmt, {"cc": corp_code, "sc": stock_code})
                    if res.rowcount > 0:
                        count += 1
                        if count % 100 == 0:
                            db.commit()
                            print(f"Synced {count} companies...", flush=True)
            
            db.commit()
            print(f"Finished. Total {count} corp_codes updated.", flush=True)
            
    except Exception as e:
        print(f"Sync Failed: {e}", flush=True)
