
import sys
import os
from sqlalchemy import text

# Setup paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/ingest")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../apps/api")))

from app.services.report_service import generate_ai_report
from ingest.db import SessionLocal

def verify_report_data():
    with SessionLocal() as db:
        # 1. Find Samsung Electronics
        # Note: In the seed script, we inserted '005930'
        company = db.execute(text("SELECT company_id, name_ko FROM company WHERE stock_code = '005930'")).fetchone()
        
        if not company:
            print("Error: Samsung Electronics (005930) not found in DB.")
            return

        cid, name = company
        print(f"Target Company: {name} (ID: {cid})")

        # 2. Check if Financial Mart data exists
        mart_count = db.execute(text("SELECT count(*) FROM fs_mart_annual WHERE company_id = :cid"), {"cid": cid}).scalar()
        print(f"found {mart_count} annual financial records in Mart.")
        
        if mart_count == 0:
            print("Error: No financial mart data found. Please run seed script.")
            return

        # 3. Create a Dummy Report Request to satisfy FK constraints
        # We need a valid report_id to pass to generate_ai_report
        stmt = text("""
            INSERT INTO report_request (company_id, template, status) 
            VALUES (:cid, 'VC_MEMO_V1.1', 'PENDING') 
            RETURNING report_id
        """)
        report_id = db.execute(stmt, {"cid": cid}).scalar()
        db.commit()
        print(f"Created temporary report request ID: {report_id}")

        # 4. Run Generation (This will confirm if the prompts are built correctly)
        # We want to capture the stdout/print from generate_ai_report to see what info it fetched
        print("-" * 20)
        print("Running Report Generation...")
        try:
            # We are calling the service function directly
            generate_ai_report(db, cid, report_id)
            print("Report Generation Completed.")
            
            # 5. Read the generated file to check for keywords
            artifact_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../artifacts/reports"))
            report_file = os.path.join(artifact_dir, f"report_{report_id}.md")
            
            if os.path.exists(report_file):
                with open(report_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                print("-" * 20)
                print("Verifying Content Inclusion:")
                
                # Check for Financial Data
                if "최근 3개년 재무 요약" in content or "매출 300,000,000,000,000" in content:
                    print("[PASS] Financial Summary included.")
                else:
                    print("[FAIL] Financial Summary NOT found.")
                    
                # Check for Risks
                if "시장 조치" in content:
                    print("[PASS] Risk Section included.")
                else:
                    print("[FAIL] Risk Section NOT found.")
            else:
                print("Error: Report file was not created.")

        except Exception as e:
            print(f"Error during generation: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    verify_report_data()
