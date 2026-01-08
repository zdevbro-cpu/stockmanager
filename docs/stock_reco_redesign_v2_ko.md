# 주식종목추천 + 매매타이밍 + VC 투자심사 리포트 시스템 재설계안 (KRX/DART/ECOS/KIS 기반)

작성일: 2026-01-08 (KST)  
목표: KRX·DART·ECOS·KIS 데이터를 통합해 **(1) 종목 스크리닝/추천**, **(2) 관심종목 매수·매도 타이밍 신호**, **(3) VC/투자심사 수준의 기업분석 보고서**를 자동 생성하는 제품으로 재정렬.

---

## 1) 제품 목표를 3개 “결과물(Outputs)”로 고정하기

### Output A. 종목추천(스크리너/랭킹)
- **유니버스**(시장/유동성/상장기간/제외규칙) + **퀀트 점수**(팩터/모델)로
- “오늘/이번주/이번달 추천 Top N” + 근거(점수, 팩터 기여도, 리스크) 제공

### Output B. 관심종목 매수·매도 타이밍(Execution/Signal)
- 추천 종목 또는 사용자가 선택한 종목에 대해
- “지금 매수/대기/축소/매도” 신호와 **트리거 조건**(가격·변동성·이벤트·시장국면)을 제공
- (선택) KIS로 모의/실거래 주문 실행

### Output C. 투자심사/VC 리포트(기업분석 보고서)
- 재무·성장·현금흐름·밸류에이션·리스크·시나리오(베어/베이스/불) + 공시 근거(링크/인용) 포함
- “투자 메모(Investment Memo)” 형태의 PDF/HTML 리포트 생성 + 버전관리

---

## 2) 핵심 설계 원칙(이번 재설계에서 반드시 지킬 것)

1. **Point-in-time**: ‘그 시점에 알 수 있었던 정보’만 사용 (재무/공시는 발표일 이후 반영)
2. **Survivorship-free**: 상장폐지/관리종목 이력 포함 유니버스
3. **설명가능성(Explainability)**: 추천/타이밍/리포트에 “근거 데이터 + 계산 경로”를 남긴다
4. **전략/리포트의 버전관리**: JSON 스키마 기반(룰·가중치·제약·비용가정·모델버전)
5. **실거래/모의 분리**: same code, different config + 권한 통제
6. **검증 우선**: 백테스트/워크포워드/과최적화 방지 프로토콜을 MVP부터 내장

---

## 3) 데이터 소스와 역할(무엇을 어디에 쓰는가)

### 3.1 KIS (한국투자증권) — 시장데이터 + 실행(주문/체결)
- 역할: 시세/호가/체결/계좌/주문 실행(실거래/모의)
- 실무 포인트:
  - REST 접근토큰(access_token) 기반 인증(유효기간/갱신 정책 존재)  
  - 실시간(WebSocket)용 별도 키(approval_key) 존재

### 3.2 KRX — 시장 통계/기본 데이터(공매도, 지수/수급 등)
- 역할: 시장/종목 통계, 참고 지표, (가능한 범위에서) 공매도/거래대금/지수 구성 등
- 대안: data.go.kr의 KRX 상장종목 기본정보도 보완재로 활용(일 1회 갱신)

### 3.3 DART — 공시/재무/주석/정정 이력(투자심사 근거의 핵심)
- 역할: 공시 원문/정기·수시공시, 재무제표/주석 추출, 이벤트 시그널(실적발표·유증·M&A 등)
- 실무 포인트: corp_code, bgn_de/end_de, 공시유형 필터 등 파라미터 제약/기간 제한 존재

### 3.4 ECOS — 거시지표(금리/물가/환율/경기지표 등)
- 역할: 시장 국면(regime) 분류, 리스크 프리미엄, 할인율/시나리오 가정, 리포트 매크로 섹션

---

## 4) 시스템 아키텍처(권장: Firebase + Cloud Run/Functions + Cloud SQL)

### 4.1 레이어 구조
1) **Ingestion Layer**: KIS/KRX/DART/ECOS 커넥터(배치/스트리밍)  
2) **Raw Store(Data Lake)**: 원본 JSON/CSV/ZIP + 공시 원문(스토리지)  
3) **Staging/ODS**: 정규화 테이블(Cloud SQL)  
4) **Feature Store(시점정합)**: 팩터/피처 테이블 + `effective_from` 관리  
5) **Signal Engine**:
   - 추천 엔진(랭킹/스코어)
   - 타이밍 엔진(진입/청산/리스크)
6) **Backtest/Validation**: 전략 실험, 워크포워드, 리포트  
7) **Report Engine**:
   - VC 리포트 템플릿
   - 근거 링크/인용(공시) 자동 첨부
8) **API Layer**: 추천/타이밍/리포트/전략관리 API  
9) **Frontend**: 스크리너/대시보드/리포트 빌더/전략 랩  
10) **Observability/Governance**: 로그, 지표, 감사추적, 권한

