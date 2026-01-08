# CODEX PROMPT (단일 파일) — StockManager 반응형 웹앱 구현 v1
작성일: 2026-01-08 (Asia/Seoul)

본 파일은 **Codex(코딩 에이전트)** 에 그대로 입력하여, 현재 `stockmanager` 백엔드 골격(FastAPI + Postgres + worker)과 연결되는 **반응형 웹앱(React + Vite + Tailwind)** 을 구현하기 위한 **단일 통합 프롬프트**입니다.
- 목적: “추천 Top N + 비중”을 빠르게 확인 → 산업/테마 필터 → 추천 근거(분석보기/Explain) → 관심종목 신호(매수/대기) → VC 리포트(초기: UI/저장/Export placeholder)
- 주문/자동매매: **없음(수동 주문만)**

---

## 0) 필수 규칙 (Codex가 지켜야 할 것)
1. **반말 금지.** 코드 주석/문서/커밋 메시지/프롬프트 출력은 **정중한 한국어**로 작성하십시오.
2. “엉뚱한 방향”으로 흐르는 것을 방지하기 위해, 아래 **요구사항/수용기준**을 벗어나는 확장은 하지 마십시오.
3. 구현은 **실행 가능**해야 합니다. 로컬에서 `pnpm dev` 혹은 `npm run dev`로 프론트가 실행되어야 합니다.
4. 스타일은 **데이터 중심(fintech)**, 과도한 일러스트/애니메이션 금지. 재사용 컴포넌트 중심.
5. UI는 **반응형**: Desktop(사이드바) / Mobile(하단 탭) 모두 지원.
6. 백엔드 인증은 현재 스텁일 수 있으므로, 프론트는 **로그인 UI는 두되** 기본은 “로컬 데모 모드”로 동작 가능하게 하십시오.

---

## 1) 기술 스택 (고정)
- Frontend: **Vite + React + TypeScript + TailwindCSS**
- Routing: React Router
- Data fetching/cache: TanStack Query(React Query) 권장
- UI 컴포넌트: 가능하면 shadcn/ui 형태(또는 최소한의 자체 컴포넌트)로 “Table / Drawer / Badge / Chip / Tabs / Dialog / Toast” 제공
- Charts: 초기에는 **placeholder(빈 박스 + 라벨)** 로 두고, 나중에 Recharts로 대체 가능하도록 인터페이스만 마련
- Lint/format: ESLint + Prettier(가능하면)

**주의:** 백엔드는 이미 존재합니다(FastAPI). 프론트는 API 호출 중심으로 구현하십시오.

---

## 2) 레포 구조 가정
현재 작업 폴더: `stockmanager`
- 백엔드: `apps/api`
- 워커: `services/worker`
- 프론트 신규 생성: `apps/web` (이번 작업에서 생성)

Codex는 `apps/web`를 새로 만들고, 루트에 실행 스크립트/문서도 추가하십시오.

---

## 3) API 엔드포인트 (현재 골격 기준 — 반드시 연결)
백엔드가 로컬에서 실행 중일 때(기본):
- Base URL: `http://localhost:8000` (백엔드 포트가 다르면 `.env`로 변경 가능)

필수 사용(최소 연결):
1. `GET /health`
2. `GET /universe?as_of_date=YYYY-MM-DD&include_industry_codes=...&include_theme_ids=...`
3. `GET /recommendations?as_of_date=YYYY-MM-DD&strategy_id=prod_v1&strategy_version=1.0`
4. `GET /signals?ticker=005930&horizon=1d`
5. `GET /classifications/taxonomies`
6. `GET /classifications/nodes?taxonomy_id=KIS_INDUSTRY&level=1`
7. `GET /classifications/securities/{ticker}` (상세보기/태그 표시용)

프론트는 위 API에 대한 **타입(interfaces)** 를 정의하고, 각 화면에서 호출/표시하십시오.

---

