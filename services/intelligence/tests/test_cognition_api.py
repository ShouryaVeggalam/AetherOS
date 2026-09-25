"""HTTP tests for `/v9` Cognition Engine routes."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aetheros.api import create_app
from services.intelligence.runtime import reset_intelligence_runtime


@pytest.fixture()
def client() -> TestClient:
    reset_intelligence_runtime()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    reset_intelligence_runtime()


def test_create_list_get_cognition(client: TestClient) -> None:
    created = client.post(
        "/v9/cognition",
        json={
            "goal": "Research markets and then plan expansion",
            "context": {"domain": "world"},
            "constraints": ["Stay within budget"],
            "workspace_id": "demo",
            "created_by": "architect",
        },
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["workspace_id"] == "demo"
    assert body["status"] == "planned"
    assert body["complexity"]["tier"]
    assert "researcher" in body["allocation"]["required_agents"]
    plan_id = body["id"]

    fetched = client.get(f"/v9/cognition/{plan_id}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == plan_id

    listed = client.get("/v9/cognition", params={"workspace_id": "demo"})
    assert listed.status_code == 200
    payload = listed.json()
    assert payload["count"] >= 1
    assert payload["plans"][0]["id"] == plan_id


def test_cognition_not_found(client: TestClient) -> None:
    response = client.get("/v9/cognition/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_empty_goal_returns_422(client: TestClient) -> None:
    response = client.post("/v9/cognition", json={"goal": "  "})
    assert response.status_code == 422


def test_intelligence_health(client: TestClient) -> None:
    client.post(
        "/v9/cognition",
        json={"goal": "Coordinate multi-agent review", "workspace_id": "health"},
    )
    response = client.get("/v9/intelligence", params={"workspace_id": "health"})
    assert response.status_code == 200
    body = response.json()
    assert body["plan_count"] == 1
    assert body["avg_confidence"] > 0
    assert "cognition" in body["modules_ready"]


def test_openapi_includes_v9(client: TestClient) -> None:
    spec = client.get("/openapi.json")
    assert spec.status_code == 200
    paths = spec.json()["paths"]
    assert "/v9/cognition" in paths
    assert "/v9/intelligence" in paths
