from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import sys
import os
import datetime

# Add ingest service path
INGEST_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../services/ingest"))
if INGEST_PATH not in sys.path:
    sys.path.append(INGEST_PATH)

from ingest.krx_loader import fetch_and_save_krx_list
from ingest.kis_loader import update_kis_prices_task

router = APIRouter(
    prefix="/ingest",
    tags=["ingest"]
)

# Real-time task tracker
TASK_STATUS = {
    "krx": "IDLE",
    "mapping": "IDLE",
    "dart": "IDLE",
    "ecos": "IDLE",
    "dart_financials": "IDLE"
}

def update_status(job_id: str, status: str):
    TASK_STATUS[job_id] = status

async def wrapped_task(func, job_id, *args, **kwargs):
    update_status(job_id, "RUNNING")
    try:
        if args or kwargs:
            func(*args, **kwargs)
        else:
            func()
        update_status(job_id, "SUCCESS")
    except Exception as e:
        print(f"Task {job_id} failed: {e}")
        update_status(job_id, "FAILURE")

class IngestResponse(BaseModel):
    task_id: str
    status: str
    message: str

class JobStatus(BaseModel):
    id: str
    row_count: int
    last_updated: str | None

class GetStatusResponse(BaseModel):
    jobs: list[JobStatus]

@router.get("/status", response_model=GetStatusResponse)
async def get_ingest_status():
    from ingest.db import SessionLocal
    from sqlalchemy import text
    
    results = []
    queries = {
        "krx": "SELECT count(*) FROM security",
        "mapping": "SELECT count(*) FROM price_daily",
        "dart": "SELECT count(*) FROM dart_filing",
        "ecos": "SELECT count(*) FROM macro_series",
        "dart_financials": "SELECT count(*) FROM financial_statement"
    }
    
    with SessionLocal() as db:
        for job_id, sql in queries.items():
            try:
                count = db.execute(text(sql)).scalar()
                table_name = sql.split("FROM ")[1]
                last_time = db.execute(text(f"SELECT MAX(created_at) FROM {table_name}")).scalar()
                
                # Use TASK_STATUS if it's RUNNING, otherwise SUCCESS if data exists
                current_status = TASK_STATUS.get(job_id, "IDLE")
                if current_status == "IDLE" and last_time:
                    current_status = "SUCCESS"

                results.append(JobStatus(
                    id=job_id,
                    row_count=count,
                    last_updated=last_time.isoformat() if last_time else None,
                    status=current_status
                ))
            except Exception:
                results.append(JobStatus(id=job_id, row_count=0, last_updated=None, status="ERROR"))
                
    return GetStatusResponse(jobs=results)

@router.post("/trigger/{job_id}", response_model=IngestResponse)
async def trigger_ingest_job(job_id: str, background_tasks: BackgroundTasks):
    if job_id in ["krx_meta", "krx"]:
        background_tasks.add_task(wrapped_task, fetch_and_save_krx_list, "krx")
        return IngestResponse(task_id=job_id, status="accepted", message="KRX Meta Ingest started.")
    elif job_id in ["kis_prices", "kis_mapping", "mapping", "kis"]:
        background_tasks.add_task(wrapped_task, update_kis_prices_task, "mapping")
        return IngestResponse(task_id=job_id, status="accepted", message="KIS Price/Mapping Ingest started.")
    elif job_id in ["dart_filings", "dart"]:
        from ingest.dart_loader import fetch_and_save_dart_filings
        background_tasks.add_task(wrapped_task, fetch_and_save_dart_filings, "dart")
        return IngestResponse(task_id=job_id, status="accepted", message="DART Filings Ingest started.")
    elif job_id in ["ecos_series", "ecos"]:
        from ingest.ecos_loader import fetch_and_save_ecos_series
        background_tasks.add_task(wrapped_task, fetch_and_save_ecos_series, "ecos")
        return IngestResponse(task_id=job_id, status="accepted", message="ECOS Series Ingest started.")
    elif job_id in ["dart_financials"]:
        from ingest.dart_financials_loader import fetch_and_save_company_financials
        background_tasks.add_task(wrapped_task, fetch_and_save_company_financials, "dart_financials")
        return IngestResponse(task_id=job_id, status="accepted", message="DART Financials Ingest started.")
    else:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not implemented.")
