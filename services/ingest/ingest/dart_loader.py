import requests
from sqlalchemy import text
from ingest.config import settings
from ingest.db import SessionLocal
from datetime import date, timedelta
import time


from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def _get_dart_session():
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session

def _iter_date_ranges(start: date, end: date, window_days: int = 90):
    current = start
    while current <= end:
        chunk_end = min(end, current + timedelta(days=window_days - 1))
        yield current, chunk_end
        current = chunk_end + timedelta(days=1)

def fetch_and_save_dart_filings(days: int = 180, progress_cb=None):
    """
    Fetch recent filings from OpenDART. 
    REAL API ONLY. Fails if credentials or network is invalid.
    """
    api_key = settings.DART_API_KEY
    if not api_key:
        print("DART_API_KEY is missing in settings/env.")
        return

    print("Starting REAL DART Filings Ingest...")
    
    with SessionLocal() as db:
        try:
            # Load filings across a wider window to cover more companies.
            start_date = date.today() - timedelta(days=days)
            end_date = date.today()
            url = "https://opendart.fss.or.kr/api/list.json"
            count = 0
            total_est = 0
            session = _get_dart_session()
            for chunk_start, chunk_end in _iter_date_ranges(start_date, end_date, window_days=90):
                bgn_de = chunk_start.strftime("%Y%m%d")
                end_de = chunk_end.strftime("%Y%m%d")
                page_no = 1
                while True:
                    params = {
                        "crtfc_key": api_key,
                        "bgn_de": bgn_de,
                        "end_de": end_de,
                        "page_count": 100,
                        "page_no": page_no,
                    }

                    try:
                        resp = session.get(url, params=params, timeout=30)
                    except requests.exceptions.RequestException as re:
                        print(f"DART Request Failed (Connection/Timeout): {re}")
                        time.sleep(2)
                        break
                    data = resp.json()

                    if resp.status_code != 200 or data.get("status") != "000":
                        print(f"DART API Error: {data.get('message')} (Code: {data.get('status')})")
                        break

                    list_data = data.get("list", [])
                    if page_no == 1:
                        raw_total = data.get("total_count", 0)
                        try:
                            total_est += int(str(raw_total).replace(",", ""))
                        except (TypeError, ValueError):
                            total_est += 0
                        if total_est and count > total_est:
                            total_est = count
                        if progress_cb:
                            progress_cb(count, total_est if total_est > 0 else None)
                    if not list_data:
                        if page_no == 1:
                            print(f"No filings found for {bgn_de}~{end_de}.")
                        break

                    for item in list_data:
                        if count == 0:
                            print(f"Sample item keys: {item.keys()}")

                        stmt = text("""
                            INSERT INTO dart_filing (rcp_no, corp_code, filing_date, filing_type, title, created_at)
                            VALUES (:rno, :cc, :d, :typ, :title, NOW())
                            ON CONFLICT (rcp_no) DO UPDATE SET title = EXCLUDED.title
                        """)

                        rdt = item.get('rcept_dt')
                        f_date = date(int(rdt[:4]), int(rdt[4:6]), int(rdt[6:8])) if rdt else date.today()

                        db.execute(stmt, {
                            "rno": item.get('rcept_no'),
                            "cc": item.get('corp_code'),
                            "d": f_date,
                            "typ": item.get('pblntf_ty', '-'),
                            "title": item.get('report_nm')
                        })
                        count += 1
                    db.commit()
                    if total_est and count > total_est:
                        total_est = count
                    if progress_cb:
                        progress_cb(count, total_est if total_est > 0 else None)
                    page_no += 1
                    time.sleep(0.2)

            print(f"Successfully saved {count} filings from DART.")
                
        except Exception as e:
            print(f"DART Ingest Failed: {e}")
            db.rollback()
        finally:
            db.close()


def fetch_and_save_dart_filings_for_corp(corp_code: str, days: int = 1095) -> int:
    """
    Fetch filings for a specific company from OpenDART across a given window.
    Returns processed count.
    """
    api_key = settings.DART_API_KEY
    if not api_key:
        print("DART_API_KEY is missing in settings/env.")
        return 0

    print(f"Starting DART Filings Backfill for {corp_code} ({days} days)...")

    with SessionLocal() as db:
        try:
            bgn_de = (date.today() - timedelta(days=days)).strftime("%Y%m%d")
            end_de = date.today().strftime("%Y%m%d")
            url = "https://opendart.fss.or.kr/api/list.json"
            count = 0
            page_no = 1

            session = _get_dart_session()
            while True:
                params = {
                    "crtfc_key": api_key,
                    "corp_code": corp_code,
                    "bgn_de": bgn_de,
                    "end_de": end_de,
                    "page_count": 100,
                    "page_no": page_no,
                }

                try:
                    resp = session.get(url, params=params, timeout=30)
                except requests.exceptions.RequestException as re:
                    print(f"DART Request Failed: {re}")
                    break
                data = resp.json()

                if resp.status_code != 200 or data.get("status") != "000":
                    print(f"DART API Error: {data.get('message')} (Code: {data.get('status')})")
                    break

                list_data = data.get("list", [])
                if not list_data:
                    break

                for item in list_data:
                    stmt = text("""
                        INSERT INTO dart_filing (rcp_no, corp_code, filing_date, filing_type, title, created_at)
                        VALUES (:rno, :cc, :d, :typ, :title, NOW())
                        ON CONFLICT (rcp_no) DO UPDATE SET title = EXCLUDED.title
                    """)

                    rdt = item.get('rcept_dt')
                    f_date = date(int(rdt[:4]), int(rdt[4:6]), int(rdt[6:8])) if rdt else date.today()

                    db.execute(stmt, {
                        "rno": item.get('rcept_no'),
                        "cc": item.get('corp_code'),
                        "d": f_date,
                        "typ": item.get('pblntf_ty', '-'),
                        "title": item.get('report_nm')
                    })
                    count += 1

                db.commit()
                page_no += 1
                time.sleep(0.2)

            print(f"Finished DART Filings Backfill for {corp_code}. Count={count}")
            return count
        except Exception as e:
            print(f"DART Backfill Failed: {e}")
            db.rollback()
            raise
        finally:
            db.close()
