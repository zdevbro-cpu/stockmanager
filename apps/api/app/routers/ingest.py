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

TASK_PROGRESS = {
    "krx": {"processed": 0, "total": None},
    "mapping": {"processed": 0, "total": None},
    "dart": {"processed": 0, "total": None},
    "ecos": {"processed": 0, "total": None},
    "dart_financials": {"processed": 0, "total": None},
}

JOB_TABLES = {
    "krx": "security",
    "mapping": "price_daily",
    "dart": "dart_filing",
    "ecos": "macro_series",
    "dart_financials": "financial_statement"
}

def update_status(job_id: str, status: str):
    TASK_STATUS[job_id] = status

def update_progress(job_id: str, processed: int, total: int | None = None):
    current = TASK_PROGRESS.get(job_id, {"processed": 0, "total": None})
    if total is not None and processed > total:
        total = processed
    TASK_PROGRESS[job_id] = {
        "processed": processed,
        "total": total if total is not None else current.get("total"),
    }

def _insert_run_log(job_id: str, status: str) -> int | None:
    from ingest.db import SessionLocal
    from sqlalchemy import text

    def _ensure_table():
        with SessionLocal() as db:
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS ingest_run_log (
                  run_id      BIGSERIAL PRIMARY KEY,
                  job_id      TEXT NOT NULL,
                  status      TEXT NOT NULL,
                  started_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
                  finished_at TIMESTAMPTZ,
                  row_count   INTEGER,
                  message     TEXT,
                  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            """))
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_ingest_run_log_job_started
                ON ingest_run_log(job_id, started_at DESC)
            """))
            db.commit()

    try:
        with SessionLocal() as db:
            run_id = db.execute(
                text("""
                    INSERT INTO ingest_run_log (job_id, status, started_at)
                    VALUES (:job_id, :status, NOW())
                    RETURNING run_id
                """),
                {"job_id": job_id, "status": status}
            ).scalar()
            db.commit()
            return run_id
    except Exception as e:
        message = str(e)
        if "ingest_run_log" in message and ("does not exist" in message or "undefined" in message.lower()):
            try:
                _ensure_table()
                with SessionLocal() as db:
                    run_id = db.execute(
                        text("""
                            INSERT INTO ingest_run_log (job_id, status, started_at)
                            VALUES (:job_id, :status, NOW())
                            RETURNING run_id
                        """),
                        {"job_id": job_id, "status": status}
                    ).scalar()
                    db.commit()
                    return run_id
            except Exception as ensure_exc:
                print(f"Failed to create ingest_run_log: {ensure_exc}")
        print(f"Failed to insert ingest_run_log: {e}")
        return None

def _update_run_log(run_id: int | None, status: str, row_count: int | None = None, message: str | None = None):
    if run_id is None:
        return
    from ingest.db import SessionLocal
    from sqlalchemy import text

    try:
        with SessionLocal() as db:
            db.execute(
                text("""
                    UPDATE ingest_run_log
                    SET status = :status,
                        row_count = :row_count,
                        message = :message,
                        finished_at = NOW()
                    WHERE run_id = :run_id
                """),
                {
                    "status": status,
                    "row_count": row_count,
                    "message": message,
                    "run_id": run_id
                }
            )
            db.commit()
    except Exception as e:
        print(f"Failed to update ingest_run_log: {e}")

def _get_row_count(job_id: str) -> int | None:
    table = JOB_TABLES.get(job_id)
    if not table:
        return None
    from ingest.db import SessionLocal
    from sqlalchemy import text

    try:
        with SessionLocal() as db:
            return db.execute(text(f"SELECT count(*) FROM {table}")).scalar()
    except Exception as e:
        print(f"Failed to count rows for {job_id}: {e}")
        return None

