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
