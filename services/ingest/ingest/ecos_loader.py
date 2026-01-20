import requests
from sqlalchemy import text
from ingest.config import settings
from ingest.db import SessionLocal
from datetime import date
import calendar
import hashlib
import re

def _parse_ecos_time(time_str: str) -> date | None:
    if not time_str:
        return None
    time_str = time_str.strip()
    try:
        if "Q" in time_str:
            year = int(time_str[:4])
            quarter = int(time_str[-1])
            month = quarter * 3
            day = calendar.monthrange(year, month)[1]
            return date(year, month, day)
        if len(time_str) == 8:
            return date(int(time_str[:4]), int(time_str[4:6]), int(time_str[6:8]))
        if len(time_str) == 6:
            return date(int(time_str[:4]), int(time_str[4:6]), 1)
        if len(time_str) == 4:
            return date(int(time_str[:4]), 1, 1)
    except Exception:
        return None
    return None


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def _build_series_code(row: dict) -> str:
    stat_code = row.get("STAT_CODE")
    item_code1 = row.get("ITEM_CODE1")
    item_code2 = row.get("ITEM_CODE2")

    # Keep base rate as a dedicated series_code for compatibility
    if stat_code == "722Y001" and item_code1 == "0101000":
        return item_code1

    parts = [p for p in [stat_code, item_code1, item_code2] if p]
    if parts:
        return ":".join(parts)

    key_name = row.get("KEYSTAT_NAME") or ""
    class_name = row.get("CLASS_NAME") or ""

    # Keep base rate as a dedicated series_code for compatibility
    if "기준금리" in key_name:
        return "0101000"

    raw = f"{class_name}-{key_name}".strip("-")
    slug = _slugify(raw)
    if slug:
        return f"key_{slug}"
    digest = hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()[:12]
    return f"key_{digest}"


def _fetch_key_statistics(api_key: str, page_size: int = 1000):
    start = 1
    while True:
        end = start + page_size - 1
        url = f"http://ecos.bok.or.kr/api/KeyStatisticList/{api_key}/json/kr/{start}/{end}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if resp.status_code != 200 or "KeyStatisticList" not in data:
            error_msg = data.get("RESULT", {}).get("MESSAGE") or data
            raise RuntimeError(f"ECOS API Error: {error_msg}")

        rows = data["KeyStatisticList"].get("row", [])
        if not rows:
            break

        yield rows

        if len(rows) < page_size:
            break
        start += page_size


def fetch_and_save_ecos_series(limit: int | None = None, progress_cb=None):
    """
    Fetch key economic indicators from BOK ECOS KeyStatisticList.
    REAL API ONLY.
    """
    api_key = settings.ECOS_API_KEY
    print(f"Starting REAL ECOS KeyStatisticList Ingest (Key: {api_key})...", flush=True)

    with SessionLocal() as db:
        try:
            count = 0
            for rows in _fetch_key_statistics(api_key):
                for row in rows:
                    if not row.get("DATA_VALUE"):
                        continue
                    obs_date = _parse_ecos_time(row.get("CYCLE", "") or row.get("TIME", ""))
                    if not obs_date:
                        continue
                    series_code = _build_series_code(row)
                    unit = row.get("UNIT_NAME")
                    db.execute(text("""
                        INSERT INTO macro_series (series_code, obs_date, value, unit, created_at)
                        VALUES (:sc, :od, :v, :u, NOW())
                        ON CONFLICT (series_code, obs_date)
                        DO UPDATE SET value = EXCLUDED.value, unit = EXCLUDED.unit
                    """), {
                        "sc": series_code,
                        "od": obs_date,
                        "v": float(row["DATA_VALUE"]),
                        "u": unit
                    })
                    count += 1
                    if progress_cb and count % 100 == 0:
                        progress_cb(count, None)
                    if limit and count >= limit:
                        break
                if limit and count >= limit:
                    break

            db.commit()
            if progress_cb:
                progress_cb(count, None)
            print(f"Successfully saved {count} records from ECOS.")
        except Exception as e:
            print(f"ECOS Ingest Failed: {e}")
            db.rollback()
        finally:
            db.close()
