import argparse
from datetime import date, datetime, timedelta
import time

from sqlalchemy import text

from ingest.db import SessionLocal
from ingest.kis_client import KisClient


def _to_int(value: str | int | None):
    if value is None:
        return None
    if isinstance(value, int):
        return value
    value = str(value).strip().replace(",", "")
    if not value:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def _get_tickers(db):
    rows = db.execute(text("""
        SELECT s.ticker
        FROM security s
        JOIN company c ON s.company_id = c.company_id
        ORDER BY s.ticker ASC
    """)).fetchall()
    return [row.ticker for row in rows if row and row.ticker]


def _backfill_date(target_date: date, dry_run: bool = False) -> int:
    kis = KisClient()
    target_str = target_date.strftime("%Y%m%d")
    total_rows = 0
    with SessionLocal() as db:
        tickers = _get_tickers(db)
        for idx, ticker in enumerate(tickers, start=1):
            rows = kis.get_stock_daily_history(ticker, target_str, target_str)
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
                if trade_date != target_date:
                    continue
                if dry_run:
                    total_rows += 1
                    continue
                db.execute(text("""
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
                """), {
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
            if not dry_run and idx % 20 == 0:
                db.commit()
            time.sleep(0.1)
        if not dry_run:
            db.commit()
    return total_rows


def _apply_retention(retention_days: int, dry_run: bool = False) -> int:
    cutoff = date.today() - timedelta(days=retention_days)
    with SessionLocal() as db:
        count = db.execute(text("""
            SELECT COUNT(*) FROM price_daily WHERE trade_date < :cutoff
        """), {"cutoff": cutoff}).scalar() or 0
        if dry_run:
            return int(count)
        db.execute(text("""
            DELETE FROM price_daily WHERE trade_date < :cutoff
        """), {"cutoff": cutoff})
        db.commit()
    return int(count)


def main():
    parser = argparse.ArgumentParser(description="Backfill yesterday and apply price_daily retention.")
    parser.add_argument("--retention-days", type=int, default=365, help="Days to keep in price_daily.")
    parser.add_argument("--skip-retention", action="store_true", help="Skip retention delete.")
    parser.add_argument("--dry-run", action="store_true", help="Print counts only, no DB writes.")
    args = parser.parse_args()

    target_date = date.today() - timedelta(days=1)
    print(f"Backfilling date: {target_date}")
    backfill_count = _backfill_date(target_date, dry_run=args.dry_run)
    print(f"Backfill rows: {backfill_count}")

    if args.skip_retention:
        print("Retention skipped.")
        return

    print(f"Applying retention: keep last {args.retention_days} days")
    deleted = _apply_retention(args.retention_days, dry_run=args.dry_run)
    print(f"Retention deleted rows: {deleted}")


if __name__ == "__main__":
    main()
