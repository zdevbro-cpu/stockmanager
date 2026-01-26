import sys
import os
import logging

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from apps.api.app.db import SessionLocal
from apps.api.app.services.report_service import generate_ai_report

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_report_generation():
    db = SessionLocal()
    try:
        # 1. Find Hanwha Aerospace (ID: 5589)
        company = db.execute(text("SELECT company_id, name_ko FROM company WHERE company_id = 5589")).fetchone()
        
        if not company:
            print("No company found in database.")
            return

        company_id = company[0]
        company_name = company[1]
        print(f"Testing report generation for: {company_name} (ID: {company_id})")

        # 2. Create a dummy report request
        result = db.execute(text("""
            INSERT INTO report_request (company_id, template, status, created_at, updated_at)
            VALUES (:cid, 'investment_memo_vc_v1', 'PENDING', NOW(), NOW())
            RETURNING report_id
        """), {"cid": company_id}).fetchone()
        
        report_id = result[0]
        db.commit()
        print(f"Created test report request ID: {report_id}")

        # 3. Run generation directly
        print("Starting generate_ai_report...")
        generate_ai_report(company_id, report_id)
        print("Finished generate_ai_report.")

        # 4. Check status
        status = db.execute(text("SELECT status FROM report_request WHERE report_id = :rid"), 
                            {"rid": report_id}).scalar()
        print(f"Final Report Status: {status}")

    except Exception as e:
        print(f"An error occurred during debugging: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_report_generation()