## 4) UI/UX 화면 분리(IA) — 반드시 이대로 구현
### 네비게이션 규칙
- Desktop(>=1024px): 좌측 Sidebar + 상단 TopBar
- Mobile(<1024px): 상단 TopBar + 하단 Bottom Tabs
- 공통 TopBar: 검색(티커/회사명), 기준일(as_of_date) 선택, (옵션) 사용자 메뉴

### 라우트(필수)
- `/` : Home Dashboard
- `/screener` : Screener(유니버스/필터)
- `/recommendations` : 추천 TopN + Explain(분석보기)
- `/signals` : Signals(타이밍)
- `/watchlist` : Watchlist
- `/reports` : Reports (VC 리포트: Library + Builder + Preview)
- `/settings` : Settings(환경/데모 모드/백엔드 URL)

---

## 5) 와이어프레임 레퍼런스(반드시 참고)
아래 이미지를 UI 구조 참고로 사용하십시오(흑백 와이어프레임).
- Desktop:
  - `wireframe_home_desktop_bw.png`
  - `wireframe_screener_desktop_bw.png`
  - `wireframe_recommendations_explain_desktop_bw.png`
  - `wireframe_signals_desktop_bw.png`
  - `wireframe_watchlist_desktop_bw.png`
  - `wireframe_reports_vc_builder_desktop_bw.png`
- Mobile:
  - `wireframe_mobile_shell_bw.png`
  - `wireframe_signals_mobile_bw.png`
  - `wireframe_watchlist_mobile_bw.png`
  - `wireframe_reports_mobile_bw.png`

## 5.1) Stitch 디자인 산출물(필수 참고)
- Stitch로 생성한 디자인(또는 코드/컴포넌트)을 “최우선 UI 기준”으로 사용하십시오.
- 구현 시 다음 우선순위를 따르십시오.
  1) Stitch 산출물의 레이아웃/컴포넌트 구조/간격/타이포/색상 토큰
  2) 본 문서의 IA(라우트/기능 배치) 및 수용 기준
  3) 와이어프레임(영역 분할)

### Stitch 산출물 배치 규칙(프로젝트 내)
- Stitch에서 export 받은 결과물을 아래 폴더에 저장(또는 복사)하여 레퍼런스로 사용하십시오.
  - `docs/ui/stitch/` : Stitch 결과물(이미지, 스펙, Figma export, 코드 스니펫 등)
  - `docs/ui/wireframes/` : 본 와이어프레임 PNG
- Stitch에서 React 코드 export가 가능하면, 우선 `apps/web/src/stitch/`에 원본을 보관한 뒤,
  실제 앱 코드는 `apps/web/src/` 구조에 맞게 재구성(리팩터링)하십시오.
- Stitch 산출물과 요구사항이 충돌하면, “기능/데이터 표시 요구사항”을 우선 충족하되
  시각 디자인(토큰/컴포넌트 스타일)은 Stitch를 최대한 유지하십시오.


**요구:** 화면 레이아웃은 위 와이어프레임의 영역 분할을 유지하되, 세부 스타일은 현대적인 fintech UI로 구현하십시오.

---

## 6) 공통 컴포넌트(반드시 구현)
1. `DatePicker` (as_of_date): 기본값은 “오늘(로컬)”
2. `SearchBox`: 티커/회사명 입력 (초기: 프론트 필터만)
3. `DataTable`: 정렬/로딩 스켈레톤/빈 상태 지원
4. `Badge` / `Chip` : Signal/Theme/Industry 표시
5. `Drawer`(Desktop 오른쪽 패널 or Mobile BottomSheet): Explain, 상세보기 등에 사용
6. `Toast` 알림: API 실패/네트워크 오류 등
7. `FilterPanel`: Screener 필터(산업/테마/가격/거래대금)
8. `EmptyState` / `ErrorState` / `Skeleton`

---

