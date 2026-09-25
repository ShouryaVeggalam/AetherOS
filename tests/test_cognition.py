"""Unit tests for AetherOS v3 Cognitive Operating Intelligence."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from rich.console import Console

from aetheros.cognition import (
    CognitiveMemory,
    CognitivePanel,
    CognitiveRuntime,
    generate_hypotheses,
    observe_from_snapshot,
    verify_hypotheses,
)
from aetheros.intent.profiles import PROFILES
from aetheros.knowledge import CORE_ONTOLOGY, WORKLOAD_EDGES, get_resource_type
from aetheros.observatory.models import TelemetryPoint
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.reasoning import abduct, deduce, trace_path


def _snap(
    *,
    cpu: float = 96.0,
    memory: float = 55.0,
    processes: tuple[str, ...] = ("Cursor", "Chrome"),
) -> TelemetrySnapshot:
    """Telemetry snapshot for cognition tests."""

    return TelemetrySnapshot(
        timestamp=datetime.now(UTC),
        cpu_percent=cpu,
        memory_percent=memory,
        disk_percent=40.0,
        battery_percent=70.0,
        process_count=len(processes),
        top_processes=processes,
    )


def _history(cpu: float = 92.0, count: int = 30) -> tuple[TelemetryPoint, ...]:
    """High-CPU history window."""

    now = datetime.now(UTC)
    return tuple(
        TelemetryPoint(
            now - timedelta(seconds=count - i), cpu, 50.0, 40.0, 70.0, "Coding"
        )
        for i in range(count)
    )


def test_knowledge_catalogs() -> None:
    """Ontology and resource catalogs should be non-empty and consistent."""

    assert len(CORE_ONTOLOGY) >= 5
    assert get_resource_type("cpu").label == "CPU"
    assert any(e.workload_id == "workload.coding" for e in WORKLOAD_EDGES)


def test_memory_seeds_and_search(tmp_path: Path) -> None:
    """Cognitive memory should seed public facts and support search."""

    mem = CognitiveMemory(tmp_path / "cog.db")
    facts = mem.list_facts()
    assert facts
    hits = mem.search("Cursor")
    assert hits
    assert "private" not in hits[0].notes.lower()


def test_hypotheses_and_verification(tmp_path: Path) -> None:
    """CPU anomaly should produce hypotheses; verification uses history."""

    obs = observe_from_snapshot(_snap())
    assert obs is not None
    assert "96" in obs.summary
    mem = CognitiveMemory(tmp_path / "cog.db")
    hyps = generate_hypotheses(
        obs,
        memory=mem,
        history=_history(),
        top_processes=("Cursor", "Chrome"),
    )
    assert hyps.hypotheses
    assert abs(sum(h.probability for h in hyps.hypotheses) - 1.0) < 0.05
    verified = verify_hypotheses(hyps, history=_history(), memory=mem)
    assert verified.confidence >= 0
    # With Cursor present + history, at least one hypothesis should verify.
    assert verified.result is not None


def test_runtime_reason_and_panel(tmp_path: Path) -> None:
    """CognitiveRuntime should return a report and Rich panel should render."""

    runtime = CognitiveRuntime(memory=CognitiveMemory(tmp_path / "cog.db"))
    report = runtime.reason(
        _snap(),
        PROFILES["Coding"],
        history=_history(),
    )
    assert report.graph.nodes
    assert report.graph.edges
    assert report.narrative
    assert "Recommendation only" in report.status
    console = Console(record=True, width=100)
    console.print(CognitivePanel(report))
    text = console.export_text()
    assert "COGNITIVE" in text
    assert "Causal Graph" in text


def test_reasoning_helpers(tmp_path: Path) -> None:
    """Abductive / deductive / causal helpers should run without side effects."""

    obs = observe_from_snapshot(_snap())
    assert obs is not None
    hyps = abduct(obs, memory=CognitiveMemory(tmp_path / "cog.db"))
    assert hyps.hypotheses
    conclusions = deduce(_snap(), "Coding")
    assert any(c.rule_id == "cpu_critical" for c in conclusions)
    runtime = CognitiveRuntime(memory=CognitiveMemory(tmp_path / "cog2.db"))
    graph = runtime.build_graph(_snap(), intent_name="Coding")
    path = trace_path(graph, "intent:active", "resource:cpu")
    assert path


def test_fastapi_health() -> None:
    """API health endpoint should report simulation-only / human control."""

    from fastapi.testclient import TestClient

    from aetheros.api import create_app

    client = TestClient(create_app(memory_db=Path("data/cognition_api_test.db")))
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "simulation-only"
    assert body.get("control") == "human"
    reason = client.post(
        "/cognition/reason",
        json={
            "cpu_percent": 96,
            "memory_percent": 50,
            "disk_percent": 40,
            "top_processes": ["Cursor"],
            "intent_name": "Coding",
        },
    )
    assert reason.status_code == 200
    payload = reason.json()
    assert "observation" in payload
    assert payload["status"].startswith("Recommendation only")
