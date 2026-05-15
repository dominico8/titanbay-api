# titanbay-api

REST API for the Titanbay private markets fund management platform.

## Quickstart

```bash
cp .env.example .env
docker compose up --build
```

- API: http://localhost:8000
- Health: http://localhost:8000/health

## Local development

```bash
uv sync
uv run uvicorn app.main:app --reload
uv run pytest
uv run ruff check .
uv run ruff format .
```

## Migrations

```bash
uv run alembic revision --autogenerate -m "message"
uv run alembic upgrade head
uv run alembic current
```
