from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db import get_db
from ..schemas import ReportRequestCreate

router = APIRouter(tags=["Reports"])


@router.post("/reports", status_code=202)
def create_report(req: ReportRequestCreate, _user=Depends(get_current_user), _db: Session = Depends(get_db)):
    # TODO: 큐(Pub/Sub 또는 Tasks)에 리포트 생성 작업 enqueue
    return {
        "report_id": 1,
        "company_id": req.company_id,
        "template": req.template,
        "status": "PENDING",
        "created_at": "2026-01-08T10:00:00+09:00",
        "updated_at": "2026-01-08T10:00:00+09:00",
    }