## 7) 도메인 모델(타입 정의) — 프론트에 필수
### UniverseItem
- ticker: string
- name_ko: string
- market: string
- sector_name: string | null
- avg_turnover_krw_20d: number | null
- last_price_krw: number | null

### RecommendationItem
- as_of_date: string
- strategy_id: string
- strategy_version: string
- ticker: string
- rank: number
- score: number | null
- target_weight: number
- rationale: object | null  (그대로 JSON 표시/해석)

### SignalItem
- ts: string (ISO)
- ticker: string
- horizon: string
- signal: "BUY" | "WAIT" | "REDUCE" | "SELL" | string
- confidence: number | null
- triggers: string[]
- risk_flags: string[]
- model_version: string | null

### Classification
- taxonomy_id: string
- code: string
- name: string
- level: number | null
- parent_code: string | null

---

## 8) 화면별 요구사항(기능 배치)
### 8.1 Home Dashboard (`/`)
- 상단 KPI 카드: Universe Count(간이), Top N, Last update(간이), 기준일 표시
- “Today’s Recommendations” 카드/테이블:
  - Rank, Ticker, Name, Target Weight, (optional) Score
  - “Explain” 버튼 → Explain Drawer 오픈(추천 근거)
  - “Add to Watchlist” 버튼
- “Watchlist Signals Summary”:
  - Watchlist에 등록된 티커들에 대해 최신 신호 표시(없으면 빈 상태)
- 우측(Desktop): Industry/Theme snapshot은 초기 placeholder

### 8.2 Screener (`/screener`)
- Desktop: 좌측 필터 패널 + 우측 결과 테이블
- Mobile: Filter Drawer(Bottom Sheet) + 결과 리스트
- 필터:
  - Industry picker (KIS): `GET /classifications/nodes?taxonomy_id=KIS_INDUSTRY&level=1`로 1차 구현(추후 tree 확장 고려)
  - Theme chips: `taxonomy_id=THEME` 노드 목록 호출(없으면 하드코딩 placeholder 가능)
  - Min price, Min turnover 입력
- 결과 테이블: ticker/name/market/sector/price/turnover
- Row 클릭 → 상세 Drawer:
  - classifications(security): `GET /classifications/securities/{ticker}`
  - quick actions: Add watchlist / Open signals / Open recommendations

### 8.3 Recommendations + Explain (`/recommendations`)
- 상단: as_of_date + strategy_id/version 선택(기본: prod_v1 / 1.0) + Export 버튼(placeholder)
- 추천 테이블: Rank / Ticker / Target Weight / Score
- Explain Drawer(핵심):
  - rationale JSON에서 아래 섹션을 “보기 좋게” 시각화
    - Summary: 총점, 타겟비중, 산업/테마
    - Filters: 통과/실패 규칙(배지)
    - Factors: 기여도 리스트(가중치/기여값)
    - Constraints: 제약조건 리스트
    - Event risk flags: 경고 영역(없으면 비표시)
  - JSON 원문 보기(접기/펼치기)도 제공

### 8.4 Signals (`/signals`)
- 상단: horizon tabs(1d/3d/1w UI만)
- 기본은 Watchlist 기반으로 보여주되, ticker 직접 입력 검색도 가능
- 리스트/테이블:
  - ticker/name(가능하면), signal badge, confidence, triggers, updated
- Row 클릭 → 상세 Drawer:
  - mini chart placeholder
  - triggers/history placeholder

### 8.5 Watchlist (`/watchlist`)
- 로컬 저장(최소): localStorage에 watchlist tickers 저장
- UI:
  - Add ticker(검색 입력 + 추가)
  - table/cards: ticker/name/industry/themes/latest signal/in-reco badge
  - per ticker note(메모) 저장(localStorage)
- 추천 포함 여부(in-reco):
  - `/recommendations` 데이터와 join하여 표시

