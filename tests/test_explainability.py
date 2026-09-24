"""Unit tests for AetherOS v1.2 Explainable Intelligence Engine."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from rich.console import Console

from aetheros.decision.models import Decision
from aetheros.explainability import (
    Evidence,
    ExplainabilityEngine,
    collect_evidence,
    compute_confidence,
    format_explanation,
)
from aetheros.explainability.evidence import EvidenceBundle
from aetheros.intent.models import IntentProfile
from aetheros.observatory.models import TelemetryPoint
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.simulation.models import SimulationResult
from aetheros.telemetry.models import ProcessSnapshot


def _snap(*, cpu: float = 91.0, memory: float = 60.0) -> TelemetrySnapshot:
    """Build a telemetry snapshot for explainability tests."""

    return TelemetrySnapshot(
        timestamp=datetime.now(UTC),
        cpu_percent=cpu,
        memory_percent=memory,
        disk_percent=40.0,
        battery_percent=72.0,
        process_count=3,
        top_processes=("Cursor", "python", "chrome"),
    )


def _intent() -> IntentProfile:
    """Coding intent with latency bias."""

    return IntentProfile(
        name="Coding",
        description="Low latency development",
        cpu_weight=20,
        memory_weight=15,
        disk_weight=5,
        latency_weight=30,
        efficiency_weight=10,
    )


def _history(count: int = 30, cpu: float = 91.0) -> tuple[TelemetryPoint, ...]:
    """Build a high-CPU history window."""

    now = datetime.now(UTC)
    points: list[TelemetryPoint] = []
    for index in range(count):
        stamp = now - timedelta(seconds=count - index)
        points.append(TelemetryPoint(stamp, cpu, 55.0, 40.0, 72.0, "Coding"))
    return tuple(points)


def _decision() -> Decision:
    """Sample decision for explanation tests."""

    return Decision(
        title="Interactive Priority Boost",
        severity="critical",
        confidence=90,
        priority_score=88,
        explanation="CPU overload.",
        action="Favor interactive processes.",
        timestamp=datetime.now(UTC),
    )


def test_collect_evidence_from_telemetry_only() -> None:
    """Telemetry-only collection should never invent history or simulation."""

    bundle = collect_evidence(_snap())
    sources = {item.source for item in bundle.items}
    assert "telemetry" in sources
    assert "history" not in sources
    assert "simulation" not in sources
    assert bundle.sample_count == 0
    assert bundle.has_simulation is False


def test_collect_evidence_includes_history_and_intent() -> None:
    """History windows and intent should produce traceable descriptions."""

    bundle = collect_evidence(
        _snap(),
        history=_history(40),
        intent=_intent(),
        processes=(ProcessSnapshot(1, "Cursor", "user", 38.0, 10.0, "running"),),
    )
    texts = " ".join(item.description for item in bundle.items)
    assert "CPU at 91%" in texts
    assert "Cursor consumed 38% CPU" in texts
    assert "Coding" in texts
    assert any(item.source == "history" for item in bundle.items)


def test_confidence_rises_with_more_evidence() -> None:
    """Confidence should increase when history and simulation are present."""

    thin = EvidenceBundle(
        items=(), sample_count=0, has_simulation=False, intent_certainty=0
    )
    assert compute_confidence(thin) == 0

    snap = _snap()
    lean = collect_evidence(snap)
    lean_score = compute_confidence(lean)

    sim = SimulationResult(
        strategy_title="Interactive Priority Boost",
        performance_score=80.0,
        stability_score=88.0,
        efficiency_score=70.0,
        overall_improvement=75.0,
        projected_cpu_percent=73.0,
        projected_memory_percent=58.0,
        notes="test",
    )
    rich = collect_evidence(
        snap,
        history=_history(120),
        intent=_intent(),
        simulation=sim,
    )
    rich_score = compute_confidence(rich, simulation=sim, current_cpu=91.0)
    assert rich_score > lean_score
    assert 0 <= rich_score <= 100


def test_explain_never_invents_without_inputs() -> None:
    """Explanation evidence must come from collected inputs."""

    engine = ExplainabilityEngine()
    explanation = engine.explain(_decision(), _snap(), intent=_intent())
    assert explanation.title == "Interactive Priority Boost"
    assert explanation.evidence
    assert all(isinstance(item, Evidence) for item in explanation.evidence)
    assert (
        "recommended because" in explanation.summary.lower()
        or "confidence" in explanation.summary.lower()
    )
    sources = {item.source for item in explanation.evidence}
    assert "telemetry" in sources
    assert "simulation" in sources
    assert "intent" in sources


def test_formatter_renders_panel() -> None:
    """Rich panel should include recommendation, confidence, and sources."""

    engine = ExplainabilityEngine()
    explanation = engine.explain(
        _decision(),
        _snap(),
        history=_history(20),
        intent=_intent(),
        processes=(ProcessSnapshot(1, "Cursor", "user", 38.0, 5.0, "running"),),
    )
    panel = format_explanation(explanation)
    console = Console(record=True, width=100)
    console.print(panel)
    text = console.export_text()
    assert "AI Explanation" in text
    assert "Interactive Priority Boost" in text
    assert "Confidence" in text
    assert "Evidence" in text
