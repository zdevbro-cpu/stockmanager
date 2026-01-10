from .base import SessionLocal, text, settings

def generate_financial_marts():
    """
    Generate/Refresh fs_mart (Annual/Quarter) and fs_ratio_mart from fs_fact.
    This is a simplified aggreglogic.
    """
    print("Starting Financial Mart Generation...", flush=True)
    
    with SessionLocal() as db:
        try:
            # 1. Clear existing marts (For full refresh in this version)
            # In production, use UPSERT or incremental
            db.execute(text("TRUNCATE TABLE fs_mart_annual"))
            db.execute(text("TRUNCATE TABLE fs_ratio_mart"))
            
            # 2. Populate Annual Mart (Pivot)
            # Assume fs_fact has standard account_codes: 'REV', 'GP', 'OP', 'NI', 'ASSETS', 'LIAB', 'EQUITY', 'OCF', 'ICF', 'FCF'
            # Note: Real implementation needs mapping table. Here we assume mapped codes.
            
            # Dummy implementation using standard SQL Pivot-like aggregation
            stmt_annual = text("""
                INSERT INTO fs_mart_annual (company_id, fiscal_year, revenue, op_income, net_income, assets, equity, generated_at)
                SELECT 
                    company_id, 
                    fiscal_year,
                    MAX(CASE WHEN account_code = 'REV' THEN amount ELSE 0 END) as revenue,
                    MAX(CASE WHEN account_code = 'OP' THEN amount ELSE 0 END) as op_income,
                    MAX(CASE WHEN account_code = 'NI' THEN amount ELSE 0 END) as net_income,
                    MAX(CASE WHEN account_code = 'TOTAL_ASSETS' THEN amount ELSE 0 END) as assets,
                    MAX(CASE WHEN account_code = 'TOTAL_EQUITY' THEN amount ELSE 0 END) as equity,
                    NOW()
                FROM fs_fact 
                WHERE period_type = 'ANNUAL'
                GROUP BY company_id, fiscal_year
            """)
            db.execute(stmt_annual)
            
            # 3. Calculate Ratios
            stmt_ratio = text("""
                INSERT INTO fs_ratio_mart (company_id, period_type, fiscal_year, op_margin, roe, debt_ratio)
                SELECT
                    company_id,
                    'ANNUAL',
                    fiscal_year,
                    CASE WHEN revenue <> 0 THEN ROUND(op_income / revenue * 100, 2) ELSE 0 END,
                    CASE WHEN equity <> 0 THEN ROUND(net_income / equity * 100, 2) ELSE 0 END,
                    CASE WHEN equity <> 0 THEN ROUND((assets - equity) / equity * 100, 2) ELSE 0 END
                FROM fs_mart_annual
            """)
            db.execute(stmt_ratio)
            
            db.commit()
            print("Financial Mart Generation Completed.")
            
        except Exception as e:
            print(f"Mart Gen Failed: {e}")
            db.rollback()
        finally:
            db.close()

if __name__ == "__main__":
    generate_financial_marts()
