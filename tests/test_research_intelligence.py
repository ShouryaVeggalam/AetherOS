"""Tests for P9 Research Intelligence Engine (evidence reports)."""

from __future__ import annotations

import dataclasses
import json
from datetime import UTC, datetime, timedelta

import pytest
from rich.console import Console

from aetheros.graph.models import ResourceEdge, ResourceGraph, ResourceNode
from aetheros.observatory.models import TelemetryPoint
from aetheros.research.analyzer import analyze_observations, context_label_from_mapping
from aetheros.research.bottlenecks import detect_bottlenecks
from aetheros.research.discoveries import verify_discoveries
from aetheros.research.engine import ResearchIntelligenceEngine
from aetheros.research.formatter import ResearchIntelligencePanel
from aetheros.research.models import (
    Discovery,
    ResearchObservation,
    SystemResearchReport,
    TrendAnalysis,
)
from aetheros.research.report import (
    build_report,
    export_json,
    export_markdown,
    report_to_dict,
)
from aetheros.research.trends import analyze_trends


def _stamp(hour: int = 9, minute: int = 0) -> datetime:
    return datetime(2026, 9, 25, hour, minute, tzinfo=UTC)


def _point(
    offset_min: int,
    *,
    cpu: float = 40.0,
    memory: float = 50.0,
    disk: float = 30.0,
    battery: float | None = 80.0,
    intent: str = "Coding",
) -> TelemetryPoint:
    return TelemetryPoint(
        timestamp=_stamp() + timedelta(minutes=offset_min),
        cpu=cpu,
        memory=memory,
        disk=disk,
        battery=battery,
        intent=intent,
    )


