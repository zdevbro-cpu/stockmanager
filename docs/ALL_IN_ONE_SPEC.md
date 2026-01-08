# STOCKMANAGER - ALL IN ONE SPEC PACK (RUNNABLE)
## 로컬 실행 요약(Quick)
1) `make db-up`
2) `.env` 생성(DATABASE_URL 설정)
3) `cd apps/api && pip install -r requirements.txt`
4) `make db-migrate`
5) `make db-seed`
6) `make worker-daily-close`
7) `make api-run`

---
# STOCKMANAGER - ALL IN ONE SPEC PACK (UPDATED)


---

# FILE: 00_NORTH_STAR.md

# 00_NORTH_STAR (실전투자용 설계 기준서)
- 작성일: 2026-01-08 10:00 (KST)
- 목적: “주식종목추천 + 타이밍 신호 + 분석보기 + VC 투자검토 리포트”를 **실전투자 운영 수준(Production-grade)** 으로 구축한다.
- 전제(확정): 코스피/코스닥, 단기 중심, Top N + 비중, 신호 발생 시 **수동 주문**, ETF/리츠는 확장 가능한 구조, VC 리포트는 **비상장 포함**.

---

## 1. 제품 목표(1문장)
KRX(코스피/코스닥) 종목을 대상으로 KRX/DART/ECOS/KIS 데이터를 결합하여 **재현 가능·검증 가능·감사 가능**한 방식으로
(1) 포트폴리오 추천(Top N+비중)과 (2) 진입/청산 타이밍 신호를 제공하고, (3) 근거 중심 분석보기와 (4) VC 투자심사 수준의 리포트를 생성한다.

---

## 2. 운영 원칙(Production-grade 원칙)
1) **재현성**: 어떤 날짜(as_of)에서 나온 추천/신호/리포트는 동일 입력이면 동일 결과가 나와야 한다. (전략/피처/모델 버전 고정)
2) **시점정합(Point-in-Time)**: DART/재무/이벤트는 “발표 시점” 이전 정보를 미래에 사용하지 않는다.
3) **설명가능성**: 추천/비중/신호에 대해 “왜?”를 데이터 기반으로 제시한다. (팩터 기여도, 필터/제약 통과, 리스크 플래그)
4) **보수적 리스크 관리**: 과도한 회전율/변동성/유동성 부족 종목을 억제한다. (제약/턴오버/최대비중/섹터 제한)
5) **감사 추적(Audit)**: 데이터 수집·가공·추천 생성·리포트 생성의 모든 실행 이력을 남긴다.
6) **안전장치**: 데이터 이상, 파이프라인 실패, 공시 이벤트 등 위험 상황에서 “진입 차단/비중 축소”가 기본값이 되도록 한다.
7) **수동주문 준수**: 본 시스템은 주문 실행을 자동화하지 않으며, “신호/가이드” 제공에 집중한다.

---

## 3. 범위(이번 버전: Production v1)
### 3.1 반드시 포함(핵심 기능)
A. 데이터 수집/정합
- KRX: 상장종목/시장/섹터/기본정보, (가능하면) 거래정지/관리종목 플래그
- DART: 공시 메타 + 재무(발표시점 포함), 정정/추가 공시 반영
- ECOS: 거시 시계열(코드 관리 + 변환)
- KIS: 일봉 가격/거래량/거래대금(최소), (가능하면) 기업기초/지표 일부

B. 추천(Top N + 비중)
- 유니버스 필터(가격/상장일수/유동성) + 점수 산출(팩터 가중치)
- 비중 산출(최대 종목/섹터, 변동성 타겟팅, 턴오버 제한)
- 추천 결과 DB 저장 + API 제공

C. 타이밍(수동주문 보조)
- 룰 기반 신호(최소 3~5개 룰): BUY/WAIT/REDUCE/SELL
- 이벤트 리스크 정책(기본: 진입 차단 또는 비중 축소)

D. 분석보기(Explainability)
- 추천/신호의 근거: 팩터 기여도, 필터/제약, 리스크 플래그, 주요 차트/지표
- “왜 이 비중인가/왜 WAIT인가”가 1스크린에서 확인 가능

E. 리포트(투자심사 수준)
- 상장: DART/가격/거시 근거 포함 “investment_memo_vc_v1” 최소 1종
- 비상장: 입력폼 + 파일업로드(피치덱/재무엑셀/IR자료) 기반 RAG 요약 + 근거 링크(문서/청크)

F. 백테스트/검증
- PIT 준수 백테스트(최소 일봉): 비용모델(수수료/세금/슬리피지) 포함
- 기본 성과지표 + 턴오버/최대낙폭(MDD) 산출

G. 운영/품질
- 스케줄(장마감 배치) + 재시도/멱등성(idempotency)
- 데이터 검증(누락/이상치/시점오류) + 알람
- 로깅/모니터링/에러 추적
- 권한(최소 RBAC) + 시크릿 관리

### 3.2 이번엔 하지 않음(비목표 / 드리프트 방지)
- 실주문 자동화(자동매매), 계좌 연동 주문 실행
- 초단타/분봉 기반 HFT
- 레버리지/파생/해외주식(확장 전제로 구조만)
- “의견형 커뮤니티/소셜 트레이딩”
- 대규모 ML(딥러닝) 먼저 도입(→ v2에서 옵션)

---

## 4. 성공 기준(Definition of Done: Production v1)
1) 특정 as_of_date에 대해 추천 Top N+비중이 **DB에 저장**되고 API로 재현 가능
2) 추천 1개 종목을 클릭하면 분석보기에서 “점수/팩터 기여/제약/리스크/차트/이벤트”가 표시됨
3) 타이밍 신호가 생성되고(룰 기반) 신뢰도/트리거/리스크 플래그를 제공
4) 상장 리포트 1종과 비상장 리포트 1종(입력+업로드 기반)이 생성되고 **근거 링크(문서/청크)** 가 남음
5) 백테스트가 PIT 준수로 실행되며, 주요 지표(수익률/변동성/MDD/턴오버)가 산출됨
6) 배치 실패/데이터 누락 시 알람이 발생하고, 재시도 후에도 실패하면 “추천 생성 차단” 등 안전장치가 작동

---

## 5. 권장 기술 스택(현재 사용 패턴 유지 + 운영성 강화)
### Frontend
- Vite + React + TypeScript
- Tailwind CSS
- TanStack Query(서버 상태), Zod(입력 검증), Recharts(차트)

### Backend/API
- Python 3.11+
- FastAPI + Pydantic v2
- SQLAlchemy 2.x + Alembic(마이그레이션)
- httpx(외부 API), pandas/numpy(피처 계산)

### Infra(GCP/Firebase 중심)
- Firebase Hosting(프론트)
- Firebase Auth(인증) + 백엔드 JWT 검증
- Cloud Run: api 서비스 / worker(배치) / ingest(수집)
- Cloud Scheduler: 장마감 배치 트리거
- Pub/Sub 또는 Cloud Tasks: 비동기 작업 큐(리포트 생성/인제스트)
- Cloud Storage: 원문/산출물 저장
- Cloud SQL(PostgreSQL): 메인 DB
  - (선택) pgvector: RAG 임베딩을 Postgres에 유지하고 싶을 때

### 운영/보안
- Secret Manager(키/토큰)
- Cloud Logging/Monitoring + Error Reporting
- (선택) Sentry(프론트/백엔드 에러 추적)

---

## 6. 파일/계약(변경 통제)
- openapi_v2.1.yaml: API 계약(변경은 PR+리뷰로만)
- strategy-definition-schema-v2.1.0.json: 전략 계약(호환성 유지)
- postgres_erd_ddl_v2.1.sql: DB 계약(변경은 migration으로만)



---

# FILE: 04_CLASSIFICATION_DESIGN.md

# 04_CLASSIFICATION_DESIGN (산업/테마 분류 설계안)

## 1. 목적
- 종목 추천/필터링/리스크제약/설명가능성(분석보기)을 위해 **산업(Industry)** 과 **테마(Theme)** 분류를 설계에 포함한다.
- 산업은 “안정적 트리(대/중/소 등)”, 테마는 “동적 태그(M:N)”로 구분하여 혼선을 방지한다.

## 2. 분류 정의
### 2.1 산업(Industry / Sector)
- 기준: **KIS 분류 체계**(권장: Primary Taxonomy)
- 구조: 트리(상위/하위) + 종목의 *주산업(primary)* 지정 가능
- 활용:
  - 유니버스 포함/제외 필터
  - 포트폴리오 제약(산업 편중 제한: max_weight_per_sector)
  - 분석보기 표기(기업의 본질적 사업영역)

### 2.2 테마(Theme)
- 기준: 내부 정의(초기에는 수기/업로드로도 시작 가능) + 추후 확장(외부/자체 추출)
- 구조: 태그(다대다 M:N). 종목은 여러 테마에 속할 수 있음
- 활용:
  - 관심 테마 기반 후보군 탐색/필터
  - 단기 모멘텀/이슈 기반 설명 보조
  - VC 리포트에서 “투자 논리/모멘텀” 보강

## 3. 데이터 모델(권장)
### 3.1 Taxonomy(분류 체계)
- 예: `KIS_INDUSTRY`, `THEME`

### 3.2 Node(분류 노드)
- 산업: code, name, level, parent_code 로 트리 구성
- 테마: code(또는 slug), name, parent는 optional(필요 시)

### 3.3 Mapping(종목 ↔ 분류 매핑)
- 종목과 분류의 관계를 M:N로 관리
- `is_primary`로 “주산업” 표시(산업에만 사용 권장)
- `effective_from/effective_to`로 변경 이력 관리(실전/백테스트 PIT에 도움)

## 4. 전략/유니버스 필터에 반영(권장 파라미터)
- include_industry_codes / exclude_industry_codes (taxonomy=KIS_INDUSTRY)
- include_theme_ids / exclude_theme_ids (taxonomy=THEME)
- portfolio.constraints:
  - max_weight_per_sector (기존)
  - sector_taxonomy: "KIS_INDUSTRY" (추가)
  - sector_level: 1|2|3 (추가)  # 대/중/소 등

## 5. 분석보기(Explainability) 표준 필드(권장)
- `classifications.industry`:
  - taxonomy: "KIS_INDUSTRY"
  - primary: {code, name, level}
  - path: [{code,name,level}, ...]  # 상위→하위
- `classifications.themes`: [{id, name}, ...]

## 6. 단계적 도입 권장(실전투자 v1 기준)
- v1(즉시): **산업(KIS) 필터 + 산업 편중 제한 + 분석보기 표기**까지 포함
- v1.1: 테마 엔티티/매핑 구조 추가(수기/업로드로 시작)
- v2: 테마 소스 확정(외부/자체 추출) + 테마 기반 전략/리포트 강화



---

# FILE: 05_RATIONALE_STANDARD.md

# 05_RATIONALE_STANDARD (추천/신호 근거 JSON 표준)

## 1. 목적
- 추천(점수/랭크/비중)과 타이밍 신호의 **근거를 표준 JSON으로 저장**하여,
  분석보기 UI/리포트 생성/감사 추적에 공통으로 사용한다.

## 2. 추천 rationale (recommendation.rationale) 권장 스키마(요약)
```json
{
  "as_of_date": "2026-01-08",
  "classifications": {
    "industry": {
      "taxonomy": "KIS_INDUSTRY",
      "primary": {"code":"...", "name":"...", "level":1},
      "path": [{"code":"...","name":"...","level":1}, {"code":"...","name":"...","level":2}]
    },
    "themes": [{"id":"theme_ai","name":"AI"}, {"id":"theme_battery","name":"2차전지"}]
  },
  "filters": {
    "passed": true,
    "rules": [{"name":"min_turnover_20d", "passed": true, "value": 1200000000, "threshold": 500000000}]
  },
  "factors": {
    "total_score": 0.85,
    "contrib": [
      {"factor":"momentum", "value":0.72, "weight":0.35, "contribution":0.252},
      {"factor":"trend", "value":0.60, "weight":0.25, "contribution":0.150},
      {"factor":"risk_penalty", "value":0.40, "weight":-0.25, "contribution":-0.100}
    ]
  },
  "portfolio": {
    "target_weight": 0.10,
    "constraints": [
      {"name":"max_weight_per_name", "passed": true, "limit":0.10},
      {"name":"max_weight_per_sector", "passed": true, "limit":0.25, "sector_taxonomy":"KIS_INDUSTRY", "sector_level":1}
    ]
  },
  "event_risk": {
    "window_days": 2,
    "policy": "block_entry",
    "flags": []
  }
}
```

## 3. 신호 rationale (timing_signal.triggers/risk_flags) 권장
- `triggers`: 어떤 룰이 발화했는지(룰명/임계값/관측값)
- `risk_flags`: 이벤트 리스크/변동성 급등/유동성 급감 등 경고



---

# FILE: 01_CODEX_RUNBOOK.md

# 01_CODEX_RUNBOOK (실전투자용 코덱스 실행 가이드)
- 작성일: 2026-01-08 10:00 (KST)
- 목적: 코덱스가 “엉뚱한 방향”으로 확장하지 않도록, **작업 단위/금지사항/체크리스트**를 고정한다.

---

## 1) 코덱스 기본 규칙(반드시 지킬 것)
1. **범위 잠금**: 00_NORTH_STAR의 “비목표”에 해당하는 기능은 절대 추가하지 않는다.
2. **계약 우선**: OpenAPI / JSON Schema / DB 스키마를 임의 변경하지 않는다.
   - 변경 필요 시: (1) 이슈 생성 → (2) PR로만 반영 → (3) 호환성 확인
3. **작은 PR**: 한 PR은 “한 기능 세로 슬라이스” 또는 “하나의 모듈”만.
4. **데이터 품질 우선**: 수집 성공보다 “정합/검증/시점정합”이 우선이다.
5. **멱등성**: 배치/수집/리포트 생성은 재실행해도 중복/오염이 없어야 한다.
6. **로그/감사**: 외부 호출, 데이터 적재, 추천 산출은 모두 실행 로그를 남긴다.

---

