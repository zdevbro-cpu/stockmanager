import time
from datetime import date, datetime, timedelta
from sqlalchemy import text
from ingest.db import SessionLocal
from ingest.kis_client import KisClient

def update_kis_prices_task(limit: int | None = None, offset: int = 0, kis: KisClient | None = None, progress_cb=None):
    """
    Fetch current prices for companies from KIS API and update 'price_daily' table.
    Commits every 10 items to ensure progress visibility.
    """
    kis = kis or KisClient()
    limit_label = "ALL" if limit is None else str(limit)
    print(f"Starting KIS Price Update Task (Limit: {limit_label})...")
    
    with SessionLocal() as db:
        try:
            stmt_get_stocks = text("""
                SELECT s.ticker, c.company_id
                FROM security s
                JOIN company c ON s.company_id = c.company_id
                ORDER BY s.ticker ASC
                OFFSET :o
                LIMIT :l
            """)
            if limit is None:
                stmt_get_stocks = text("""
                    SELECT s.ticker, c.company_id
                    FROM security s
                    JOIN company c ON s.company_id = c.company_id
                    ORDER BY s.ticker ASC
                """)
                stocks = db.execute(stmt_get_stocks).fetchall()
            else:
                stocks = db.execute(stmt_get_stocks, {"l": limit, "o": offset}).fetchall()
            total = len(stocks)
            if progress_cb:
                progress_cb(0, total)
            today = date.today()
            
            count = 0
            for ticker, company_id in stocks:
                if not ticker: continue
                
                price_data = kis.get_stock_price(ticker)
                
                if price_data:
                    try:
                        stmt_upsert = text("""
                            INSERT INTO price_daily (ticker, trade_date, open, high, low, close, volume, turnover_krw, source, created_at)
                            VALUES (:t, :d, :o, :h, :l, :c, :v, :val, 'KIS', NOW())
                            ON CONFLICT (ticker, trade_date) 
                            DO UPDATE SET close = EXCLUDED.close, volume = EXCLUDED.volume, created_at = NOW()
                        """)
                        db.execute(stmt_upsert, {
                            "t": ticker, "d": today,
                            "o": int(price_data.get('stck_oprc', 0)),
                            "h": int(price_data.get('stck_hgpr', 0)),
                            "l": int(price_data.get('stck_lwpr', 0)),
                            "c": int(price_data.get('stck_prpr', 0)),
                            "v": int(price_data.get('acml_vol', 0)),
                            "val": int(price_data.get('acml_tr_pbmn', 0))
                        })
                        count += 1
                        print(f"[{count}] Updated {ticker}")
                        
                        # Commit every 5 items for better progress visibility
                        if count % 5 == 0:
                            db.commit()
                        if progress_cb:
                            progress_cb(count, total)
                            
                    except Exception as e:
                        print(f"Error for {ticker}: {e}")
                
                time.sleep(0.1)
                
            db.commit()
            print(f"Total {count} prices updated successfully.")
            
        except Exception as e:
            print(f"KIS Update CRITICAL Failed: {e}")
            db.rollback()
        finally:
            db.close()


def _to_int(value: str | int | None):
    if value is None:
        return None
    if isinstance(value, int):
        return value
    value = value.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def backfill_kis_prices_task(
    days: int = 90,
    limit: int | None = None,
    offset: int = 0,
    kis: KisClient | None = None,
    tickers: list[str] | None = None,
):
    """
    Fetch historical daily prices for a date range and upsert into price_daily.
    """
    kis = kis or KisClient()
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")
    print(f"Starting KIS Price Backfill (days={days}, {start_str}~{end_str})...")

    with SessionLocal() as db:
        try:
            if tickers:
                stocks = [(t, None) for t in tickers]
            else:
                stmt_get_stocks = text("""
                    SELECT s.ticker, c.company_id
                    FROM security s
                    JOIN company c ON s.company_id = c.company_id
                    ORDER BY s.ticker ASC
                    OFFSET :o
                    LIMIT :l
                """)
                if limit is None:
                    stmt_get_stocks = text("""
                        SELECT s.ticker, c.company_id
                        FROM security s
                        JOIN company c ON s.company_id = c.company_id
                        ORDER BY s.ticker ASC
                    """)
                    stocks = db.execute(stmt_get_stocks).fetchall()
                else:
                    stocks = db.execute(stmt_get_stocks, {"l": limit, "o": offset}).fetchall()

            total_rows = 0
            for ticker, _company_id in stocks:
                if not ticker:
                    continue

                rows = kis.get_stock_daily_history(ticker, start_str, end_str)
                if not rows:
                    continue

                for row in rows:
                    trade_date_str = row.get("stck_bsop_date")
                    if not trade_date_str:
                        continue
                    try:
                        trade_date = datetime.strptime(trade_date_str, "%Y%m%d").date()
                    except ValueError:
                        continue

                    stmt_upsert = text("""
                        INSERT INTO price_daily (
                            ticker, trade_date, open, high, low, close, volume, turnover_krw, source, created_at
                        )
                        VALUES (:t, :d, :o, :h, :l, :c, :v, :val, 'KIS', NOW())
                        ON CONFLICT (ticker, trade_date)
                        DO UPDATE SET
                            open = EXCLUDED.open,
                            high = EXCLUDED.high,
                            low = EXCLUDED.low,
                            close = EXCLUDED.close,
                            volume = EXCLUDED.volume,
                            turnover_krw = EXCLUDED.turnover_krw,
                            created_at = NOW()
                    """)
                    db.execute(stmt_upsert, {
                        "t": ticker,
                        "d": trade_date,
                        "o": _to_int(row.get("stck_oprc")),
                        "h": _to_int(row.get("stck_hgpr")),
                        "l": _to_int(row.get("stck_lwpr")),
                        "c": _to_int(row.get("stck_clpr")),
                        "v": _to_int(row.get("acml_vol")),
                        "val": _to_int(row.get("acml_tr_pbmn")),
                    })
                    total_rows += 1

                    if total_rows % 200 == 0:
                        db.commit()

                db.commit()
                print(f"Backfilled {ticker} ({len(rows)} rows)")
                time.sleep(0.2)

            db.commit()
            if progress_cb:
                progress_cb(count, total)
            print(f"Backfill complete. Total rows upserted: {total_rows}")
        except Exception as e:
            print(f"KIS Backfill CRITICAL Failed: {e}")
            db.rollback()
        finally:
            db.close()
