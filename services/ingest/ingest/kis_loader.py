import time
from sqlalchemy import text
from ingest.db import SessionLocal
from ingest.kis_client import KisClient
from datetime import date

def update_kis_prices_task(limit: int | None = 50, offset: int = 0, kis: KisClient | None = None):
    """
    Fetch current prices for companies from KIS API and update 'price_daily' table.
    Commits every 10 items to ensure progress visibility.
    """
    kis = kis or KisClient()
    print(f"Starting KIS Price Update Task (Limit: {limit})...")
    
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