## 2) 권장 레포 구조(예시)
```
/apps
  /web                # Vite+React
  /api                # FastAPI (REST)
/services
  /ingest             # KRX/DART/ECOS/KIS 수집 워커
  /worker             # 피처/추천/신호/리포트 배치 워커
/packages
  /shared             # 공통 타입, 유틸, 도메인 모델(선택)
/db
  /migrations         # Alembic
/docs
  00_NORTH_STAR.md
  01_CODEX_RUNBOOK.md
  openapi_v2.1.yaml
  strategy-definition-schema-v2.1.0.json
```

---

## 3) 구현 순서(드리프트 최소화: 계약→데이터→파이프라인→UI)
### Phase 1: 기반 구축
1) DB 연결 + Alembic 초기 마이그레이션 구성
2) FastAPI 골격 + OpenAPI를 기준으로 라우트 스텁 생성
3) 인증(Firebase Auth JWT) 미들웨어/디펜던시 적용

### Phase 2: 데이터 수집(최소 일봉 기준)
4) KIS 일봉 수집 → price_daily 적재(멱등)
5) KRX 종목/섹터/시장 정보 적재
6) DART 공시 메타 + 재무(announced_at 포함) 적재
7) ECOS 시계열 적재

### Phase 3: 피처/추천/신호(엔드투엔드)
8) feature_snapshot 생성(시점정합) + factor_score 산출
9) recommendation(TopN+비중) 산출 + DB 저장
10) timing_signal 산출(룰 3~5개) + DB 저장
11) /recommendations, /signals API로 조회 가능하게 구현

### Phase 4: 분석보기/리포트
12) 분석보기 API(근거: rationale + 지표) 제공
13) 웹(분석보기 화면) 구현
14) 리포트 생성 파이프라인(상장 1종, 비상장 1종) + citations(문서/청크 참조) 저장

### Phase 5: 운영 강화
15) 스케줄러/큐 연결(Cloud Scheduler + Pub/Sub/Tasks)
16) 모니터링/알람/에러추적(Sentry 선택)

---

## 4) PR 체크리스트(필수)
- [ ] OpenAPI/Schema/DDL 변경이 있으면 “변경 사유 + 호환성”을 문서에 기록했는가?
- [ ] 외부 API 호출에 타임아웃/재시도/레이트리밋이 있는가?
- [ ] 멱등성 키(예: ticker+date, rcp_no 등)가 적용되어 중복 적재가 없는가?
- [ ] point-in-time을 위반하는 미래정보 사용이 없는가?
- [ ] 단위 테스트(최소 핵심 로직) 또는 통합 테스트(핵심 API)가 있는가?
- [ ] 로그에 민감정보/토큰이 남지 않는가?
- [ ] 실패 시 안전장치(추천 생성 중단/신호 차단)가 있는가?

---

## 5) 코덱스 프롬프트 템플릿(권장)
아래 형식으로 요청하면 드리프트가 크게 줄어듭니다.

- 목표: (예: KIS 일봉 수집을 price_daily에 멱등 적재)
- 입력: (예: KIS API 응답 샘플/엔드포인트/인증 방식)
- 출력: (예: ingest 서비스에 모듈 추가 + 테스트 + 설정)
- 금지: (예: 스키마 변경 금지, 분봉 금지, 자동주문 금지)
- 완료조건: (예: 특정 티커/기간 적재 후 row count 검증)



---

# FILE: 02_PHASE_PLAN.md

# 02_PHASE_PLAN (실전투자용 구현 우선순위/Phase)

## Phase 0: 프로젝트 기본기(1~2일)
- [ ] 레포 구조 확정(모노레포)
- [ ] 환경변수/시크릿(Secret Manager) 정책 확정
- [ ] CI(테스트/린트) 기본 파이프라인

## Phase 1: API/DB/인증(3~5일)
- [ ] Cloud SQL(PostgreSQL) 연결
- [ ] Alembic 마이그레이션 구성
- [ ] Firebase Auth JWT 검증 미들웨어/의존성
- [ ] OpenAPI 계약 기반 라우트 스텁

## Phase 2: 데이터 수집(일봉, PIT)(1~2주)
- [ ] KIS 일봉 수집 → price_daily 멱등 적재
- [ ] KRX 종목/섹터/시장 메타 적재
- [ ] DART 공시 메타 + 재무(announced_at 포함) 적재
- [ ] ECOS 거시 시계열 적재
- [ ] 데이터 품질 검사(누락/중복/이상치/시점오류) + 알람

## Phase 3: 피처/점수/추천/신호(1~2주)
- [ ] feature_snapshot 생성(PIT)
- [ ] factor_score 생성(가중합 모델 v1)
- [ ] recommendation(TopN+비중) 생성 + 저장
- [ ] timing_signal(룰 3~5개) 생성 + 저장
- [ ] 분석보기용 rationale(근거) JSON 저장

## Phase 4: 분석보기/리포트(1~2주)
- [ ] 분석보기 API + UI(차트/기여도/리스크/이벤트)
- [ ] 상장 리포트(investment_memo_vc_v1) 자동 생성 + citations 저장
- [ ] 비상장 입력폼 + 파일업로드 + RAG 기반 요약 + citations 저장

## Phase 5: 운영 강화(지속)
- [ ] 스케줄러(장마감 배치) + 큐(Pub/Sub 또는 Tasks)
- [ ] 모니터링/알람/에러추적(Sentry 선택)
- [ ] 성능/비용 최적화, 캐시/파티셔닝



---

# FILE: 03_RISK_QUALITY_CHECKLIST.md

# 03_RISK_QUALITY_CHECKLIST (실전투자 운영 체크리스트)

## A. 데이터 품질/정합
- [ ] 거래일 캘린더 기준으로 누락일 체크(휴장 포함)
- [ ] 종가/거래대금 0 또는 급변 이상치 탐지(윈저라이징/클리핑 정책)
- [ ] 중복 적재 방지(멱등 키: ticker+trade_date, rcp_no 등)
- [ ] 공시 정정/추가 공시 반영 정책 정의

## B. Point-in-Time(PIT)
- [ ] 재무/이벤트는 announced_at(발표시점) 이전에는 사용 금지
- [ ] 백테스트도 동일 PIT 규칙 적용(미래정보 누수 방지)

## C. 리스크 관리(권장 기본값)
- [ ] 최소 유동성 필터(20D 평균 거래대금)
- [ ] 종목 최대비중/섹터 최대비중
- [ ] 변동성 타겟팅(20D) + 급변동 시 비중 축소
- [ ] 이벤트 리스크(실적/유증/감사/소송 등) 진입 차단 또는 비중 축소

## D. 운영 안전장치(Kill-switch)
- [ ] 데이터 수집 실패/검증 실패 시 추천 생성 차단
- [ ] 모델/전략 버전 불일치 시 결과 폐기
- [ ] 알람: Slack/메일 등(선택) + 대시보드

## E. 감사/재현성
- [ ] 파이프라인 실행 로그(run_id), 입력 스냅샷 버전(data_version) 기록
- [ ] 추천/신호/리포트 산출물에 전략/모델/피처 버전 기록



---

# FILE: openapi_v2.2.yaml

openapi: 3.0.3
info:
  title: StockReco API
  version: "2.2.0"
  description: >
    코스피/코스닥 단기 종목추천(TopN+비중) + 타이밍 신호(수동주문) + 상장/비상장 VC 리포트 생성 시스템 API
servers:
  - url: https://api.example.com
security:
  - bearerAuth: []
tags:
  - name: Universe
  - name: Recommendations
  - name: Signals
  - name: Watchlists
  - name: Reports
  - name: Strategies
  - name: Backtests

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    Error:
      type: object
      properties:
        code: { type: string }
        message: { type: string }
        details: { type: object, additionalProperties: true }

    MarketScope:
      type: string
      enum: [KRX_KOSPI, KRX_KOSDAQ, KRX_ETF, KRX_REIT]

    UniverseItem:
      type: object
      required: [ticker, name_ko, market]
      properties:
        ticker: { type: string }
        name_ko: { type: string }
        market: { $ref: "#/components/schemas/MarketScope" }
        sector_name: { type: string }
        avg_turnover_krw_20d: { type: number }
        last_price_krw: { type: number }

    Recommendation:
      type: object
      required: [as_of_date, strategy_id, strategy_version, ticker, rank, target_weight]
      properties:
        as_of_date: { type: string, format: date }
        strategy_id: { type: string }
        strategy_version: { type: string }
        ticker: { type: string }
        rank: { type: integer }
        score: { type: number }
        target_weight: { type: number, minimum: 0, maximum: 1 }
        rationale: { type: object, additionalProperties: true }

    TimingSignal:
      type: object
      required: [ts, ticker, horizon, signal]
      properties:
        ts: { type: string, format: date-time }
        ticker: { type: string }
        horizon: { type: string, enum: [1d, 3d, 1w] }
        signal: { type: string, enum: [BUY, WAIT, REDUCE, SELL] }
        confidence: { type: number, minimum: 0, maximum: 1 }
        triggers: { type: array, items: { type: string } }
        risk_flags: { type: array, items: { type: string } }
        model_version: { type: string }

    StrategyDefinition:
      type: object
      required: [strategy_id, version, schema_version, json_def]
      properties:
        strategy_id: { type: string }
        version: { type: string }
        schema_version: { type: string, example: "2.1.0" }
        name: { type: string }
        json_def: { type: object, description: strategy-definition-schema-v2.1.0.json에 부합해야 함 }

    BacktestRun:
      type: object
      required: [run_id, strategy_id, strategy_version, start_date, end_date]
      properties:
        run_id: { type: integer }
        strategy_id: { type: string }
        strategy_version: { type: string }
        start_date: { type: string, format: date }
        end_date: { type: string, format: date }
        cost_model: { type: object, additionalProperties: true }
        metrics: { type: object, additionalProperties: true }
        artifacts_path: { type: string }

    ReportRequestCreate:
      type: object
      required: [company_id, template]
      properties:
        company_id: { type: integer }
        template: { type: string, enum: [investment_memo_v1, investment_memo_vc_v1, short_brief_v1] }
        as_of_date: { type: string, format: date }
        params: { type: object, additionalProperties: true }

    ReportRequest:
      type: object
      required: [report_id, company_id, template, status]
      properties:
        report_id: { type: integer }
        company_id: { type: integer }
        template: { type: string }
        status: { type: string, enum: [PENDING, RUNNING, DONE, FAILED, CANCELED] }
        created_at: { type: string, format: date-time }
        updated_at: { type: string, format: date-time }

    ReportArtifact:
      type: object
      required: [artifact_id, report_id, format, file_path]
      properties:
        artifact_id: { type: integer }
        report_id: { type: integer }
        format: { type: string, enum: [pdf, html] }
        file_path: { type: string }
        citations: { type: object, additionalProperties: true }
        created_at: { type: string, format: date-time }

    WatchlistCreate:
      type: object
      required: [name]
      properties:
        name: { type: string }

    WatchlistItemAdd:
      type: object
      required: [ticker]
      properties:
        ticker: { type: string }

paths:
  /universe:
    get:
      tags: [Universe]
      summary: 유니버스 조회(코스피/코스닥, ETF/리츠 확장 옵션)
      parameters:
        - in: query
          name: markets
          schema:
            type: array
            items: { $ref: "#/components/schemas/MarketScope" }
          explode: true
        - in: query
          name: include_etf_reit
          schema: { type: boolean, default: false }
        - in: query
          name: min_price_krw
          schema: { type: number }
        - in: query
          name: min_avg_turnover_krw_20d
          schema: { type: number }
        - in: query
          name: min_listing_days
          schema: { type: integer }
        - in: query
          name: as_of_date
          schema: { type: string, format: date }
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                type: object
                properties:
                  items:
                    type: array
                    items: { $ref: "#/components/schemas/UniverseItem" }

  /recommendations:
    get:
      tags: [Recommendations]
      summary: 추천 결과 조회(Top N + 비중)
      parameters:
        - in: query
          name: as_of_date
          required: true
          schema: { type: string, format: date }
        - in: query
          name: strategy_id
          required: true
          schema: { type: string }
        - in: query
          name: strategy_version
          required: true
          schema: { type: string }
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                type: object
                properties:
                  items:
                    type: array
                    items: { $ref: "#/components/schemas/Recommendation" }

  /signals:
    get:
      tags: [Signals]
      summary: 타이밍 신호 조회(수동주문용)
      parameters:
        - in: query
          name: ticker
          required: true
          schema: { type: string }
        - in: query
          name: horizon
          schema: { type: string, enum: [1d, 3d, 1w] }
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                type: object
                properties:
                  items:
                    type: array
                    items: { $ref: "#/components/schemas/TimingSignal" }

  /reports:
    post:
      tags: [Reports]
      summary: 리포트 생성 요청(상장/비상장)
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: "#/components/schemas/ReportRequestCreate" }
      responses:
        "202":
          description: Accepted
          content:
            application/json:
              schema: { $ref: "#/components/schemas/ReportRequest" }

  /strategies:
    post:
      tags: [Strategies]
      summary: 전략 등록(전략 정의 JSON 업로드)
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: "#/components/schemas/StrategyDefinition" }
      responses:
        "201":
          description: Created
          content:
            application/json:
              schema: { $ref: "#/components/schemas/StrategyDefinition" }


/classifications/taxonomies:
    get:
      tags: [Universe]
      summary: 분류 체계 목록 조회(산업/테마)
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                type: object
                properties:
                  items:
                    type: array
                    items:
                      type: object
                      properties:
                        taxonomy_id: { type: string }
                        name: { type: string }
                        kind: { type: string, enum: [INDUSTRY, THEME] }


/classifications/nodes:
    get:
      tags: [Universe]
      summary: 분류 노드 조회(산업 트리/테마 목록)
      parameters:
        - in: query
          name: taxonomy_id
          required: true
          schema: { type: string, enum: [KIS_INDUSTRY, THEME] }
        - in: query
          name: parent_code
          schema: { type: string }
        - in: query
          name: level
          schema: { type: integer }
        - in: query
          name: q
          schema: { type: string }
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                type: object
                properties:
                  items:
                    type: array
                    items:
                      type: object
                      properties:
                        taxonomy_id: { type: string }
                        code: { type: string }
                        name: { type: string }
                        level: { type: integer }
                        parent_code: { type: string, nullable: true }


