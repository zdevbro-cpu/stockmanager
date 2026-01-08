# GCP Deploy Notes (권장)

## Cloud Run
- apps/api: API 서비스
- services/ingest: 수집 워커(Cloud Run jobs 또는 service+Scheduler)
- services/worker: 배치 워커(Cloud Run jobs 또는 service+Scheduler)

## Scheduler
- 장마감 이후(KST) daily_close job 트리거

## Queue
- 리포트 생성/문서 인제스트는 Pub/Sub 또는 Cloud Tasks 권장

## Secrets
- Secret Manager에 KIS/DART/ECOS 키 보관
