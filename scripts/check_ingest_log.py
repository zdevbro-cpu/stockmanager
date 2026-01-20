
import sys
import os
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/ingest")))

from ingest.db import SessionLocal

def check_logs():
    db = SessionLocal()
    try:
        # Check if table exists first
        exists = db.execute(text("SELECT to_regclass('public.ingest_run_log')")).scalar()
        if not exists:
            print("Table 'ingest_run_log' does not exist.")
            return

        stmt = text("""
            SELECT run_id, job_id, status, started_at, message 
            FROM ingest_run_log 
            ORDER BY started_at DESC 
            LIMIT 5
        """)
        rows = db.execute(stmt).fetchall()
        
        print(f"{'RunID':<8} {'JobID':<30} {'Status':<10} {'Started At':<25}")
        print("-" * 80)
        for r in rows:
            msg = r.message if r.message else ""
            print(f"{r.run_id:<8} {r.job_id:<30} {r.status:<10} {str(r.started_at):<25}")
            if msg:
                print(f"   ERROR MESSAGE: {msg}")
                
    except Exception as e:
        print(f"Error checking logs: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_logs()
