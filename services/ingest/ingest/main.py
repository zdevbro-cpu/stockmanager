"""Ingest entrypoint (Cloud Run job / Cloud Run service / local 실행용)

사용 예:
  python -m ingest.main --task kis_prices --from 2025-01-01 --to 2026-01-08

실제 구현은 TODO로 남겨둡니다. (본 스켈레톤은 방향 고정이 목적)
"""

import argparse


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--task", required=True, choices=["kis_prices", "krx_meta", "dart_filings", "ecos_series"])
    p.add_argument("--from", dest="date_from")
    p.add_argument("--to", dest="date_to")
    args = p.parse_args()

    # TODO: task별 실행
    print({"task": args.task, "from": args.date_from, "to": args.date_to})


if __name__ == "__main__":
    main()
