from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator, Iterator
from urllib.parse import urlparse, urlunparse

import asyncpg
import pytest
import pytest_asyncio
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from alembic import command
from app.config import get_settings
from app.database import get_db
from app.main import app


def _derive_test_database_url() -> str:
    explicit = os.environ.get("TEST_DATABASE_URL")
    if explicit:
        return explicit
    base = os.environ.get("DATABASE_URL")
    if not base:
        raise RuntimeError("DATABASE_URL must be set to derive TEST_DATABASE_URL")
    parsed = urlparse(base)
    db_name = parsed.path.lstrip("/")
    if not db_name:
        raise RuntimeError(f"DATABASE_URL missing database name: {base}")
    return urlunparse(parsed._replace(path="/" + db_name + "_test"))


async def _create_database_if_missing(url: str) -> None:
    parsed = urlparse(url)
    db_name = parsed.path.lstrip("/")
    conn = await asyncpg.connect(
        user=parsed.username,
        password=parsed.password,
        host=parsed.hostname,
        port=parsed.port or 5432,
        database="postgres",
    )
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", db_name)
        if not exists:
            # Identifier cannot be parameterised; db_name is derived from our own config.
            await conn.execute(f'CREATE DATABASE "{db_name}"')
    finally:
        await conn.close()


def _run_alembic(direction: str, test_url: str) -> None:
    """Run alembic upgrade/downgrade against the test DB.

    env.py reads DATABASE_URL via get_settings(), so we temporarily swap the env
    var and clear the settings cache for the duration of the migration.
    """
    saved = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = test_url
    get_settings.cache_clear()
    try:
        cfg = Config("alembic.ini")
        if direction == "upgrade":
            command.upgrade(cfg, "head")
        elif direction == "downgrade":
            command.downgrade(cfg, "base")
        else:
            raise ValueError(direction)
    finally:
        if saved is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = saved
        get_settings.cache_clear()


@pytest.fixture(scope="session")
def _migrated_test_db_url() -> Iterator[str]:
    test_url = _derive_test_database_url()
    asyncio.run(_create_database_if_missing(test_url))
    _run_alembic("upgrade", test_url)
    yield test_url
    _run_alembic("downgrade", test_url)


@pytest_asyncio.fixture
async def _test_engine(_migrated_test_db_url: str) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(_migrated_test_db_url, poolclass=NullPool)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(_test_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with _test_engine.connect() as conn:
        outer = await conn.begin()
        session_maker = async_sessionmaker(
            bind=conn,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            join_transaction_mode="create_savepoint",
        )
        async with session_maker() as session:
            try:
                yield session
            finally:
                await outer.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def _override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.pop(get_db, None)
