from __future__ import annotations

import argparse
from datetime import date

from worker.jobs.daily_close import StrategyParams, run as run_daily_close


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--job", required=True, choices=["daily_close"])
    p.add_argument("--asof", required=True, help="YYYY-MM-DD")
    p.add_argument("--top_n", type=int, default=5)
    args = p.parse_args()

    as_of = date.fromisoformat(args.asof)

    if args.job == "daily_close":
        params = StrategyParams(top_n=args.top_n)
        run_daily_close(as_of, params)
        print({"job": args.job, "asof": as_of.isoformat(), "status": "OK"})


if __name__ == "__main__":
    main()
