import argparse
import sys
from sqlalchemy import text

sys.path.append("services/ingest")

from ingest.db import SessionLocal  # noqa: E402
from ingest.kis_loader import backfill_kis_prices_task  # noqa: E402


def load_watchlist_tickers() -> list[str]:
    with SessionLocal() as db:
        rows = db.execute(text("SELECT DISTINCT ticker FROM watchlist_item ORDER BY ticker")).fetchall()
    return [row[0] for row in rows if row[0]]


def main():
    parser = argparse.ArgumentParser(description="Backfill KIS daily prices.")
    parser.add_argument("--days", type=int, default=252, help="Number of days to backfill.")
    parser.add_argument("--tickers", type=str, default="", help="Comma-separated tickers.")
    parser.add_argument("--watchlist", action="store_true", help="Use watchlist tickers.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of tickers when using universe.")
    parser.add_argument("--offset", type=int, default=0, help="Offset for ticker list.")
    args = parser.parse_args()

    tickers: list[str] | None = None
    if args.tickers:
        tickers = [t.strip() for t in args.tickers.split(",") if t.strip()]
    elif args.watchlist:
        tickers = load_watchlist_tickers()

    backfill_kis_prices_task(
        days=args.days,
        tickers=tickers,
        limit=args.limit,
        offset=args.offset,
    )


if __name__ == "__main__":
    main()