/classifications/securities/{ticker}:
    get:
      tags: [Universe]
      summary: 특정 종목의 산업/테마 분류 조회
      parameters:
        - in: path
          name: ticker
          required: true
          schema: { type: string }
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                type: object
                properties:
                  ticker: { type: string }
                  industry:
                    type: object
                    properties:
                      taxonomy_id: { type: string }
                      primary: { type: object, additionalProperties: true }
                      path:
                        type: array
                        items: { type: object, additionalProperties: true }
                  themes:
                    type: array
                    items: { type: object, additionalProperties: true }



---

# FILE: strategy-definition-schema-v2.2.0.json

{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/strategy-definition-2.2.0.json",
  "title": "StrategyDefinition",
  "description": "전략 정의(추천 TopN+비중, 타이밍 신호, 상장/비상장 리포트) 스키마 v2.2.0 - 산업/테마 필터 반영",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "strategy",
    "universe",
    "features",
    "scoring",
    "portfolio",
    "timing",
    "reporting",
    "backtest"
  ],
  "properties": {
    "schema_version": {
      "type": "string",
      "const": "2.2.0"
    },
    "strategy": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "strategy_id",
        "name",
        "created_at",
        "owner",
        "mode"
      ],
      "properties": {
        "strategy_id": {
          "type": "string",
          "pattern": "^[a-zA-Z0-9._-]+$",
          "minLength": 3,
          "maxLength": 80
        },
        "name": {
          "type": "string",
          "minLength": 3,
          "maxLength": 120
        },
        "created_at": {
          "type": "string",
          "format": "date-time"
        },
        "owner": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "org",
            "user"
          ],
          "properties": {
            "org": {
              "type": "string"
            },
            "user": {
              "type": "string"
            }
          }
        },
        "mode": {
          "type": "string",
          "enum": [
            "paper_signal_only",
            "paper_with_simulation",
            "production_signal_only"
          ],
          "description": "본 프로젝트는 수동주문 전제이므로 production_signal_only 권장"
        },
        "notes": {
          "type": "string"
        }
      }
    },
    "universe": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "market_scope",
        "include_etf_reit",
        "eligibility",
        "exclusions"
      ],
      "properties": {
        "market_scope": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": [
              "KRX_KOSPI",
              "KRX_KOSDAQ"
            ]
          },
          "minItems": 1,
          "uniqueItems": true
        },
        "include_etf_reit": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "enabled"
          ],
          "properties": {
            "enabled": {
              "type": "boolean",
              "default": false
            },
            "notes": {
              "type": "string"
            }
          }
        },
        "eligibility": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "min_price_krw",
            "min_avg_turnover_krw_20d",
            "min_listing_days",
            "allow_trading_halt"
          ],
          "properties": {
            "min_price_krw": {
              "type": "number",
              "minimum": 0,
              "default": 1000
            },
            "min_avg_turnover_krw_20d": {
              "type": "number",
              "minimum": 0,
              "default": 500000000
            },
            "min_listing_days": {
              "type": "integer",
              "minimum": 0,
              "default": 120
            },
            "allow_trading_halt": {
              "type": "boolean",
              "default": false
            }
          }
        },
        "exclusions": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "exclude_delisted",
            "exclude_management"
          ],
          "properties": {
            "exclude_delisted": {
              "type": "boolean",
              "default": true
            },
            "exclude_management": {
              "type": "boolean",
              "default": true
            },
            "ticker_whitelist": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "default": []
            }
          }
        },
        "classification_filters": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "industry",
            "theme"
          ],
          "properties": {
            "industry": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "taxonomy",
                "include_codes",
                "exclude_codes",
                "level"
              ],
              "properties": {
                "taxonomy": {
                  "type": "string",
                  "enum": [
                    "KIS_INDUSTRY"
                  ],
                  "default": "KIS_INDUSTRY"
                },
                "include_codes": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "default": []
                },
                "exclude_codes": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "default": []
                },
                "level": {
                  "type": "integer",
                  "minimum": 1,
                  "maximum": 5,
                  "default": 1,
                  "description": "산업 분류 레벨(대/중/소 등). 시스템 설정에 맞게 사용"
                }
              }
            },
            "theme": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "taxonomy",
                "include_ids",
                "exclude_ids"
              ],
              "properties": {
                "taxonomy": {
                  "type": "string",
                  "enum": [
                    "THEME"
                  ],
                  "default": "THEME"
                },
                "include_ids": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "default": []
                },
                "exclude_ids": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "default": []
                }
              }
            }
          }
        }
      }
    },
    "features": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "asof_timezone",
        "price_features",
        "fundamental_features",
        "event_features",
        "macro_features",
        "standardization"
      ],
      "properties": {
        "asof_timezone": {
          "type": "string",
          "default": "Asia/Seoul"
        },
        "price_features": {
          "type": "array",
          "minItems": 1,
          "items": {
            "$ref": "#/$defs/FeatureSpec"
          }
        },
        "fundamental_features": {
          "type": "array",
          "default": [],
          "items": {
            "$ref": "#/$defs/FeatureSpec"
          }
        },
        "event_features": {
          "type": "array",
          "default": [],
          "items": {
            "$ref": "#/$defs/EventFeatureSpec"
          }
        },
        "macro_features": {
          "type": "array",
          "default": [],
          "items": {
            "$ref": "#/$defs/MacroFeatureSpec"
          }
        },
        "standardization": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "method",
            "winsorize"
          ],
          "properties": {
            "method": {
              "type": "string",
              "enum": [
                "percentile_rank",
                "zscore"
              ],
              "default": "percentile_rank"
            },
            "winsorize": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "enabled",
                "p_low",
                "p_high"
              ],
              "properties": {
                "enabled": {
                  "type": "boolean",
                  "default": true
                },
                "p_low": {
                  "type": "number",
                  "minimum": 0,
                  "maximum": 0.5,
                  "default": 0.01
                },
                "p_high": {
                  "type": "number",
                  "minimum": 0.5,
                  "maximum": 1,
                  "default": 0.99
                }
              }
            }
          }
        }
      }
    },
    "scoring": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "model_type",
        "weights",
        "top_n"
      ],
      "properties": {
        "model_type": {
          "type": "string",
          "enum": [
            "factor_weighted",
            "ml_ranking"
          ],
          "default": "factor_weighted"
        },
        "weights": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "momentum",
            "trend",
            "risk_penalty",
            "liquidity_bonus",
            "value",
            "quality"
          ],
          "properties": {
            "momentum": {
              "type": "number",
              "default": 0.35
            },
            "trend": {
              "type": "number",
              "default": 0.25
            },
            "risk_penalty": {
              "type": "number",
              "default": 0.25
            },
            "liquidity_bonus": {
              "type": "number",
              "default": 0.15
            },
            "value": {
              "type": "number",
              "default": 0.0
            },
            "quality": {
              "type": "number",
              "default": 0.0
            }
          }
        },
        "top_n": {
          "type": "integer",
          "minimum": 1,
          "maximum": 200,
          "default": 20
        },
        "ml": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "model_name": {
              "type": "string"
            },
            "model_version": {
              "type": "string"
            },
            "featureset_version": {
              "type": "string"
            },
            "training_window": {
              "type": "string"
            },
            "label": {
              "type": "string"
            }
          }
        }
      }
    },
    "portfolio": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "weighting",
        "constraints",
        "rebalance"
      ],
      "properties": {
        "weighting": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "method",
            "score_power",
            "vol_targeting"
          ],
          "properties": {
            "method": {
              "type": "string",
              "enum": [
                "equal",
                "score_proportional",
                "score_risk_adjusted"
              ],
              "default": "score_risk_adjusted"
            },
            "score_power": {
              "type": "number",
              "minimum": 0.1,
              "maximum": 5,
              "default": 1.0
            },
            "vol_targeting": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "enabled",
                "lookback_days"
              ],
              "properties": {
                "enabled": {
                  "type": "boolean",
                  "default": true
                },
                "lookback_days": {
                  "type": "integer",
                  "minimum": 5,
                  "maximum": 252,
                  "default": 20
                }
              }
            }
          }
        },
        "constraints": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "max_weight_per_name",
            "max_weight_per_sector",
            "max_turnover",
            "min_avg_turnover_krw_20d"
          ],
          "properties": {
            "max_weight_per_name": {
              "type": "number",
              "minimum": 0,
              "maximum": 1,
              "default": 0.1
            },
            "max_weight_per_sector": {
              "type": "number",
              "minimum": 0,
              "maximum": 1,
              "default": 0.25
            },
            "max_turnover": {
              "type": "number",
              "minimum": 0,
              "maximum": 5,
              "default": 0.8
            },
            "min_avg_turnover_krw_20d": {
              "type": "number",
              "minimum": 0,
              "default": 500000000
            },
            "sector_taxonomy": {
              "type": "string",
              "enum": [
                "KIS_INDUSTRY"
              ],
              "default": "KIS_INDUSTRY",
              "description": "섹터(산업) 편중 제한 적용 기준 분류체계"
            },
            "sector_level": {
              "type": "integer",
              "minimum": 1,
              "maximum": 5,
              "default": 1,
              "description": "섹터(산업) 편중 제한 적용 레벨(대/중/소 등)"
            }
          }
        },
        "rebalance": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "frequency",
            "execution_price"
          ],
          "properties": {
            "frequency": {
              "type": "string",
              "enum": [
                "daily",
                "weekly",
                "monthly"
              ],
              "default": "weekly"
            },
            "execution_price": {
              "type": "string",
              "enum": [
                "next_open",
                "close",
                "vwap"
              ],
              "default": "next_open"
            }
          }
        }
      }
    },
    "timing": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "enabled",
        "horizons",
        "rules",
        "event_risk"
      ],
      "properties": {
        "enabled": {
          "type": "boolean",
          "default": true
        },
        "horizons": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": [
              "1d",
              "3d",
              "1w"
            ]
          },
          "minItems": 1,
          "uniqueItems": true,
          "default": [
            "1d",
            "1w"
          ]
        },
        "rules": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "object",
            "additionalProperties": false,
            "required": [
              "name",
              "signal",
              "priority",
              "when",
              "then"
            ],
            "properties": {
              "name": {
                "type": "string"
              },
              "signal": {
                "type": "string",
                "enum": [
                  "BUY",
                  "WAIT",
                  "REDUCE",
                  "SELL"
                ]
              },
              "priority": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "default": 50
              },
              "when": {
                "type": "object",
                "description": "간단 DSL(예: all/any + gt/lt 등) 또는 룰엔진 표현"
              },
              "then": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "confidence",
                  "triggers",
                  "risk_flags"
                ],
                "properties": {
                  "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1
                  },
                  "triggers": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "risk_flags": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  }
                }
              }
            }
          }
        },
        "event_risk": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "enabled",
            "default_window_days",
            "default_policy"
          ],
          "properties": {
            "enabled": {
              "type": "boolean",
              "default": true
            },
            "default_window_days": {
              "type": "integer",
              "minimum": 0,
              "maximum": 30,
              "default": 2
            },
            "default_policy": {
              "type": "string",
              "enum": [
                "block_entry",
                "reduce_size",
                "no_action"
              ],
              "default": "block_entry"
            }
          }
        }
      }
    },
    "reporting": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "enabled",
        "templates",
        "citations",
        "listed_company",
        "private_company"
      ],
      "properties": {
        "enabled": {
          "type": "boolean",
          "default": true
        },
        "templates": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": [
              "investment_memo_v1",
              "investment_memo_vc_v1",
              "short_brief_v1"
            ]
          },
          "default": [
            "investment_memo_vc_v1"
          ]
        },
        "citations": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "require_citations",
            "min_coverage_ratio"
          ],
          "properties": {
            "require_citations": {
              "type": "boolean",
              "default": true
            },
            "min_coverage_ratio": {
              "type": "number",
              "minimum": 0,
              "maximum": 1,
              "default": 0.6
            }
          }
        },
        "listed_company": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "sources"
          ],
          "properties": {
            "sources": {
              "type": "array",
              "items": {
                "type": "string",
                "enum": [
                  "DART",
                  "KRX",
                  "KIS",
                  "ECOS"
                ]
              },
              "default": [
                "DART",
                "KIS",
                "ECOS"
              ]
            }
          }
        },
        "private_company": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "inputs",
            "doc_ingestion"
          ],
          "properties": {
            "inputs": {
              "type": "array",
              "items": {
                "type": "string",
                "enum": [
                  "manual_form",
                  "file_upload",
                  "external_connector"
                ]
              },
              "default": [
                "manual_form",
                "file_upload"
              ]
            },
            "doc_ingestion": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "rag_enabled",
                "supported_file_types"
              ],
              "properties": {
                "rag_enabled": {
                  "type": "boolean",
                  "default": true
                },
                "supported_file_types": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "default": [
                    "pdf",
                    "pptx",
                    "xlsx",
                    "docx"
                  ]
                }
              }
            }
          }
        }
      }
    },
    "backtest": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "enabled",
        "window",
        "cost_model",
        "validation"
      ],
      "properties": {
        "enabled": {
          "type": "boolean",
          "default": true
        },
        "window": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "start_date",
            "end_date"
          ],
          "properties": {
            "start_date": {
              "type": "string",
              "format": "date"
            },
            "end_date": {
              "type": "string",
              "format": "date"
            }
          }
        },
        "cost_model": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "commission_rate",
            "tax_rate_on_sell",
            "slippage_bps"
          ],
          "properties": {
            "commission_rate": {
              "type": "number",
              "minimum": 0,
              "default": 0.00015
            },
            "tax_rate_on_sell": {
              "type": "number",
              "minimum": 0,
              "default": 0.0023
            },
            "slippage_bps": {
              "type": "number",
              "minimum": 0,
              "default": 5
            }
          }
        },
        "validation": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "walk_forward",
            "turnover_sanity_check"
          ],
          "properties": {
            "walk_forward": {
              "type": "boolean",
              "default": true
            },
            "turnover_sanity_check": {
              "type": "boolean",
              "default": true
            }
          }
        }
      }
    }
  },
  "$defs": {
    "FeatureSpec": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "name",
        "source",
        "params"
      ],
      "properties": {
        "name": {
          "type": "string"
        },
        "source": {
          "type": "string",
          "enum": [
            "KIS",
            "KRX",
            "DART",
            "ECOS",
            "INTERNAL"
          ]
        },
        "params": {
          "type": "object",
          "additionalProperties": true
        }
      }
    },
    "EventFeatureSpec": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "name",
        "source",
        "window_days",
        "policy"
      ],
      "properties": {
        "name": {
          "type": "string",
          "enum": [
            "earnings",
            "revision",
            "rights_issue",
            "audit_opinion",
            "litigation",
            "mna"
          ]
        },
        "source": {
          "type": "string",
          "enum": [
            "DART"
          ]
        },
        "window_days": {
          "type": "integer",
          "minimum": 0,
          "maximum": 30,
          "default": 2
        },
        "policy": {
          "type": "string",
          "enum": [
            "block_entry",
            "reduce_size",
            "no_action"
          ],
          "default": "block_entry"
        }
      }
    },
    "MacroFeatureSpec": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "name",
        "source",
        "series_code",
        "transform"
      ],
      "properties": {
        "name": {
          "type": "string"
        },
        "source": {
          "type": "string",
          "enum": [
            "ECOS"
          ]
        },
        "series_code": {
          "type": "string"
        },
        "transform": {
          "type": "string",
          "enum": [
            "level",
            "diff",
            "pct_change",
            "zscore"
          ],
          "default": "level"
        }
      }
    }
  }
}