### 8.6 Reports (`/reports`)
- 상단 세그먼트: Library | Builder | Preview (모바일과 데스크톱 공통)
- Library: 생성된 리포트 목록(초기 localStorage로 저장)
- Builder(VC 리포트 빌더):
  - Stepper: Company → Business → Financials → Risks → Memo
  - 폼 입력 결과는 localStorage에 저장
- Preview:
  - 문서형 레이아웃(타이틀/섹션/불릿)
  - Export PDF 버튼은 placeholder(비활성 가능)
- 비상장도 포함: Company 선택 단계에서 “listed/unlisted” 토글 필수

### 8.7 Settings (`/settings`)
- API Base URL 설정(기본 http://localhost:8000)
- 데모 모드 토글(오프라인: fixture JSON으로 화면 렌더) — **필수 구현**
  - 백엔드가 꺼져 있어도 UI 데모 가능해야 합니다.

---

## 9) 상태/데이터 패턴(반드시 적용)
- 전역 상태:
  - as_of_date (전역)
  - apiBaseUrl (settings)
  - watchlist (localStorage + in-memory)
- 데이터 fetch:
  - React Query를 사용하여 캐싱/리패치/에러 처리
- 모든 API 호출은 `src/lib/apiClient.ts`에 모아서 구현
- 요청 실패 시 Toast + ErrorState를 표시

---

## 10) 구현 단계(작업 순서) — Codex가 그대로 따라야 함
1) `apps/web` 생성 (Vite React TS + Tailwind 설정) + 실행 확인
2) 라우팅/레이아웃(Desktop Sidebar + Mobile Bottom Tabs) 공통 골격 구현
3) Settings 페이지 + apiBaseUrl 저장(localStorage) + demoMode 토글 구현
4) API Client + 타입 정의 + React Query provider 구성
5) Home 화면: 추천/설명 Drawer 연결
6) Screener: 필터 UI + universe 호출 + row detail drawer
7) Recommendations: 추천 테이블 + Explain Drawer(JSON 해석)
8) Watchlist: localStorage 기반 CRUD + 신호/추천 join 표시
9) Signals: watchlist 기반 신호 표시 + 상세 drawer
10) Reports: Library/Builder/Preview + localStorage 저장
11) Empty/Error/Skeleton 정리 + 접근성(키보드 포커스) 확인
12) README 업데이트(실행 방법/환경변수)

---

## 11) 수용 기준(완료 정의) — 반드시 모두 만족
- [ ] `apps/web`에서 `npm run dev`(또는 pnpm)로 프론트 실행 가능
- [ ] 모바일/데스크톱 반응형 네비게이션 동작
- [ ] as_of_date 변경 시 Home/Screener/Recommendations가 함께 갱신
- [ ] Screener: 산업/테마/가격/거래대금 필터가 API 파라미터로 반영
- [ ] Recommendations: Explain Drawer가 rationale JSON을 사람이 읽기 좋게 표시
- [ ] Watchlist: 종목 추가/삭제/메모 저장/복원(localStorage)
- [ ] Signals: Watchlist 기반 최신 신호 표시
- [ ] Reports: Builder 입력 저장/Preview 렌더
- [ ] Demo mode에서 백엔드 없이도 주요 화면 렌더 가능
- [ ] 코드 품질: 타입 에러 없고, 빌드 시도 시 큰 오류 없음

---

## 12) 출력물 요구(필수 파일)
Codex는 작업 완료 후 아래를 반드시 포함하여 제출하십시오.
- 변경된 파일 목록 요약
- 실행 방법(명령어) 요약
- (가능하면) 화면 확인 가이드(어느 페이지에서 무엇을 확인하면 되는지)

---

## 13) Codex에게 마지막 요청
위 요구사항을 기준으로 `apps/web`를 구현하십시오.
- 과도한 추상화/과도한 기능 추가는 금지합니다.
- “데이터를 잘 보여주는 UX”와 “근거(Explain) 가독성”에 집중하십시오.
- 모든 텍스트는 기본적으로 **한국어**(기업명/티커는 원문)로 표현하십시오.
