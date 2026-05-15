from __future__ import annotations

from httpx import AsyncClient

VALID_INVESTOR = {
    "name": "CalPERS",
    "investor_type": "Institution",
    "email": "pe@calpers.ca.gov",
}


async def test_create_investor_returns_201(client: AsyncClient) -> None:
    response = await client.post("/investors", json=VALID_INVESTOR)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == VALID_INVESTOR["name"]
    assert body["investor_type"] == VALID_INVESTOR["investor_type"]
    assert body["email"] == VALID_INVESTOR["email"]
    assert body["id"]
    assert body["created_at"]


async def test_create_investor_duplicate_email_returns_409_with_envelope(
    client: AsyncClient,
) -> None:
    assert (await client.post("/investors", json=VALID_INVESTOR)).status_code == 201
    response = await client.post("/investors", json=VALID_INVESTOR)
    assert response.status_code == 409
    body = response.json()
    assert body["error"]["code"] == "CONFLICT"
    assert "email" in body["error"]["message"].lower()


async def test_create_investor_bad_email_returns_422(client: AsyncClient) -> None:
    response = await client.post(
        "/investors",
        json={**VALID_INVESTOR, "email": "not-an-email"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_create_investor_invalid_type_returns_422(client: AsyncClient) -> None:
    response = await client.post(
        "/investors",
        json={**VALID_INVESTOR, "investor_type": "Corporation"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_create_investor_empty_name_returns_422(client: AsyncClient) -> None:
    response = await client.post("/investors", json={**VALID_INVESTOR, "name": ""})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_list_investors(client: AsyncClient) -> None:
    a = (
        await client.post(
            "/investors",
            json={**VALID_INVESTOR, "name": "Alice", "email": "alice@example.com"},
        )
    ).json()
    b = (
        await client.post(
            "/investors",
            json={**VALID_INVESTOR, "name": "Bob", "email": "bob@example.com"},
        )
    ).json()
    response = await client.get("/investors")
    assert response.status_code == 200
    ids = {i["id"] for i in response.json()}
    assert {a["id"], b["id"]} <= ids
