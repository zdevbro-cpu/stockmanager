from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from datetime import datetime
import json
import time
from sqlalchemy import text
import sys
import os
import requests
import re

# Create path to services
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../../services/ingest"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../services")) # For scrapers

from ingest.kis_client import KisClient
from app.services import scrapers
import FinanceDataReader as fdr
from ..db import get_db, SessionLocal
from sqlalchemy.orm import Session
from ..config import settings

router = APIRouter(tags=["Market"])

kis = KisClient()

_POPULAR_CACHE: list[dict] | None = None
_POPULAR_CACHE_AT: float | None = None
_POPULAR_ALL_CACHE: list[dict] | None = None
_POPULAR_ALL_CACHE_AT: float | None = None
_BREADTH_CACHE: dict | None = None
_BREADTH_CACHE_AT: float | None = None
_BREADTH_REFRESHING: bool = False
_BREADTH_TABLE_READY: bool = False
_INDICES_CACHE: list[dict] | None = None
_INDICES_CACHE_AT: float | None = None
_INDICES_REFRESHING: bool = False
_INDICES_TABLE_READY: bool = False
_POPULAR_TABLE_READY: bool = False


def _ensure_breadth_table(db: Session) -> None:
    global _BREADTH_TABLE_READY
    if _BREADTH_TABLE_READY:
        return
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS market_breadth_snapshot (
            as_of_date DATE NOT NULL,
            up INTEGER NOT NULL,
            down INTEGER NOT NULL,
            flat INTEGER NOT NULL,
            program_net_krw BIGINT,
            arbitrage_net_krw BIGINT,
            non_arbitrage_net_krw BIGINT,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    db.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_market_breadth_snapshot_updated
        ON market_breadth_snapshot(updated_at DESC)
    """))
    db.commit()
    _BREADTH_TABLE_READY = True


def _ensure_indices_table(db: Session) -> None:
    global _INDICES_TABLE_READY
    if _INDICES_TABLE_READY:
        return
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS market_index_snapshot (
            payload JSONB NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    db.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_market_index_snapshot_updated
        ON market_index_snapshot(updated_at DESC)
    """))
    db.commit()
    _INDICES_TABLE_READY = True


