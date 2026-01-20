.PHONY: api-run api-test api-lint db-up db-down db-migrate db-seed worker-daily-close

db-up:
	docker compose up -d

db-down:
	docker compose down

db-migrate:
	cd apps/api && alembic upgrade head

db-seed:
	PYTHONPATH=. python scripts/seed_sample_data.py

api-run:
	cd apps/api && uvicorn app.main:app --reload --port 8010

api-test:
	cd apps/api && pytest -q

api-lint:
	cd apps/api && ruff check .

worker-daily-close:
	PYTHONPATH=. python -m services.worker.worker.main --job daily_close --asof 2026-01-08
