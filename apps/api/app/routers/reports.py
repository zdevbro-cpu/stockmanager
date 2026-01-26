from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import datetime
import os
import sys
import threading

from ..auth import get_current_user
from ..db import get_db
from ..schemas import ReportRequestCreate
from ..services.report_service import generate_ai_report

router = APIRouter(tags=["Reports"])

INGEST_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../services/ingest"))
if INGEST_PATH not in sys.path:
    sys.path.append(INGEST_PATH)

def _ensure_ingest_run_log(db: Session) -> None:
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS ingest_run_log (
          run_id      BIGSERIAL PRIMARY KEY,
          job_id      TEXT NOT NULL,
          status      TEXT NOT NULL,
          started_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
          finished_at TIMESTAMPTZ,
          row_count   INTEGER,
          total_count INTEGER,
          message     TEXT,
          created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """))
    db.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_ingest_run_log_job_started
        ON ingest_run_log(job_id, started_at DESC)
    """))
    db.execute(text("""
        ALTER TABLE ingest_run_log
        ADD COLUMN IF NOT EXISTS total_count INTEGER
    """))
    db.commit()

def _resolve_corp_code(db: Session, company_id: int) -> str | None:
    row = db.execute(
        text("SELECT corp_code, stock_code, name_ko FROM company WHERE company_id = :cid"),
        {"cid": company_id},
    ).fetchone()
    if not row:
        return None
    corp_code, stock_code, name_ko = row
    if corp_code:
        return corp_code
    if stock_code:
        if stock_code.endswith("5"):
            base_code = f"{stock_code[:-1]}0"
            base = db.execute(
                text("SELECT corp_code FROM company WHERE stock_code = :sc AND corp_code IS NOT NULL"),
                {"sc": base_code},
            ).fetchone()
            if base and base[0]:
                return base[0]
    if name_ko and name_ko.endswith("우"):
        base_name = name_ko[:-1]
        base = db.execute(
            text("SELECT corp_code FROM company WHERE name_ko = :name AND corp_code IS NOT NULL"),
            {"name": base_name},
        ).fetchone()
        if base and base[0]:
            return base[0]
    return None


from fastapi import Response

