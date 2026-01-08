# ingest service
KRX/DART/ECOS/KIS 데이터를 수집하여 Cloud SQL에 적재하는 워커입니다.

## 원칙
- 멱등 적재(중복 없음)
- 실패 재시도
- 데이터 검증(누락/이상치/시점오류) 후 저장/차단

TODO:
- 각 커넥터 구현(krx.py, dart.py, ecos.py, kis.py)
