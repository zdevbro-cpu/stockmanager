from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
import os
import shutil
import hashlib
from datetime import datetime

from ..db import get_db

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    responses={404: {"description": "Not found"}},
)

UPLOAD_DIR = os.path.join(os.getcwd(), "artifacts", "uploads", "documents")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_document(
    company_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a document (PDF, etc.) for a specific company.
    This saves the file and creates a DB record.
    """
    try:
        # 1. Validate Company Exists
        company = db.execute(text("SELECT company_id FROM company WHERE company_id = :cid"), {"cid": company_id}).fetchone()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        # 2. File Save
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ['.pdf', '.txt', '.docx', '.pptx']:
             raise HTTPException(status_code=400, detail="Unsupported file format")

        # Create unique filename: {company_id}_{timestamp}_{original_name}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{company_id}_{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        
        # Calculate SHA256 while saving
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "wb") as buffer:
            while content := await file.read(1024 * 1024): # 1MB chunk
                sha256_hash.update(content)
                buffer.write(content)
                
        file_hash = sha256_hash.hexdigest()
        
        # 3. DB Insert
        # Check duplicate by hash? (Optional)
        
        sql = text("""
            INSERT INTO document (company_id, source_type, source_ref, file_path, file_type, sha256)
            VALUES (:cid, 'UPLOAD', :fname, :fpath, :ftype, :fhash)
            RETURNING document_id
        """)
        
        result = db.execute(sql, {
            "cid": company_id,
            "fname": file.filename,
            "fpath": file_path,
            "ftype": file_ext.replace('.', ''),
            "fhash": file_hash
        })
        db.commit()
        
        doc_id = result.scalar()
        
        return {
            "status": "success",
            "document_id": doc_id,
            "filename": file.filename,
            "message": "File uploaded successfully"
        }

    except Exception as e:
        print(f"Upload failed: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{company_id}")
def list_documents(company_id: int, db: Session = Depends(get_db)):
    """
    List uploaded documents for a company
    """
    documents = db.execute(text("""
        SELECT document_id, source_type, source_ref, file_type, created_at, file_path
        FROM document
        WHERE company_id = :cid
        ORDER BY created_at DESC
    """), {"cid": company_id}).fetchall()
    
    result = []
    for row in documents:
        result.append({
            "id": row.document_id,
            "type": row.source_type,
            "filename": row.source_ref,
            "ext": row.file_type,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "has_chunks": False # To be implemented
        })
        
    return result

from ..services.document_service import parse_and_chunk_document

@router.post("/{document_id}/parse")
def parse_document(document_id: int, db: Session = Depends(get_db)):
    """
    Trigger parsing (chunking) of a document.
    """
    try:
        chunk_count = parse_and_chunk_document(db, document_id)
        return {
            "status": "success", 
            "message": f"Document parsed into {chunk_count} chunks",
            "chunk_count": chunk_count
        }
    except Exception as e:
        print(f"Parsing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