def wrapped_task(func, job_id, *args, **kwargs):
    update_status(job_id, "RUNNING")
    update_progress(job_id, 0, None)
    run_id = _insert_run_log(job_id, "RUNNING")
    try:
        def progress_cb(processed: int, total: int | None = None):
            update_progress(job_id, processed, total)

        kwargs.setdefault("progress_cb", progress_cb)
        if args or kwargs:
            func(*args, **kwargs)
        else:
            func()
        update_status(job_id, "SUCCESS")
        progress = TASK_PROGRESS.get(job_id, {"processed": 0, "total": None})
        if progress.get("total"):
            update_progress(job_id, progress.get("total") or 0, progress.get("total"))
        row_count = _get_row_count(job_id)
        _update_run_log(run_id, "SUCCESS", row_count=row_count)
    except Exception as e:
        print(f"Task {job_id} failed: {e}")
        update_status(job_id, "FAILED")
        _update_run_log(run_id, "FAILED", message=str(e)[:500])

class IngestResponse(BaseModel):
    task_id: str
    status: str
    message: str

class JobStatus(BaseModel):
    id: str
    row_count: int
    last_updated: str | None
    status: str
    last_result_status: str | None = None
    is_running: bool = False
    message: str | None = None
    processed_count: int | None = None
    total_count: int | None = None

class GetStatusResponse(BaseModel):
    jobs: list[JobStatus]

@router.get("/status", response_model=GetStatusResponse)
def get_ingest_status():
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
    last_time_queries = {
        "krx": [
            "SELECT MAX(created_at) FROM security"
        ],
        "mapping": [
            "SELECT MAX(created_at) FROM price_daily",
            "SELECT MAX(trade_date) FROM price_daily"
        ],
        "dart": [
            "SELECT MAX(created_at) FROM dart_filing",
            "SELECT MAX(filing_date) FROM dart_filing"
        ],
        "ecos": [
            "SELECT MAX(created_at) FROM macro_series",
            "SELECT MAX(obs_date) FROM macro_series"
        ],
        "dart_financials": [
            "SELECT MAX(created_at) FROM financial_statement",
            "SELECT MAX(announced_at) FROM financial_statement"
        ]
    }
    
    with SessionLocal() as db:
        for job_id, sql in queries.items():
            count = None
            last_time = None
            try:
                count = db.execute(text(sql)).scalar()
            except Exception:
                results.append(JobStatus(id=job_id, row_count=0, last_updated=None, status="ERROR"))
                continue

            for last_sql in last_time_queries.get(job_id, []):
                try:
                    last_time = db.execute(text(last_sql)).scalar()
                    if last_time:
                        break
                except Exception:
                    continue

            last_run_status = None
            last_run_time = None
            last_run_message = None
            try:
                last_run = db.execute(
                    text("""
                        SELECT status, finished_at, started_at, message
                        FROM ingest_run_log
                        WHERE job_id = :job_id
                        ORDER BY started_at DESC
                        LIMIT 1
                    """),
                    {"job_id": job_id}
                ).fetchone()
                if last_run:
                    last_run_status = last_run[0]
                    last_run_time = last_run[1] or last_run[2]
                    last_run_message = last_run[3]
            except Exception:
                last_run = None

            # Use TASK_STATUS if it's RUNNING, otherwise last run status or SUCCESS if data exists
            current_status = TASK_STATUS.get(job_id, "IDLE")
            is_running = current_status == "RUNNING"
            last_result_status = None
            if last_run_status and last_run_status != "RUNNING":
                last_result_status = last_run_status
            elif last_time:
                last_result_status = "SUCCESS"
            else:
                last_result_status = "IDLE"

            if not is_running:
                current_status = last_result_status

            effective_last_time = last_run_time or last_time

            results.append(JobStatus(
                id=job_id,
                row_count=count or 0,
                last_updated=effective_last_time.isoformat() if effective_last_time else None,
                status=current_status,
                last_result_status=last_result_status,
                is_running=is_running,
                message=last_run_message,
                processed_count=TASK_PROGRESS.get(job_id, {}).get("processed") if is_running else None,
                total_count=TASK_PROGRESS.get(job_id, {}).get("total") if is_running else None,
            ))
                
    return GetStatusResponse(jobs=results)

@router.post("/trigger/{job_id}", response_model=IngestResponse)
def trigger_ingest_job(job_id: str, background_tasks: BackgroundTasks):

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
