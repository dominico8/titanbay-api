## Titanbay Private Markets API

![ci](https://github.com/dominico8/titanbay-api/actions/workflows/ci.yml/badge.svg)

A REST API for managing funds, investors, and investments in a private-markets fund platform. Built with FastAPI and async SQLAlchemy 2.0 on top of PostgreSQL 16 and Alembic, packaged with uv, and shipped via Docker Compose.

## Quickstart

```bash
cp .env.example .env
docker compose up --build
docker compose exec api uv run python -m scripts.seed
```

Then open http://localhost:8000/docs for the interactive Swagger UI. A health probe is at http://localhost:8000/health.

If port 5432 or 8000 is already in use on your machine, override them via environment variables:

```bash
POSTGRES_HOST_PORT=5433 API_HOST_PORT=8001 docker compose up --build
```

`GET /health` is a shallow liveness check (process running). `GET /ready` additionally confirms the database is reachable.

## Local development (without Docker)

Prereqs: Python 3.12, [uv](https://docs.astral.sh/uv/), and a running PostgreSQL 16 with a `titanbay` database. Set `DATABASE_URL` in `.env`, then:

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
# in another shell:
uv run python -m scripts.seed
```

## Running tests

```bash
docker compose exec api uv run pytest -v
```

Integration tests cover all 8 endpoints, validation rules, error envelopes, name normalization, the request-ID middleware, and HTTP-level error envelopes for unknown routes and methods. They finish in ~1 second against a separate `titanbay_test` database, each test isolated by a SAVEPOINT that is rolled back on teardown. The real Alembic migration is exercised on every run, not a `metadata.create_all` shortcut.

Locally (without Docker), the same command works after `uv sync`.

## API reference

Endpoints match the provided specification: same paths, methods, field names, and field types, including JSON-number money fields. The interactive documentation at `/docs` (Swagger UI) and `/redoc` is generated from the router definitions.

```
GET    /funds
POST   /funds
PUT    /funds                              # id in body, per spec
GET    /funds/{id}
GET    /investors
POST   /investors
GET    /funds/{fund_id}/investments
POST   /funds/{fund_id}/investments
```

## Error envelope

All errors return a consistent JSON shape:

```json
{
  "error": {
    "code": "NOT_FOUND | CONFLICT | VALIDATION_ERROR | INTERNAL_ERROR",
    "message": "human-readable",
    "details": { "...": "optional; contains Pydantic errors on 422" },
    "request_id": "uuid-or-supplied"
  }
}
```

The `X-Request-ID` header is echoed when supplied, generated otherwise, and propagated into the error body so client-side trace IDs surface in logs and error reports.

## Project structure

```
app/main.py            FastAPI app factory, middleware, exception handlers
app/config.py          pydantic-settings configuration
app/database.py        async SQLAlchemy engine, session, Base
app/exceptions.py      DomainError hierarchy
app/models/            SQLAlchemy 2.0 mapped classes
app/schemas/           Pydantic v2 request/response models
app/repositories/      Async data-access layer; commits at this boundary
app/routers/           Thin HTTP handlers, one file per resource
alembic/               Migrations
tests/                 Integration tests with savepoint isolation
scripts/seed.py        Idempotent seed data
```

## Design decisions

**FastAPI + async SQLAlchemy 2.0.** Pydantic v2 gives validation and OpenAPI generation for free, and end-to-end async matches a Postgres backend that benefits from connection-level concurrency. SQLAlchemy 2.0's `Mapped` / `mapped_column` style produces cleaner types than the legacy `Column` declarative and integrates well with type checkers.

**Decimal in storage, float64 on the wire.** All money fields are `NUMERIC(20, 2)` in Postgres and `Decimal` in Python, so storage and arithmetic are exact. JSON responses convert to a bare number at the serialization boundary; this is float64 on the wire, which is precise to ~15 significant digits, well beyond any value in the spec or any realistic fund size (a `target_size_usd` up to ~9 quadrillion USD round-trips exactly). Inputs are required to be JSON numbers (string inputs rejected with 422 via a Pydantic before-validator). If exact end-to-end Decimal preservation is later required, the serialization boundary is the only conversion point and can be swapped (e.g. simplejson with `use_decimal=True`).

**Postgres ENUMs, not just Pydantic Literals.** `status` and `investor_type` are enforced as native Postgres enum types in addition to Pydantic `Literal` types. A direct INSERT bypassing the app would still fail on an invalid value. Defence in depth: Pydantic catches it at the request boundary, Postgres catches it again at the storage boundary.

**Repository pattern between routers and ORM.** Routers depend on repositories via FastAPI `Depends`, and translate HTTP ↔ Pydantic ↔ repository calls. Business rules (existence checks before insert, `IntegrityError` → `ConflictError` translation, commit-and-refresh, NOT_FOUND messages identifying which entity is missing) live in repositories. The persistence boundary is small enough that swapping the ORM would require touching the repository implementations but not the router code.

**Server-side UUID generation via `gen_random_uuid()`.** IDs come from Postgres' pgcrypto extension rather than Python's `uuid` module. There is one source of truth for primary keys and any client that bypasses the API still gets correctly-shaped IDs.

**Email uniqueness on investors.** Not specified in the API doc, but enforced via a UNIQUE constraint, a duplicate POST returns 409 rather than silently creating a second investor. Called out here because it's an assumption beyond the spec.

**PUT /funds with id in the body.** Unusual REST, typically the id lives in the path, but the spec is unambiguous, so the implementation follows the spec rather than convention. Noted so reviewers know it's deliberate.

**No DELETE endpoints.** The spec does not include them. Adding speculative endpoints would expand the surface area without an authoritative contract.

**Consistent error envelope.** All errors (validation, not-found, conflict, 500) share `{error: {code, message, details?, request_id}}`. Clients write one error path. The catch-all 500 handler logs the traceback but returns only a generic message, no internal detail leaks to the client.

**Request-ID propagation.** Middleware reads `X-Request-ID` (or generates a UUID), stashes it on `request.state`, echoes it on the response, and the error helper embeds it in the error body. A client trace ID surfaces through logs and error reports without per-endpoint wiring.

**Migrations, not `metadata.create_all`.** Tests run the real Alembic `upgrade head`, so a broken migration fails the build. The CHECK constraints, ENUM types, and pgcrypto setup are exercised on every test run rather than only in CI against a fresh database.

## Assumptions

- Investor email is unique (not specified but enforced).
- Investor emails are normalized to lowercase on write; uniqueness is therefore case-insensitive.
- `vintage_year` is bounded to `[1900, 2100]`.
- All amounts (`target_size_usd`, `amount_usd`) must be strictly positive.
- `investment_date` is not constrained relative to fund lifecycle, the spec is silent and there is no `Fund.created_at`-vs-`investment_date` check.
- Money fields are stored and computed as `Decimal` (NUMERIC(20,2)); request inputs must be JSON numbers (string inputs rejected); responses serialize as float64 JSON numbers (~15-digit precision, more than the domain needs).
- `PUT /funds` is a full replacement of mutable fields (`name`, `vintage_year`, `target_size_usd`, `status`); `id` and `created_at` are not modified.
- Request bodies must contain exactly the documented fields; unknown fields are rejected with 422 (Pydantic `extra="forbid"`).

## Working with AI tools

I used Claude Code through the VS Code extension as an implementation and review assistant during development. I broke the project into a series of narrowly scoped tasks, setting up the FastAPI/Docker/Alembic skeleton, defining models and migrations, building schemas and repository abstractions, wiring routers and middleware, adding integration tests, and finally polishing documentation and seed data.

After each stage I validated the work myself by running the docker-compose stack, linting with ruff, executing pytest, and manually checking endpoints with curl before committing incrementally. The workflow was intentionally iterative: I refined generated code, adjusted architecture decisions, and corrected issues surfaced during testing and review.

The core architectural decisions were made independently: choosing FastAPI + SQLAlchemy 2.0 + Alembic over alternatives such as Django or Litestar, defining the repository-pattern transaction boundary, designing the error-envelope structure, enforcing enums at the database layer instead of only through Pydantic, using Decimal for storage while exposing float64 over the API with strict string-input rejection, and implementing savepoint-based rollback isolation for tests.

I also ran two rounds of independent hostile review using a different model and triaged the findings myself rather than acting on them wholesale. One instructive case: a review round flagged a theoretical precision-loss risk on the money serialization boundary, which I addressed by adding simplejson and two monkey-patches on FastAPI internals. After implementing it I rolled the change back, float64 covers fund sizes up to ~9 quadrillion USD exactly, and the patches introduced fragile dependencies on framework private APIs that weren't justified by the domain. The commit history shows both directions and the reasoning.

Two framework-specific issues the model caught are worth naming: a ruff B008 violation on Depends() defaults, which I resolved by refactoring to Annotated dependency aliases, and a Decimal JSON serialization failure affecting 422 validation responses, which I fixed using jsonable_encoder in the error response helper.