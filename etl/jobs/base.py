import sys
import os

# Add services/ingest to path to reuse existing DB logic
INGEST_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../services/ingest"))
if INGEST_PATH not in sys.path:
    sys.path.append(INGEST_PATH)
    
from ingest.db import SessionLocal
from ingest.config import settings
from sqlalchemy import text
