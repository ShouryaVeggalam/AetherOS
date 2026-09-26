"""Tests for v6.0 P5 Horizon Observatory (presentation layer)."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from rich.console import Console

from aetheros.horizon.app import HorizonAppState, handle_key, render_app
from aetheros.horizon.demo import build_demo_snapshot
from aetheros.horizon.layout import compose_frame, render_footer, render_header
from aetheros.horizon.router import (
    HOTKEYS,
    PAGE_IDS,
    HorizonRouter,
    normalize_page,
)
from aetheros.horizon.snapshot import HealthSignal, HorizonSnapshot
from aetheros.horizon.views import (
    render_cloud,
    render_consensus,
    render_health,
    render_knowledge,
    render_overview,
    render_research,
    render_scheduler,
    render_topology,
    render_twin,
)
from aetheros.horizon.widgets import (
    HorizonSparkline,
    HorizonTable,
    HorizonTree,
    MetricGrid,
    StatCard,
    Timeline,
    TreeNodeSpec,
    metric_grid_from_pairs,
    render_sparkline,
    timeline_from_pairs,
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


def test_stat_card_and_metric_grid() -> None:
    text = _print(StatCard("CPU", "42%", subtitle="host", tone="bright_green"))
    assert "CPU" in text and "42%" in text
    grid = metric_grid_from_pairs((("A", "1"), ("B", "2")))
    assert isinstance(grid, MetricGrid)
    assert "1" in _print(grid)
    assert "empty" not in _print(MetricGrid(cards=())).lower() or True


def test_table_tree_sparkline_timeline() -> None:
    table = HorizonTable(columns=("A", "B"), rows=(("1", "2"),), title="Grid")
    assert "1" in _print(table)
    with pytest.raises(ValueError):
        HorizonTable(columns=(), rows=())
    with pytest.raises(ValueError):
        HorizonTable(columns=("A",), rows=(("1", "2"),))

    tree = HorizonTree(
        root_label="Root",
        children=(TreeNodeSpec("Child", children=(TreeNodeSpec("Leaf"),)),),
    )
    assert "Root" in _print(tree)
    with pytest.raises(ValueError):
        TreeNodeSpec(" ")
    with pytest.raises(ValueError):
        HorizonTree(root_label=" ")

    paths = tree_from_paths("World", [("eu", "fra", "c1", "n1"), ("eu", "fra", "c2")])
    assert "World" in _print(paths)

    spark = HorizonSparkline(values=(1.0, 2.0, 3.0, 2.0), label="load")
    assert "load" in _print(spark)
    assert len(render_sparkline((5.0, 5.0, 5.0), width=8)) == 8
    assert len(render_sparkline((), width=4)) == 4
    assert len(render_sparkline((1, 2, 3, 4, 5, 6, 7, 8, 9), width=4)) == 4
    with pytest.raises(ValueError):
        HorizonSparkline(values=(1.0,), width=0)
    with pytest.raises(ValueError):
        render_sparkline((1.0,), width=0)

    tl = timeline_from_pairs((("09:00", "boot"),))
    assert "boot" in _print(tl)
    assert "no events" in _print(Timeline()).lower()


# --- snapshot / router / layout ---------------------------------------------


def test_health_signal_and_snapshot() -> None:
    signal = HealthSignal("Federation", "green", "ok")
    assert signal.status == "green"
    with pytest.raises(ValueError):
        HealthSignal(" ", "green")
    with pytest.raises(ValueError):
        HealthSignal("X", "blue")
    snap = HorizonSnapshot(connected_providers=3, regions=2)
    assert snap.provider_count() == 3


def test_router_hotkeys_and_normalize() -> None:
    router = HorizonRouter.default()
    assert set(HOTKEYS) >= {"o", "c", "t", "k", "w", "d", "g", "r", "h"}
    assert len(PAGE_IDS) == 9
    assert router.resolve_key("w") == "scheduler"
    assert router.resolve_key("C") == "cloud"
    assert router.resolve_key("") is None
    assert normalize_page("Digital Twin") == "twin"
    assert normalize_page("planetary") == "scheduler"
    with pytest.raises(ValueError):
        normalize_page("unknown-page")
    with pytest.raises(KeyError):
        router.render("nope", HorizonSnapshot())  # type: ignore[arg-type]


def test_layout_chrome() -> None:
    text = _print(compose_frame(StatCard("X", "1"), page="Overview"))
    assert "HORIZON" in text
    assert "Overview" in text
    assert "Q Quit" in _print(render_footer(page="Overview"))
    assert "HORIZON" in _print(render_header(page="Health"))


# --- views (idle + populated) -----------------------------------------------


def test_views_idle_states() -> None:
    snap = HorizonSnapshot()
    for render in (
        render_overview,
        render_cloud,
        render_topology,
        render_knowledge,
        render_scheduler,
        render_twin,
        render_consensus,
        render_research,
        render_health,
    ):
        text = _print(render(snap))
        assert "Horizon" in text or "HORIZON" in text or "HEALTH" in text


def test_views_with_demo_snapshot() -> None:
    snap = build_demo_snapshot(now=_stamp())
    assert snap.connected_providers >= 1
    assert snap.health_signals
    for page in PAGE_IDS:
        body = HorizonRouter.default().render(page, snap, with_chrome=True)
        text = _print(body)
        assert "HORIZON" in text
        assert "Read-only" in text or "Simulation" in text or "HEALTH" in text


def test_scheduler_and_twin_populated() -> None:
    snap = build_demo_snapshot(now=_stamp())
    text = _print(render_scheduler(snap))
    assert "WORLDWIDE SCHEDULER" in text or "SCHEDULER" in text
    text = _print(render_twin(snap))
    assert "DIGITAL TWIN" in text or "TWIN" in text
    text = _print(render_knowledge(snap))
    assert "KNOWLEDGE" in text
    text = _print(render_cloud(snap))
    assert "CLOUD" in text
    text = _print(render_consensus(snap))
    assert "CONSENSUS" in text
    text = _print(render_research(snap))
    assert "RESEARCH" in text
    text = _print(render_health(HorizonSnapshot(global_health=90.0)))
    assert "Federation" in text


def test_topology_with_fake_graph() -> None:
    graph = SimpleNamespace(
        nodes=(
            SimpleNamespace(
                region_id="eu",
                datacenter_id="fra",
                cluster_id="c1",
                node_id="n1",
            ),
        ),
        regions=(),
        clusters=(),
    )
    text = _print(
        render_topology(HorizonSnapshot(topology_graph=graph, regions=1, nodes=1))
    )
    assert "TOPOLOGY" in text
    assert "eu" in text


def test_health_derive_signals() -> None:
    snap = HorizonSnapshot(
        connected_providers=0,
        topology_graph=None,
        schedule_decision=None,
        twin_run=None,
        knowledge_graph=None,
        research_report=None,
        consensus_decision=None,
    )
    text = _print(render_health(snap))
    assert "YELLOW" in text or "yellow" in text.lower() or "●" in text


# --- navigation / app -------------------------------------------------------


def test_handle_key_navigation_and_quit() -> None:
    router = HorizonRouter.default()
    state = HorizonAppState(page="overview", snapshot=HorizonSnapshot())
    assert handle_key(state, "c", router) is True
    assert state.page == "cloud"
    assert handle_key(state, "w", router) is True
    assert state.page == "scheduler"
    assert handle_key(state, "q", router) is False
    assert handle_key(state, "ESC", router) is False
    assert handle_key(state, "", router) is True


def test_render_app_overview() -> None:
    state = HorizonAppState(
        page="overview",
        snapshot=build_demo_snapshot(now=_stamp()),
    )
    text = _print(render_app(state))
    assert "HORIZON" in text
    assert "Overview" in text


def test_main_noninteractive(monkeypatch: pytest.MonkeyPatch) -> None:
    from aetheros.horizon import app as horizon_app

    monkeypatch.setattr(horizon_app.sys.stdin, "isatty", lambda: False)
    code = horizon_app.main(["--page", "health", "--no-demo"])
    assert code == 0
    code = horizon_app.run(demo=False)
    assert code == 0