---

# FILE: postgres_erd_ddl_v2.2.sql

-- PostgreSQL Schema (ERD/DDL) v2.1
-- Generated: 2026-01-08 (KST)
-- 목적: 코스피/코스닥 단기 추천(TopN+비중) + 타이밍 신호 + 상장/비상장 VC 리포트 + 문서 인제스트/RAG + 백테스트/버전관리

BEGIN;

DO $$ BEGIN
  CREATE TYPE market_scope AS ENUM ('KRX_KOSPI','KRX_KOSDAQ','KRX_ETF','KRX_REIT');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE signal_type AS ENUM ('BUY','WAIT','REDUCE','SELL');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE report_status AS ENUM ('PENDING','RUNNING','DONE','FAILED','CANCELED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE company_type AS ENUM ('LISTED','PRIVATE');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS company (
  company_id        BIGSERIAL PRIMARY KEY,
  company_type      company_type NOT NULL,
  name_ko           TEXT NOT NULL,
  name_en           TEXT,
  -- listed
  corp_code         TEXT UNIQUE,
  stock_code        TEXT UNIQUE,
  market            market_scope,
  sector_code       TEXT,
  sector_name       TEXT,
  listing_date      DATE,
  delisting_date    DATE,
  status            TEXT,
  -- private (민감정보는 해시/암호화 권장)
  external_id_hash  TEXT UNIQUE,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_company_type ON company(company_type);
CREATE INDEX IF NOT EXISTS idx_company_market ON company(market);

CREATE TABLE IF NOT EXISTS security (
  security_id   BIGSERIAL PRIMARY KEY,
  ticker        TEXT NOT NULL UNIQUE,
  isin          TEXT,
  market        market_scope,
  currency      TEXT DEFAULT 'KRW',
  lot_size      INTEGER DEFAULT 1,
  tick_size     NUMERIC,
  company_id    BIGINT REFERENCES company(company_id) ON DELETE SET NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_security_company_id ON security(company_id);

CREATE TABLE IF NOT EXISTS price_daily (
  ticker        TEXT NOT NULL,
  trade_date    DATE NOT NULL,
  open          NUMERIC,
  high          NUMERIC,
  low           NUMERIC,
  close         NUMERIC,
  volume        NUMERIC,
  turnover_krw  NUMERIC,
  adj_factor    NUMERIC,
  source        TEXT DEFAULT 'KIS',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (ticker, trade_date)
);
CREATE INDEX IF NOT EXISTS idx_price_daily_date ON price_daily(trade_date);

CREATE TABLE IF NOT EXISTS market_index_daily (
  index_code    TEXT NOT NULL,
  trade_date    DATE NOT NULL,
  close         NUMERIC,
  ret_1d        NUMERIC,
  vol_20d       NUMERIC,
  source        TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (index_code, trade_date)
);

CREATE TABLE IF NOT EXISTS dart_filing (
  rcp_no        TEXT PRIMARY KEY,
  corp_code     TEXT NOT NULL,
  filing_date   DATE NOT NULL,
  filing_time   TIME,
  filing_type   TEXT,
  title         TEXT,
  url           TEXT,
  is_last_report BOOLEAN DEFAULT FALSE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_dart_filing_corp_date ON dart_filing(corp_code, filing_date);

CREATE TABLE IF NOT EXISTS financial_statement (
  corp_code        TEXT NOT NULL,
  period_end       DATE NOT NULL,
  announced_at     TIMESTAMPTZ NOT NULL,
  item_code        TEXT NOT NULL,
  item_name        TEXT,
  value            NUMERIC,
  unit             TEXT,
  consolidated_flag BOOLEAN DEFAULT TRUE,
  source_rcp_no    TEXT REFERENCES dart_filing(rcp_no) ON DELETE SET NULL,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (corp_code, period_end, item_code, announced_at)
);
CREATE INDEX IF NOT EXISTS idx_fs_announced_at ON financial_statement(announced_at);
CREATE INDEX IF NOT EXISTS idx_fs_corp_period ON financial_statement(corp_code, period_end);

CREATE TABLE IF NOT EXISTS document (
  document_id    BIGSERIAL PRIMARY KEY,
  company_id     BIGINT REFERENCES company(company_id) ON DELETE CASCADE,
  source_type    TEXT NOT NULL, -- DART, UPLOAD, EXTERNAL
  source_ref     TEXT,          -- rcp_no 등
  file_path      TEXT NOT NULL, -- storage path
  file_type      TEXT,          -- pdf/pptx/xlsx/docx
  sha256         TEXT,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_document_company ON document(company_id);
CREATE INDEX IF NOT EXISTS idx_document_source ON document(source_type, source_ref);

CREATE TABLE IF NOT EXISTS document_chunk (
  chunk_id       BIGSERIAL PRIMARY KEY,
  document_id    BIGINT NOT NULL REFERENCES document(document_id) ON DELETE CASCADE,
  chunk_no       INTEGER NOT NULL,
  text_path      TEXT,
  content_text   TEXT,
  token_count    INTEGER,
  embedding_id   TEXT,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(document_id, chunk_no)
);
CREATE INDEX IF NOT EXISTS idx_document_chunk_doc ON document_chunk(document_id);

CREATE TABLE IF NOT EXISTS macro_series (
  series_code   TEXT NOT NULL,
  obs_date      DATE NOT NULL,
  value         NUMERIC,
  unit          TEXT,
  source        TEXT DEFAULT 'ECOS',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (series_code, obs_date)
);

CREATE TABLE IF NOT EXISTS feature_snapshot (
  as_of_date     DATE NOT NULL,
  ticker         TEXT NOT NULL,
  feature_name   TEXT NOT NULL,
  value          NUMERIC,
  effective_from TIMESTAMPTZ,
  data_version   TEXT NOT NULL DEFAULT 'v1',
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (as_of_date, ticker, feature_name, data_version)
);
CREATE INDEX IF NOT EXISTS idx_feature_snapshot_ticker_date ON feature_snapshot(ticker, as_of_date);

CREATE TABLE IF NOT EXISTS factor_score (
  as_of_date      DATE NOT NULL,
  ticker          TEXT NOT NULL,
  model_version   TEXT NOT NULL,
  total_score     NUMERIC,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (as_of_date, ticker, model_version)
);

CREATE TABLE IF NOT EXISTS strategy_def (
  strategy_id    TEXT NOT NULL,
  version        TEXT NOT NULL,
  schema_version TEXT NOT NULL DEFAULT '2.1.0',
  name           TEXT,
  json_def       JSONB NOT NULL,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY(strategy_id, version)
);

CREATE TABLE IF NOT EXISTS backtest_run (
  run_id           BIGSERIAL PRIMARY KEY,
  strategy_id      TEXT NOT NULL,
  strategy_version TEXT NOT NULL,
  start_date       DATE NOT NULL,
  end_date         DATE NOT NULL,
  cost_model       JSONB NOT NULL,
  metrics          JSONB,
  artifacts_path   TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  FOREIGN KEY(strategy_id, strategy_version) REFERENCES strategy_def(strategy_id, version) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS recommendation (
  as_of_date       DATE NOT NULL,
  strategy_id      TEXT NOT NULL,
  strategy_version TEXT NOT NULL,
  ticker           TEXT NOT NULL,
  rank             INTEGER NOT NULL,
  score            NUMERIC,
  target_weight    NUMERIC,
  rationale        JSONB,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY(as_of_date, strategy_id, strategy_version, ticker),
  FOREIGN KEY(strategy_id, strategy_version) REFERENCES strategy_def(strategy_id, version) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS idx_reco_asof_rank ON recommendation(as_of_date, rank);

CREATE TABLE IF NOT EXISTS timing_signal (
  ts            TIMESTAMPTZ NOT NULL,
  ticker        TEXT NOT NULL,
  horizon       TEXT NOT NULL,
  signal        signal_type NOT NULL,
  confidence    NUMERIC,
  triggers      JSONB,
  risk_flags    JSONB,
  model_version TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY(ts, ticker, horizon)
);
CREATE INDEX IF NOT EXISTS idx_signal_ticker_ts ON timing_signal(ticker, ts DESC);

CREATE TABLE IF NOT EXISTS watchlist (
  watchlist_id  BIGSERIAL PRIMARY KEY,
  owner_user_id TEXT NOT NULL,
  name          TEXT NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS watchlist_item (
  watchlist_id  BIGINT NOT NULL REFERENCES watchlist(watchlist_id) ON DELETE CASCADE,
  ticker        TEXT NOT NULL,
  added_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY(watchlist_id, ticker)
);

CREATE TABLE IF NOT EXISTS report_request (
  report_id     BIGSERIAL PRIMARY KEY,
  company_id    BIGINT NOT NULL REFERENCES company(company_id) ON DELETE CASCADE,
  template      TEXT NOT NULL,
  as_of_date    DATE,
  status        report_status NOT NULL DEFAULT 'PENDING',
  requested_by  TEXT,
  params        JSONB,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_report_company ON report_request(company_id, created_at DESC);

CREATE TABLE IF NOT EXISTS report_artifact (
  artifact_id   BIGSERIAL PRIMARY KEY,
  report_id     BIGINT NOT NULL REFERENCES report_request(report_id) ON DELETE CASCADE,
  format        TEXT NOT NULL, -- pdf/html
  file_path     TEXT NOT NULL,
  citations     JSONB,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMIT;


-- === Classification (Industry/Theme) v2.2 ===
DO $$ BEGIN
  CREATE TYPE taxonomy_kind AS ENUM ('INDUSTRY','THEME');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS classification_taxonomy (
  taxonomy_id   TEXT PRIMARY KEY,  -- e.g., KIS_INDUSTRY, THEME
  kind          taxonomy_kind NOT NULL,
  name          TEXT NOT NULL,
  provider      TEXT,              -- e.g., KIS, INTERNAL
  version       TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS classification_node (
  taxonomy_id   TEXT NOT NULL REFERENCES classification_taxonomy(taxonomy_id) ON DELETE CASCADE,
  code          TEXT NOT NULL,      -- industry code or theme id/slug
  name          TEXT NOT NULL,
  level         INTEGER,            -- industry tree level (theme can be NULL/1)
  parent_code   TEXT,               -- nullable
  extra         JSONB,              -- provider-specific fields
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (taxonomy_id, code)
);
CREATE INDEX IF NOT EXISTS idx_class_node_tax_parent ON classification_node(taxonomy_id, parent_code);
CREATE INDEX IF NOT EXISTS idx_class_node_tax_level ON classification_node(taxonomy_id, level);

-- M:N mapping: security ↔ classification (industry/theme)
CREATE TABLE IF NOT EXISTS security_classification (
  ticker         TEXT NOT NULL,
  taxonomy_id    TEXT NOT NULL,
  code           TEXT NOT NULL,
  is_primary     BOOLEAN NOT NULL DEFAULT FALSE,  -- industry primary classification
  effective_from DATE,
  effective_to   DATE,
  confidence     NUMERIC,                         -- for theme inference later
  source         TEXT,                            -- KIS / INTERNAL / MANUAL
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (ticker, taxonomy_id, code, effective_from),
  FOREIGN KEY (taxonomy_id, code) REFERENCES classification_node(taxonomy_id, code) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS idx_sec_class_ticker ON security_classification(ticker);
CREATE INDEX IF NOT EXISTS idx_sec_class_tax_code ON security_classification(taxonomy_id, code);



---

# FILE: openapi_v2.1.yaml

openapi: 3.0.3
info:
  title: StockReco API
  version: "2.1.0"
  description: >
    코스피/코스닥 단기 종목추천(TopN+비중) + 타이밍 신호(수동주문) + 상장/비상장 VC 리포트 생성 시스템 API
servers:
  - url: https://api.example.com
security:
  - bearerAuth: []
tags:
  - name: Universe
  - name: Recommendations
  - name: Signals
  - name: Watchlists
  - name: Reports
  - name: Strategies
  - name: Backtests

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    Error:
      type: object
      properties:
        code: { type: string }
        message: { type: string }
        details: { type: object, additionalProperties: true }

    MarketScope:
      type: string
      enum: [KRX_KOSPI, KRX_KOSDAQ, KRX_ETF, KRX_REIT]

    UniverseItem:
      type: object
      required: [ticker, name_ko, market]
      properties:
        ticker: { type: string }
        name_ko: { type: string }
        market: { $ref: "#/components/schemas/MarketScope" }
        sector_name: { type: string }
        avg_turnover_krw_20d: { type: number }
        last_price_krw: { type: number }

    Recommendation:
      type: object
      required: [as_of_date, strategy_id, strategy_version, ticker, rank, target_weight]
      properties:
        as_of_date: { type: string, format: date }
        strategy_id: { type: string }
        strategy_version: { type: string }
        ticker: { type: string }
        rank: { type: integer }
        score: { type: number }
        target_weight: { type: number, minimum: 0, maximum: 1 }
        rationale: { type: object, additionalProperties: true }

    TimingSignal:
      type: object
      required: [ts, ticker, horizon, signal]
      properties:
        ts: { type: string, format: date-time }
        ticker: { type: string }
        horizon: { type: string, enum: [1d, 3d, 1w] }
        signal: { type: string, enum: [BUY, WAIT, REDUCE, SELL] }
        confidence: { type: number, minimum: 0, maximum: 1 }
        triggers: { type: array, items: { type: string } }
        risk_flags: { type: array, items: { type: string } }
        model_version: { type: string }

    StrategyDefinition:
      type: object
      required: [strategy_id, version, schema_version, json_def]
      properties:
        strategy_id: { type: string }
        version: { type: string }
        schema_version: { type: string, example: "2.1.0" }
        name: { type: string }
        json_def: { type: object, description: strategy-definition-schema-v2.1.0.json에 부합해야 함 }

    BacktestRun:
      type: object
      required: [run_id, strategy_id, strategy_version, start_date, end_date]
      properties:
        run_id: { type: integer }
        strategy_id: { type: string }
        strategy_version: { type: string }
        start_date: { type: string, format: date }
        end_date: { type: string, format: date }
        cost_model: { type: object, additionalProperties: true }
        metrics: { type: object, additionalProperties: true }
        artifacts_path: { type: string }

    ReportRequestCreate:
      type: object
      required: [company_id, template]
      properties:
        company_id: { type: integer }
        template: { type: string, enum: [investment_memo_v1, investment_memo_vc_v1, short_brief_v1] }
        as_of_date: { type: string, format: date }
        params: { type: object, additionalProperties: true }

    ReportRequest:
      type: object
      required: [report_id, company_id, template, status]
      properties:
        report_id: { type: integer }
        company_id: { type: integer }
        template: { type: string }
        status: { type: string, enum: [PENDING, RUNNING, DONE, FAILED, CANCELED] }
        created_at: { type: string, format: date-time }
        updated_at: { type: string, format: date-time }

    ReportArtifact:
      type: object
      required: [artifact_id, report_id, format, file_path]
      properties:
        artifact_id: { type: integer }
        report_id: { type: integer }
        format: { type: string, enum: [pdf, html] }
        file_path: { type: string }
        citations: { type: object, additionalProperties: true }
        created_at: { type: string, format: date-time }

    WatchlistCreate:
      type: object
      required: [name]
      properties:
        name: { type: string }

    WatchlistItemAdd:
      type: object
      required: [ticker]
      properties:
        ticker: { type: string }

paths:
  /universe:
    get:
      tags: [Universe]
      summary: 유니버스 조회(코스피/코스닥, ETF/리츠 확장 옵션)
      parameters:
        - in: query
          name: markets
          schema:
            type: array
            items: { $ref: "#/components/schemas/MarketScope" }
          explode: true
        - in: query
          name: include_etf_reit
          schema: { type: boolean, default: false }
        - in: query
          name: min_price_krw
          schema: { type: number }
        - in: query
          name: min_avg_turnover_krw_20d
          schema: { type: number }
        - in: query
          name: min_listing_days
          schema: { type: integer }
        - in: query
          name: as_of_date
          schema: { type: string, format: date }
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                type: object
                properties:
                  items:
                    type: array
                    items: { $ref: "#/components/schemas/UniverseItem" }

  /recommendations:
    get:
      tags: [Recommendations]
      summary: 추천 결과 조회(Top N + 비중)
      parameters:
        - in: query
          name: as_of_date
          required: true
          schema: { type: string, format: date }
        - in: query
          name: strategy_id
          required: true
          schema: { type: string }
        - in: query
          name: strategy_version
          required: true
          schema: { type: string }
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                type: object
                properties:
                  items:
                    type: array
                    items: { $ref: "#/components/schemas/Recommendation" }

  /signals:
    get:
      tags: [Signals]
      summary: 타이밍 신호 조회(수동주문용)
      parameters:
        - in: query
          name: ticker
          required: true
          schema: { type: string }
        - in: query
          name: horizon
          schema: { type: string, enum: [1d, 3d, 1w] }
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                type: object
                properties:
                  items:
                    type: array
                    items: { $ref: "#/components/schemas/TimingSignal" }

  /reports:
    post:
      tags: [Reports]
      summary: 리포트 생성 요청(상장/비상장)
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: "#/components/schemas/ReportRequestCreate" }
      responses:
        "202":
          description: Accepted
          content:
            application/json:
              schema: { $ref: "#/components/schemas/ReportRequest" }

  /strategies:
    post:
      tags: [Strategies]
      summary: 전략 등록(전략 정의 JSON 업로드)
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: "#/components/schemas/StrategyDefinition" }
      responses:
        "201":
          description: Created
          content:
            application/json:
              schema: { $ref: "#/components/schemas/StrategyDefinition" }



---

# FILE: strategy-definition-schema-v2.1.0.json

{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/strategy-definition-2.1.0.json",
  "title": "StrategyDefinition",
  "description": "전략 정의(추천 TopN+비중, 타이밍 신호, 상장/비상장 리포트) 스키마 v2.1.0",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "strategy", "universe", "features", "scoring", "portfolio", "timing", "reporting", "backtest"],
  "properties": {
    "schema_version": { "type": "string", "const": "2.1.0" },

    "strategy": {
      "type": "object",
      "additionalProperties": false,
      "required": ["strategy_id", "name", "created_at", "owner", "mode"],
      "properties": {
        "strategy_id": { "type": "string", "pattern": "^[a-zA-Z0-9._-]+$", "minLength": 3, "maxLength": 80 },
        "name": { "type": "string", "minLength": 3, "maxLength": 120 },
        "created_at": { "type": "string", "format": "date-time" },
        "owner": {
          "type": "object",
          "additionalProperties": false,
          "required": ["org", "user"],
          "properties": {
            "org": { "type": "string" },
            "user": { "type": "string" }
          }
        },
        "mode": {
          "type": "string",
          "enum": ["paper_signal_only", "paper_with_simulation", "production_signal_only"],
          "description": "본 프로젝트는 수동주문 전제이므로 production_signal_only 권장"
        },
        "notes": { "type": "string" }
      }
    },

    "universe": {
      "type": "object",
      "additionalProperties": false,
      "required": ["market_scope", "include_etf_reit", "eligibility", "exclusions"],
      "properties": {
        "market_scope": {
          "type": "array",
          "items": { "type": "string", "enum": ["KRX_KOSPI", "KRX_KOSDAQ"] },
          "minItems": 1,
          "uniqueItems": true
        },
        "include_etf_reit": {
          "type": "object",
          "additionalProperties": false,
          "required": ["enabled"],
          "properties": {
            "enabled": { "type": "boolean", "default": false },
            "notes": { "type": "string" }
          }
        },
        "eligibility": {
          "type": "object",
          "additionalProperties": false,
          "required": ["min_price_krw", "min_avg_turnover_krw_20d", "min_listing_days", "allow_trading_halt"],
          "properties": {
            "min_price_krw": { "type": "number", "minimum": 0, "default": 1000 },
            "min_avg_turnover_krw_20d": { "type": "number", "minimum": 0, "default": 500000000 },
            "min_listing_days": { "type": "integer", "minimum": 0, "default": 120 },
            "allow_trading_halt": { "type": "boolean", "default": false }
          }
        },
        "exclusions": {
          "type": "object",
          "additionalProperties": false,
          "required": ["exclude_delisted", "exclude_management"],
          "properties": {
            "exclude_delisted": { "type": "boolean", "default": true },
            "exclude_management": { "type": "boolean", "default": true },
            "ticker_whitelist": { "type": "array", "items": { "type": "string" }, "default": [] }
          }
        }
      }
    },

    "features": {
      "type": "object",
      "additionalProperties": false,
      "required": ["asof_timezone", "price_features", "fundamental_features", "event_features", "macro_features", "standardization"],
      "properties": {
        "asof_timezone": { "type": "string", "default": "Asia/Seoul" },

        "price_features": {
          "type": "array",
          "minItems": 1,
          "items": { "$ref": "#/$defs/FeatureSpec" }
        },
        "fundamental_features": {
          "type": "array",
          "default": [],
          "items": { "$ref": "#/$defs/FeatureSpec" }
        },
        "event_features": {
          "type": "array",
          "default": [],
          "items": { "$ref": "#/$defs/EventFeatureSpec" }
        },
        "macro_features": {
          "type": "array",
          "default": [],
          "items": { "$ref": "#/$defs/MacroFeatureSpec" }
        },
        "standardization": {
          "type": "object",
          "additionalProperties": false,
          "required": ["method", "winsorize"],
          "properties": {
            "method": { "type": "string", "enum": ["percentile_rank", "zscore"], "default": "percentile_rank" },
            "winsorize": {
              "type": "object",
              "additionalProperties": false,
              "required": ["enabled", "p_low", "p_high"],
              "properties": {
                "enabled": { "type": "boolean", "default": true },
                "p_low": { "type": "number", "minimum": 0, "maximum": 0.5, "default": 0.01 },
                "p_high": { "type": "number", "minimum": 0.5, "maximum": 1, "default": 0.99 }
              }
            }
          }
        }
      }
    },

    "scoring": {
      "type": "object",
      "additionalProperties": false,
      "required": ["model_type", "weights", "top_n"],
      "properties": {
        "model_type": { "type": "string", "enum": ["factor_weighted", "ml_ranking"], "default": "factor_weighted" },
        "weights": {
          "type": "object",
          "additionalProperties": false,
          "required": ["momentum", "trend", "risk_penalty", "liquidity_bonus", "value", "quality"],
          "properties": {
            "momentum": { "type": "number", "default": 0.35 },
            "trend": { "type": "number", "default": 0.25 },
            "risk_penalty": { "type": "number", "default": 0.25 },
            "liquidity_bonus": { "type": "number", "default": 0.15 },
            "value": { "type": "number", "default": 0.0 },
            "quality": { "type": "number", "default": 0.0 }
          }
        },
        "top_n": { "type": "integer", "minimum": 1, "maximum": 200, "default": 20 },
        "ml": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "model_name": { "type": "string" },
            "model_version": { "type": "string" },
            "featureset_version": { "type": "string" },
            "training_window": { "type": "string" },
            "label": { "type": "string" }
          }
        }
      }
    },

    "portfolio": {
      "type": "object",
      "additionalProperties": false,
      "required": ["weighting", "constraints", "rebalance"],
      "properties": {
        "weighting": {
          "type": "object",
          "additionalProperties": false,
          "required": ["method", "score_power", "vol_targeting"],
          "properties": {
            "method": { "type": "string", "enum": ["equal", "score_proportional", "score_risk_adjusted"], "default": "score_risk_adjusted" },
            "score_power": { "type": "number", "minimum": 0.1, "maximum": 5, "default": 1.0 },
            "vol_targeting": {
              "type": "object",
              "additionalProperties": false,
              "required": ["enabled", "lookback_days"],
              "properties": {
                "enabled": { "type": "boolean", "default": true },
                "lookback_days": { "type": "integer", "minimum": 5, "maximum": 252, "default": 20 }
              }
            }
          }
        },
        "constraints": {
          "type": "object",
          "additionalProperties": false,
          "required": ["max_weight_per_name", "max_weight_per_sector", "max_turnover", "min_avg_turnover_krw_20d"],
          "properties": {
            "max_weight_per_name": { "type": "number", "minimum": 0, "maximum": 1, "default": 0.10 },
            "max_weight_per_sector": { "type": "number", "minimum": 0, "maximum": 1, "default": 0.25 },
            "max_turnover": { "type": "number", "minimum": 0, "maximum": 5, "default": 0.80 },
            "min_avg_turnover_krw_20d": { "type": "number", "minimum": 0, "default": 500000000 }
          }
        },
        "rebalance": {
          "type": "object",
          "additionalProperties": false,
          "required": ["frequency", "execution_price"],
          "properties": {
            "frequency": { "type": "string", "enum": ["daily", "weekly", "monthly"], "default": "weekly" },
            "execution_price": { "type": "string", "enum": ["next_open", "close", "vwap"], "default": "next_open" }
          }
        }
      }
    },

    "timing": {
      "type": "object",
      "additionalProperties": false,
      "required": ["enabled", "horizons", "rules", "event_risk"],
      "properties": {
        "enabled": { "type": "boolean", "default": true },
        "horizons": {
          "type": "array",
          "items": { "type": "string", "enum": ["1d", "3d", "1w"] },
          "minItems": 1,
          "uniqueItems": true,
          "default": ["1d", "1w"]
        },
        "rules": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "object",
            "additionalProperties": false,
            "required": ["name", "signal", "priority", "when", "then"],
            "properties": {
              "name": { "type": "string" },
              "signal": { "type": "string", "enum": ["BUY", "WAIT", "REDUCE", "SELL"] },
              "priority": { "type": "integer", "minimum": 1, "maximum": 100, "default": 50 },
              "when": { "type": "object", "description": "간단 DSL(예: all/any + gt/lt 등) 또는 룰엔진 표현" },
              "then": {
                "type": "object",
                "additionalProperties": false,
                "required": ["confidence", "triggers", "risk_flags"],
                "properties": {
                  "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
                  "triggers": { "type": "array", "items": { "type": "string" } },
                  "risk_flags": { "type": "array", "items": { "type": "string" } }
                }
              }
            }
          }
        },
        "event_risk": {
          "type": "object",
          "additionalProperties": false,
          "required": ["enabled", "default_window_days", "default_policy"],
          "properties": {
            "enabled": { "type": "boolean", "default": true },
            "default_window_days": { "type": "integer", "minimum": 0, "maximum": 30, "default": 2 },
            "default_policy": { "type": "string", "enum": ["block_entry", "reduce_size", "no_action"], "default": "block_entry" }
          }
        }
      }
    },

    "reporting": {
      "type": "object",
      "additionalProperties": false,
      "required": ["enabled", "templates", "citations", "listed_company", "private_company"],
      "properties": {
        "enabled": { "type": "boolean", "default": true },
        "templates": {
          "type": "array",
          "items": { "type": "string", "enum": ["investment_memo_v1", "investment_memo_vc_v1", "short_brief_v1"] },
          "default": ["investment_memo_vc_v1"]
        },
        "citations": {
          "type": "object",
          "additionalProperties": false,
          "required": ["require_citations", "min_coverage_ratio"],
          "properties": {
            "require_citations": { "type": "boolean", "default": true },
            "min_coverage_ratio": { "type": "number", "minimum": 0, "maximum": 1, "default": 0.6 }
          }
        },
        "listed_company": {
          "type": "object",
          "additionalProperties": false,
          "required": ["sources"],
          "properties": {
            "sources": {
              "type": "array",
              "items": { "type": "string", "enum": ["DART", "KRX", "KIS", "ECOS"] },
              "default": ["DART", "KIS", "ECOS"]
            }
          }
        },
        "private_company": {
          "type": "object",
          "additionalProperties": false,
          "required": ["inputs", "doc_ingestion"],
          "properties": {
            "inputs": {
              "type": "array",
              "items": { "type": "string", "enum": ["manual_form", "file_upload", "external_connector"] },
              "default": ["manual_form", "file_upload"]
            },
            "doc_ingestion": {
              "type": "object",
              "additionalProperties": false,
              "required": ["rag_enabled", "supported_file_types"],
              "properties": {
                "rag_enabled": { "type": "boolean", "default": true },
                "supported_file_types": {
                  "type": "array",
                  "items": { "type": "string" },
                  "default": ["pdf", "pptx", "xlsx", "docx"]
                }
              }
            }
          }
        }
      }
    },

    "backtest": {
      "type": "object",
      "additionalProperties": false,
      "required": ["enabled", "window", "cost_model", "validation"],
      "properties": {
        "enabled": { "type": "boolean", "default": true },
        "window": {
          "type": "object",
          "additionalProperties": false,
          "required": ["start_date", "end_date"],
          "properties": {
            "start_date": { "type": "string", "format": "date" },
            "end_date": { "type": "string", "format": "date" }
          }
        },
        "cost_model": {
          "type": "object",
          "additionalProperties": false,
          "required": ["commission_rate", "tax_rate_on_sell", "slippage_bps"],
          "properties": {
            "commission_rate": { "type": "number", "minimum": 0, "default": 0.00015 },
            "tax_rate_on_sell": { "type": "number", "minimum": 0, "default": 0.0023 },
            "slippage_bps": { "type": "number", "minimum": 0, "default": 5 }
          }
        },
        "validation": {
          "type": "object",
          "additionalProperties": false,
          "required": ["walk_forward", "turnover_sanity_check"],
          "properties": {
            "walk_forward": { "type": "boolean", "default": true },
            "turnover_sanity_check": { "type": "boolean", "default": true }
          }
        }
      }
    }
  },

  "$defs": {
    "FeatureSpec": {
      "type": "object",
      "additionalProperties": false,
      "required": ["name", "source", "params"],
      "properties": {
        "name": { "type": "string" },
        "source": { "type": "string", "enum": ["KIS", "KRX", "DART", "ECOS", "INTERNAL"] },
        "params": { "type": "object", "additionalProperties": true }
      }
    },
    "EventFeatureSpec": {
      "type": "object",
      "additionalProperties": false,
      "required": ["name", "source", "window_days", "policy"],
      "properties": {
        "name": { "type": "string", "enum": ["earnings", "revision", "rights_issue", "audit_opinion", "litigation", "mna"] },
        "source": { "type": "string", "enum": ["DART"] },
        "window_days": { "type": "integer", "minimum": 0, "maximum": 30, "default": 2 },
        "policy": { "type": "string", "enum": ["block_entry", "reduce_size", "no_action"], "default": "block_entry" }
      }
    },
    "MacroFeatureSpec": {
      "type": "object",
      "additionalProperties": false,
      "required": ["name", "source", "series_code", "transform"],
      "properties": {
        "name": { "type": "string" },
        "source": { "type": "string", "enum": ["ECOS"] },
        "series_code": { "type": "string" },
        "transform": { "type": "string", "enum": ["level", "diff", "pct_change", "zscore"], "default": "level" }
      }
    }
  }
}


---

# FILE: postgres_erd_ddl_v2.1.sql

-- PostgreSQL Schema (ERD/DDL) v2.1
-- Generated: 2026-01-08 (KST)
-- 목적: 코스피/코스닥 단기 추천(TopN+비중) + 타이밍 신호 + 상장/비상장 VC 리포트 + 문서 인제스트/RAG + 백테스트/버전관리

BEGIN;

DO $$ BEGIN
  CREATE TYPE market_scope AS ENUM ('KRX_KOSPI','KRX_KOSDAQ','KRX_ETF','KRX_REIT');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE signal_type AS ENUM ('BUY','WAIT','REDUCE','SELL');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE report_status AS ENUM ('PENDING','RUNNING','DONE','FAILED','CANCELED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE company_type AS ENUM ('LISTED','PRIVATE');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS company (
  company_id        BIGSERIAL PRIMARY KEY,
  company_type      company_type NOT NULL,
  name_ko           TEXT NOT NULL,
  name_en           TEXT,
  -- listed
  corp_code         TEXT UNIQUE,
  stock_code        TEXT UNIQUE,
  market            market_scope,
  sector_code       TEXT,
  sector_name       TEXT,
  listing_date      DATE,
  delisting_date    DATE,
  status            TEXT,
  -- private (민감정보는 해시/암호화 권장)
  external_id_hash  TEXT UNIQUE,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_company_type ON company(company_type);
CREATE INDEX IF NOT EXISTS idx_company_market ON company(market);

CREATE TABLE IF NOT EXISTS security (
  security_id   BIGSERIAL PRIMARY KEY,
  ticker        TEXT NOT NULL UNIQUE,
  isin          TEXT,
  market        market_scope,
  currency      TEXT DEFAULT 'KRW',
  lot_size      INTEGER DEFAULT 1,
  tick_size     NUMERIC,
  company_id    BIGINT REFERENCES company(company_id) ON DELETE SET NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_security_company_id ON security(company_id);

CREATE TABLE IF NOT EXISTS price_daily (
  ticker        TEXT NOT NULL,
  trade_date    DATE NOT NULL,
  open          NUMERIC,
  high          NUMERIC,
  low           NUMERIC,
  close         NUMERIC,
  volume        NUMERIC,
  turnover_krw  NUMERIC,
  adj_factor    NUMERIC,
  source        TEXT DEFAULT 'KIS',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (ticker, trade_date)
);
CREATE INDEX IF NOT EXISTS idx_price_daily_date ON price_daily(trade_date);

CREATE TABLE IF NOT EXISTS market_index_daily (
  index_code    TEXT NOT NULL,
  trade_date    DATE NOT NULL,
  close         NUMERIC,
  ret_1d        NUMERIC,
  vol_20d       NUMERIC,
  source        TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (index_code, trade_date)
);

CREATE TABLE IF NOT EXISTS dart_filing (
  rcp_no        TEXT PRIMARY KEY,
  corp_code     TEXT NOT NULL,
  filing_date   DATE NOT NULL,
  filing_time   TIME,
  filing_type   TEXT,
  title         TEXT,
  url           TEXT,
  is_last_report BOOLEAN DEFAULT FALSE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_dart_filing_corp_date ON dart_filing(corp_code, filing_date);

CREATE TABLE IF NOT EXISTS financial_statement (
  corp_code        TEXT NOT NULL,
  period_end       DATE NOT NULL,
  announced_at     TIMESTAMPTZ NOT NULL,
  item_code        TEXT NOT NULL,
  item_name        TEXT,
  value            NUMERIC,
  unit             TEXT,
  consolidated_flag BOOLEAN DEFAULT TRUE,
  source_rcp_no    TEXT REFERENCES dart_filing(rcp_no) ON DELETE SET NULL,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (corp_code, period_end, item_code, announced_at)
);
CREATE INDEX IF NOT EXISTS idx_fs_announced_at ON financial_statement(announced_at);
CREATE INDEX IF NOT EXISTS idx_fs_corp_period ON financial_statement(corp_code, period_end);

CREATE TABLE IF NOT EXISTS document (
  document_id    BIGSERIAL PRIMARY KEY,
  company_id     BIGINT REFERENCES company(company_id) ON DELETE CASCADE,
  source_type    TEXT NOT NULL, -- DART, UPLOAD, EXTERNAL
  source_ref     TEXT,          -- rcp_no 등
  file_path      TEXT NOT NULL, -- storage path
  file_type      TEXT,          -- pdf/pptx/xlsx/docx
  sha256         TEXT,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_document_company ON document(company_id);
CREATE INDEX IF NOT EXISTS idx_document_source ON document(source_type, source_ref);

CREATE TABLE IF NOT EXISTS document_chunk (
  chunk_id       BIGSERIAL PRIMARY KEY,
  document_id    BIGINT NOT NULL REFERENCES document(document_id) ON DELETE CASCADE,
  chunk_no       INTEGER NOT NULL,
  text_path      TEXT,
  content_text   TEXT,
  token_count    INTEGER,
  embedding_id   TEXT,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(document_id, chunk_no)
);
CREATE INDEX IF NOT EXISTS idx_document_chunk_doc ON document_chunk(document_id);

CREATE TABLE IF NOT EXISTS macro_series (
  series_code   TEXT NOT NULL,
  obs_date      DATE NOT NULL,
  value         NUMERIC,
  unit          TEXT,
  source        TEXT DEFAULT 'ECOS',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (series_code, obs_date)
);

CREATE TABLE IF NOT EXISTS feature_snapshot (
  as_of_date     DATE NOT NULL,
  ticker         TEXT NOT NULL,
  feature_name   TEXT NOT NULL,
  value          NUMERIC,
  effective_from TIMESTAMPTZ,
  data_version   TEXT NOT NULL DEFAULT 'v1',
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (as_of_date, ticker, feature_name, data_version)
);
CREATE INDEX IF NOT EXISTS idx_feature_snapshot_ticker_date ON feature_snapshot(ticker, as_of_date);

CREATE TABLE IF NOT EXISTS factor_score (
  as_of_date      DATE NOT NULL,
  ticker          TEXT NOT NULL,
  model_version   TEXT NOT NULL,
  total_score     NUMERIC,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (as_of_date, ticker, model_version)
);

CREATE TABLE IF NOT EXISTS strategy_def (
  strategy_id    TEXT NOT NULL,
  version        TEXT NOT NULL,
  schema_version TEXT NOT NULL DEFAULT '2.1.0',
  name           TEXT,
  json_def       JSONB NOT NULL,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY(strategy_id, version)
);

CREATE TABLE IF NOT EXISTS backtest_run (
  run_id           BIGSERIAL PRIMARY KEY,
  strategy_id      TEXT NOT NULL,
  strategy_version TEXT NOT NULL,
  start_date       DATE NOT NULL,
  end_date         DATE NOT NULL,
  cost_model       JSONB NOT NULL,
  metrics          JSONB,
  artifacts_path   TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  FOREIGN KEY(strategy_id, strategy_version) REFERENCES strategy_def(strategy_id, version) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS recommendation (
  as_of_date       DATE NOT NULL,
  strategy_id      TEXT NOT NULL,
  strategy_version TEXT NOT NULL,
  ticker           TEXT NOT NULL,
  rank             INTEGER NOT NULL,
  score            NUMERIC,
  target_weight    NUMERIC,
  rationale        JSONB,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY(as_of_date, strategy_id, strategy_version, ticker),
  FOREIGN KEY(strategy_id, strategy_version) REFERENCES strategy_def(strategy_id, version) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS idx_reco_asof_rank ON recommendation(as_of_date, rank);

CREATE TABLE IF NOT EXISTS timing_signal (
  ts            TIMESTAMPTZ NOT NULL,
  ticker        TEXT NOT NULL,
  horizon       TEXT NOT NULL,
  signal        signal_type NOT NULL,
  confidence    NUMERIC,
  triggers      JSONB,
  risk_flags    JSONB,
  model_version TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY(ts, ticker, horizon)
);
CREATE INDEX IF NOT EXISTS idx_signal_ticker_ts ON timing_signal(ticker, ts DESC);

CREATE TABLE IF NOT EXISTS watchlist (
  watchlist_id  BIGSERIAL PRIMARY KEY,
  owner_user_id TEXT NOT NULL,
  name          TEXT NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS watchlist_item (
  watchlist_id  BIGINT NOT NULL REFERENCES watchlist(watchlist_id) ON DELETE CASCADE,
  ticker        TEXT NOT NULL,
  added_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY(watchlist_id, ticker)
);

CREATE TABLE IF NOT EXISTS report_request (
  report_id     BIGSERIAL PRIMARY KEY,
  company_id    BIGINT NOT NULL REFERENCES company(company_id) ON DELETE CASCADE,
  template      TEXT NOT NULL,
  as_of_date    DATE,
  status        report_status NOT NULL DEFAULT 'PENDING',
  requested_by  TEXT,
  params        JSONB,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_report_company ON report_request(company_id, created_at DESC);

CREATE TABLE IF NOT EXISTS report_artifact (
  artifact_id   BIGSERIAL PRIMARY KEY,
  report_id     BIGINT NOT NULL REFERENCES report_request(report_id) ON DELETE CASCADE,
  format        TEXT NOT NULL, -- pdf/html
  file_path     TEXT NOT NULL,
  citations     JSONB,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMIT;



---

# FILE: stock_reco_redesign_v3_confirmed_ko.md

# 주식종목추천(코스피/코스닥) + 단기 타이밍 + VC급 리포트(비상장 포함) 재설계 v3
작성일: 2026-01-08 (KST)

본 문서는 사용자께서 확정해주신 방향을 “제품 요구사항(결정 사항)”으로 반영하고, 그에 맞춰 **아키텍처/데이터/퀀트/리포트**를 디테일하게 재정렬한 버전입니다.

---

## 1. 확정된 제품 방향(결정 사항)

### 1) 대상 시장
- 기본: **국내 주식(코스피/코스닥)**
- 확장: **ETF/리츠는 구조적으로 확장 가능하도록 설계** (초기에는 유니버스에서 제외 가능)

### 2) 운용 지평
- **단기 중심(일~주)**  
  - 추천(스크리닝)은 주/월 단위로 후보군 유지 가능  
  - **타이밍/신호는 일~분 단위**(가능 범위에서)로 설계

### 3) 추천 결과
- **Top N + 비중(weight)까지 산출**
- 비중은 “점수 기반 + 리스크 제약”으로 자동 산출(설명 가능해야 함)

### 4) 실행(주문)
- 시스템은 **신호만 제공**,  
- **실주문은 사용자가 수동으로 진행** (법/인가 리스크 최소화)

### 5) VC 리포트 대상
- **상장 + 비상장 포함**
- 비상장은 DART 중심이 불가능하므로 **데이터 수집 방식(입력/연동/검증)을 별도 설계**해야 함

---

## 2. 제품을 3개 출력물(Output)로 고정(변하지 않는 중심축)

### Output A. 종목추천(Top N + 비중)
- 코스피/코스닥 유니버스에서 **퀀트 점수 기반 Top N** 산출
- 각 종목의 목표 비중(weight)과 근거(팩터 기여, 리스크, 제약 충족)를 함께 제공

### Output B. 관심종목 타이밍 신호(일~주)
- 사용자가 선택한 관심종목(또는 추천 종목)에 대해
- `BUY / WAIT / REDUCE / SELL` + 트리거 조건 + 신뢰도 + 리스크 플래그 제공
- 알림(푸시/메일/슬랙 등)은 운영 옵션

### Output C. 투자심사 보고서(상장+비상장)
- 상장: DART+시장데이터 기반 “투자 메모(Investment Memo)” 자동 생성
- 비상장: 업로드/입력/외부DB(선택) 기반 “투자 메모” 자동 생성
- 정량(코드 계산) + 정성(LLM 서술) + 근거/인용(가능한 경우)을 결합

---

## 3. 전체 아키텍처(단기·수동주문·VC리포트에 맞춘 형태)

### 3.1 레이어
1) Ingestion (KRX/DART/ECOS/KIS + 비상장 입력/업로드)
2) Raw Store (원본 저장: JSON/CSV/PDF/엑셀/피치덱)
3) Staging/ODS (정규화 테이블)
4) Feature Store (시점 정합 + 피처 버전)
5) Engines
   - 추천 엔진(랭킹+비중)
   - 타이밍 엔진(진입/청산/리스크)
   - 리포트 엔진(상장/비상장 템플릿)
6) API (조회/검색/리포트/전략관리)
7) UI (스크리너/종목 상세/관심목록/리포트 빌더)
8) Observability (감사로그/재현성/데이터 품질)

### 3.2 저장소 권장
- Cloud SQL(PostgreSQL): 정규화 데이터, 피처, 전략, 결과, 리포트 메타
- Storage(GCS/Firebase): 공시원문, 비상장 자료(PDF/엑셀/피치덱), 리포트 산출물(PDF)
- (선택) Vector DB: 공시/비상장 문서 RAG(근거 기반 서술)

---

## 4. 데이터 설계(상장 vs 비상장 분기)

### 4.1 공통 “엔티티” 기준
- 상장: `ticker(stock_code)` 중심 + `corp_code` 매핑
- 비상장: `company_id` 중심(내부키) + 외부 식별자(사업자번호 등)는 **암호화/마스킹 정책** 필요

### 4.2 상장 데이터(코스피/코스닥)
- 시장: 가격/거래량(일봉), (선택) 분봉, 호가/체결
- 공시/재무: DART 공시, 재무제표(발표일 기준)
- 거시: ECOS 주요 시계열(금리/물가/환율 등)
- 수급/지수/기타: KRX 범위 내 통계(가능한 항목만)

### 4.3 비상장 데이터(핵심: “수집 방식”이 곧 제품 경쟁력)
비상장은 공시·시장가격이 없으므로, 시스템이 아래 입력을 수용해야 합니다.

**(1) 구조화 입력(폼)**
- 기업개요: 업종, 제품/서비스, 고객군, 경쟁사
- 재무(연도/분기): 매출, 매출총이익, 영업이익, 당기순이익, 현금흐름(가능한 범위)
- 지표: GM%, OPM%, 성장률, CAC/LTV(가능 시)
- 자본구조: 투자 라운드, 밸류, 희석, 캡테이블(선택)

**(2) 파일 업로드**
- 피치덱(PDF), IR 자료, 감사보고서/재무제표(엑셀), 계약서/주요 고객 증빙(선택)
- 업로드 파일은 원본 보관 + 추출 텍스트(검색/RAG용) 생성

**(3) 외부 데이터베이스 연동(선택)**
- 국내 기업정보/재무 데이터 제공 서비스(유료) 연동 가능하도록 “커넥터 인터페이스”만 설계
  - 초기 MVP에서는 연동 없이도 동작(입력/업로드 중심)

---

## 5. 퀀트 추천 엔진(단기 중심 + 비중 산출)

### 5.1 추천 엔진의 역할(중요)
- 추천은 “실행”이 아니라 **후보군을 체계적으로 뽑는 단계**
- 단기 운용이라도 **리스크/유동성/턴오버**가 성과를 좌우 → 제약조건이 핵심 디테일

### 5.2 기본 추천 파이프라인(권장)
1) Universe 필터(코스피/코스닥)
2) 팩터/피처 계산(설명 가능)
3) 점수 결합(가중치) → 랭킹
4) Top N 선택
5) 비중 산출(제약 포함)
6) 추천 근거 생성(팩터 기여도/리스크/필터 통과 사유)

