.PHONY: up down build restart logs shell-api shell-db migrate seed clean

# ── Lifecycle ──────────────────────────────────────────────────────────────────
up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build --no-cache

restart:
	docker compose restart

# ── Logs ───────────────────────────────────────────────────────────────────────
logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api

logs-worker:
	docker compose logs -f worker

logs-beat:
	docker compose logs -f beat

# ── Shells ─────────────────────────────────────────────────────────────────────
shell-api:
	docker compose exec api bash

shell-db:
	docker compose exec postgres psql -U postgres -d aistudio

shell-worker:
	docker compose exec worker bash

shell-redis:
	docker compose exec redis redis-cli

# ── Database ───────────────────────────────────────────────────────────────────
migrate:
	docker compose exec api alembic upgrade head

migrate-new:
	docker compose exec api alembic revision --autogenerate -m "$(msg)"

migrate-down:
	docker compose exec api alembic downgrade -1

# ── Agents (manual trigger) ────────────────────────────────────────────────────
scan-opportunities:
	docker compose exec worker celery -A workers.celery_app call tasks.scan_opportunities

scout-architecture:
	docker compose exec worker celery -A workers.celery_app call tasks.scout_architecture

monitor-press:
	docker compose exec worker celery -A workers.celery_app call tasks.monitor_press

# ── Dev setup ──────────────────────────────────────────────────────────────────
setup:
	cp -n .env.example .env || true
	docker compose up -d postgres redis
	@echo "Waiting for postgres..." && sleep 3
	docker compose up -d api
	@echo "API running at http://localhost:8000/docs"

# ── Telegram / OpenClaw plugin sync ────────────────────────────────────────────
sync-plugin:
	rsync -av --delete openclaw-plugin/ ~/.openclaw/extensions/openclaw-aistudioos/
	openclaw daemon restart
	@echo "Plugin synced and gateway restarted"

# ── Clean ──────────────────────────────────────────────────────────────────────
clean:
	docker compose down -v --remove-orphans
	docker system prune -f
