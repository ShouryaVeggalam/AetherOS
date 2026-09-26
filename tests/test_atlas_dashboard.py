"""Tests for v4.0 P5 Atlas Dashboard (presentation layer)."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from rich.console import Console

from aetheros.atlas.app import AtlasAppState, handle_key, render_app
from aetheros.atlas.demo import build_demo_snapshot
from aetheros.atlas.layout import compose_frame, render_footer, render_header
from aetheros.atlas.router import (
    HOTKEYS,
    PAGE_IDS,
    AtlasRouter,
    normalize_page,
)
from aetheros.atlas.snapshot import AtlasSnapshot, HealthSignal
from aetheros.atlas.views import (
    render_consensus,
    render_federation,
    render_health,
    render_overview,
    render_research,
    render_scheduler,
    render_topology,
    render_twin,
)
from aetheros.atlas.widgets import (
    AtlasProgressBar,
    AtlasSparkline,
    AtlasTable,
    AtlasTree,
    StatCard,
    TreeNodeSpec,
    render_sparkline,
    tree_from_paths,
)


def _stamp() -> datetime:
    return datetime(2026, 9, 26, 12, 0, tzinfo=UTC)


def _console() -> Console:
    return Console(record=True, width=100, force_terminal=True)


def _print(renderable: object) -> str:
    console = _console()
    console.print(renderable)
    return console.export_text()


# --- widgets -----------------------------------------------------------------


def test_stat_card_and_progress_bar() -> None:
    text = _print(StatCard("CPU", "42%", subtitle="host", tone="bright_green"))
    assert "CPU" in text and "42%" in text
    text = _print(AtlasProgressBar("Memory", 72.5))
    assert "Memory" in text
    with pytest.raises(ValueError):
        AtlasProgressBar("X", 10, width=2)


def test_table_tree_sparkline() -> None:
    table = AtlasTable(
        columns=("A", "B"),
        rows=(("1", "2"),),
        title="Grid",
    )
    assert "1" in _print(table)
    with pytest.raises(ValueError):
        AtlasTable(columns=(), rows=())
    with pytest.raises(ValueError):
        AtlasTable(columns=("A",), rows=(("1", "2"),))

    tree = AtlasTree(
        root_label="WORLD",
        children=(
            TreeNodeSpec(
                label="Asia",
                children=(TreeNodeSpec(label="Node A"),),
            ),
        ),
    )
    assert "WORLD" in _print(tree)
    with pytest.raises(ValueError):
        TreeNodeSpec(label=" ")
    with pytest.raises(ValueError):
        AtlasTree(root_label=" ")

    built = tree_from_paths("WORLD", [("Asia", "Hyd", "A"), ("Asia", "Hyd", "B")])
    assert "Asia" in _print(built)

    spark = render_sparkline((1, 2, 3, 4), width=8)
    assert len(spark) == 8
    assert "▁" in _print(AtlasSparkline((1.0, 5.0, 2.0), label="cpu"))
    assert render_sparkline((), width=4) == "····"
    assert len(render_sparkline((3, 3, 3), width=5)) == 5
    with pytest.raises(ValueError):
        render_sparkline((1,), width=0)
    with pytest.raises(ValueError):
        AtlasSparkline((1,), width=0)


# --- snapshot / router / layout ---------------------------------------------


def test_health_signal_and_snapshot() -> None:
    with pytest.raises(ValueError):
        HealthSignal(" ", "green")
    with pytest.raises(ValueError):
        HealthSignal("X", "blue")
    snap = AtlasSnapshot(connected_nodes=4, online_nodes=3)
    assert snap.online_percent() == 75.0
    assert AtlasSnapshot().online_percent() == 0.0


def test_router_hotkeys_and_pages() -> None:
    router = AtlasRouter.default()
    assert set(HOTKEYS.values()) <= set(PAGE_IDS)
    assert router.resolve_key("o") == "overview"
    assert router.resolve_key("G") == "consensus"
    assert router.resolve_key("z") is None
    assert normalize_page("Digital Twin") == "twin"
    assert normalize_page("global_consensus") == "consensus"
    with pytest.raises(ValueError):
        normalize_page("nope")
    empty = AtlasSnapshot()
    for page in PAGE_IDS:
        text = _print(router.render(page, empty, with_chrome=True))
        assert "ATLAS" in text or "Atlas" in text


def test_layout_chrome() -> None:
    header = _print(render_header(page="Overview"))
    assert "ATLAS" in header and "Overview" in header
    footer = _print(render_footer(page="Health"))
    assert "Quit" in footer
    frame = _print(compose_frame("body-text", page="Overview"))
    assert "ATLAS" in frame


# --- views ------------------------------------------------------------------


def test_views_idle_and_populated() -> None:
    idle = AtlasSnapshot()
    assert (
        "idle" in _print(render_federation(idle)).lower()
        or "no registry" in _print(render_federation(idle)).lower()
    )
    assert "idle" in _print(render_topology(idle)).lower()
    assert "idle" in _print(render_scheduler(idle)).lower()
    assert "idle" in _print(render_consensus(idle)).lower()
    assert "idle" in _print(render_twin(idle)).lower()
    assert "idle" in _print(render_research(idle)).lower()
    assert "HEALTH" in _print(render_health(idle))
    assert "OVERVIEW" in _print(render_overview(idle))

    # Populated synthetic objects (duck-typed).
    decision = SimpleNamespace(
        recommendation="Hold steady",
        confidence=88.0,
        supporting_agents=("telemetry", "performance"),
        quorum=True,
    )
    findings = (
        SimpleNamespace(agent="telemetry", summary="CPU stable", confidence=90.0),
    )
    conflicts = (SimpleNamespace(topic="disk", summary="pressure"),)
    snap = AtlasSnapshot(
        cpu_percent=40,
        memory_percent=50,
        disk_percent=20,
        connected_nodes=2,
        online_nodes=2,
        cluster_health=80,
        discoveries=3,
        active_simulations=1,
        consensus_decision=decision,
        consensus_findings=findings,
        consensus_conflicts=conflicts,
        schedule_workload=SimpleNamespace(name="AI Training"),
        schedule_result=SimpleNamespace(
            plans=(
                SimpleNamespace(
                    target_node="B",
                    score=70.0,
                    predicted_latency_ms=3.0,
                    predicted_cpu=61.0,
                    predicted_memory=55.0,
                ),
            ),
            best_plan=SimpleNamespace(target_node="B"),
            trade_offs=(
                SimpleNamespace(versus_node="A", summary="B leads", score_delta=10.0),
            ),
            confidence=92.0,
        ),
        twin_scenario_name="CPU_OVERLOAD",
        twin_baseline=SimpleNamespace(
            telemetry=SimpleNamespace(
                cpu_percent=40, memory_percent=50, disk_percent=20
            )
        ),
        twin_report=SimpleNamespace(
            result=SimpleNamespace(
                scenario=SimpleNamespace(name="CPU_OVERLOAD"),
                predicted_cpu=75,
                predicted_memory=50,
                predicted_disk=20,
                stability=70,
                risk="medium",
                reasoning="elevated cpu",
            ),
            diff=SimpleNamespace(changes=(SimpleNamespace(name="cpu", delta="+35"),)),
            baseline=None,
        ),
        research_report=SimpleNamespace(
            generated_at=_stamp(),
            context="demo",
            discoveries=(
                SimpleNamespace(
                    title="Pattern A", confidence=91.0, evidence=("e1", "e2")
                ),
            ),
            observations=("o1",),
            trends=("weekly up",),
        ),
        research_journal=(SimpleNamespace(summary="noted"),),
        federation_registry=SimpleNamespace(
            nodes=(
                SimpleNamespace(
                    identity=SimpleNamespace(node_id="n1", version="4.0.0"),
                    status="online",
                    last_seen=_stamp(),
                ),
            )
        ),
        federation_heartbeats=(SimpleNamespace(node_id="n1"),),
        protocol_version="1.0.0",
        topology_graph=SimpleNamespace(
            regions=(SimpleNamespace(id="r1", name="Asia", country="IN"),),
            datacenters=(SimpleNamespace(id="d1", region_id="r1", name="Hyd"),),
            clusters=(SimpleNamespace(id="c1", datacenter_id="d1", name="Alpha"),),
            nodes=(
                SimpleNamespace(
                    cluster_id="c1", hostname="node-a", status="online", node_id="a"
                ),
            ),
        ),
        health_signals=(HealthSignal("Telemetry", "green", "ok"),),
    )
    assert "Hold steady" in _print(render_consensus(snap))
    assert "AI Training" in _print(render_scheduler(snap))
    assert "CPU_OVERLOAD" in _print(render_twin(snap))
    assert "Pattern A" in _print(render_research(snap))
    assert "n1" in _print(render_federation(snap, now=_stamp()))
    assert "Asia" in _print(render_topology(snap))
    assert "Telemetry" in _print(render_health(snap))
    assert (
        "Connected" in _print(render_overview(snap))
        or "CONNECTED" in _print(render_overview(snap)).upper()
    )


def test_demo_snapshot_and_navigation() -> None:
    snap = build_demo_snapshot(now=_stamp())
    assert snap.connected_nodes >= 1
    assert snap.topology_graph is not None
    assert snap.schedule_result is not None
    router = AtlasRouter.default()
    for page in PAGE_IDS:
        text = _print(router.render(page, snap, with_chrome=False))
        assert len(text) > 10

    state = AtlasAppState(page="overview", snapshot=snap)
    assert handle_key(state, "t", router) is True
    assert state.page == "topology"
    assert handle_key(state, "q", router) is False
    frame = _print(render_app(state, router=router))
    assert "Atlas" in frame or "ATLAS" in frame


def test_federation_age_helpers_and_health_derive() -> None:
    from aetheros.atlas.views.federation import _age_seconds

    assert _age_seconds(None, _stamp()) == "—"
    assert _age_seconds(_stamp(), _stamp()).endswith("s")
    older = datetime(2026, 9, 26, 10, 0, tzinfo=UTC)
    assert _age_seconds(older, _stamp()).endswith("h") or _age_seconds(
        older, _stamp()
    ).endswith("m")
    # Derived health when signals empty
    text = _print(render_health(AtlasSnapshot(cpu_percent=90, memory_percent=40)))
    assert "Telemetry" in text
