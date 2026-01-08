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
