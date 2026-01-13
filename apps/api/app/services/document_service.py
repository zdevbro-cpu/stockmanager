import os
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List

def parse_and_chunk_document(db: Session, document_id: int):
    import fitz # PyMuPDF
    """
    Parse PDF/Doc content and split into chunks.
    Save chunks to document_chunk table.
    """
    # 1. Get Document Info
    doc_row = db.execute(text("SELECT file_path, file_type FROM document WHERE document_id = :did"), {"did": document_id}).fetchone()
    if not doc_row:
        raise Exception("Document not found")
    
    file_path, file_type = doc_row
    
    if not os.path.exists(file_path):
        raise Exception(f"File not found on disk: {file_path}")

    # 2. Extract Text
    full_text = ""
    try:
        if 'pdf' in file_type.lower():
            with fitz.open(file_path) as doc:
                for page in doc:
                    full_text += page.get_text() + "\n"
        else:
            # Simple text fallback (TODO: Add support for docx using python-docx)
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                full_text = f.read()
    except Exception as e:
        raise Exception(f"Failed to extract text: {e}")

    # 3. Chunking (Simple Character Split with Overlap)
    CHUNK_SIZE = 1000
    OVERLAP = 100
    
    chunks = []
    text_len = len(full_text)
    start = 0
    
    while start < text_len:
        end = min(start + CHUNK_SIZE, text_len)
        chunk_text = full_text[start:end]
        chunks.append(chunk_text)
        
        if end == text_len:
            break
            
        start += (CHUNK_SIZE - OVERLAP)

    # 4. Save to DB
    # Clear existing chunks first (re-parse scenario)
    db.execute(text("DELETE FROM document_chunk WHERE document_id = :did"), {"did": document_id})
    
    for idx, chunk in enumerate(chunks):
        # Calculate approximate token count (simple whitespace split)
        token_count = len(chunk.split())
        
        db.execute(text("""
            INSERT INTO document_chunk (document_id, chunk_no, content_text, token_count)
            VALUES (:did, :no, :content, :tokens)
        """), {
            "did": document_id, 
            "no": idx + 1, 
            "content": chunk, 
            "tokens": token_count
        })
    
    db.commit()
    
    return len(chunks)