### 4.2 저장소 권장 조합
- Cloud SQL(PostgreSQL): 정규화 데이터/피처/전략/결과
- Firebase Storage(or GCS): 공시 원문/리포트(PDF)/학습 아티팩트
- (선택) Vector DB: 공시/뉴스 RAG(근거 기반 서술)

---

## 5) 데이터 모델(핵심 테이블) — “추천 + 타이밍 + VC 리포트”를 위한 최소 세트

### 5.1 마스터
- `company`(corp_code, stock_code, name, market, sector, listing_date, delisting_date, status)
- `security`(ticker, isin, market, currency, lot_size, tick_size 등)

### 5.2 시세/시장
- `price_daily`(ticker, date, ohlcv, adj_factor)
- `orderbook_snapshot`(ticker, ts, bid/ask levels) *(선택)*
- `market_index_daily`(index_code, date, close, ret, vol)
- `short_selling_stats`(ticker, date, short_vol, short_ratio) *(가능 범위)*

### 5.3 공시/재무(DART)
- `dart_filing`(rcp_no, corp_code, filing_date, type, title, url, is_last_report)
- `financial_statement`(corp_code, period_end, announced_at, item_code, value, unit, consolidated_flag)
- `fs_notes_doc`(rcp_no, doc_uri, extracted_text_path) *(RAG용)*

### 5.4 거시(ECOS)
- `macro_series`(series_code, date, value, unit, source)

### 5.5 피처/팩터(시점정합)
- `feature_snapshot`(as_of_date, ticker, feature_name, value, effective_from, data_version)
- `factor_score`(as_of_date, ticker, value_score, quality_score, momentum_score, total_score, model_version)

### 5.6 전략/실험/결과
- `strategy_def`(strategy_id, version, json, created_at)
- `backtest_run`(run_id, strategy_id, version, start, end, cost_model, metrics_json, artifacts_path)
- `recommendation`(as_of_date, strategy_id, version, ticker, rank, score, rationale_json)
- `timing_signal`(ts, ticker, horizon, signal, confidence, triggers_json, risk_flags_json)

### 5.7 리포트
- `report_request`(report_id, corp_code/ticker, template, as_of, status)
- `report_artifact`(report_id, file_path, format, created_at, citations_json)

---

## 6) 퀀트 추천 엔진(랭킹) 설계 — “결정이 아니라 근거 있는 후보군 생성”

### 6.1 추천의 기본 형태(권장)
- **(월/주) 스크리닝 랭킹** + **(일/분) 타이밍 필터**의 2단 구조
  - 추천 엔진은 “좋은 후보”를 뽑고
  - 타이밍 엔진이 “언제 들어갈지/나올지”를 결정

### 6.2 추천 알고리즘 3단계
1) **Universe 필터**
   - 유동성(거래대금), 상장기간, 거래정지 제외 규칙 등
2) **팩터 점수화(설명가능)**
   - Value: PBR, PER(주의: 음수/적자 처리 정책 필요)
   - Quality: ROE, 영업이익률, 부채비율, 이익의 질(현금흐름)
   - Momentum: 3/6/12개월 수익률(단, 최근 1개월 역모멘텀 방지 옵션)
   - Risk: 변동성/베타/최대낙폭을 패널티로 반영 가능
3) **결합 + 제약**
   - total_score = w1*value + w2*quality + w3*momentum - w4*risk
   - 섹터 편중 제한, 개별 종목 최대비중, 턴오버 제한

### 6.3 (선택) ML 랭킹으로 확장
- label을 “다음 1개월 초과수익 상위구간”으로 두고
- 트리 기반 모델로 랭킹 점수 산출
- 단, **시간분할 검증**과 **피처 누수 방지**가 필수

---

## 7) 타이밍 엔진(매매/매수 타이밍) — “추천 종목의 진입/청산 규칙”

### 7.1 타이밍 신호의 기본 구성(권장)
- **추세 필터**(진입 허용/금지): 예) 60일 MA 위에 있을 때만 매수
- **변동성 필터**: 변동성 급등 시 신규 진입 금지
- **이벤트 리스크 필터(DART)**: 실적발표/유증/소송/감사/정정 등 이벤트 전후 정책
- **포지션 관리**: 손절/익절/트레일링 스탑(정책), 포지션 크기(리스크 기반)

### 7.2 신호 출력 예시(제품 UX)
- 상태: `BUY / WAIT / REDUCE / SELL`
- 신뢰도: 0~1
- 트리거:
  - “종가가 20일 고점 돌파 시 BUY”
  - “변동성 z-score > 2면 WAIT”
  - “중요 공시 예정일 2거래일 전이면 WAIT”

### 7.3 KIS 연동 범위(선택)
- MVP: 신호만 제공(실거래는 미포함)
- 확장: 모의투자 실행 → 실거래 실행(권한/감사로그/리스크 제한 필요)

---

## 8) VC/투자심사 리포트 엔진 설계(핵심: 근거 + 시나리오 + 리스크)