@router.get("/reports")
def list_reports(response: Response, db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    stmt = text("""
        SELECT r.report_id, r.company_id, c.name_ko as company_name, r.template, r.status, r.created_at 
        FROM report_request r
        JOIN company c ON r.company_id = c.company_id
        ORDER BY r.created_at DESC
    """)
    rows = db.execute(stmt).fetchall()
    return [
        {
            "id": r.report_id,
            "company_name": r.company_name,
            "template": r.template,
            "status": r.status,
            "created_at": r.created_at.isoformat()
        } for r in rows
    ]

@router.get("/reports/{report_id}")
def get_report_content(report_id: int, db: Session = Depends(get_db)):
    stmt = text("SELECT company_id, status, created_at FROM report_request WHERE report_id = :rid")
    row = db.execute(stmt, {"rid": report_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    
    company_id, status, created_at = row
    import os
    # Use absolute path to project root
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
    md_path = os.path.join(root_dir, "artifacts", "reports", f"report_{report_id}.md")
    docx_path = os.path.join(root_dir, "artifacts", "reports", f"report_{report_id}.docx")

    def _artifact_is_fresh(path: str) -> bool:
        if not os.path.exists(path):
            return False
        if created_at:
            try:
                mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path), tz=created_at.tzinfo)
                if mtime < (created_at - datetime.timedelta(seconds=5)):
                    return False
            except Exception:
                return False
        return True

    # If status didn't update but artifacts exist, treat as DONE.
    if status != 'DONE':
        if _artifact_is_fresh(md_path) or _artifact_is_fresh(docx_path):
            db.execute(text("UPDATE report_request SET status = 'DONE' WHERE report_id = :rid"), {"rid": report_id})
            db.commit()
            status = 'DONE'
        else:
            return {
                "id": report_id,
                "status": status,
                "company_id": company_id,
                "content": f"보고서 생성 중입니다... (현재 상태: {status})"
            }
    
    # Check for MD file first (new format - for preview)
    if os.path.exists(md_path):
        try:
            if created_at:
                mtime = datetime.datetime.fromtimestamp(os.path.getmtime(md_path), tz=created_at.tzinfo)
                if mtime < (created_at - datetime.timedelta(seconds=5)):
                    return {
                        "id": report_id,
                        "status": status,
                        "company_id": company_id,
                        "content": "보고서 파일이 최신 상태가 아닙니다. 다시 생성해 주세요.",
                        "format": "none"
                    }
        except Exception:
            pass
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()

        if "부록: 최근 공시 50건" not in content:
            corp_code = _resolve_corp_code(db, company_id)
            if corp_code:
                dart_rows = db.execute(
                    text("""
                        SELECT filing_date, filing_type, title, rcp_no
                        FROM dart_filing
                        WHERE corp_code = :cc
                        ORDER BY filing_date DESC
                        LIMIT 50
                    """),
                    {"cc": corp_code},
                ).fetchall()
                if not dart_rows:
                    try:
                        from ingest.dart_loader import fetch_and_save_dart_filings_for_corp
                        fetch_and_save_dart_filings_for_corp(corp_code, days=1095)
                        dart_rows = db.execute(
                            text("""
                                SELECT filing_date, filing_type, title, rcp_no
                                FROM dart_filing
                                WHERE corp_code = :cc
                                ORDER BY filing_date DESC
                                LIMIT 50
                            """),
                            {"cc": corp_code},
                        ).fetchall()
                    except Exception as exc:
                        print(f"DART filings fetch failed: {exc}")
                if dart_rows:
                    lines = []
                    for row in dart_rows:
                        filing_date = str(row.filing_date) if row.filing_date else "-"
                        filing_type = row.filing_type or "-"
                        title = row.title or "-"
                        rcp_no = row.rcp_no or "-"
                        lines.append(f"- {filing_date} [{filing_type}] {title} (rcp_no: {rcp_no})")
                    appendix = f"## 부록: 최근 공시 50건\n" + "\n".join(lines)
                else:
                    appendix = "## 부록: 최근 공시 50건\n공시 데이터가 없습니다."
                content = f"{content}\n\n{appendix}"

        return {"id": report_id, "status": status, "company_id": company_id, "content": content, "format": "markdown"}
    
    # Fallback: Check for DOCX file
    if os.path.exists(docx_path):
        try:
            if created_at:
                mtime = datetime.datetime.fromtimestamp(os.path.getmtime(docx_path), tz=created_at.tzinfo)
                if mtime < (created_at - datetime.timedelta(seconds=5)):
                    return {
                        "id": report_id,
                        "status": status,
                        "company_id": company_id,
                        "content": "보고서 파일이 최신 상태가 아닙니다. 다시 생성해 주세요.",
                        "format": "none"
                    }
        except Exception:
            pass
        return {
            "id": report_id, 
            "status": status, 
            "company_id": company_id, 
            "content": "# 보고서 미리보기 불가\n\n이 보고서는 다운로드 전용 형식(DOCX)으로 생성되었습니다.\n\n우측 상단의 **다운로드 버튼**을 클릭해 확인해 주세요.",
            "format": "docx"
        }
    
    return {
        "id": report_id,
        "status": status,
        "company_id": company_id,
        "content": "보고서 파일이 서버에 존재하지 않습니다.",
        "format": "none"
    }

@router.get("/reports/{report_id}/download")
def download_report(report_id: int, db: Session = Depends(get_db)):
    """Download DOCX report file"""
    from fastapi.responses import FileResponse
    import os
    
    # Check if report exists
    stmt = text("SELECT status FROM report_request WHERE report_id = :rid")
    row = db.execute(stmt, {"rid": report_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    
    status = row[0]
    if status != 'DONE':
        raise HTTPException(status_code=400, detail=f"Report not ready. Current status: {status}")
    
    # Find DOCX file
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
    file_path = os.path.join(root_dir, "artifacts", "reports", f"report_{report_id}.docx")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report file not found on server")
    
    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"investment_report_{report_id}.docx"
    )

@router.delete("/reports/{report_id}")
def delete_report(report_id: int, _user=Depends(get_current_user), db: Session = Depends(get_db)):
    # 1. Get info before delete
    stmt = text("SELECT company_id FROM report_request WHERE report_id = :rid")
    row = db.execute(stmt, {"rid": report_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # 2. Delete dependents (artifacts) first to satisfy FK constraints
    db.execute(text("DELETE FROM report_artifact WHERE report_id = :rid"), {"rid": report_id})
    
    # 3. Delete from DB
    db.execute(text("DELETE FROM report_request WHERE report_id = :rid"), {"rid": report_id})
    db.commit()

    # 4. Attempt to delete physical files (both DOCX and MD)
    import os
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
    
    # Try to delete DOCX file
    docx_path = os.path.join(root_dir, "artifacts", "reports", f"report_{report_id}.docx")
    try:
        if os.path.exists(docx_path):
            os.remove(docx_path)
            print(f"Deleted DOCX file: {docx_path}")
    except Exception as e:
        print(f"DOCX file deletion failed: {e}")
    
    # Try to delete MD file (legacy)
    md_path = os.path.join(root_dir, "artifacts", "reports", f"report_{report_id}.md")
    try:
        if os.path.exists(md_path):
            os.remove(md_path)
            print(f"Deleted MD file: {md_path}")
    except Exception as e:
        print(f"MD file deletion failed: {e}")
    
    return {"message": "Report deleted successfully"}

@router.post("/reports", status_code=202)
def create_report(req: ReportRequestCreate, background_tasks: BackgroundTasks, _user=Depends(get_current_user), db: Session = Depends(get_db)):
    import datetime
    # 1. Insert report request into DB
    stmt = text("""
        INSERT INTO report_request (company_id, template, as_of_date, status, created_at, updated_at)
        VALUES (:cid, :tmp, :ad, 'PENDING', NOW(), NOW())
        RETURNING report_id
    """)
    result = db.execute(stmt, {
        "cid": req.company_id,
        "tmp": req.template,
        "ad": req.as_of_date or datetime.date.today().isoformat()
    })
    report_id = result.fetchone()[0]
    db.commit()

    # 2. Enqueue AI generation task (detach from request lifecycle)
    thread = threading.Thread(target=generate_ai_report, args=(req.company_id, report_id), daemon=True)
    thread.start()

    return {
        "report_id": report_id,
        "company_id": req.company_id,
        "template": req.template,
        "status": "PENDING",
        "message": "AI Report generation started in background."
    }


@router.post("/reports/dart-backfill")
def trigger_dart_backfill(company_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT name_ko FROM company WHERE company_id = :cid"),
        {"cid": company_id},
    ).fetchone()
    corp_code = _resolve_corp_code(db, company_id)
    if not row or not corp_code:
        raise HTTPException(status_code=404, detail="corp_code not found for company")

    name_ko = row[0]
    job_id = f"dart_backfill:{corp_code}"
    _ensure_ingest_run_log(db)
    run_id = db.execute(
        text("""
            INSERT INTO ingest_run_log (job_id, status, started_at)
            VALUES (:job_id, 'RUNNING', NOW())
            RETURNING run_id
        """),
        {"job_id": job_id},
    ).scalar()
    db.commit()

    def run_task():
        from ingest.dart_loader import fetch_and_save_dart_filings_for_corp
        from ..db import SessionLocal
        def update_progress(processed: int, total: int | None):
            with SessionLocal() as task_db:
                task_db.execute(
                    text("""
                        UPDATE ingest_run_log
                        SET row_count = :processed, total_count = :total
                        WHERE run_id = :run_id
                    """),
                    {"processed": processed, "total": total, "run_id": run_id},
                )
                task_db.commit()
        try:
            count = fetch_and_save_dart_filings_for_corp(corp_code, days=1095, progress_cb=update_progress)
            with SessionLocal() as task_db:
                task_db.execute(
                    text("""
                        UPDATE ingest_run_log
                        SET status = 'SUCCESS', row_count = :cnt, finished_at = NOW()
                        WHERE run_id = :run_id
                    """),
                    {"cnt": count, "run_id": run_id},
                )
                task_db.commit()
        except Exception as exc:
            with SessionLocal() as task_db:
                task_db.execute(
                    text("""
                        UPDATE ingest_run_log
                        SET status = 'FAILED', message = :msg, finished_at = NOW()
                        WHERE run_id = :run_id
                    """),
                    {"msg": str(exc)[:500], "run_id": run_id},
                )
                task_db.commit()

    background_tasks.add_task(run_task)
    return {"status": "accepted", "job_id": job_id, "company_id": company_id, "company_name": name_ko}


@router.get("/reports/dart-backfill/status")
def get_dart_backfill_status(company_id: int, db: Session = Depends(get_db)):
    corp_code = _resolve_corp_code(db, company_id)
    if not corp_code:
        raise HTTPException(status_code=404, detail="corp_code not found for company")
    job_id = f"dart_backfill:{corp_code}"
    _ensure_ingest_run_log(db)
    last_run = db.execute(
        text("""
            SELECT status, started_at, finished_at, message, row_count, total_count
            FROM ingest_run_log
            WHERE job_id = :job_id
            ORDER BY started_at DESC
            LIMIT 1
        """),
        {"job_id": job_id},
    ).fetchone()
    if not last_run:
        return {"status": "IDLE", "job_id": job_id}

    status, started_at, finished_at, message, row_count, total_count = last_run
    if status == "RUNNING" and started_at and finished_at is None:
        now = datetime.datetime.now(started_at.tzinfo)
        if now - started_at > datetime.timedelta(minutes=30):
            message = "?묒뾽??30遺??댁긽 吏?띾릺??以묒???寃껋쑝濡??먮떒?섏뿀?듬땲??"
            db.execute(
                text("""
                    UPDATE ingest_run_log
                    SET status = 'FAILED', message = :msg, finished_at = :finished_at
                    WHERE job_id = :job_id AND started_at = :started_at
                """),
                {
                    "msg": message,
                    "finished_at": now,
                    "job_id": job_id,
                    "started_at": started_at,
                },
            )
            db.commit()
            status = "FAILED"
            finished_at = now
    return {
        "status": status,
        "job_id": job_id,
        "started_at": started_at.isoformat() if started_at else None,
        "finished_at": finished_at.isoformat() if finished_at else None,
        "message": message,
        "processed": row_count,
        "total": total_count,
    }

