import os
import sys
from sqlalchemy import text
from dotenv import load_dotenv

# Add the app directory to sys.path
sys.path.append(os.getcwd())

from app.db import SessionLocal
from app.services.report_service import generate_ai_report

def test():
    load_dotenv(".env")
    db = SessionLocal()
    
    # 1. Choose a target company (Samsung Electronics is 5582)
    company_id = 5582
    
    # 2. Create a dummy report request
    try:
        stmt = text("""
            INSERT INTO report_request (company_id, template, status, created_at, updated_at)
            VALUES (:cid, 'investment_memo_vc_v1', 'PENDING', NOW(), NOW())
            RETURNING report_id
        """)
        report_id = db.execute(stmt, {"cid": company_id}).scalar()
        db.commit()
        print(f"Created dummy report_id: {report_id}")
        
        # 3. Call the actual service function
        print("Starting AI report generation...")
        generate_ai_report(company_id, report_id)
        
        # 4. Check the result
        result = db.execute(text("SELECT status FROM report_request WHERE report_id = :rid"), {"rid": report_id}).fetchone()
        print(f"Final status in DB: {result[0]}")
        
        file_path = os.path.join(os.getcwd(), "..", "..", "artifacts", "reports", f"report_{report_id}.md")
        if os.path.exists(file_path):
            print(f"File created successfully at {file_path}")
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                print("\n--- REPORT PREVIEW (First 500 chars) ---")
                print(content[:500])
                print("------------------------------------------\n")
                
                # Check for clumping and table
                if "o " in content and "\n" in content:
                    print("SUCCESS: Found bullet points.")
                if "|" in content and "매출액" in content:
                    print("SUCCESS: Found financial table.")
        else:
            print("ERROR: Report file was not created.")
            
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test()
