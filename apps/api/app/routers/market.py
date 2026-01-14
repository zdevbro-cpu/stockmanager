from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from sqlalchemy import text
import sys
import os

# Create path to services
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../../services/ingest"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../services")) # For scrapers

from ingest.kis_client import KisClient
from app.services import scrapers
import FinanceDataReader as fdr
from ..db import get_db
from sqlalchemy.orm import Session

router = APIRouter(tags=["Market"])

kis = KisClient()
# ... (indices code remains same) ...

# ... (investor trends code remains same) ...

@router.get("/themes/rankings")
def get_theme_rankings():
    # Fetch real data via scraping
    data = scrapers.get_naver_themes()
    return data[:5] if data else []

@router.get("/themes/all")
def get_all_themes():
    return scrapers.get_naver_themes()

@router.get("/industries/rankings")
def get_industry_rankings():
    data = scrapers.get_naver_industries()
    return data[:5] if data else []

@router.get("/industries/all")
def get_all_industries():
    return scrapers.get_naver_industries()

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

@router.get("/indices")
def get_indices():
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

        results.append({
            "name": t["name"],
            "value": "-",
            "change": "-",
            "changePercent": "-",
            "up": False
        })
             
    return results


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

@router.get("/popular-searches")
def get_popular_searches():
    # Use Volume Rank as proxy for popular searches
    data = kis.get_volume_rank()
    # KIS returns list of dicts: hts_kor_isnm(Name), stck_prpr(Price), prdy_vrss(Change), prdy_ctrt(Rate), acml_vol(Vol)
    
    results = []
    if data:
        for idx, item in enumerate(data[:12]): # Top 12
            change_rate = float(item['prdy_ctrt'])
            results.append({
                "rank": idx + 1,
                "name": item['hts_kor_isnm'],
                "price": format(int(item['stck_prpr']), ","),
                "changePercent": f"{change_rate:+.2f}%",
                "up": change_rate > 0
            })
    return results

@router.get("/popular-searches/all")
def get_all_popular_searches():
    # Use Volume Rank as proxy for popular searches
    data = kis.get_volume_rank()
    
    results = []
    if data:
        for idx, item in enumerate(data[:50]): # Top 50 for full page
            change_rate = float(item['prdy_ctrt'])
            results.append({
                "rank": idx + 1,
                "name": item['hts_kor_isnm'],
                "price": format(int(item['stck_prpr']), ","),
                "changePercent": f"{change_rate:+.2f}%",
                "up": change_rate > 0,
                "volume": format(int(item['acml_vol']), ",")
            })
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


