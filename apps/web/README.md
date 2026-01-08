# StockManager Web

FastAPI 백엔드와 연동되는 반응형 웹 프론트엔드입니다.

## 실행 방법
```bash
cd apps/web
npm install
npm run dev
```

## 주요 기능
- 데스크톱 Sidebar + 모바일 Bottom Tabs 기반 네비게이션
- 추천 TopN 및 Explain(근거 시각화)
- Screener 필터(산업/테마/가격/거래대금)
- 관심종목/시그널/VC 리포트 빌더
- 데모 모드(오프라인 fixture 데이터 렌더)

## 환경/설정
- 기본 API Base URL: `http://localhost:8000`
- 설정 화면에서 API URL 및 데모 모드를 변경할 수 있습니다.
