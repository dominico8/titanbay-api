.PHONY: up up-d down logs test lint format seed shell psql migrate

up:
	docker compose up --build

up-d:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f api

test:
	docker compose exec api uv run pytest -v

lint:
	docker compose exec api uv run ruff check .

format:
	docker compose exec api uv run ruff format .

seed:
	docker compose exec api uv run python -m scripts.seed

shell:
	docker compose exec api bash

psql:
	docker compose exec postgres psql -U titanbay -d titanbay

migrate:
	docker compose exec api uv run alembic upgrade head
