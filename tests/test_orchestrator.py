"""Unit tests for AetherOS v1.5 Resource Orchestrator."""

from __future__ import annotations

from datetime import UTC, datetime

from rich.console import Console

from aetheros.cluster.models import ClusterNode
from aetheros.orchestrator import (
    ResourcePlanner,
    WorkloadPlannerPanel,
    evaluate_constraints,
    get_workload,
    next_workload,
    to_candidate,
    workload_names,
)


def _cluster_node(
    *,
    node_id: str,
    hostname: str,
    cpu: float,
    memory: float = 40.0,
    disk: float = 30.0,
    battery: float | None = None,
    latency: float = 1.0,
) -> ClusterNode:
    """Build a cluster node for planner tests."""

    return ClusterNode(
        node_id=node_id,
        hostname=hostname,
        platform="Linux",
        cpu=cpu,
        memory=memory,
        disk=disk,
        battery=battery,
        latency=latency,
        last_seen=datetime.now(UTC),
    )


def test_workload_catalog() -> None:
    """Catalog should include the six required workload types."""

    names = set(workload_names())
    assert "AI Training" in names
    assert "Video Rendering" in names
    assert "Gaming" in names
    assert len(names) == 6
    nxt = next_workload("AI Training")
    assert nxt.name != "AI Training"


def test_constraints_reject_unsafe_nodes() -> None:
    """Hard constraints should reject overloaded / offline / low-battery nodes."""

    online = to_candidate(
        _cluster_node(node_id="d", hostname="Desktop", cpu=40.0),
        online=True,
    )
    hot = to_candidate(
        _cluster_node(node_id="h", hostname="Hot", cpu=95.0),
        online=True,
    )
    mem = to_candidate(
        _cluster_node(node_id="m", hostname="Mem", cpu=20.0, memory=92.0),
        online=True,
    )
    battery = to_candidate(
        _cluster_node(
            node_id="l",
            hostname="Laptop",
            cpu=20.0,
            battery=10.0,
        ),
        online=True,
    )
    offline = to_candidate(
        _cluster_node(node_id="o", hostname="OfflineBox", cpu=10.0),
        online=False,
    )
    eligible, rejected = evaluate_constraints((online, hot, mem, battery, offline))
    assert len(eligible) == 1
    assert eligible[0].hostname == "Desktop"
    reasons = {item.hostname: item.reason for item in rejected}
    assert "Critical" in reasons["Hot"] or "CPU" in reasons["Hot"]
    assert "Memory above" in reasons["Mem"]
    assert "Battery below" in reasons["Laptop"]
    assert reasons["OfflineBox"] == "Offline"


def test_planner_recommends_desktop_for_ai_training() -> None:
    """AI Training should prefer a powerful desktop over Pi / low-battery laptop."""

    nodes = (
        _cluster_node(
            node_id="laptop",
            hostname="Laptop",
            cpu=22.0,
            memory=45.0,
            battery=12.0,
            latency=2.0,
        ),
        _cluster_node(
            node_id="desktop",
            hostname="Desktop",
            cpu=30.0,
            memory=35.0,
            latency=1.0,
        ),
        _cluster_node(
            node_id="pi",
            hostname="Pi",
            cpu=17.0,
            memory=88.0,
            latency=5.0,
        ),
        _cluster_node(
            node_id="cloud",
            hostname="Cloud",
            cpu=40.0,
            memory=50.0,
            latency=45.0,
        ),
    )
    online = frozenset(n.node_id for n in nodes)
    plan = ResourcePlanner().plan(
        "AI Training",
        nodes,
        online_ids=online,
    )
    assert plan.recommended_node is not None
    assert plan.recommended_node.hostname == "Desktop"
    assert plan.score > 0
    assert any(r.hostname == "Laptop" for r in plan.rejected_nodes)
    assert "Recommendation only" in plan.status
    assert plan.explanation


def test_video_rendering_prefers_disk_headroom() -> None:
    """Video Rendering weights disk; node with freer disk should score higher."""

    tight = _cluster_node(
        node_id="a",
        hostname="DesktopA",
        cpu=25.0,
        memory=40.0,
        disk=88.0,
    )
    free = _cluster_node(
        node_id="b",
        hostname="DesktopB",
        cpu=28.0,
        memory=42.0,
        disk=20.0,
    )
    plan = ResourcePlanner().plan(
        get_workload("Video Rendering"),
        (tight, free),
        online_ids=frozenset({"a", "b"}),
    )
    assert plan.recommended_node is not None
    assert plan.recommended_node.hostname == "DesktopB"


def test_planner_panel_renders() -> None:
    """Rich panel should show workload, score, and recommendation-only status."""

    nodes = (
        _cluster_node(node_id="desktop", hostname="Desktop", cpu=25.0),
        _cluster_node(node_id="pi", hostname="Pi", cpu=20.0, memory=70.0),
    )
    plan = ResourcePlanner().plan(
        "AI Training",
        nodes,
        online_ids=frozenset({"desktop", "pi"}),
    )
    panel = WorkloadPlannerPanel(plan=plan, selected=plan.workload)
    console = Console(record=True, width=100)
    console.print(panel)
    text = console.export_text()
    assert "WORKLOAD PLANNER" in text
    assert "AI Training" in text
    assert "Desktop" in text
    assert "Recommendation only" in text
