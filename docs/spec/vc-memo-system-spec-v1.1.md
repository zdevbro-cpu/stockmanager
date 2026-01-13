# VC 투자심사 보고서 시스템 구축설계서 v1.1 (보완본)

본 문서는 기존 v1.0 설계(Deal/Evidence/Memo/DD/Verification/IC Pack)를 기반으로,
아래 3가지 보완 요구사항을 “실구축 가능한 수준(데이터모델/ETL/차트/UI/보고서)”으로 반영한 설계서입니다.

- (1) 재무제표 3개년 자료 정리 + 시계열 추이곡선(차트) 기능
- (2) 현재 적재(ECOS / KRX / 종목매핑 / DART공시 / DART 재무제표) + KIS 시세 연계 고려
- (3) KRX KIND 연계(시장조치/투자유의/공시) 포함

---

## 1. 보완 요구사항 반영 요약

### 1.1 재무제표 3개년 시계열 + 추이곡선(차트)

- 기본 범위
  - 연간: 최근 3개년(기본)
  - 분기: 최근 12분기(기본)
- 자동 산출/표현 항목
  - 손익: 매출, 매출총이익, 영업이익, 순이익
  - 재무상태: 자산, 부채, 자본
  - 현금흐름: 영업CF, 투자CF, FCF(=영업CF-투자CF)
  - 성장률: YoY(연간/분기), QoQ(분기), CAGR(가능 시)
  - 마진: GPM/OPM/NPM
  - 안정성: 부채비율, 유동비율, 이자보상배율(데이터 가능 범위)
- 정정/재표시 추적
  - 공시 정정(revision) 발생 시, 최신 revision을 대표값으로 사용하되, revision 로그를 별도 보관
  - IC 제출본에는 “정정 발생 여부/횟수”를 부록으로 자동 첨부

### 1.2 현재 데이터 소스 + KIS 시세 고려

- “기업 마스터키(Company)”와 “상장 종목(Security)”를 분리하여,
  - 우선주/스핀오프/복수상장/상폐 이력까지 안정적으로 처리
- Deal 화면에서
  - ECOS(거시) + KRX(시장/산업) + DART(공시/재무) + KIS(가격)을 한 축(타임라인)으로 겹쳐 분석 가능하게 구성

### 1.3 KIND 연계 정보 포함

- KIND는 “공시 원문”보다 VC 심사 관점에서 아래를 우선 반영
  - 시장조치/투자유의 플래그(거래정지, 관리종목, 불성실공시, 실질심사 등)
  - 자사주/배당/지배구조 관련 항목/공시
- 시스템 내 반영 방식
  - KIND 시장조치 수집 → Risk Register(risk_item) 자동 생성/갱신 → IC Pack의 Risks 섹션에 자동 포함

---

## 2. 데이터 아키텍처 (소스 → 저장 → 가공 → 보고서)

### 2.1 레이어 구분

- RAW (원천 적재)
  - ECOS/ KRX/ DART 공시/ DART 재무/ KIS 시세/ KIND 원문
- CORE (정규화/표준화)
  - Company/Security Master
  - fs_fact(표준 재무 팩트)
  - price_ohlcv(표준 가격)
  - kind_market_action(표준 시장조치)
- MART (보고서·차트용 집계)
  - 3개년/12분기 재무 요약
  - 재무비율/성장률
  - 수익률/변동성
  - 이벤트 타임라인(공시/시장조치/주가 오버레이)

---

## 3. 데이터 모델 (PostgreSQL 기준)

### 3.1 Company/Security Master

- company
  - company_id (PK)
  - name_ko, name_en, aliases(jsonb)
  - dart_corp_code, corp_reg_no, biz_reg_no
  - hq_address, industry, website
- security_master
  - security_id (PK)
  - company_id (FK)
  - stock_code(6), isin, market
  - share_type(보통주/우선주/리츠/ETF 등)
  - listing_date, delisting_date

> 권장: 회사와 종목 분리(회사 1 : 종목 N)

### 3.2 재무 표준 팩트 (DART FS)

- fs_fact (계정과목 단위)
  - company_id
  - period_type(ANNUAL/QUARTER)
  - fiscal_year, fiscal_quarter(nullable)
  - statement_type(IS/BS/CF)
  - consolidated(CFS/OFS)
  - account_code, account_name, amount, currency
  - as_of_date, disclosure_id(optional)
  - revision_no
  - loaded_at

### 3.3 재무 MART