### 5.3 단기 중심 피처 세트(예시)
- 모멘텀/추세:
  - 5/10/20일 수익률, 20일 돌파, 이동평균(20/60)
- 변동성/리스크:
  - 10/20일 변동성, ATR(선택), 최대낙폭(lookback)
- 유동성:
  - 거래대금(최근 20일 평균), 스프레드 근사(가능 시)
- 이벤트/필터(DART):
  - 실적 발표/정정/유증/감사 관련 이벤트 전후 필터(정책)

> 가치/퀄리티는 단기 타이밍에는 직접효과가 약할 수 있으나, “후보군 질”을 올리는 보조팩터로 사용 가능합니다(단, 발표일 정합 필수).

### 5.4 비중(weight) 산출(설명 가능한 방식 우선)
권장 기본:
- **Score-proportional + 리스크 패널티**
- 제약조건:
  - 종목 최대비중(예: 10%)
  - 섹터 최대비중(예: 25%)
  - 유동성 한도(일평균 거래대금 대비 주문 비율 제한)
  - 턴오버 제한(리밸런싱 시 과도한 교체 방지)

대안:
- 변동성 타겟팅: 변동성이 큰 종목 비중 축소
- 간단 리스크 패리티 응용(종목 단위)

### 5.5 전략 정의 JSON(필수: 버전관리)
- `universe_rules`
- `features`
- `scoring_weights`
- `constraints`
- `rebalance_schedule`
- `cost_model_assumptions`
- `explainability`(근거 생성 규칙)

