import hashlib
import os
import sys

from sqlalchemy import text

from ingest.db import SessionLocal


def _load_scrapers():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    sys.path.append(os.path.join(repo_root, "apps/api"))
    from app.services import scrapers
    return scrapers


def backfill_company_sectors():
    scrapers = _load_scrapers()
    industries = scrapers.get_naver_industries()
    if not industries:
        print("No industries found from Naver.")
        return

    ticker_to_industry: dict[str, str] = {}
    for industry in industries:
        name = industry.get("name")
        link = industry.get("link")
        if not name or not link:
            continue
        members = scrapers.get_naver_industry_members(link)
        for ticker in members:
            ticker_to_industry.setdefault(ticker, name)

    if not ticker_to_industry:
        print("No industry members found from Naver.")
        return

    updated = 0
    with SessionLocal() as db:
        for ticker, name in ticker_to_industry.items():
            digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:10]
            sector_code = f"NAVER_SECTOR_{digest}"
            result = db.execute(
                text("""
                    UPDATE company
                    SET sector_name = :name,
                        sector_code = COALESCE(sector_code, :code),
                        updated_at = NOW()
                    WHERE stock_code = :ticker
                """),
                {"name": name, "code": sector_code, "ticker": ticker},
            )
            if result.rowcount:
                updated += result.rowcount
        db.commit()

    print(f"Updated sector info for {updated} companies.")


if __name__ == "__main__":
    backfill_company_sectors()