- fs_mart_annual_3y (연간)
  - company_id, fiscal_year
  - revenue, gross_profit, op_income, net_income
  - assets, liabilities, equity
  - op_cf, inv_cf, fin_cf, fcf
- fs_mart_quarter_12q (분기)
  - company_id, fiscal_year, fiscal_quarter
  - 위 항목 + yoy/qoq 캐시(선택)
- fs_ratio_mart
  - company_id, period_type, fiscal_year, fiscal_quarter
  - gross_margin, op_margin, net_margin
  - debt_ratio, current_ratio, interest_coverage
  - revenue_yoy, op_income_yoy, cagr_3y(연간)

### 3.4 KIS 가격

- price_ohlcv_d
  - security_id, trade_date
  - open, high, low, close, volume, value
  - adj_close(optional), adj_factor(optional)
- price_return_mart
  - security_id, as_of_date
  - return_1m/3m/6m/1y, volatility_1y, max_drawdown_1y(optional)

### 3.5 ECOS

- macro_series / macro_point / macro_mart_for_deal(선택)

### 3.6 KIND

- kind_market_action
  - security_id
  - action_type, start_at, end_at, reason
  - severity(low/med/high)
- kind_disclosure(선택)
  - security_id, published_at, type, title, url, raw_payload

---

## 4. ETL/배치(운영 정책)

### 4.1 Daily

- KIS 일봉 적재
- KIND 시장조치/투자유의 업데이트
- DART 공시 신규/정정 모니터링

### 4.2 Quarterly/Annual

- DART 재무제표 갱신 → fs_fact 적재
- fs_mart_annual_3y / fs_mart_quarter_12q 재생성
- fs_ratio_mart 재계산
- 정정(revision) 발생 시 대표값 교체 + revision 로그 유지

### 4.3 On-demand(딜 생성 시)

- 회사/종목 매핑 검증
- 피어그룹(산업) 추천/조정
- “재무 3년 + 주가 1~3년 + 거시 3년” 차트 캐시 생성

---

## 5. 재무 3개년 시계열 추이곡선 기능(구현 지침)

### 5.1 기본 차트 세트

1) 손익 추이(연간/분기): 매출/영업이익/순이익
2) 마진 추이: GPM/OPM/NPM
3) 재무상태: 자산/부채/자본 + 부채비율
4) 현금흐름: 영업CF/투자CF/FCF
5) 성장률: YoY/QoQ

### 5.2 계산 로직

- YoY(연간): v[y]/v[y-1]-1
- YoY(분기): v[y,q]/v[y-1,q]-1
- QoQ: v[y,q]/v[y,q-1]-1
- CAGR(3Y): (v[y]/v[y-3])^(1/3)-1
- 정정: 최신 revision을 대표값으로 사용, revision 로그 별도 관리

### 5.3 차트 캐시

- chart_cache(company_id, chart_key, payload_json, generated_at)
- 프론트는 payload_json으로 렌더링(차트 라이브러리 교체가 쉬움)

---

## 6. 보고서(Investment Memo) 반영

### 6.1 FINANCIALS 섹션 자동 구성

- 3개년 요약 테이블
- 핵심 비율 테이블
- 차트 3~5개(기본세트)
- 정정 발생 시 배지/부록 자동 첨부
- 모든 수치는 근거 Evidence 링크를 자동 연결(가능한 범위)

### 6.2 RISKS 섹션: KIND 시장조치 자동 반영

- kind_market_action → risk_item 자동 생성/갱신
- IC Pack에 “시장조치 요약 + 기간 + 사유” 자동 포함

---

## 7. UI(권장 탭 구조)

- Deal
  - Overview
  - Evidence
  - Memo Builder
  - **Financials** (신규)
  - **Market & Price** (ECOS/KRX/KIS 통합)
  - DD & Risks (KIND 연계 포함)
  - IC Pack

---

## 8. 구현 체크리스트

1) fs_fact 표준화 + account_mapping
2) 3Y/12Q MART 배치
3) ratio 배치
4) KIS OHLCV 표준화 + return_mart
5) KIND market_action 적재 + risk_item 자동 반영 룰
6) Financials 탭 UI + chart_cache 렌더링
7) Memo Generator 재무 테이블/차트 삽입
8) IC Pack(PDF/DOCX) 차트 이미지 임베딩

---

## 9. 폴더 배치(권장)

- docs/spec/vc-memo-system-spec-v1.1.md  (본 문서)
- db/migrations/*.sql
- etl/jobs/*.ts
- functions/src/api/*.ts
- apps/web/src/features/deals/*.tsx
- templates/memo/memo-1.1.json
