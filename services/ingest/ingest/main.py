"""Ingest entrypoint"""
import argparse
from datetime import date
from sqlalchemy import text
from ingest.db import get_db
from ingest.kis_client import KisClient

from ingest.krx_loader import fetch_and_save_krx_list
from ingest.kis_loader import update_kis_prices_task

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--task", required=True, choices=["kis_prices", "kis_prices_all", "krx_meta", "dart_filings", "ecos_series", "dart_financials", "naver_industries"])
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--batch", type=int, default=500)
    p.add_argument("--from", dest="date_from")
    p.add_argument("--to", dest="date_to")
    args = p.parse_args()

    print(f"Running Task: {args.task}")
    
    if args.task == "kis_prices":
        update_kis_prices_task(limit=args.limit, offset=args.offset)
    elif args.task == "kis_prices_all":
        from sqlalchemy import text
        import time
        from ingest.db import SessionLocal
        from ingest.kis_client import KisClient

        with SessionLocal() as db:
            total = db.execute(text("SELECT COUNT(*) FROM security")).scalar() or 0
        batch = args.batch or 500
        kis = KisClient()
        for offset in range(0, total, batch):
            update_kis_prices_task(limit=batch, offset=offset, kis=kis)
            time.sleep(0.5)
    elif args.task == "krx_meta":
        fetch_and_save_krx_list()
    elif args.task == "dart_filings":
        from ingest.dart_loader import fetch_and_save_dart_filings
        fetch_and_save_dart_filings()
    elif args.task == "dart_financials":
        from ingest.dart_financials_loader import fetch_and_save_company_financials
        fetch_and_save_company_financials()
    elif args.task == "ecos_series":
        from ingest.ecos_loader import fetch_and_save_ecos_series
        fetch_and_save_ecos_series()
    elif args.task == "naver_industries":
        from ingest.naver_industry_backfill import backfill_company_sectors
        backfill_company_sectors()
    else:
        print(f"Unknown task: {args.task}")

if __name__ == "__main__":
    main()