### 8.1 리포트 템플릿(권장 섹션)
1) Executive Summary (핵심 결론/리스크/다음 액션)
2) Business & Moat(사업/경쟁우위) *(정성+정량)*
3) Market/TAM & 경쟁환경 *(자료 출처 표기)*
4) Financial Deep Dive (DART 기반)
   - 성장률, 마진, ROIC/ROE, 레버리지, 현금흐름
5) Valuation (멀티플/DCF 선택)
   - 할인율/성장률 가정은 ECOS 지표로 보조(금리 등)
6) Catalysts & Risks
   - 공시 기반 이벤트 타임라인(유증, 소송, 감사의견 등)
7) Scenario(베어/베이스/불) + 감도분석
8) Appendix
   - 주요 공시 링크/발췌(근거), 지표 테이블, 차트

### 8.2 “근거 기반 작성”을 위한 RAG 구조(권장)
- 입력 문서: 사업보고서/분기보고서/주요사항보고서 + 정정 포함
- 파이프라인:
  1) 공시 원문 수집 → 2) 문단/표 단위 분해 → 3) 벡터 인덱싱
  4) 리포트 섹션별 질문 템플릿 → 5) 답변 생성 + **인용** 첨부
- 결과: “서술(LLM)” + “정량 계산(코드)”를 결합(가장 중요)

---

## 9) 검증/품질(이번 재설계에서 ‘디테일’을 담보하는 장치)

### 9.1 실험 프로토콜(기본)
- 워크포워드(rolling) 백테스트
- 거래비용/슬리피지 기본 탑재
- 파라미터 민감도(조금 바꿔도 유지되는지)
- 데이터 누수 체크 자동화(재무 발표일 이전 사용 금지)

### 9.2 운영 품질 지표
- 추천 품질: hit ratio, top-decile spread, 정보비율(가능하면)
- 타이밍 품질: 신호 후 성과, false signal ratio, turnover
- 리포트 품질: 인용 커버리지(%), 최신성(데이터 스탬프), 누락 경고

---

## 10) API/화면(기능 블록) — “디테일이 떨어지지 않게” 경계 정의

### 10.1 주요 API
- `GET /universe` (필터/조건)
- `GET /recommendations?as_of=...&strategy=...`
- `GET /signals?ticker=...&horizon=...`
- `POST /watchlist/{id}/simulate` (타이밍 시뮬레이션)
- `POST /reports` (리포트 생성 요청)
- `GET /reports/{id}` (상태/다운로드)
- `POST /strategies` / `POST /backtests` (전략/실험 관리)

### 10.2 화면(UX)
- Screener: 필터 + 랭킹 + 근거 패널
- Stock Detail: 팩터/재무/공시 타임라인 + 타이밍 신호
- Watchlist: 신호 알림 + 리밸런싱 추천
- Strategy Lab: 전략 정의/백테스트/비교
- Report Builder: 템플릿 선택 → 근거 확인 → PDF 생성

---

## 11) 단계별 구현 로드맵(현실적인 MVP → 확장)

### Phase 0 (2~3주): 데이터 기반 구축
- corp_code/종목코드 매핑, 가격 일봉 적재, DART 공시/재무 기본 적재, ECOS 주요 금리/물가 적재
- point-in-time 메타(announced_at/effective_from) 설계

### Phase 1 (3~5주): 추천 MVP
- 팩터 3종 랭킹(가치/퀄리티/모멘텀) + 유니버스 필터 + 월 1회 리밸런싱 백테스트
- 추천 결과(근거 포함) API/화면 제공

### Phase 2 (3~5주): 타이밍 MVP
- 추세/변동성/이벤트 필터 기반 BUY/WAIT/SELL 신호
- 관심종목 알림(푸시/메일) + 시뮬레이션 리포트

### Phase 3 (4~8주): VC 리포트 MVP
- 공시 RAG + 재무지표 자동 계산 + 템플릿 PDF 생성
- 인용/근거 커버리지, 최신성 경고

### Phase 4: 실거래/고급화(선택)
- KIS 모의→실거래, 리스크 제한, 감사로그
- ML 랭킹 모델/시나리오 자동화/감도 분석 고급화

---

## 12) “추가로 필요한 정보” (있으면 설계를 더 정확히 좁힐 수 있음)
- 대상 시장: 국내(코스피/코스닥)만? ETF/리츠 포함?  
- 운용 지평: 단기(일~주) vs 중기(월~분기) vs 장기  
- 추천 출력: Top N(예: 10/20/50) + 비중까지?  
- 실거래 범위: 신호만 vs 모의주문 vs 실주문  
- VC 리포트 대상: 상장사만? 비상장(스타트업)도 포함?  
- 리포트 포맷: PDF 중심? PPT/워드도 필요한지?

---

## 13) 바로 다음 액션(추천)
1) **“Output A/B/C” 각각의 성공 기준(KPI)** 1줄씩 정의  
2) Universe 규칙과 거래비용/슬리피지 가정을 고정  
3) 전략 정의 JSON 스키마 v2(추천+타이밍+리포트)로 확장  
4) Phase 0 데이터 매핑(회사/종목코드/공시)부터 안정화
