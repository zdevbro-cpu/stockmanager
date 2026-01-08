from __future__ import annotations

import os
import random
from datetime import date, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.orm import (
    Security,
    ClassificationTaxonomy,
    ClassificationNode,
    SecurityClassification,
    PriceDaily,
)

DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    raise RuntimeError("DATABASE_URL env var is required")

engine = create_engine(DB_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

random.seed(42)


def main():
    session = SessionLocal()

    # Taxonomies
    session.merge(
        ClassificationTaxonomy(
            taxonomy_id="KIS_INDUSTRY",
            kind="INDUSTRY",
            name="KIS 산업분류",
            provider="KIS",
            version="v1",
        )
    )
    session.merge(
        ClassificationTaxonomy(
            taxonomy_id="THEME",
            kind="THEME",
            name="테마(내부)",
            provider="INTERNAL",
            version="v1",
        )
    )

    # Minimal industry nodes (sample)
    industry_nodes = [
        ("KIS_L1_10", "반도체", 1, None),
        ("KIS_L1_20", "화학", 1, None),
        ("KIS_L1_30", "기계", 1, None),
        ("KIS_L1_40", "금융", 1, None),
    ]
    for code, name, level, parent in industry_nodes:
        session.merge(
            ClassificationNode(
                taxonomy_id="KIS_INDUSTRY",
                code=code,
                name=name,
                level=level,
                parent_code=parent,
                extra=None,
            )
        )

    # Themes (sample)
    themes = [
        ("theme_ai", "AI", 1, None),
        ("theme_battery", "2차전지", 1, None),
        ("theme_fintech", "핀테크", 1, None),
    ]
    for code, name, level, parent in themes:
        session.merge(
            ClassificationNode(
                taxonomy_id="THEME",
                code=code,
                name=name,
                level=level,
                parent_code=parent,
                extra=None,
            )
        )

    # Securities (sample)
    securities = [
        ("005930", "삼성전자", "KRX_KOSPI", "KIS_L1_10", ["theme_ai"]),
        ("000660", "SK하이닉스", "KRX_KOSPI", "KIS_L1_10", ["theme_ai"]),
        ("051910", "LG화학", "KRX_KOSPI", "KIS_L1_20", ["theme_battery"]),
        ("006400", "삼성SDI", "KRX_KOSPI", "KIS_L1_20", ["theme_battery"]),
        ("035420", "NAVER", "KRX_KOSPI", "KIS_L1_10", ["theme_ai"]),
        ("035720", "카카오", "KRX_KOSPI", "KIS_L1_10", ["theme_ai"]),
        ("105560", "KB금융", "KRX_KOSPI", "KIS_L1_40", ["theme_fintech"]),
        ("055550", "신한지주", "KRX_KOSPI", "KIS_L1_40", ["theme_fintech"]),
        ("028260", "삼성물산", "KRX_KOSPI", "KIS_L1_30", []),
        ("012330", "현대모비스", "KRX_KOSPI", "KIS_L1_30", []),
    ]

    end = date.today()
    start = end - timedelta(days=120)
    effective_from = start

    for tkr, name, market, ind_code, tms in securities:
        session.merge(
            Security(
                ticker=tkr,
                name_ko=name,
                market=market,
                listed_date=None,
                is_active=True,
            )
        )
        session.merge(
            SecurityClassification(
                ticker=tkr,
                taxonomy_id="KIS_INDUSTRY",
                code=ind_code,
                effective_from=effective_from,
                is_primary=True,
                source="SEED",
            )
        )
        for tm in tms:
            session.merge(
                SecurityClassification(
                    ticker=tkr,
                    taxonomy_id="THEME",
                    code=tm,
                    effective_from=effective_from,
                    is_primary=False,
                    confidence=0.90,
                    source="SEED",
                )
            )

    # Prices (sample random walk for ~90 business days)
    for tkr, *_ in securities:
        price = random.uniform(30000, 150000)
        d = start
        while d <= end:
            if d.weekday() < 5:
                r = random.gauss(0, 0.015)
                price = max(1000, price * (1 + r))
                turnover = abs(random.gauss(1.5e11, 8e10))
                volume = abs(random.gauss(2e6, 1e6))
                session.merge(
                    PriceDaily(
                        ticker=tkr,
                        trade_date=d,
                        close=float(price),
                        volume=float(volume),
                        turnover_krw=float(turnover),
                    )
                )
            d += timedelta(days=1)

    session.commit()
    session.close()
    print("Seed 완료: taxonomy/nodes/securities/prices")


if __name__ == "__main__":
    main()