def _graph(
    *,
    cpu_pct: float = 90.0,
    mem_pct: float = 85.0,
    disk_pct: float = 90.0,
    net_pct: float = 85.0,
) -> ResourceGraph:
    stamp = _stamp()
    nodes = (
        ResourceNode(
            id="cpu",
            type="CPU",
            name="CPU",
            metadata=(("percent", "55.0"),),
            created_at=stamp,
        ),
        ResourceNode(
            id="memory",
            type="Memory",
            name="Memory",
            metadata=(("percent", f"{mem_pct:.1f}"),),
            created_at=stamp,
        ),
        ResourceNode(
            id="disk",
            type="Disk",
            name="Disk",
            metadata=(("percent", f"{disk_pct:.1f}"),),
            created_at=stamp,
        ),
        ResourceNode(
            id="network",
            type="Network",
            name="Network",
            metadata=(("utilization", f"{net_pct:.1f}"),),
            created_at=stamp,
        ),
        ResourceNode(
            id="process:compiler",
            type="Process",
            name="compiler",
            metadata=(
                ("cpu_percent", f"{cpu_pct:.1f}"),
                ("memory_percent", "40.0"),
            ),
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
        ResourceEdge(
            source="process:compiler",
            target="memory",
            relationship="ALLOCATES",
            weight=0.7,
        ),
        ResourceEdge(
            source="process:compiler",
            target="disk",
            relationship="USES",
            weight=0.5,
        ),
        ResourceEdge(
            source="process:compiler",
            target="network",
            relationship="COMMUNICATES",
            weight=0.4,
        ),
    )
    return ResourceGraph(nodes=nodes, edges=edges)


def test_analyzer_requires_evidence() -> None:
    assert analyze_observations() == ()
    history = (_point(0, cpu=20), _point(1, cpu=21))
    assert analyze_observations(history=history) == ()  # < min samples / delta


def test_analyzer_from_history_and_graph() -> None:
    history = tuple(_point(i, cpu=20 + i * 5) for i in range(5))
    obs = analyze_observations(
        graph=_graph(cpu_pct=40.0, mem_pct=40.0, disk_pct=40.0, net_pct=10.0),
        history=history,
        context_label="CODING",
        now=_stamp(10),
    )
    assert obs
    assert all(o.evidence for o in obs)
    assert any("CPU" in o.title or "cpu" in o.metric for o in obs)


def test_analyzer_reasoning_and_twin() -> None:
    obs = analyze_observations(
        reasoning_verified=("Causal path verified: compile → CPU.",),
        twin_summaries=("CPU_OVERLOAD scenario agrees with load spike.",),
        now=_stamp(),
    )
    assert len(obs) == 2
    assert obs[0].metric == "reasoning"


def test_context_label_helpers() -> None:
    assert context_label_from_mapping({"intent": "AI"}) == "AI"
    assert context_label_from_mapping(None) is None

    class _Intent:
        name = "GAMING"

    class _Ctx:
        active_intent = _Intent()

    assert context_label_from_mapping(_Ctx()) == "GAMING"


def test_trends_windows_and_insufficient() -> None:
    history = tuple(_point(i, cpu=30 + i) for i in range(12))
    trends = analyze_trends(history, now=_stamp(0) + timedelta(minutes=20))
    assert {t.metric for t in trends} >= {"cpu", "memory", "disk", "battery"}
    network = [t for t in trends if t.metric == "network"]
    assert network
    assert all(t.direction == "insufficient_data" for t in network)
    with_net = analyze_trends(
        history,
        now=_stamp(0) + timedelta(minutes=20),
        network_series=[10, 20, 30, 40],
        cluster_health_series=[90, 88, 85, 80],
        windows=("last_hour",),
        metrics=("network", "cluster_health"),
    )
    assert with_net[0].direction in {"rising", "falling", "stable"}


def test_bottlenecks_require_graph_paths() -> None:
    assert detect_bottlenecks() == ()
    history = tuple(_point(i, cpu=90, memory=90, disk=90) for i in range(5))
    findings = detect_bottlenecks(graph=_graph(), history=history)
    assert findings
    assert all(f.graph_paths for f in findings)
    kinds = {f.kind for f in findings}
    assert "foreground_cpu_saturation" in kinds
    assert "memory_pressure" in kinds


def test_discovery_gates() -> None:
    assert verify_discoveries(observations=(), verified_reasoning=()) == ()
    obs = (
        ResearchObservation(
            id="o1",
            timestamp=_stamp(),
            title="CODING workloads decreased CPU utilization by 9%.",
            metric="cpu",
            value=9.0,
            evidence=("history_start_cpu=40", "history_end_cpu=31"),
        ),
    )
    trends = (
        TrendAnalysis(
            metric="cpu",
            window="last_hour",
            direction="falling",
            confidence=80.0,
        ),
    )
    # Too little evidence
    assert (
        verify_discoveries(
            observations=obs,
            trends=trends,
            verified_reasoning=("Verified path compile→CPU.",),
            session_count=2,
            min_evidence=5,
        )
        == ()
    )
    # Simulation agreement too low
    assert (
        verify_discoveries(
            observations=obs,
            trends=trends,
            verified_reasoning=("Verified path compile→CPU.",),
            session_count=22,
            simulation_agreement=50.0,
            min_simulation_agreement=80.0,
        )
        == ()
    )
    discoveries = verify_discoveries(
        observations=obs,
        trends=trends,
        verified_reasoning=("Verified path compile→CPU.",),
        session_count=22,
        simulation_agreement=94.0,
    )
    assert len(discoveries) == 1
    assert discoveries[0].confidence >= 70.0
    assert discoveries[0].simulation_agreement == 94.0


def test_report_exports_and_immutability() -> None:
    report = build_report(
        context="CODING",
        observations=(
            ResearchObservation(
                id="o1",
                timestamp=_stamp(),
                title="Sample observation.",
                metric="cpu",
                value=12.0,
                evidence=("e1",),
            ),
        ),
        discoveries=(
            Discovery(
                title="Morning coding sessions reduced compile latency by 9%",
                summary="Evidence-backed latency relief.",
                evidence_count=22,
                confidence=92.0,
                supporting_reasoning=("Verified reasoning.",),
                simulation_agreement=94.0,
            ),
        ),
        kind="daily",
        generated_at=_stamp(),
        report_id="rep-1",
    )
    assert report.kind == "daily"
    md = export_markdown(report)
    assert "Research Report" in md
    assert "Morning coding" in md
    payload = json.loads(export_json(report))
    assert payload["id"] == "rep-1"
    assert report_to_dict(report)["context"] == "CODING"
    with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
        report.context = "AI"  # type: ignore[misc]


def test_engine_pipeline_and_views(tmp_path) -> None:
    history = tuple(_point(i, cpu=25 + i * 4, memory=80 + i) for i in range(10))
    engine = ResearchIntelligenceEngine(
        reports_dir=tmp_path,
        min_evidence=5,
    )
    report = engine.daily(
        graph=_graph(),
        history=history,
        context="CODING",
        verified_reasoning=("Graph path process→CPU verified.",),
        twin_summaries=("Twin agrees with elevated compile load.",),
        simulation_agreement=91.0,
        session_count=18,
        write_markdown=True,
        now=_stamp(11),
    )
    assert isinstance(report, SystemResearchReport)
    assert report.kind == "daily"
    assert report.observations or report.bottlenecks or report.trends
    weekly = engine.weekly(history=history, context="CODING", now=_stamp(12))
    assert weekly.kind == "weekly"
    files = list(tmp_path.glob("*_system_research.md"))
    assert files


def test_formatter_rich_panel() -> None:
    console = Console(record=True, width=80)
    console.print(ResearchIntelligencePanel(report=None))
    idle = console.export_text()
    assert "RESEARCH REPORT" in idle or "Research" in idle

    report = build_report(
        context="Coding",
        discoveries=(
            Discovery(
                title="Morning coding sessions reduced compile latency by 9%",
                summary="ok",
                evidence_count=22,
                confidence=92.0,
                supporting_reasoning=("Verified.",),
                simulation_agreement=94.0,
            ),
        ),
        generated_at=_stamp(),
    )
    console = Console(record=True, width=80)
    console.print(ResearchIntelligencePanel(report=report, view="daily"))
    text = console.export_text()
    assert "RESEARCH REPORT" in text
    assert "92%" in text
    assert "Research Grade" in text


def test_model_validation_errors() -> None:
    with pytest.raises(ValueError):
        ResearchObservation(
            id="",
            timestamp=_stamp(),
            title="x",
            metric="cpu",
            value=1.0,
            evidence=("e",),
        )
    with pytest.raises(ValueError):
        ResearchObservation(
            id="ok",
            timestamp=_stamp(),
            title=" ",
            metric="cpu",
            value=1.0,
            evidence=("e",),
        )
    with pytest.raises(ValueError):
        ResearchObservation(
            id="ok",
            timestamp=_stamp(),
            title="t",
            metric="cpu",
            value=1.0,
            evidence=(),
        )
    with pytest.raises(ValueError):
        TrendAnalysis(
            metric="cpu",
            window="today",
            direction="rising",
            confidence=120.0,
        )
    with pytest.raises(ValueError):
        Discovery(
            title="t",
            summary="s",
            evidence_count=0,
            confidence=50.0,
            supporting_reasoning=("r",),
        )
    with pytest.raises(ValueError):
        Discovery(
            title="t",
            summary="s",
            evidence_count=2,
            confidence=50.0,
            supporting_reasoning=(),
        )
    with pytest.raises(ValueError):
        Discovery(
            title="t",
            summary="s",
            evidence_count=2,
            confidence=50.0,
            supporting_reasoning=("r",),
            simulation_agreement=120.0,
        )
    from aetheros.research.models import BottleneckFinding

    with pytest.raises(ValueError):
        BottleneckFinding(
            kind="memory_pressure",
            title="t",
            summary="s",
            graph_paths=(),
            evidence_count=1,
            confidence=50.0,
        )
    with pytest.raises(ValueError):
        SystemResearchReport(
            id="",
            generated_at=_stamp(),
            context="C",
            observations=(),
            trends=(),
            bottlenecks=(),
            discoveries=(),
            simulations=(),
            conclusion="ok",
        )
    with pytest.raises(ValueError):
        SystemResearchReport(
            id="r1",
            generated_at=_stamp(),
            context="C",
            observations=(),
            trends=(),
            bottlenecks=(),
            discoveries=(),
            simulations=(),
            conclusion=" ",
        )


def test_analyzer_empty_reasoning_skipped_and_meta_float() -> None:
    from aetheros.research.analyzer import meta_float

    node = ResourceNode(
        id="cpu",
        type="CPU",
        name="CPU",
        metadata=(("percent", "bad"), ("other", "12.5")),
        created_at=_stamp(),
    )
    assert meta_float(node, "percent", "other") == 12.5
    assert meta_float(node, "missing") == 0.0
    obs = analyze_observations(
        reasoning_verified=("  ",),
        twin_summaries=("  ",),
        now=_stamp(),
    )
    assert obs == ()


def test_bottleneck_thresholds_skip_without_pressure() -> None:
    quiet = _graph(cpu_pct=10.0, mem_pct=10.0, disk_pct=10.0, net_pct=10.0)
    assert detect_bottlenecks(graph=quiet, history=()) == ()


def test_report_conclusions_without_discoveries() -> None:
    from aetheros.research.models import BottleneckFinding

    empty = build_report(context="BALANCED", kind="research_summary")
    assert "insufficient" in empty.conclusion.lower()
    with_obs = build_report(
        context="AI",
        observations=(
            ResearchObservation(
                id="o",
                timestamp=_stamp(),
                title="Obs.",
                metric="cpu",
                value=1.0,
                evidence=("e",),
            ),
        ),
    )
    assert "observation" in with_obs.conclusion.lower()
    with_bn = build_report(
        context="AI",
        bottlenecks=(
            BottleneckFinding(
                kind="memory_pressure",
                title="Memory pressure",
                summary="high",
                graph_paths=("memory:memory@90%",),
                evidence_count=3,
                confidence=80.0,
            ),
        ),
    )
    assert "bottleneck" in with_bn.conclusion.lower()
    md = export_markdown(with_bn)
    assert "Bottlenecks" in md
    assert "Memory pressure" in md


def test_formatter_without_discovery_and_with_bottleneck() -> None:
    from aetheros.research.models import BottleneckFinding

    report = build_report(
        context="Coding",
        bottlenecks=(
            BottleneckFinding(
                kind="disk_contention",
                title="High disk contention",
                summary="disk hot",
                graph_paths=("disk:disk@90%",),
                evidence_count=4,
                confidence=77.0,
            ),
        ),
        generated_at=_stamp(),
    )
    console = Console(record=True, width=80)
    console.print(ResearchIntelligencePanel(report=report, view="bottlenecks"))
    text = console.export_text()
    assert "Top Discovery" in text
    assert "High disk contention" in text


def test_engine_context_object_and_string(tmp_path) -> None:
    class _Intent:
        name = "EDITING"

    class _Ctx:
        active_intent = _Intent()

    engine = ResearchIntelligenceEngine(reports_dir=tmp_path, min_evidence=1)
    report = engine.generate(
        context=_Ctx(),
        history=(_point(0), _point(1), _point(2, cpu=40)),
        verified_reasoning=("ok",),
        now=_stamp(),
    )
    assert report.context == "EDITING"
    report2 = engine.generate(context="  BATTERY  ", now=_stamp())
    assert report2.context == "BATTERY"
