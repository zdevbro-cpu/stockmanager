# Alembic Migrations

- apps/api에서 Alembic을 사용하여 DB 스키마 변경을 관리합니다.
- 초기 스키마는 docs/postgres_erd_ddl_v2.1.sql을 참고하세요.

## 예시(로컬)
- alembic init db/migrations
- alembic revision --autogenerate -m "init"
- alembic upgrade head
