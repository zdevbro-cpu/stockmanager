import sys
import os

# Add relevant paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../apps/api")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/ingest")))

from app.db import SessionLocal
from app.services.report_service import generate_ai_report
from sqlalchemy import text

def test_report():
    with SessionLocal() as db:
        # Create a dummy report_request first
        stmt = text("""
            INSERT INTO report_request (company_id, template, status, created_at, updated_at)
            VALUES (5704, 'investment_memo_vc_v1', 'PENDING', NOW(), NOW())
            RETURNING report_id
        """)
        report_id = db.execute(stmt).scalar()
        db.commit()
        
        print(f"Created report_request ID: {report_id}")
        
        content = generate_ai_report(db, 5704, report_id)
        print("\nReport generation completed.")

if __name__ == "__main__":
    test_report()