---

## 6. 타이밍 엔진(신호만 제공, 단기 최적화)

### 6.1 신호 구조(표준)
- `signal`: BUY / WAIT / REDUCE / SELL
- `confidence`: 0~1
- `horizon`: 1d / 3d / 1w 등
- `triggers`: 조건 리스트(가격/변동성/이벤트)
- `risk_flags`: 거래정지, 변동성 급등, 이벤트 리스크 등

### 6.2 단기 타이밍 룰(예시 템플릿)
- 진입(매수) 예:
  - `close > max(close, 20d)` AND `volatility_z < 2`
  - `close > MA20` AND `MA20 상승`
- 대기(WAIT) 예:
  - `volatility_z >= 2` (급변 구간)
  - `중요 공시 전후 N일` (정책)
- 축소/청산 예:
  - `close < MA20` 또는 `trailing_stop hit`
  - `MDD > threshold`

> 본 설계는 수동주문이므로, 신호는 “행동 권고”와 “근거”를 명확히 제시하는 UX가 중요합니다.

---

## 7. VC/투자심사 리포트 엔진(상장 + 비상장)

### 7.1 리포트 공통 템플릿(권장)
1) Executive Summary
2) Business & Moat
3) Market/TAM & 경쟁환경
4) Financial Deep Dive
5) Valuation (상장: 멀티플/DCF, 비상장: 라운드/멀티플/시나리오 중심)
6) Catalysts & Risks
7) Scenario(베어/베이스/불) + 감도분석
8) Appendix(근거/자료 목록)

