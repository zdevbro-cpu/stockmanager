import FinanceDataReader as fdr
from sqlalchemy import text
from ingest.db import get_db

def fetch_and_save_krx_list():
    db = next(get_db())
    print("Fetching KRX stock list via FinanceDataReader...")
    
    try:
        # Fetch KOSPI and KOSDAQ
        df_kospi = fdr.StockListing('KOSPI')
        df_kosdaq = fdr.StockListing('KOSDAQ')
        
        # Add market column
        df_kospi['Market'] = 'KRX_KOSPI'
        df_kosdaq['Market'] = 'KRX_KOSDAQ'
        
        # Combine
        combined = [df_kospi, df_kosdaq]
        
        count = 0
        for df in combined:
            for _, row in df.iterrows():
                ticker = str(row['Code'])
                name = row['Name']
                market = row['Market']
                
                # FinanceDataReader columns vary, but Code/Name are standard
                # 1. Insert/Update Company
                # Setting company_type to 'LISTED' explicitly as we are loading listed stocks
                stmt_company = text("""
                    INSERT INTO company (name_ko, stock_code, company_type, created_at)
                    VALUES (:n, :sc, 'LISTED', NOW())
                    ON CONFLICT (stock_code) DO UPDATE SET updated_at = NOW(), name_ko = :n
                    RETURNING company_id
                """)
                # fdr returns Code/Name. We treat Code as stock_code.
                result = db.execute(stmt_company, {"n": name, "sc": ticker})
                company_id = result.fetchone()[0]

                # 2. Insert/Update Security (Removed is_active as per schema)
                stmt_security = text("""
                    INSERT INTO security (ticker, company_id, market, created_at)
                    VALUES (:t, :cid, :m, NOW())
                    ON CONFLICT (ticker) DO UPDATE SET market = :m, company_id = :cid
                """)
                db.execute(stmt_security, {"t": ticker, "cid": company_id, "m": market})
                count += 1
                
                if count % 100 == 0:
                    print(f"Processed {count} stocks...")
        
        db.commit()
        print(f"Successfully loaded {count} KRX stocks.")
        
    except Exception as e:
        print(f"Error loading KRX list: {e}")
        db.rollback()
        raise e
