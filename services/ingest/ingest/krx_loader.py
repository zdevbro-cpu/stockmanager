import FinanceDataReader as fdr
from sqlalchemy import text
from ingest.db import get_db
import hashlib

def fetch_and_save_krx_list(progress_cb=None):
    db = next(get_db())
    print("Fetching KRX stock list via FinanceDataReader...")
    
    try:
        # Fetch KRX with sector metadata
        df_krx = fdr.StockListing('KRX')
        if 'Market' in df_krx.columns:
            df_krx = df_krx[df_krx['Market'].isin(['KOSPI', 'KOSDAQ'])]
        
        count = 0
        total = len(df_krx)
        if progress_cb:
            progress_cb(0, total)
        for _, row in df_krx.iterrows():
            ticker = str(row['Code'])
            name = row['Name']
            market_raw = row.get('Market', '')
            market = 'KRX_KOSPI' if market_raw == 'KOSPI' else 'KRX_KOSDAQ'
            sector_name = row.get('Sector') if 'Sector' in row.index else None

            sector_code = None
            if isinstance(sector_name, str) and sector_name.strip():
                digest = hashlib.sha1(sector_name.strip().encode('utf-8')).hexdigest()[:10]
                sector_code = f"KRX_SECTOR_{digest}"

            # 1. Insert/Update Company
            # Setting company_type to 'LISTED' explicitly as we are loading listed stocks
            stmt_company = text("""
                INSERT INTO company (name_ko, stock_code, company_type, sector_name, sector_code, created_at)
                VALUES (:n, :sc, 'LISTED', :sn, :scd, NOW())
                ON CONFLICT (stock_code) DO UPDATE
                SET updated_at = NOW(),
                    name_ko = :n,
                    sector_name = COALESCE(EXCLUDED.sector_name, company.sector_name),
                    sector_code = COALESCE(EXCLUDED.sector_code, company.sector_code)
                RETURNING company_id
            """)
            # fdr returns Code/Name. We treat Code as stock_code.
            result = db.execute(stmt_company, {"n": name, "sc": ticker, "sn": sector_name, "scd": sector_code})
            company_id = result.fetchone()[0]

            # 2. Insert/Update Security (Removed is_active as per schema)
            stmt_security = text("""
                INSERT INTO security (ticker, company_id, market, created_at)
                VALUES (:t, :cid, :m, NOW())
                ON CONFLICT (ticker) DO UPDATE SET market = :m, company_id = :cid
            """)
            db.execute(stmt_security, {"t": ticker, "cid": company_id, "m": market})
            count += 1
            if progress_cb and count % 50 == 0:
                progress_cb(count, total)
            
            if count % 200 == 0:
                print(f"Processed {count} stocks...")
        
        db.commit()
        if progress_cb:
            progress_cb(count, total)
        print(f"Successfully loaded {count} KRX stocks.")
        
    except Exception as e:
        print(f"Error loading KRX list: {e}")
        db.rollback()
        raise e