### 7.2 상장 리포트(근거: 공시/재무/시장)
- DART 공시/재무를 자동 수집·정규화
- 발표일 기준으로 성장률/마진/현금흐름 추세 계산
- 공시 타임라인과 리스크 이벤트 자동 요약(인용 가능)

### 7.3 비상장 리포트(근거: 입력/업로드/검증)
- 사용자가 입력한 재무 + 업로드 문서에서 추출한 근거를 결합
- “자료 신뢰도 레벨”을 명시:
  - (A) 감사보고서 기반
  - (B) 내부 결산/추정
  - (C) 피치덱 주장(검증 필요)
- 캡테이블/희석/라운드 히스토리(가능 시) 포함
- KPI가 있는 경우(SaaS, 커머스 등) 템플릿별 확장

### 7.4 RAG(근거 기반 서술) 적용 범위
- 상장: 공시 원문(사업보고서/분기보고서/주요사항) 중심
- 비상장: 피치덱/IR/재무 엑셀/계약 증빙 중심
- 산출물에는 “인용/근거 링크/파일 참조”를 남김(감사/검토 용)

---

## 8. 데이터/모델 품질 장치(디테일 확보)

### 8.1 필수 품질 규칙
- point-in-time 강제(발표일 이전 사용 금지)
- 유니버스/필터/전략/결과는 모두 버전으로 재현 가능해야 함
- 비용/슬리피지 가정은 전략 정의에 포함(비교 가능)

### 8.2 단기 전략 검증(권장)
- 워크포워드(rolling) + 거래비용 반영
- 회전율(턴오버) 제한 없이 성과가 좋은 전략은 의심(현실 체결 문제)
- 스트레스 테스트(변동성 급등 구간 별도 평가)

---

## 9. UI/기능 구성(결정 사항 반영)

### 9.1 Screener(추천)
- 필터(시장/유동성/섹터) + Top N + 비중
- 추천 근거: 점수/팩터 기여/리스크/제약 충족 여부

### 9.2 종목 상세(상장)
- 가격/추세/변동성 + 공시 타임라인 + 재무 요약
- 타이밍 신호(트리거 포함) + “수동 주문 체크리스트”

### 9.3 관심종목(Watchlist)
- 신호 알림 + 시뮬레이션(가상 진입/청산 성과)
- 사용자 정의 룰(간단한 트리거 커스텀)

### 9.4 리포트(상장/비상장)
- 템플릿 선택 → 자료 연결(공시/업로드/입력) → 자동 생성 → 검토/수정 → PDF 저장

---

## 10. 로드맵(결정 사항에 맞춘 현실적 단계)

### Phase 0: 공통 기반(데이터/버전관리)
- 상장: 종목마스터/일봉/기본지수
- DART 기본 적재(공시 메타 + 재무)
- ECOS 핵심 시계열
- 전략 정의 JSON v2 + 결과/리포트 버전관리

### Phase 1: 단기 추천(Top N + 비중) MVP
- 단기 피처 + 랭킹 + 제약 비중 산출
- 추천 근거 패널/리포트(간단) 제공

### Phase 2: 타이밍 신호 MVP(수동 주문)
- 추세/변동성/이벤트 기반 신호
- 관심종목 알림 + 시뮬레이션

### Phase 3: VC 리포트 MVP(상장 먼저)
- 상장 투자메모 자동생성 + 공시 근거 인용

### Phase 4: 비상장 리포트 확장
- 입력폼/업로드 + 신뢰도 레벨 + KPI 템플릿 확장
- (선택) 외부DB 커넥터 인터페이스 도입

---

## 11. 다음 설계 산출물(원하시면 바로 생성)
사용자 결정 사항이 확정되었으므로, 다음 3개를 “파일로” 만들어 드릴 수 있습니다.

1) **전략 정의 JSON 스키마 v2.1**  
   - 추천(Top N + 비중) + 타이밍 + 리포트 설정까지 포함

2) **PostgreSQL ERD 초안(v2.1)**  
   - 상장/비상장 분기 테이블 + 문서 업로드/RAG 인덱싱 테이블 포함

3) **API(OpenAPI) 초안(v2.1)**  
   - Screener/Signals/Watchlist/Reports/Strategies/Backtests 전부

---

## 12. 최소로 추가로 필요한 정보(정확도 상승용, 필수는 아님)
- 단기 타이밍의 기본 주기: 일봉 기준(장마감)만? 분봉(장중)까지?  
- 추천 Top N 기본값: 10/20/50 중 선호  
- 비상장 리포트 템플릿: SaaS/제조/커머스 등 “주력 섹터”가 있으신지

(위 3개는 없어도 진행 가능하며, 기본값으로 설계해도 됩니다.)



---

# FILE: stock_reco_redesign_v2_ko.md

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



---

# FILE: quant_algorithms_reference_ko.md

# 퀀트(Quant) 알고리즘 참고 문서 (주식 종목추천/시스템 구축용)

> 목적: “주식 종목추천” 시스템에서 흔히 쓰는 **퀀트 알고리즘을 설계·구현·검증·운영**까지 한 번에 참고할 수 있도록, 핵심 개념과 실무 체크리스트를 문서 형태로 정리했습니다.  
> 범위: 교육/연구/개발 관점(투자 자문 아님). 실제 투자 적용 시 규정·리스크·수수료/세금·시장제도 등을 별도로 확인하세요.

---

## 0. 퀀트 알고리즘 한 장 요약(전체 흐름)

1) **데이터 수집**(가격/거래량/재무/공시/뉴스 등)  
2) **정합성/시간정렬**(point-in-time, 공시발표 시점 반영)  
3) **유니버스 선정**(상장폐지 포함, 유동성/가격 필터)  
4) **피처(특성) 생성**(모멘텀, 가치, 퀄리티, 변동성 등)  
5) **시그널 생성**(룰 기반 팩터 점수 / 통계 / ML 예측)  
6) **포트폴리오 구성**(종목 선택 + 비중 결정 + 제약조건)  
7) **백테스트**(거래비용·슬리피지·리밸런싱 반영)  
8) **검증/강건성 테스트**(워크포워드, 과최적화 진단)  
9) **실거래/모니터링**(주문·체결·리스크·드리프트 감시)  
10) **운영 자동화**(재학습/리밸런싱/리포트/버전관리)

---

## 1. 데이터: 퀀트가 실패하는 가장 흔한 이유

