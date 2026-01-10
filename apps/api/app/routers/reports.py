from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import datetime

from ..auth import get_current_user
from ..db import get_db
from ..schemas import ReportRequestCreate
from ..services.report_service import generate_ai_report

router = APIRouter(tags=["Reports"])


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
    stmt = text("SELECT company_id, status FROM report_request WHERE report_id = :rid")
    row = db.execute(stmt, {"rid": report_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    
    company_id, status = row
    if status != 'DONE':
        return {"id": report_id, "status": status, "company_id": company_id, "content": f"보고서 생성 중입니다... (현재 상태: {status})"}

    import os
    # Use absolute path to project root
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
    
    # Check for MD file first (new format - for preview)
    md_path = os.path.join(root_dir, "artifacts", "reports", f"report_{report_id}.md")
    if os.path.exists(md_path):
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"id": report_id, "status": status, "company_id": company_id, "content": content, "format": "markdown"}
    
    # Fallback: Check for DOCX file
    docx_path = os.path.join(root_dir, "artifacts", "reports", f"report_{report_id}.docx")
    if os.path.exists(docx_path):
        return {
            "id": report_id, 
            "status": status, 
            "company_id": company_id, 
            "content": "# 보고서 미리보기 불가\n\n이 보고서는 다운로드 전용 형식(DOCX)으로 생성되었습니다.\n\n우측 상단의 **다운로드 버튼**을 클릭하여 확인하세요.",
            "format": "docx"
        }
    
    return {"id": report_id, "status": status, "company_id": company_id, "content": "보고서 파일이 서버에 존재하지 않습니다.", "format": "none"}

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

    # 2. Enqueue AI generation task (It will create its own session)
    background_tasks.add_task(generate_ai_report, req.company_id, report_id)

    return {
        "report_id": report_id,
        "company_id": req.company_id,
        "template": req.template,
        "status": "PENDING",
        "message": "AI Report generation started in background."
    }
