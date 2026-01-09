from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import datetime

from ..auth import get_current_user
from ..db import get_db
from ..schemas import ReportRequestCreate
from ..services.report_service import generate_ai_report

router = APIRouter(tags=["Reports"])


@router.get("/reports")
def list_reports(db: Session = Depends(get_db)):
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
    stmt = text("SELECT company_id, status FROM report_request WHERE report_id = :rid")
    row = db.execute(stmt, {"rid": report_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    
    company_id, status = row
    if status != 'DONE':
        return {"id": report_id, "status": status, "content": f"보고서 생성 중입니다... (현재 상태: {status})"}

    import os
    # Use absolute path to project root
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
    file_path = os.path.join(root_dir, "artifacts", "reports", f"report_{report_id}.md")
    
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"id": report_id, "status": status, "content": content}
    
    return {"id": report_id, "status": status, "content": "보고서 파일이 서버에 존재하지 않습니다."}

@router.delete("/reports/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db)):
    # 1. Get info before delete
    stmt = text("SELECT company_id FROM report_request WHERE report_id = :rid")
    row = db.execute(stmt, {"rid": report_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # 2. Delete from DB
    db.execute(text("DELETE FROM report_request WHERE report_id = :rid"), {"rid": report_id})
    db.commit()

    # 3. Attempt to delete physical file
    import os
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
    file_path = os.path.join(root_dir, "artifacts", "reports", f"report_{report_id}.md")
    if os.path.exists(file_path):
        os.remove(file_path)
    
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

    # 2. Enqueue AI generation task
    background_tasks.add_task(generate_ai_report, db, req.company_id, report_id)

    return {
        "report_id": report_id,
        "company_id": req.company_id,
        "template": req.template,
        "status": "PENDING",
        "message": "AI Report generation started in background."
    }