### 1.1 데이터 종류
- **가격/거래량(OHLCV)**: 일/분/틱  
- **기업행동(Corporate Actions)**: 액면분할, 배당, 유상증자 등  
- **재무/펀더멘털**: 분기/연간(발표 시점 중요)  
- **시장/섹터 분류**: GICS 등(리밸런싱/중립화에 활용)  
- **대체데이터(선택)**: 뉴스/공시 텍스트, 검색량, 위성 등

### 1.2 Point-in-time(시점 정합성)
백테스트가 “너무 좋게” 나오는 대표 원인:
- **미래 데이터를 과거에 사용**(Look-ahead bias)
- 재무데이터는 “해당 분기 종료일”이 아니라 **공시 발표일 이후**에만 사용해야 함  
- 데이터 공급사가 **backfill**(정정/추가)하는 경우, 과거 시점에서 알 수 없었던 값이 포함될 수 있음

**실무 체크**
- 각 데이터 row에 `effective_from`(사용 가능 시점), `as_of`(기준 시점) 메타를 둔다
- 재무/공시 데이터는 반드시 **발표일/수정일**을 추적한다

### 1.3 Survivorship bias(생존자 편향)
- 현재 살아남은 종목만으로 과거를 테스트하면 성과가 과대평가됨  
- **상장폐지/관리종목/거래정지** 이력 포함 필요

**실무 체크**
- 유니버스를 “그 당시 상장되어 있던 종목 전체”로 구성
- 가능한 경우 “상장/상폐 마스터 테이블”을 별도로 유지

### 1.4 데이터 품질 QA 체크리스트
- 결측치/이상치: 0 가격, 음수 거래량, 급격한 점프
- Corporate action 반영: 수정주가/원주가 혼용 금지
- 시간대/캘린더: 휴장일 처리, 리밸런싱 날짜 규칙 고정
- 종목코드 변경: 코드 체계 변경 시 mapping 필요

---

## 2. 유니버스(Universe) 설계

### 2.1 왜 유니버스가 중요?
전략의 절반은 “무엇을 투자 대상으로 삼느냐”에서 결정됩니다.
- 소형주·저유동성주를 포함하면 백테스트 수익이 좋아 보이지만 현실 체결이 어려울 수 있음
- 거래정지/급등락 종목이 많으면 슬리피지가 폭발

### 2.2 일반적인 유니버스 필터 예시(일봉 기준)
- 가격: `price > 1,000원` 같은 최소단위(시장별 상이)
- 유동성: `최근 20일 평균 거래대금 > X`
- 상장기간: `상장 후 6개월 이상`
- 관리/거래정지 제외(정책 결정 필요)
- 섹터 제한(선택)

> 팁: 시스템에서는 `universe_rule_version`을 별도로 두고, 전략과 독립적으로 관리하면 좋습니다.

---

## 3. 시그널 생성의 큰 분류(퀀트 알고리즘 지도)

퀀트 알고리즘은 크게 아래로 묶입니다.

1) **팩터/랭킹(크로스섹션)**: “오늘 기준 좋은 종목 Top N”  
2) **시계열(Time-series)**: “이 종목이 지금 추세/회귀 상태인가?”  
3) **통계적 차익/페어**: “두 자산 관계가 벌어졌으니 수렴을 노린다”  
4) **이벤트 기반**: “공시/실적/뉴스 이벤트 이후 평균 패턴”  
5) **마켓메이킹/초단타**: 개인/일반 프로젝트에서는 보통 제외(체결/인프라 난이도 큼)

이 문서는 1)~4)에 집중합니다.

---

## 4. 팩터(요인) 기반 종목추천 알고리즘

### 4.1 팩터 투자란?
“특정 특성(팩터)이 장기적으로 보상받는 경향”을 이용해  
종목을 점수화하고 상위/하위를 매수·매도(또는 롱/숏)합니다.

대표 팩터
- **Value**: 저평가(PBR↓, PER↓ 등)
- **Quality**: 수익성/재무건전(ROE↑, 부채↓, 이익의 질 등)
- **Momentum**: 과거 강한 수익률이 이어지는 경향
- **Low Volatility**: 변동성이 낮은 자산의 효율
- **Size**: 소형주 프리미엄(시장/국가별 상이)

### 4.2 가장 흔한 구현: “점수 → 랭킹 → 상위 N”
1) 각 종목에 대해 팩터 값을 계산  
2) 팩터별로 **표준화(z-score) 또는 퍼센타일 랭크**  
3) 여러 팩터를 가중합해 총점 `score` 생성  
4) 상위 N개 매수(또는 상위/하위 롱-숏)  
5) 월 1회/주 1회 리밸런싱

#### 표준화 방식 예시
- 퍼센타일: `rank_pct = rank(x) / (N-1)`
- z-score: `z = (x - mean(x)) / std(x)` (이상치에 취약)

#### 점수 결합 예시
- 단순 가중합: `score = 0.4*value + 0.3*quality + 0.3*momentum`
- 안전장치: `winsorize`(극단치 컷), `sector-neutral`(섹터 중립화)

### 4.3 리밸런싱 규칙
- **월말/월초 고정**: 운영/리포팅에 유리
- **주기**는 전략 성격과 거래비용에 좌우됨  
  - 모멘텀: 월/주  
  - 가치/퀄리티: 분기/월  
- 리밸런싱 때 “모든 종목 전량 교체”는 회전율 폭증 → **턴오버 제한**이 중요

### 4.4 턴오버(회전율) 제어
- 버퍼링: 기존 보유 종목은 **순위가 일정 수준 아래로 내려가야** 매도
- 최소 보유기간: N일/1개월 등
- 거래금지 구간: 이벤트/변동성 급증 시 리밸런싱 스킵(정책)

---

## 5. 시계열(Time-series) 기반 알고리즘

### 5.1 추세추종(Trend Following)
핵심 아이디어: 상승 추세면 보유/매수, 하락이면 축소/매도.

대표 시그널
- 이동평균 교차: `MA_short > MA_long`
- N일 수익률: `ret_12m` 등
- 돌파: `price > max(price, lookback)`

주의점
- 횡보장에서 휩쏘(가짜 신호) 많음
- 거래비용을 반드시 반영해야 함

### 5.2 평균회귀(Mean Reversion)
핵심 아이디어: 단기 급락/급등은 평균으로 되돌아온다.

대표 시그널
- 볼린저 밴드: `price < MA - k*std`
- z-score: `z < -2` 같은 과매도/과매수
- RSI(보조)

주의점
- 추세장에서는 “떨어지는 칼”이 될 수 있음 → 레짐 필터(추세/변동성) 필요

---

## 6. 페어/통계적 차익(StatArb) 기초

### 6.1 페어 트레이딩 기본
- 같은 업종/유사 비즈니스 두 종목 A,B를 선택
- 스프레드(가격 비율/차이)가 비정상적으로 벌어지면 수렴을 기대해 포지션 설정

대표 접근
- 상관/공적분(cointegration) 기반
- 스프레드 z-score 기반 진입/청산

현실 난점
- 차입/공매도 제약(시장별)
- 구조적 변화(기업 펀더멘털 변화)로 관계 붕괴

---

## 7. 포트폴리오 구성(비중 결정) 알고리즘

### 7.1 단순하지만 강력한 방식
- **Equal Weight**: 선택된 종목에 동일 비중
- **Score Proportional**: 점수에 비례해 비중 배분(상한/하한 필요)
- **Volatility Targeting**: 변동성이 큰 종목 비중 축소

### 7.2 리스크 예산: Risk Parity(개념)
- “자산/팩터별 위험 기여도를 비슷하게 맞추자”  
- 기대수익 추정이 어려울 때 포트폴리오를 안정적으로 만드는 접근

(리스크 패리티는 다자산에 더 흔하지만, **종목/섹터 단위**로 응용 가능)

### 7.3 제약조건(실무에서 꼭 필요)
- 종목 최대비중: `w_i <= 5%`
- 섹터 최대비중: `sector_w <= 25%`
- 최소 거래단위/호가단위 반영
- 유동성 한도: “일평균 거래대금의 x% 이상 매수 금지”
- 턴오버 제한: `sum(|w_t - w_{t-1}|) <= T`

---

## 8. 백테스트 설계(실패를 막는 핵심 파트)

### 8.1 백테스트 “필수” 구성요소
- 리밸런싱 캘린더(예: 매월 첫 거래일)
- 체결 가정(종가/시가/다음날 VWAP 등)
- 거래비용(수수료+세금+슬리피지)
- 결측/거래정지 처리 정책
- 기업행동 반영(수정주가/배당 재투자 여부)

### 8.2 대표적인 함정 체크(반드시 방지)
- Look-ahead bias(미래 정보 사용)
- Survivorship bias(생존자 편향)
- Data-snooping(너무 많은 실험 후 우연히 맞은 모델 선택)
- Overfitting(과최적화) / 미세 파라미터 튜닝 중독
- 거래비용/슬리피지 무시

### 8.3 과최적화 진단(고급)
- 워크포워드(rolling) 평가
- 파라미터 민감도 분석(조금 바꿔도 성과가 유지되는가?)
- Combinatorially Symmetric Cross-Validation(CSCV) 같은 방법으로
  “좋아 보이는 백테스트가 우연일 확률”을 추정(PBO, PSR 등)

---

## 9. ML(머신러닝) 기반 종목추천 알고리즘

### 9.1 문제정의 3가지 패턴
1) **회귀**: 미래 수익률 예측(노이즈 큼)  
2) **분류**: “상위 수익률 그룹인가?”(Top/Bottom)  
3) **랭킹/스코어링**: 종목을 순서대로 정렬하는 점수 예측(실무 적합)

> 실무 팁: “정확한 수익률 수치”보다 **랭킹 문제**가 더 안정적인 편입니다.

### 9.2 피처 엔지니어링(예시)
- 가격 기반: 1/5/20/60/252일 수익률, 변동성, 최대낙폭, 거래대금 변화
- 팩터 기반: value/quality/momentum 점수
- 위험: 베타, 섹터 더미, 시장국면 지표(변동성)

### 9.3 학습/평가 프로토콜(중요)
- 시간 순서 유지: 랜덤 셔플 금지(시계열 누수)
- 학습/검증/테스트를 시간으로 분리
- 지표:
  - 예측 정확도보다 **포트폴리오 성과 지표**가 더 중요(샤프, MDD, 턴오버)
- 안정화:
  - 규제/정규화, 단순 모델부터(Linear/Tree) → 복잡 모델은 마지막

### 9.4 “모델 성능”과 “전략 성능”은 다르다
- 모델의 AUC가 좋아도, 거래비용 고려하면 수익이 안 날 수 있음
- 모델 출력 → 포트폴리오 구성 단계가 성과를 크게 좌우

---

## 10. 운영(Production) 관점 체크리스트

### 10.1 파이프라인 구성
- 배치 스케줄:
  - 장 마감 후 데이터 적재
  - 신호 계산
  - 리밸런싱 주문 리스트 생성
  - 리포트/알림 생성
- 버전관리:
  - 전략 정의 JSON(룰/가중치/유니버스/비용 가정) 버전
  - 데이터 스냅샷 버전(재현 가능성)

### 10.2 모니터링
- 데이터 누락/지연 알림
- 백테스트 대비 드리프트:
  - 수익률/변동성/턴오버/섹터 편중
- 체결 리포트:
  - 예상 대비 슬리피지, 미체결률

### 10.3 “설명 가능한 추천”
종목추천 시스템이라면 “왜 추천했는지”가 중요합니다.
- 팩터 기여도(각 팩터 점수)
- 최근 변화(모멘텀 개선, 밸류 저평가 확대 등)
- 리스크(변동성, 섹터 편중)와 제약조건 만족 여부

---

## 11. 구현 템플릿(의사코드)

### 11.1 팩터 랭킹 기반 월간 리밸런싱
```pseudo
for each rebalance_date t:
  universe = get_universe(t)

  features = compute_features(universe, as_of=t)        # point-in-time
  scores   = rank_and_combine(features)                 # percentile or zscore
  picks    = topN(scores, N)

  target_weights = equal_weight(picks)
  target_weights = apply_constraints(target_weights)    # max weight, sector cap
  orders = diff_to_orders(current_positions, target_weights)

  simulated_fills = execute(orders, price_model="next_open", tc_model=...)
  update_portfolio(simulated_fills)
```

### 11.2 거래비용 모델(단순형)
- 수수료: `commission = notional * fee_rate`
- 세금(해당 시장 적용): `tax = sell_notional * tax_rate`
- 슬리피지(예): `slippage = notional * slip_bps / 10000`

> 단순형이라도 “0”보다 훨씬 낫습니다. 전략 비교에는 충분히 유용합니다.

---

## 12. 추천: “주식종목추천 MVP”에서 가장 현실적인 2가지

### MVP-1: 팩터 3종(가치+퀄리티+모멘텀) 랭킹
- 장점: 구현/설명 쉬움, 과최적화 위험 상대적으로 낮음  
- 구성:
  - Universe: 유동성 필터
  - Features: PBR/ROE/12m momentum 등
  - Rebalance: 월 1회
  - Portfolio: equal-weight + sector cap + turnover limit

### MVP-2: 랭킹 ML(트리 기반) + 단순 제약 포트폴리오
- 장점: 피처 추가에 유연, RAG/뉴스점수도 합칠 수 있음  
- 구성:
  - Label: 다음 1개월 수익률 상위 20% 여부(분류) 또는 수익률(랭킹)
  - Model: LightGBM/XGBoost(가능하면 단순부터)
  - Output: 종목 점수 → Top N → 제약 포트폴리오

---

## 13. 참고 문헌/키워드(검색용)
- “Fama-French factors (Mkt-RF, SMB, HML, RMW, CMA)”
- “Momentum factor UMD”
- “Backtest overfitting, PBO, CSCV”
- “Point-in-time data, survivorship bias”
- “Risk parity portfolio construction”
- “Factor investing value quality momentum”

---

## 14. 다음 단계(원하시면)
원하시면 아래 중 하나를 골라서, **당장 코드로 옮길 수 있게** 더 구체화해드릴게요.
1) “팩터 3종 랭킹 전략”을 **DB 스키마 + 배치잡 + 백테스트 구조**로 설계  
2) “ML 랭킹 모델”을 **학습/검증 분리 + 피처 스토어 + 리포트**까지 설계  
3) “RAG로 공시/뉴스 근거”를 붙여 **설명 가능한 추천 리포트** 템플릿 제작

