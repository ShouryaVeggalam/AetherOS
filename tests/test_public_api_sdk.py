"""Tests for v5.0 P2 Public API (/api/v1) and Python SDK client."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from aetheros import AetherClient
from aetheros.api import create_app
from aetheros.api.routes import context as context_route
from aetheros.api.routes import graph as graph_route
from aetheros.api.routes import plugins as plugins_route
from aetheros.api.routes import reasoning as reasoning_route
from aetheros.api.routes import research as research_route
from aetheros.sdk.client import AetherClient as ClientDirect


@pytest.fixture()
def api_client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(memory_db=tmp_path / "cog.db"))


def _asgi_mock_transport(app: Any) -> httpx.MockTransport:
    """Sync httpx transport that forwards to Starlette TestClient."""

    starlette = TestClient(app)

    def handler(request: httpx.Request) -> httpx.Response:
        url = httpx.URL(request.url)
        headers = {
            k: v
            for k, v in request.headers.items()
            if k.lower() not in {"host", "content-length"}
        }
        response = starlette.request(
            request.method,
            url.path,
            params=dict(url.params),
            content=request.content,
            headers=headers,
        )
        return httpx.Response(
            response.status_code,
            headers=response.headers,
            content=response.content,
            request=request,
        )

    return httpx.MockTransport(handler)


def test_v1_health(api_client: TestClient) -> None:
    data = api_client.get("/api/v1/health").json()
    assert data["status"] == "ok"
    assert data["api_version"] == "v1"
    assert data["mode"] == "read-only"


def test_v1_context_and_graph(api_client: TestClient) -> None:
    ctx = api_client.get("/api/v1/context", params={"intent_name": "Balanced"}).json()
    assert "intent" in ctx
    assert ctx["source"] in {"context-engine", "fallback"}
    graph = api_client.get("/api/v1/graph").json()
    assert graph["node_count"] >= 1
    assert isinstance(graph["nodes"], list)
    assert isinstance(graph["edges"], list)


def test_v1_reasoning_research_plugins(api_client: TestClient) -> None:
    reasoning = api_client.get("/api/v1/reasoning").json()
    assert "confidence" in reasoning
    assert "observation" in reasoning
    research = api_client.get("/api/v1/research").json()
    assert "discoveries" in research
    plugins = api_client.get("/api/v1/plugins").json()
    assert plugins["count"] >= 1
    assert plugins["sdk_version"].startswith("5.")
    assert any(p["id"] == "hello-insight" for p in plugins["plugins"])


def test_v1_twin_simulate(api_client: TestClient) -> None:
    ok = api_client.post(
        "/api/v1/twin/simulate",
        json={
            "scenario": "CPU_OVERLOAD",
            "cpu_percent": 42.0,
            "memory_percent": 50.0,
            "disk_percent": 30.0,
        },
    )
    assert ok.status_code == 200
    body = ok.json()
    assert body["status"] == "simulation_only"
    assert body["scenario"] == "CPU_OVERLOAD"
    assert body["predicted_cpu"] >= 0

    bad = api_client.post(
        "/api/v1/twin/simulate",
        json={"scenario": "NOT_A_REAL_SCENARIO"},
    )
    assert bad.status_code == 400


def test_aether_client_against_asgi(api_client: TestClient) -> None:
    transport = _asgi_mock_transport(api_client.app)
    with AetherClient(
        base_url="http://test",
        api_key="dev-token",
        transport=transport,
    ) as client:
        assert client.health()["api_version"] == "v1"
        assert "intent" in client.context()
        assert client.graph()["node_count"] >= 1
        assert "confidence" in client.reasoning()
        sim = client.simulate(scenario="MEMORY_PRESSURE", cpu_percent=30)
        assert sim["status"] == "simulation_only"
        assert "discoveries" in client.research()
        assert client.plugins()["count"] >= 1

    assert ClientDirect is AetherClient


def test_client_non_dict_json_wrap(
    api_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    transport = _asgi_mock_transport(api_client.app)
    client = AetherClient(base_url="http://test", transport=transport)

    class _Resp:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> list[int]:
            return [1, 2]

    monkeypatch.setattr(
        client._client,
        "request",
        lambda *a, **k: _Resp(),
    )
    assert client._request("GET", "/x") == {"data": [1, 2]}
    client.close()


def test_context_fallback_and_notes(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Boom:
        def refresh(self, *a: Any, **k: Any) -> Any:
            raise RuntimeError("boom")

    monkeypatch.setattr(context_route, "ContextEngine", _Boom)
    fallback = context_route.get_context()
    assert fallback.source == "fallback"

    rich = SimpleNamespace(
        intent=SimpleNamespace(name="Perf"),
        historical_pattern=SimpleNamespace(summary="recurring load"),
        explanation="elevated cpu",
    )

    class _Ok:
        def refresh(self, *a: Any, **k: Any) -> Any:
            return rich

    monkeypatch.setattr(context_route, "ContextEngine", _Ok)
    ok = context_route.get_context()
    assert ok.source == "context-engine"
    assert ok.intent == "Perf"
    assert any("recurring" in n for n in ok.notes)
    assert any("elevated" in n for n in ok.notes)


def test_graph_normalization_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Nested:
        def to_dict(self) -> dict[str, Any]:
            return {
                # Non-list "nodes" forces the flatten path.
                "nodes": {"nested": True},
                "regions": [{"id": "r1", "name": "R1", "kind": "Region"}],
                "datacenters": [{"node_id": "dc1", "type": "DC", "attributes": "bad"}],
                "clusters": ["skip-me"],
                "sample_nodes": [{"id": "n1", "attributes": {"z": 1}}],
                "edges": [
                    {"source_id": "a", "target_id": "b", "relation": "LINKS"},
                    "bad-edge",
                ],
            }

    monkeypatch.setattr(graph_route, "WorldGraph", _Nested)
    nested = graph_route.get_graph()
    assert nested.node_count >= 3
    assert nested.edge_count == 1

    class _CensusOnly:
        def to_dict(self) -> dict[str, Any]:
            return {
                "nodes": "not-a-list",
                "edges": [],
                "regions": [{"id": "ignored-when-census"}],
                "census": {"regions": 2, "datacenters": 2, "clusters": 2, "nodes": 5},
            }

    monkeypatch.setattr(graph_route, "WorldGraph", _CensusOnly)
    census = graph_route.get_graph()
    assert census.node_count >= 1
    assert all(n.id for n in census.nodes)

    class _MixedList:
        def to_dict(self) -> dict[str, Any]:
            return {
                "nodes": [
                    {"id": "a"},
                    "skip-me",
                    {"name": "no-id"},
                    {"id": "b", "attributes": 3},
                ],
                "edges": [],
            }

    monkeypatch.setattr(graph_route, "WorldGraph", _MixedList)
    mixed = graph_route.get_graph()
    assert {n.id for n in mixed.nodes} == {"a", "b"}

    class _Empty:
        def to_dict(self) -> dict[str, Any]:
            return {"nodes": [], "edges": [], "regions": ["x"]}

    monkeypatch.setattr(graph_route, "WorldGraph", _Empty)
    empty = graph_route.get_graph()
    assert empty.node_count == 0

    class _RawCounts:
        def to_dict(self) -> dict[str, Any]:
            return {
                "nodes": [],
                "edges": [],
                "census": {"regions": "nope"},
                "datacenters": 2,
                "clusters": 1,
                "nodes_count_ignored": 0,
            }

    monkeypatch.setattr(graph_route, "WorldGraph", _RawCounts)
    raw_counts = graph_route.get_graph()
    assert any(n.kind == "Datacenter" for n in raw_counts.nodes)


def test_reasoning_profile_match_and_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    # Case-insensitive profile name path
    out = reasoning_route.get_reasoning(intent_name="balanced")
    assert out.confidence >= 0.0

    class _FailRuntime:
        def __init__(self, *a: Any, **k: Any) -> None:
            pass

        def reason(self, *a: Any, **k: Any) -> Any:
            raise RuntimeError("offline")

    monkeypatch.setattr(reasoning_route, "CognitiveRuntime", _FailRuntime)
    unavailable = reasoning_route.get_reasoning()
    assert unavailable.status == "unavailable"

    report = SimpleNamespace(
        status="ok",
        confidence=0.9,
        observation=SimpleNamespace(summary="cpu high"),
        hypotheses=SimpleNamespace(hypotheses=[SimpleNamespace(title="h1"), "raw"]),
        plans=SimpleNamespace(recommended=SimpleNamespace(summary="scale out")),
        narrative=("step-1",),
    )

    class _OkRuntime:
        def __init__(self, *a: Any, **k: Any) -> None:
            pass

        def reason(self, *a: Any, **k: Any) -> Any:
            return report

    monkeypatch.setattr(reasoning_route, "CognitiveRuntime", _OkRuntime)
    rich = reasoning_route.get_reasoning(intent_name="NoSuchProfile")
    assert rich.observation == "cpu high"
    assert "h1" in rich.hypotheses
    assert "scale" in rich.recommendation


def test_research_fallback_and_top(monkeypatch: pytest.MonkeyPatch) -> None:
    class _BoomEngine:
        def __init__(self, *a: Any, **k: Any) -> None:
            raise RuntimeError("no research")

    monkeypatch.setattr(
        "aetheros.research.ResearchIntelligenceEngine",
        _BoomEngine,
    )
    fallback = research_route.get_research()
    assert fallback.status == "unavailable"

    class _Engine:
        def __init__(self, *a: Any, **k: Any) -> None:
            pass

        def generate(self, *a: Any, **k: Any) -> Any:
            return SimpleNamespace(
                discoveries=(SimpleNamespace(title="find-me", confidence=0.8),),
                observations=(1, 2),
                context="unit",
            )

    monkeypatch.setattr(
        "aetheros.research.ResearchIntelligenceEngine",
        _Engine,
    )
    rich = research_route.get_research()
    assert rich.top_discovery == "find-me"
    assert rich.confidence == 0.8
    assert rich.discoveries == 1


def test_plugins_skip_invalid_and_exception(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class _Loader:
        def discover(self, root: Path) -> list[Path]:
            return [tmp_path / "bad", tmp_path / "good"]

    class _Validator:
        def validate_directory(self, path: Path) -> Any:
            if path.name == "bad":
                return SimpleNamespace(ok=False, manifest=None)
            return SimpleNamespace(
                ok=True,
                manifest=SimpleNamespace(
                    id="p1",
                    name="P1",
                    version="0.0.1",
                    description="d",
                    capabilities=["read_graph"],
                ),
            )

    import plugins.sdk as plugin_sdk

    monkeypatch.setattr(plugin_sdk, "PluginLoader", _Loader)
    monkeypatch.setattr(plugin_sdk, "PluginValidator", _Validator)
    catalog = plugins_route.get_plugins()
    assert catalog.count == 1
    assert catalog.plugins[0].id == "p1"

    class _BoomLoader:
        def discover(self, root: Path) -> list[Path]:
            raise RuntimeError("discover failed")

    monkeypatch.setattr(plugin_sdk, "PluginLoader", _BoomLoader)
    empty = plugins_route.get_plugins()
    assert empty.count == 0