def _ensure_popular_table(db: Session) -> None:
    global _POPULAR_TABLE_READY
    if _POPULAR_TABLE_READY:
        return
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS market_popular_snapshot (
            payload JSONB NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    db.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_market_popular_snapshot_updated
        ON market_popular_snapshot(updated_at DESC)
    """))
    db.commit()
    _POPULAR_TABLE_READY = True


def _load_latest_snapshot(db: Session, table: str):
    row = db.execute(text(f"""
        SELECT payload, updated_at
        FROM {table}
        ORDER BY updated_at DESC
        LIMIT 1
    """)).fetchone()
    if not row:
        return None, None
    return row.payload, row.updated_at


def _save_snapshot(db: Session, table: str, payload) -> None:
    db.execute(text(f"""
        INSERT INTO {table} (payload, updated_at)
        VALUES (CAST(:payload AS jsonb), NOW())
    """), {"payload": json.dumps(payload, ensure_ascii=False)})
    db.commit()


def _to_int(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text_value = str(value).strip().replace(",", "")
    if not text_value:
        return None
    try:
        return int(float(text_value))
    except ValueError:
        return None


def _format_krw_100m(value):
    if value is None:
        return None
    abs_value = abs(value)
    if abs_value >= 100000000:
        amount = value / 100000000
    elif abs_value >= 100:
        amount = value / 100
    else:
        amount = value
    return f"{amount:+,.0f}억"


def _pick_value(row, keys):
    if not row:
        return None
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return _to_int(row[key])
    return None


def _pick_value_by_hint(row, include_hints, exclude_hints=None):
    if not row:
        return None
    exclude_hints = exclude_hints or []
    for key, value in row.items():
        key_lower = str(key).lower()
        if any(hint in key_lower for hint in exclude_hints):
            continue
        if all(hint in key_lower for hint in include_hints):
            parsed = _to_int(value)
            if parsed is not None:
                return parsed
    return None


def _pick_latest_row(rows):
    if isinstance(rows, dict):
        return rows
    if not isinstance(rows, list):
        return None
    if not rows:
        return None
    date_keys = ["stck_bsop_date", "bsop_date", "date", "trd_dt", "trd_date"]
    best_row = rows[0]
    best_date = ""
    for row in rows:
        if not isinstance(row, dict):
            continue
        for key in date_keys:
            value = row.get(key)
            if not value:
                continue
            value_str = str(value)
            if value_str > best_date:
                best_date = value_str
                best_row = row
    return best_row


def _compute_market_breadth(db: Session, debug: bool = False):
    row = db.execute(text("""
        WITH latest AS (
            SELECT MAX(trade_date) AS dt FROM price_daily
        ),
        prev AS (
            SELECT MAX(trade_date) AS dt
            FROM price_daily
            WHERE trade_date < (SELECT dt FROM latest)
        ),
        today AS (
            SELECT ticker, close FROM price_daily
            WHERE trade_date = (SELECT dt FROM latest)
        ),
        yday AS (
            SELECT ticker, close FROM price_daily
            WHERE trade_date = (SELECT dt FROM prev)
        ),
        cmp AS (
            SELECT t.ticker, t.close AS c, y.close AS p
            FROM today t
            JOIN yday y USING (ticker)
        )
        SELECT
            (SELECT dt FROM latest) AS as_of_date,
            SUM(CASE WHEN c > p THEN 1 ELSE 0 END) AS up_count,
            SUM(CASE WHEN c < p THEN 1 ELSE 0 END) AS down_count,
            SUM(CASE WHEN c = p THEN 1 ELSE 0 END) AS flat_count
        FROM cmp
    """)).fetchone()
    if not row or not row[0]:
        return None, None, None
    as_of_date, up_count, down_count, flat_count = row

    program_debug = None
    try:
        if debug:
            program_payload = kis.get_program_trade_daily("0001", return_raw=True)
            if isinstance(program_payload, dict):
                program_rows = program_payload.get("parsed")
                raw_data = program_payload.get("raw")
                program_debug = {
                    "status": program_payload.get("status"),
                    "error": program_payload.get("error"),
                    "raw_keys": sorted(raw_data.keys()) if isinstance(raw_data, dict) else [],
                    "raw_output1_keys": sorted(raw_data.get("output1", {}).keys()) if isinstance(raw_data, dict) and isinstance(raw_data.get("output1"), dict) else [],
                    "raw_output2_length": len(raw_data.get("output2", [])) if isinstance(raw_data, dict) and isinstance(raw_data.get("output2"), list) else 0,
                    "tried": program_payload.get("tried"),
                }
            else:
                program_rows = None
        else:
            program_rows = kis.get_program_trade_daily("0001")
    except Exception as exc:
        program_rows = None
        if debug:
            program_debug = {
                "status": "exception",
                "error": {"message": str(exc)},
            }
    program_row = _pick_latest_row(program_rows)

    program_val = _pick_value(program_row, [
        "whol_smtn_ntby_tr_pbmn",
        "whol_entm_ntby_tr_pbmn",
        "whol_onsl_ntby_tr_pbmn",
        "whol_ntby_tr_pbmn",
        "prgm_ntby_tr_pbmn",
        "prgm_ntby_amt",
        "prgm_netby_amt",
        "program_net",
    ])
    if program_val is None:
        program_val = _pick_value_by_hint(program_row, ["prgm", "ntby"])
    if program_val is None:
        program_val = _pick_value_by_hint(program_row, ["program", "net"])
    arbitrage_val = _pick_value(program_row, [
        "arbt_smtn_ntby_tr_pbmn",
        "arbt_entm_ntby_tr_pbmn",
        "arbt_onsl_ntby_tr_pbmn",
        "arbt_ntby_tr_pbmn",
        "arbt_ntby_amt",
        "arbt_netby_amt",
        "arbitrage_net",
    ])
    if arbitrage_val is None:
        arbitrage_val = _pick_value_by_hint(program_row, ["arbt", "ntby"])
    if arbitrage_val is None:
        arbitrage_val = _pick_value_by_hint(program_row, ["arbitrage", "net"])
    non_arbitrage_val = _pick_value(program_row, [
        "nabt_smtn_ntby_tr_pbmn",
        "nabt_entm_ntby_tr_pbmn",
        "nabt_onsl_ntby_tr_pbmn",
        "nabt_ntby_tr_pbmn",
        "narb_ntby_tr_pbmn",
        "narb_ntby_amt",
        "nonarbt_ntby_amt",
        "non_arbitrage_net",
    ])
    if non_arbitrage_val is None:
        non_arbitrage_val = _pick_value_by_hint(program_row, ["narb", "ntby"])
    if non_arbitrage_val is None:
        non_arbitrage_val = _pick_value_by_hint(program_row, ["non", "arbitrage"], exclude_hints=["arbt"])

    snapshot = {
        "as_of_date": as_of_date,
        "up": int(up_count or 0),
        "down": int(down_count or 0),
        "flat": int(flat_count or 0),
        "program_net_krw": program_val,
        "arbitrage_net_krw": arbitrage_val,
        "non_arbitrage_net_krw": non_arbitrage_val,
    }
    return snapshot, program_debug, program_row


def _save_breadth_snapshot(db: Session, snapshot: dict) -> None:
    if not snapshot:
        return
    db.execute(text("""
        INSERT INTO market_breadth_snapshot (
            as_of_date, up, down, flat,
            program_net_krw, arbitrage_net_krw, non_arbitrage_net_krw, updated_at
        )
        VALUES (
            :as_of_date, :up, :down, :flat,
            :program, :arbitrage, :non_arbitrage, NOW()
        )
    """), {
        "as_of_date": snapshot["as_of_date"],
        "up": snapshot["up"],
        "down": snapshot["down"],
        "flat": snapshot["flat"],
        "program": snapshot.get("program_net_krw"),
        "arbitrage": snapshot.get("arbitrage_net_krw"),
        "non_arbitrage": snapshot.get("non_arbitrage_net_krw"),
    })
    db.commit()


def _build_breadth_response(snapshot: dict) -> dict:
    return {
        "as_of_date": snapshot["as_of_date"].isoformat() if snapshot.get("as_of_date") else None,
        "up": snapshot.get("up", 0),
        "down": snapshot.get("down", 0),
        "flat": snapshot.get("flat", 0),
        "program_net_krw": _format_krw_100m(snapshot.get("program_net_krw")),
        "arbitrage_net_krw": _format_krw_100m(snapshot.get("arbitrage_net_krw")),
        "non_arbitrage_net_krw": _format_krw_100m(snapshot.get("non_arbitrage_net_krw")),
    }


def _has_program_values(snapshot: dict | None) -> bool:
    if not snapshot:
        return False
    keys = ("program_net_krw", "arbitrage_net_krw", "non_arbitrage_net_krw")
    for key in keys:
        value = snapshot.get(key)
        if value not in (None, "", "-"):
            return True
    return False


def _refresh_breadth_snapshot() -> None:
    global _BREADTH_CACHE, _BREADTH_CACHE_AT, _BREADTH_REFRESHING
    if _BREADTH_REFRESHING:
        return
    _BREADTH_REFRESHING = True
    db = SessionLocal()
    try:
        _ensure_breadth_table(db)
        snapshot, _, _ = _compute_market_breadth(db, debug=False)
        if snapshot:
            _save_breadth_snapshot(db, snapshot)
            _BREADTH_CACHE = snapshot
            _BREADTH_CACHE_AT = time.time()
    finally:
        db.close()
        _BREADTH_REFRESHING = False


def _try_refresh_breadth_now(db: Session) -> dict | None:
    snapshot, _, _ = _compute_market_breadth(db, debug=False)
    if snapshot:
        _save_breadth_snapshot(db, snapshot)
        global _BREADTH_CACHE, _BREADTH_CACHE_AT
        _BREADTH_CACHE = snapshot
        _BREADTH_CACHE_AT = time.time()
        return _build_breadth_response(snapshot)
    return None
# ... (indices code remains same) ...

# ... (investor trends code remains same) ...

@router.get("/themes/rankings")
def get_theme_rankings():
    # Fetch real data via scraping
    data = scrapers.get_naver_themes(include_leading_stock=False, pages=1)
    return data[:5] if data else []

@router.get("/themes/all")
def get_all_themes():
    return scrapers.get_naver_themes(include_leading_stock=False)

@router.get("/industries/rankings")
def get_industry_rankings():
    data = scrapers.get_naver_industries(include_leading_stock=True, limit_leading=5)
    return data[:5] if data else []

@router.get("/industries/all")
def get_all_industries():
    return scrapers.get_naver_industries(include_leading_stock=True)

@router.get("/industries/members")
def get_industry_members(names: str):
    name_list = [v.strip() for v in names.split(",") if v.strip()]
    if not name_list:
        return {"items": []}
    tickers: set[str] = set()
    for name in name_list:
        link = scrapers.get_industry_link_by_name(name)
        if not link:
            continue
        tickers.update(scrapers.get_naver_industry_members(link))
    return {"items": sorted(tickers)}

@router.get("/themes/members")
def get_theme_members(names: str):
    name_list = [v.strip() for v in names.split(",") if v.strip()]
    if not name_list:
        return {"items": []}
    tickers: set[str] = set()
    for name in name_list:
        link = scrapers.get_theme_link_by_name(name)
        if not link:
            continue
        tickers.update(scrapers.get_naver_theme_members(link))
    return {"items": sorted(tickers)}


@router.get("/ecos/fx")
def get_ecos_fx_today():
    api_key = settings.ECOS_API_KEY or os.environ.get("ECOS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ECOS_API_KEY is missing")

    url = f"http://ecos.bok.or.kr/api/KeyStatisticList/{api_key}/json/kr/1/200"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    rows = data.get("KeyStatisticList", {}).get("row", [])
    if not rows:
        raise HTTPException(status_code=404, detail="ECOS data not found")

    def match_fx(name: str) -> bool:
        return bool(re.search(r"(원/달러|원\\s*/\\s*달러|달러\\s*환율|USD)", name))

    for row in rows:
        name = row.get("KEYSTAT_NAME") or ""
        if match_fx(name):
            value = row.get("DATA_VALUE")
            cycle = row.get("CYCLE")
            return {
                "pair": "USD/KRW",
                "name": name,
                "value": float(value) if value is not None else None,
                "date": cycle,
                "unit": row.get("UNIT_NAME"),
            }

    raise HTTPException(status_code=404, detail="USD/KRW not found")

def _has_numeric_value(value) -> bool:
    if value in (None, "-", ""):
        return False
    try:
        float(str(value).replace(",", ""))
        return True
    except (TypeError, ValueError):
        return False


def _compute_indices_from_db(db: Session, index_code: str):
    rows = db.execute(
        text("""
            SELECT trade_date, close
            FROM market_index_daily
            WHERE index_code = :index_code
            ORDER BY trade_date DESC
            LIMIT 2
        """),
        {"index_code": index_code},
    ).fetchall()
    if not rows:
        return None
    latest = rows[0]
    prev = rows[1] if len(rows) > 1 else rows[0]
    if latest.close is None:
        return None
    price = float(latest.close)
    prev_close = float(prev.close) if prev.close is not None else price
    change = price - prev_close
    rate = (change / prev_close * 100) if prev_close else 0.0
    return {
        "value": format(price, ",.2f"),
        "change": f"{change:+.2f}",
        "changePercent": f"{rate:+.2f}%",
        "up": change > 0,
    }


def _compute_indices(db: Session):
    # KOSPI (0001), KOSDAQ (1001), KOSPI200 (2001)
    results = []
    targets = [
        {"code": "0001", "name": "KOSPI"},
        {"code": "1001", "name": "KOSDAQ"},
        {"code": "2001", "name": "KOSPI200"},
    ]
    
    for t in targets:
        fdr_map = {
            "0001": "KS11",
            "1001": "KQ11",
            "2001": "KS200",
        }
        fdr_code = fdr_map.get(t["code"])
        if fdr_code:
            try:
                df = fdr.DataReader(fdr_code)
                latest = df.iloc[-1]
                price = float(latest["Close"])
                prev = float(df.iloc[-2]["Close"]) if len(df) > 1 else price
                change = price - prev
                rate = (change / prev * 100) if prev else 0.0
                results.append({
                    "name": t["name"],
                    "value": format(price, ",.2f"),
                    "change": f"{change:+.2f}",
                    "changePercent": f"{rate:+.2f}%",
                    "up": change > 0
                })
                continue
            except Exception:
                pass

        data = kis.get_market_index(t["code"])
        if data:
            try:
                if 'bstp_nmix_prpr' in data:
                    price = float(data['bstp_nmix_prpr'])
                    change = float(data['bstp_nmix_prdy_vrss'])
                    rate = float(data['bstp_nmix_prdy_ctrt'])
                elif 'stck_clpr' in data:
                    price = float(data['stck_clpr'])
                    change = float(data['prdy_vrss'])
                    rate = float(data['prdy_ctrt'])
                else:
                    raise KeyError("Unknown key format")
                results.append({
                    "name": t["name"],
                    "value": format(price, ","),
                    "change": f"{change:+.2f}",
                    "changePercent": f"{rate:+.2f}%",
                    "up": change > 0
                })
                continue
            except (ValueError, KeyError):
                pass

        db_payload = _compute_indices_from_db(db, t["code"])
        if db_payload:
            results.append({
                "name": t["name"],
                **db_payload,
            })
            continue

        results.append({
            "name": t["name"],
            "value": "-",
            "change": "-",
            "changePercent": "-",
            "up": False
        })
             
    return results


def _refresh_indices_snapshot() -> None:
    global _INDICES_CACHE, _INDICES_CACHE_AT, _INDICES_REFRESHING
    if _INDICES_REFRESHING:
        return
    _INDICES_REFRESHING = True
    db = SessionLocal()
    try:
        _ensure_indices_table(db)
        payload = _compute_indices(db)
        if payload and any(_has_numeric_value(item.get("value")) for item in payload):
            _save_snapshot(db, "market_index_snapshot", payload)
            _INDICES_CACHE = payload
            _INDICES_CACHE_AT = time.time()
    finally:
        db.close()
        _INDICES_REFRESHING = False


@router.get("/indices")
def get_indices(db: Session = Depends(get_db), background_tasks: BackgroundTasks = BackgroundTasks()):
    global _INDICES_CACHE, _INDICES_CACHE_AT
    _ensure_indices_table(db)

    now = time.time()
    if _INDICES_CACHE and _INDICES_CACHE_AT and (now - _INDICES_CACHE_AT) < 3600:
        return _INDICES_CACHE

    payload, updated_at = _load_latest_snapshot(db, "market_index_snapshot")
    if payload:
        _INDICES_CACHE = payload
        _INDICES_CACHE_AT = time.time()
        if not updated_at or (now - updated_at.timestamp()) >= 3600:
            background_tasks.add_task(_refresh_indices_snapshot)
        return payload

    db_payload = _compute_indices(db)
    if db_payload and any(_has_numeric_value(item.get("value")) for item in db_payload):
        _INDICES_CACHE = db_payload
        _INDICES_CACHE_AT = time.time()
        return db_payload

    background_tasks.add_task(_refresh_indices_snapshot)
    return [
        {"name": "KOSPI", "value": "-", "change": "-", "changePercent": "-", "up": False},
        {"name": "KOSDAQ", "value": "-", "change": "-", "changePercent": "-", "up": False},
        {"name": "KOSPI200", "value": "-", "change": "-", "changePercent": "-", "up": False},
    ]


@router.get("/market/breadth")
def get_market_breadth(
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    debug: bool = False,
):
    global _BREADTH_CACHE, _BREADTH_CACHE_AT
    _ensure_breadth_table(db)

    if debug:
        snapshot, program_debug, program_row = _compute_market_breadth(db, debug=True)
        if not snapshot:
            return {
                "as_of_date": None,
                "up": 0,
                "down": 0,
                "flat": 0,
                "program_net_krw": None,
                "arbitrage_net_krw": None,
                "non_arbitrage_net_krw": None,
                "program_debug": program_debug,
            }
        response = _build_breadth_response(snapshot)
        response["program_debug"] = {
            "has_kis_credentials": bool(getattr(kis, "app_key", None) and getattr(kis, "app_secret", None)),
            "program_row_keys": sorted(program_row.keys()) if isinstance(program_row, dict) else [],
            "program_row_sample": program_row if isinstance(program_row, dict) else None,
            "program_api": program_debug,
            "program_tried_paths": program_debug.get("tried") if isinstance(program_debug, dict) else None,
        }
        return response

    now = time.time()
    if _BREADTH_CACHE and _BREADTH_CACHE_AT and (now - _BREADTH_CACHE_AT) < 3600:
        if not _has_program_values(_BREADTH_CACHE):
            refreshed = _try_refresh_breadth_now(db)
            if refreshed:
                return refreshed
            background_tasks.add_task(_refresh_breadth_snapshot)
        return _build_breadth_response(_BREADTH_CACHE)

    snapshot_row = db.execute(text("""
        SELECT as_of_date, up, down, flat,
               program_net_krw, arbitrage_net_krw, non_arbitrage_net_krw, updated_at
        FROM market_breadth_snapshot
        ORDER BY updated_at DESC
        LIMIT 1
    """)).fetchone()
    if snapshot_row:
        snapshot = {
            "as_of_date": snapshot_row.as_of_date,
            "up": snapshot_row.up,
            "down": snapshot_row.down,
            "flat": snapshot_row.flat,
            "program_net_krw": snapshot_row.program_net_krw,
            "arbitrage_net_krw": snapshot_row.arbitrage_net_krw,
            "non_arbitrage_net_krw": snapshot_row.non_arbitrage_net_krw,
        }
        _BREADTH_CACHE = snapshot
        _BREADTH_CACHE_AT = time.time()
        if not _has_program_values(snapshot):
            refreshed = _try_refresh_breadth_now(db)
            if refreshed:
                return refreshed
        if (not snapshot_row.updated_at
                or (now - snapshot_row.updated_at.timestamp()) >= 3600
                or not _has_program_values(snapshot)):
            background_tasks.add_task(_refresh_breadth_snapshot)
        return _build_breadth_response(snapshot)

    refreshed = _try_refresh_breadth_now(db)
    if refreshed:
        return refreshed

    return {
        "as_of_date": None,
        "up": 0,
        "down": 0,
        "flat": 0,
        "program_net_krw": None,
        "arbitrage_net_krw": None,
        "non_arbitrage_net_krw": None,
    }


@router.get("/indices/chart")
def get_index_chart(
    market: str = "KOSPI",
    days: int = 30,
    interval: str = "1d",
    db: Session = Depends(get_db),
):
    market_map = {
        "KOSPI": "0001",
        "KOSDAQ": "1001",
        "KOSPI200": "2001",
    }
    code = market_map.get(market.upper())
    if not code:
        raise HTTPException(status_code=400, detail="Unsupported market code")

    from datetime import datetime, timedelta

    end_date = datetime.now()
    start_date = end_date - timedelta(days=max(days, 5))
    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")
    start_str_fdr = start_date.strftime("%Y-%m-%d")
    end_str_fdr = end_date.strftime("%Y-%m-%d")

    fdr_map = {
        "0001": "KS11",
        "1001": "KQ11",
        "2001": "KS200",
    }
    fdr_code = fdr_map.get(code)

    interval_key = interval.lower()
    if interval_key in ("1m", "1min", "minute"):
        target_date = end_date.strftime("%Y%m%d")
        if fdr_code:
            try:
                df_latest = fdr.DataReader(fdr_code)
                if not df_latest.empty:
                    latest_date = df_latest.index[-1].strftime("%Y%m%d")
                    if latest_date < target_date:
                        target_date = latest_date
            except Exception:
                pass
        try:
            daily_rows = kis.get_market_index_history(code, start_str, end_str)
            if daily_rows:
                last_daily = daily_rows[-1].get("stck_bsop_date")
                if last_daily and last_daily < target_date:
                    target_date = last_daily
        except Exception:
            pass
        print(f"Index intraday request market={market} code={code} target_date={target_date}")
        rows = kis.get_market_index_intraday(code, target_date)
        if rows:
            results = []
            for row in rows:
                date_str = row.get("stck_bsop_date") or end_date.strftime("%Y%m%d")
                time_raw = row.get("stck_cntg_hour") or row.get("stck_hgpr_hour") or ""
                if len(time_raw) >= 4:
                    time_fmt = f"{time_raw[0:2]}:{time_raw[2:4]}"
                else:
                    time_fmt = ""
                value_raw = (
                    row.get("bstp_nmix_prpr")
                    or row.get("stck_clpr")
                    or row.get("indx_clpr")
                    or row.get("clpr")
                )
                try:
                    value = float(value_raw) if value_raw is not None else None
                except (TypeError, ValueError):
                    value = None
                if not date_str or value is None:
                    continue
                label = f"{date_str} {time_fmt}".strip()
                results.append({"date": label, "value": value})
            if results:
                return results

    if fdr_code:
        try:
            df = fdr.DataReader(fdr_code, start_str_fdr, end_str_fdr)
            if df.empty:
                df = fdr.DataReader(fdr_code)
            if not df.empty:
                df = df.tail(days)
                rows = [
                    {"date": idx.strftime("%Y%m%d"), "value": float(row["Close"])}
                    for idx, row in df.iterrows()
                ]
                return _normalize_chart_rows(rows, days)
        except Exception as exc:
            print(f"FDR Index Chart Error for {fdr_code}: {exc}")

    raw_rows = kis.get_market_index_history(code, start_str, end_str)
    results = []
    for row in raw_rows:
        date_str = row.get("stck_bsop_date") or row.get("date") or ""
        value_raw = (
            row.get("bstp_nmix_prpr")
            or row.get("stck_clpr")
            or row.get("indx_clpr")
            or row.get("clpr")
        )
        try:
            value = float(value_raw) if value_raw is not None else None
        except (TypeError, ValueError):
            value = None
        if not date_str or value is None:
            continue
        results.append({
            "date": date_str,
            "value": value,
        })

    if results:
        return _normalize_chart_rows(results, days)

    # Fallback to stored data if KIS is unavailable.
    rows = db.execute(
        text("""
            SELECT trade_date, close
            FROM market_index_daily
            WHERE index_code = :index_code
            ORDER BY trade_date DESC
            LIMIT :limit
        """),
        {"index_code": code, "limit": days},
    ).fetchall()

    if rows:
        data = [
            {"date": r.trade_date.strftime("%Y%m%d"), "value": float(r.close)}
            for r in reversed(rows)
            if r.trade_date and r.close is not None
        ]
        return _normalize_chart_rows(data, days)

    return []

def _normalize_chart_rows(rows: list[dict], days: int) -> list[dict]:
    if not rows:
        return []
    today = datetime.now().strftime("%Y%m%d")
    filtered = [
        row for row in rows
        if row.get("date") and row.get("value") is not None and row["date"] <= today
    ]
    if not filtered:
        return []
    filtered.sort(key=lambda row: row["date"])
    if days <= 1:
        today_rows = [row for row in filtered if row["date"] == today]
        if today_rows:
            return today_rows
        latest_date = filtered[-1]["date"]
        return [row for row in filtered if row["date"] == latest_date]
    return filtered[-days:]


@router.get("/prices/quotes")
def get_price_quotes(
    tickers: str,
    db: Session = Depends(get_db),
):
    ticker_list = [t.strip() for t in tickers.split(",") if t.strip()]
    if not ticker_list:
        return {"items": []}

    rows = db.execute(
        text(
            """
            SELECT ticker, trade_date, close
            FROM price_daily
            WHERE ticker = ANY(:tickers)
            ORDER BY ticker, trade_date DESC
            """
        ),
        {"tickers": ticker_list},
    ).fetchall()

    result: dict[str, dict] = {}
    for row in rows:
        entry = result.setdefault(row.ticker, {
            "ticker": row.ticker,
            "close": None,
            "prev_close": None,
            "trade_date": None,
        })
        if entry["close"] is None:
            entry["close"] = float(row.close) if row.close is not None else None
            entry["trade_date"] = row.trade_date.isoformat() if row.trade_date else None
            continue
        if entry["prev_close"] is None:
            entry["prev_close"] = float(row.close) if row.close is not None else None

    items = []
    for entry in result.values():
        close = entry["close"]
        prev = entry["prev_close"]
        change = None
        change_percent = None
        if close is not None and prev is not None and prev != 0:
            change = close - prev
            change_percent = (change / prev) * 100
        entry["change"] = change
        entry["change_percent"] = change_percent
        items.append(entry)

    return {"items": items}

def _fallback_volume_rank(db: Session, limit: int):
    rows = db.execute(text("""
        WITH latest AS (
            SELECT MAX(trade_date) AS dt FROM price_daily
        ),
        prev AS (
            SELECT MAX(trade_date) AS dt
            FROM price_daily
            WHERE trade_date < (SELECT dt FROM latest)
        ),
        today AS (
            SELECT ticker, close, volume
            FROM price_daily
            WHERE trade_date = (SELECT dt FROM latest)
        ),
        yday AS (
            SELECT ticker, close AS prev_close
            FROM price_daily
            WHERE trade_date = (SELECT dt FROM prev)
        )
        SELECT t.ticker, t.close, t.volume, y.prev_close, c.name_ko
        FROM today t
        LEFT JOIN yday y USING (ticker)
        LEFT JOIN security s ON s.ticker = t.ticker
        LEFT JOIN company c ON c.company_id = s.company_id
        ORDER BY t.volume DESC NULLS LAST
        LIMIT :limit
    """), {"limit": limit}).fetchall()
    results = []
    for idx, row in enumerate(rows):
        change_rate = None
        if row.prev_close and row.prev_close != 0 and row.close is not None:
            change_rate = (row.close - row.prev_close) / row.prev_close * 100
        results.append({
            "rank": idx + 1,
            "name": row.name_ko or row.ticker,
            "price": format(int(row.close or 0), ","),
            "changePercent": f"{change_rate:+.2f}%" if change_rate is not None else "-",
            "up": change_rate is not None and change_rate > 0,
            "volume": format(int(row.volume or 0), ","),
        })
    return results


def _compute_popular_searches(db: Session) -> list[dict]:
    data = None
    try:
        data = kis.get_volume_rank()
    except Exception:
        data = None

    results = []
    if data:
        for idx, item in enumerate(data[:12]):
            try:
                change_rate = float(item.get('prdy_ctrt', 0))
            except (TypeError, ValueError):
                change_rate = 0
            results.append({
                "rank": idx + 1,
                "name": item.get('hts_kor_isnm') or item.get('stck_shrn_iscd') or '-',
                "price": format(int(item.get('stck_prpr', 0)), ","),
                "changePercent": f"{change_rate:+.2f}%",
                "up": change_rate > 0
            })
        _POPULAR_CACHE = results
        _POPULAR_CACHE_AT = time.time()
        return results

    results = _fallback_volume_rank(db, 12)
    _POPULAR_CACHE = results
    _POPULAR_CACHE_AT = time.time()
    return results


def _refresh_popular_snapshot() -> None:
    global _POPULAR_CACHE, _POPULAR_CACHE_AT
    db = SessionLocal()
    try:
        _ensure_popular_table(db)
        payload = _compute_popular_searches(db)
        if payload:
            _save_snapshot(db, "market_popular_snapshot", payload)
            _POPULAR_CACHE = payload
            _POPULAR_CACHE_AT = time.time()
    finally:
        db.close()


@router.get("/popular-searches")
def get_popular_searches(db: Session = Depends(get_db), background_tasks: BackgroundTasks = BackgroundTasks()):
    global _POPULAR_CACHE, _POPULAR_CACHE_AT
    _ensure_popular_table(db)
    now = time.time()
    if _POPULAR_CACHE and _POPULAR_CACHE_AT and (now - _POPULAR_CACHE_AT) < 3600:
        return _POPULAR_CACHE

    payload, updated_at = _load_latest_snapshot(db, "market_popular_snapshot")
    if payload:
        _POPULAR_CACHE = payload
        _POPULAR_CACHE_AT = time.time()
        if not updated_at or (now - updated_at.timestamp()) >= 3600:
            background_tasks.add_task(_refresh_popular_snapshot)
        return payload

    background_tasks.add_task(_refresh_popular_snapshot)
    return _POPULAR_CACHE or []

@router.get("/popular-searches/all")
def get_all_popular_searches(db: Session = Depends(get_db)):
    global _POPULAR_ALL_CACHE, _POPULAR_ALL_CACHE_AT
    now = time.time()
    if _POPULAR_ALL_CACHE and _POPULAR_ALL_CACHE_AT and (now - _POPULAR_ALL_CACHE_AT) < 300:
        return _POPULAR_ALL_CACHE

    data = None
    try:
        data = kis.get_volume_rank()
    except Exception:
        data = None

    results = []
    if data:
        for idx, item in enumerate(data[:50]):
            try:
                change_rate = float(item.get('prdy_ctrt', 0))
            except (TypeError, ValueError):
                change_rate = 0
            results.append({
                "rank": idx + 1,
                "name": item.get('hts_kor_isnm') or item.get('stck_shrn_iscd') or '-',
                "price": format(int(item.get('stck_prpr', 0)), ","),
                "changePercent": f"{change_rate:+.2f}%",
                "up": change_rate > 0,
                "volume": format(int(item.get('acml_vol', 0)), ",")
            })
        _POPULAR_ALL_CACHE = results
        _POPULAR_ALL_CACHE_AT = time.time()
        return results

    results = _fallback_volume_rank(db, 50)
    _POPULAR_ALL_CACHE = results
    _POPULAR_ALL_CACHE_AT = time.time()
    return results

# Stubs for others to prevent 404
@router.get("/investor-trends")
def get_investor_trends():
    # Attempt to fetch real investory trends (KOSPI base: 0001)
    data = kis.get_investor_trend("0001")
    
    if data and len(data) > 0:
        recent = data[0]
        
        def format_billion(val_str):
            try:
                val = int(val_str)
                # Convert to Billion Won (100 Million)
                billions = val // 100
                return f"{billions:,}억"
            except:
                return "-"
        
        personal_val = int(recent.get('prsn_ntby_tr_pbmn', 0))
        foreigner_val = int(recent.get('frgn_ntby_tr_pbmn', 0))
        institution_val = int(recent.get('orgn_ntby_tr_pbmn', 0))
        
        return [
            { "type": "개인", "value": format_billion(personal_val), "buying": personal_val > 0, "up": personal_val > 0 },
            { "type": "외국인", "value": format_billion(foreigner_val), "buying": foreigner_val > 0, "up": foreigner_val > 0 },
            { "type": "기관", "value": format_billion(institution_val), "buying": institution_val > 0, "up": institution_val > 0 },
        ]

    # No Mock Data allowed. Return empty list if API fails.
    return []


