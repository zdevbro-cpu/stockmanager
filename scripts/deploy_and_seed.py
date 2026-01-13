
import sys
import os

# Add services/ingest to path
INGEST_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/ingest"))
ETL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../etl"))

if INGEST_PATH not in sys.path:
    sys.path.append(INGEST_PATH)
if ETL_PATH not in sys.path:
    sys.path.append(ETL_PATH)

from ingest.db import SessionLocal
from sqlalchemy import text

def run_migration():
    print("Applying Migration: 001_vc_memo_core_v1_1.sql...")
    migration_file = os.path.join(os.path.dirname(__file__), "../db/migrations/001_vc_memo_core_v1_1.sql")
    
    with open(migration_file, "r", encoding="utf-8") as f:
        sql = f.read()

    with SessionLocal() as db:
        try:
            # Split by statement if needed, or execute whole block if driver supports it.
            # Psycopg2 usually handles multiple statements in one execute if textual.
            db.execute(text(sql))
            db.commit()
            print("Migration applied successfully.")
        except Exception as e:
            print(f"Migration failed: {e}")
            db.rollback()

def load_initial_data():
    print("Loading Initial Data (Stubs/Marts)...")
    # Need to import these here to avoid import errors if paths weren't set up top
    try:
        from jobs.fetch_kind import crawl_kind_market_actions
        # from jobs.mart_generation import generate_financial_marts 
        # Note: mart_generation depends on existing 'fs_fact' data. 
        # If fs_fact is empty, mart will be empty.
        # We might need to insert some dummy fs_fact data for demonstration if real data isn't there.
        
        crawl_kind_market_actions()
        print("KIND Market Actions Loaded.")
        
        # Check company existence
        with SessionLocal() as db:
            cid = db.execute(text("SELECT company_id FROM company WHERE stock_code='005930'")).scalar()
            if not cid:
                print("No company found. Creating dummy company...")
                db.execute(text("INSERT INTO company (name_ko, stock_code, company_type) VALUES ('삼성전자', '005930', 'LISTED')"))
                db.commit()
                cid = db.execute(text("SELECT company_id FROM company WHERE stock_code='005930'")).scalar()
            
            print(f"Generating financials for Company ID: {cid}")
            
            # Clean up existing mock data for this company to avoid duplicates on re-run
            db.execute(text("DELETE FROM fs_fact WHERE company_id = :cid"), {"cid": cid})
            
            # Insert 3 years of data (2021, 2022, 2023)
            years = [2021, 2022, 2023]
            base_rev = 300000000000000 # 300T
            
            for idx, year in enumerate(years):
                rev = base_rev + (idx * 10000000000000)
                op = rev * 0.15
                net = op * 0.8
                assets = rev * 1.5
                equity = assets * 0.7
                
                # Manual Insert into fs_fact columns: 
                # company_id, period_type, fiscal_year, statement_type, account_code, amount...
                
                # Actually, for the MART generation to work, we need specific codes.
                # Or we can just insert directly into MART for the demo if we want to confirm UI.
                # But better to test the pipeline: Fact -> Mart.
                
                params = {
                    "cid": cid, "y": year, 
                    "rev": rev, "op": op, "ni": net, 
                    "ast": assets, "eq": equity
                }
                
                # Insert Fact Rows (Expanded for Mart Pivot)
                # REV, OP, NI, TOTAL_ASSETS, TOTAL_EQUITY
                codes = {
                    'REV': rev, 'OP': op, 'NI': net, 
                    'TOTAL_ASSETS': assets, 'TOTAL_EQUITY': equity
                }
                
                for code, val in codes.items():
                    db.execute(text("""
                        INSERT INTO fs_fact (company_id, period_type, fiscal_year, statement_type, account_code, amount, is_consolidated)
                        VALUES (:cid, 'ANNUAL', :y, 'IS', :code, :val, true)
                    """), {"cid": cid, "y": year, "code": code, "val": val})
            
            db.commit()
            print("Dummy fs_fact data created.")

        from jobs.mart_generation import generate_financial_marts
        generate_financial_marts()
        print("Financial Marts Generated.")
        
    except Exception as e:
        print(f"Data Loading failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_migration()
    load_initial_data()
