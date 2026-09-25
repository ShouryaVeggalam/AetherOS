"""Tests for v3 Cognition Core (isolated intelligence layer)."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import pytest
from rich.console import Console

from aetheros.cognition import (
    CognitionCorePanel,
    CognitionEngine,
    CoreHypothesis,
    Evidence,
    OperationalMemory,
    collect_evidence,
    generate_cognition_plans,
    generate_core_hypotheses,
    verify_core_hypotheses,
)
from aetheros.cognition.models import CognitionState, OperationalPattern
from aetheros.graph.models import ResourceEdge, ResourceGraph, ResourceNode
from aetheros.observatory.models import TelemetryPoint


def _stamp(minute: int = 0) -> datetime:
    return datetime(2026, 9, 25, 9, minute, tzinfo=UTC)


def _point(minute: int, *, cpu: float = 40.0, memory: float = 50.0) -> TelemetryPoint:
    return TelemetryPoint(
        timestamp=_stamp(minute),
        cpu=cpu,
        memory=memory,
        disk=30.0,
        battery=80.0,
        intent="Coding",
    )


def _graph(*, cpu_pct: float = 90.0) -> ResourceGraph:
    stamp = _stamp()
    nodes = (
        ResourceNode(
            id="cpu",
            type="CPU",
            name="CPU",
            metadata=(("percent", "60.0"),),
            created_at=stamp,
        ),
        ResourceNode(
            id="memory",
            type="Memory",
            name="Memory",
            metadata=(("percent", "55.0"),),
            created_at=stamp,
        ),
        ResourceNode(
            id="process:compiler",
            type="Process",
            name="compiler",
            metadata=(("cpu_percent", f"{cpu_pct:.1f}"),),
            created_at=stamp,
        ),
    )
    edges = (
        ResourceEdge(
            source="process:compiler",
            target="cpu",
            relationship="USES",
            weight=0.9,
        ),
    )
    return ResourceGraph(nodes=nodes, edges=edges)


def test_evidence_collection_and_validation() -> None:
    assert collect_evidence() == ()
    history = tuple(_point(i, cpu=20 + i * 6) for i in range(5))
    evidence = collect_evidence(
        graph=_graph(),
        history=history,
        context="CODING",
        twin_summaries=("twin agrees",),
        memory_patterns=(
            "Morning coding sessions typically increase CPU before memory pressure.",
        ),
        now=_stamp(10),
    )
    assert evidence
    assert any(e.source == "resource_graph" for e in evidence)
    assert any(e.source == "telemetry_history" for e in evidence)
    assert any(e.source == "graph_context" for e in evidence)
    assert any(e.source == "digital_twin" for e in evidence)
    with pytest.raises(ValueError):
        Evidence(
            id="", source="resource_graph", metric="cpu", value=1.0, timestamp=_stamp()
        )


def test_operational_memory_patterns() -> None:
    mem = OperationalMemory()
    patterns = mem.list_patterns()
    assert patterns
    assert all(isinstance(p, OperationalPattern) for p in patterns)
    assert mem.match("coding")
    assert mem.verified_only(min_confidence=85.0)
    assert mem.statements()
    assert mem.match("   ") == ()


def test_core_hypotheses_from_evidence() -> None:
    history = tuple(_point(i, cpu=20 + i * 8) for i in range(6))
    evidence = collect_evidence(graph=_graph(), history=history, context="CODING")
    hyps = generate_core_hypotheses(
        evidence,
        context_label="CODING",
        patterns=(
            "Morning coding sessions typically increase CPU before memory pressure.",
        ),
    )
    assert hyps
    assert all(isinstance(h, CoreHypothesis) for h in hyps)
    assert all(h.supporting_evidence for h in hyps)
    assert generate_core_hypotheses(()) == ()


def test_verification_gates() -> None:
    history = tuple(_point(i, cpu=25 + i * 7) for i in range(6))
    evidence = collect_evidence(
        graph=_graph(),
        history=history,
        twin_summaries=("simulation agrees",),
    )
    hyps = generate_core_hypotheses(evidence, context_label="CODING")
    # Reject low simulation agreement
    assert (
        verify_core_hypotheses(hyps, evidence, simulation_agreement=10.0) == () or True
    )
    rejected = verify_core_hypotheses(hyps, evidence, simulation_agreement=10.0)
    # agreement < 70 ⇒ all rejected
    assert rejected == ()
    verified = verify_core_hypotheses(hyps, evidence, simulation_agreement=90.0)
    assert verified
    assert all(v.graph_support or v.historical_support for v in verified)
    # No evidence refs ⇒ reject
    bad = CoreHypothesis(
        id="bad",
        title="Unsupported",
        description="x",
        supporting_evidence=("missing",),
        confidence=90.0,
    )
    assert verify_core_hypotheses((bad,), evidence, simulation_agreement=90.0) == ()


def test_planner_requires_simulation() -> None:
    assert generate_cognition_plans() == ()
    history = tuple(_point(i, cpu=30 + i * 5) for i in range(5))
    evidence = collect_evidence(graph=_graph(), history=history, twin_summaries=("ok",))
    hyps = generate_core_hypotheses(evidence)
    verified = verify_core_hypotheses(hyps, evidence, simulation_agreement=88.0)
    plans = generate_cognition_plans(
        verified=verified,
        simulation_agreement=88.0,
        context_label="CODING",
    )
    assert len(plans) == 3
    assert {p.kind for p in plans} == {"performance", "efficiency", "balanced"}
    assert all(p.simulation_backed for p in plans)


def test_engine_pipeline_and_state() -> None:
    engine = CognitionEngine()
    history = tuple(_point(i, cpu=20 + i * 6) for i in range(6))
    state = engine.run(
        graph=_graph(),
        history=history,
        context="CODING",
        twin_summaries=("Digital twin agrees with compile load.",),
        simulation_agreement=92.0,
        now=_stamp(12),
    )
    assert isinstance(state, CognitionState)
    assert state.context == "CODING"
    assert state.evidence
    assert state.active_hypotheses
    assert state.verified_explanations
    assert state.plans
    assert 0 <= state.confidence <= 100
    with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
        state.confidence = 0.0  # type: ignore[misc]


def test_engine_stepwise_api() -> None:
    engine = CognitionEngine()
    ev = engine.observe(graph=_graph(cpu_pct=40.0), context={"intent": "AI"})
    assert ev
    hyps = engine.reason()
    verified = engine.verify(simulation_agreement=80.0)
    plans = engine.plan()
    state = engine.state(now=_stamp())
    assert isinstance(hyps, tuple)
    assert isinstance(verified, tuple)
    assert isinstance(plans, tuple)
    assert state.timestamp == _stamp()


def test_formatter_panel() -> None:
    console = Console(record=True, width=80)
    console.print(CognitionCorePanel(state=None))
    assert (
        "COGNITION CORE" in console.export_text()
        or "Cognition" in console.export_text()
    )

    engine = CognitionEngine()
    state = engine.run(
        graph=_graph(),
        history=tuple(_point(i, cpu=15 + i * 10) for i in range(5)),
        context="CODING",
        twin_summaries=("agree",),
        simulation_agreement=85.0,
    )
    console = Console(record=True, width=80)
    console.print(CognitionCorePanel(state=state))
    text = console.export_text()
    assert "COGNITION CORE" in text
    assert "CODING" in text


def test_legacy_cognitive_runtime_untouched(tmp_path) -> None:
    """Existing CognitiveRuntime API still imports and runs."""

    from aetheros.cognition import CognitiveMemory, CognitiveRuntime
    from aetheros.intent.profiles import PROFILES
    from aetheros.policy_engine.models import TelemetrySnapshot

    runtime = CognitiveRuntime(memory=CognitiveMemory(tmp_path / "cog.db"))
    snap = TelemetrySnapshot(
        timestamp=_stamp(),
        cpu_percent=70.0,
        memory_percent=50.0,
        disk_percent=30.0,
        battery_percent=80.0,
        process_count=1,
        top_processes=("Cursor",),
    )
    report = runtime.reason(snap, PROFILES["Coding"], history=())
    assert report.confidence >= 0


def test_model_validation_edges() -> None:
    from aetheros.cognition.models import CognitionPlan, VerifiedCoreExplanation

    with pytest.raises(ValueError):
        Evidence(
            id="x",
            source="resource_graph",
            metric=" ",
            value=1.0,
            timestamp=_stamp(),
        )
    with pytest.raises(ValueError):
        CoreHypothesis(
            id="h",
            title=" ",
            description="d",
            supporting_evidence=("e",),
            confidence=50.0,
        )
    with pytest.raises(ValueError):
        CoreHypothesis(
            id="h",
            title="t",
            description="d",
            supporting_evidence=(),
            confidence=50.0,
        )
    with pytest.raises(ValueError):
        CoreHypothesis(
            id="h",
            title="t",
            description="d",
            supporting_evidence=("e",),
            confidence=120.0,
        )
    with pytest.raises(ValueError):
        CognitionPlan(
            kind="balanced",
            title="t",
            summary="s",
            steps=(),
            simulation_backed=True,
            confidence=50.0,
        )
    with pytest.raises(ValueError):
        CognitionPlan(
            kind="balanced",
            title="t",
            summary="s",
            steps=("a",),
            simulation_backed=False,
            confidence=50.0,
        )
    with pytest.raises(ValueError):
        OperationalPattern(key="", statement="s", evidence_count=1, confidence=50.0)
    with pytest.raises(ValueError):
        OperationalPattern(key="k", statement="s", evidence_count=0, confidence=50.0)
    with pytest.raises(ValueError):
        CognitionState(
            context="C",
            active_hypotheses=(),
            verified_explanations=(),
            confidence=120.0,
            timestamp=_stamp(),
        )
    hyp = CoreHypothesis(
        id="h1",
        title="t",
        description="d",
        supporting_evidence=("e",),
        confidence=70.0,
    )
    with pytest.raises(ValueError):
        VerifiedCoreExplanation(
            hypothesis=hyp,
            graph_support=True,
            historical_support=False,
            simulation_agreement=120.0,
            reasons=("ok",),
            confidence=70.0,
        )


def test_evidence_context_object_and_bad_metadata() -> None:
    class _Intent:
        name = "GAMING"

    class _Ctx:
        active_intent = _Intent()

    ev = collect_evidence(context=_Ctx(), now=_stamp())
    assert any(e.metric == "active_intent" for e in ev)
    stamp = _stamp()
    node = ResourceNode(
        id="cpu",
        type="CPU",
        name="CPU",
        metadata=(("percent", "NaN-ish"), ("utilization", "12.5")),
        created_at=stamp,
    )
    graph = ResourceGraph(nodes=(node,), edges=())
    out = collect_evidence(graph=graph, now=stamp)
    assert out
    assert collect_evidence(context="  ") == ()
    assert collect_evidence(twin_summaries=("  ",), memory_patterns=("  ",)) == ()


def test_engine_state_without_verified() -> None:
    engine = CognitionEngine()
    engine.observe(history=(_point(0), _point(1, cpu=21.0)))
    engine.reason()
    # Tiny delta / sparse evidence may yield no hypotheses
    state = engine.state(now=_stamp())
    assert state.confidence >= 0.0
    engine2 = CognitionEngine()
    engine2.observe(graph=_graph(cpu_pct=15.0), context="BALANCED")
    engine2.reason()
    engine2.verify(simulation_agreement=None, min_confidence=99.0)
    state2 = engine2.state(now=_stamp())
    assert isinstance(state2, CognitionState)
