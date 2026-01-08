# stockmanager

실전 투자용 리서치/추천/시그널 시스템입니다. FastAPI 백엔드와 React 기반 웹앱을 함께 제공합니다.

## 로컬 실행 (Quick Start)
### 1) DB 기동
```bash
make db-up
```

### 2) `.env` 생성
루트의 `.env.example`을 참고하여 `.env`를 구성합니다.

### 3) API 의존성 설치
```bash
cd apps/api
pip install -r requirements.txt
```

### 4) 마이그레이션
```bash
make db-migrate
```

### 5) 샘플 데이터 로드
```bash
make db-seed
```

### 6) 추천/시그널 배치 실행
```bash
make worker-daily-close
```

### 7) API 실행
```bash
make api-run
```

### 8) Web 실행
```bash
cd apps/web
npm install
npm run dev
```

## API 확인 예시
- `GET /health`
- `GET /universe?as_of_date=2026-01-08&include_industry_codes=KIS_L1_10`
- `GET /recommendations?as_of_date=2026-01-08&strategy_id=prod_v1&strategy_version=1.0`
- `GET /signals?ticker=005930&horizon=1d`
- `GET /classifications/taxonomies`
- `GET /classifications/nodes?taxonomy_id=KIS_INDUSTRY&level=1`

## Web 기능 요약
- 데스크톱 Sidebar + 모바일 Bottom Tabs
- 추천 TopN + Explain(근거 시각화)
- Screener 필터(산업/테마/가격/거래대금)
- 관심종목/시그널/VC 리포트
- 데모 모드(오프라인 fixture 데이터)
