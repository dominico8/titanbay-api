from __future__ import annotations

from uuid import UUID

from httpx import AsyncClient


async def test_request_id_echoed_when_supplied(client: AsyncClient) -> None:
    response = await client.get("/health", headers={"X-Request-ID": "my-id"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "my-id"


async def test_request_id_generated_when_absent(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    rid = response.headers.get("X-Request-ID")
    assert rid is not None
    UUID(rid)  # raises if not a UUID


async def test_request_id_in_error_envelope(client: AsyncClient) -> None:
    response = await client.get(
        "/funds/00000000-0000-0000-0000-000000000000",
        headers={"X-Request-ID": "trace-abc"},
    )
    assert response.status_code == 404
    assert response.headers["X-Request-ID"] == "trace-abc"
    body = response.json()
    assert body["error"]["request_id"] == "trace-abc"
