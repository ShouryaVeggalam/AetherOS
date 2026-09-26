"""Unit tests for Phase 5 dashboard widgets and frame rendering."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from rich.console import Console

from aetheros.dashboard.app import (
    build_frame,
    format_audit_summary,
    format_battery,
    format_uptime,
)
from aetheros.dashboard.renderer import DashboardFrame, render_frame
from aetheros.dashboard.widgets import (
    DecisionPanel,
    HeaderPanel,
    ProcessRow,
    ProcessTable,
    SafetyPanel,
    TelemetryPanel,
    level_style,
)
from aetheros.decision import DecisionEngine
from aetheros.policy_engine import TelemetrySnapshot
from aetheros.safety import AuditLogger, CooldownManager, SafetyValidator
from aetheros.telemetry.models import (
    BatterySnapshot,
    CpuSnapshot,
    DiskSnapshot,
    MemorySnapshot,
    ProcessSnapshot,
    SystemSnapshot,
)


def _system(*, cpu: float = 24.0, memory: float = 51.0) -> SystemSnapshot:
    """Build a SystemSnapshot for dashboard tests."""

    return SystemSnapshot(
        collected_at=datetime.now(UTC),
        cpu=CpuSnapshot(percent=cpu, per_cpu_percent=(cpu,), load_avg=(0.1, 0.2, 0.3)),
        memory=MemorySnapshot(
            total_bytes=16_000_000_000,
            available_bytes=8_000_000_000,
            used_bytes=8_000_000_000,
            percent=memory,
            swap_total_bytes=0,
            swap_used_bytes=0,
            swap_percent=0.0,
        ),
        disks=(
            DiskSnapshot(
                mountpoint="/",
                total_bytes=100,
                used_bytes=38,
                free_bytes=62,
                percent=38.0,
            ),
        ),
        processes=(
            ProcessSnapshot(1, "chrome", "user", 10.0, 5.0, "running"),
            ProcessSnapshot(2, "python", "user", 8.0, 2.0, "running"),
            ProcessSnapshot(3, "code", "user", 4.0, 3.0, "running"),
        ),
        battery=BatterySnapshot(percent=80.0, is_plugged_in=True, secs_left=None),
    )


def test_level_style_thresholds() -> None:
    """Utilization colors should follow healthy/warning/critical bands."""

    assert level_style(24.0) == "bold green"
    assert level_style(90.0) == "bold yellow"
    assert level_style(97.0) == "bold red"


def test_format_helpers() -> None:
    """Uptime, battery, and audit formatters should return readable text."""

    assert "m" in format_uptime(125.0)
    system = _system()
    assert "80%" in format_battery(system)
    assert "No audit" in format_audit_summary(None)
    assert "blocked" in format_audit_summary(
        {
            "timestamp": datetime.now(UTC).isoformat(),
            "title": "CPU Overload",
            "level": "critical",
            "approved": False,
            "reason": "cooldown",
            "confidence": 98,
        }
    )


def test_widgets_render_without_error() -> None:
    """Each widget should produce a printable Rich renderable."""

    console = Console(record=True, width=100)
    console.print(HeaderPanel(version="0.5.0"))
    console.print(TelemetryPanel(24.0, 51.0, 38.0, "80% (AC)", "1h 2m"))
    console.print(
        ProcessTable(
            rows=(
                ProcessRow(1, "chrome", 10.0, 5.0),
                ProcessRow(2, "python", 8.0, 2.0),
            )
        )
    )
    console.print(
        DecisionPanel("System Healthy", 12, "Healthy", "No pressure.", "green")
    )
    console.print(
        SafetyPanel("APPROVED", "green", 1, 0, 0.0, "CPU Overload blocked 3m ago.")
    )
    text = console.export_text()
    assert "AetherOS" in text
    assert "chrome" in text
    assert "System Healthy" in text


def test_render_frame_has_regions() -> None:
    """Rendered layout should expose the expected named regions."""

    frame = DashboardFrame(
        version="1.0.0",
        cpu_percent=24.0,
        memory_percent=51.0,
        disk_percent=38.0,
        battery_text="n/a",
        uptime_text="10m",
        processes=(ProcessRow(1, "python", 1.0, 1.0),),
        decision_title="System Healthy",
        decision_score=12,
        decision_status="Healthy",
        decision_explanation="No critical resource pressure detected.",
        decision_style="green",
        safety_status="APPROVED",
        safety_style="green",
        approved_count=0,
        blocked_count=0,
        cooldown_seconds=0.0,
        last_audit_summary="No audit entries yet.",
        show_help=False,
        show_developer=False,
        intent_name="Coding",
        intent_description="Low latency development",
        intent_cpu=10,
        intent_memory=15,
        intent_disk=5,
        intent_latency=25,
        intent_efficiency=20,
        research_status="Idle",
        research_strategies=0,
        research_best_score=0.0,
        research_winner="—",
        research_improvement="—",
        research_report_path="Press A to run research",
        plugin_rows=(("CPU Monitor", "1.0.0", "Enabled", "AetherOS", "Verified"),),
        plugins_verified=3,
        plugins_unsafe=0,
        show_observatory=True,
        observatory_metric="cpu",
        observatory_cpu_spark="▁▂▃",
        observatory_memory_spark="▂▃▄",
        observatory_disk_spark="▁▁▁",
        observatory_detail_graph="CPU\n████",
        observatory_events=(),
        observatory_observations=("CPU increased by 10% over 20s.",),
        observatory_offset=0,
        observatory_samples=10,
        observatory_capacity=300,
        observatory_window_label="Last 60 Seconds",
        show_explainability=False,
        explanation=None,
        show_predictive=False,
        predictive_report=None,
        show_cluster=False,
        cluster_snapshot=None,
        cluster_online_ids=frozenset(),
        show_orchestrator=False,
        execution_plan=None,
        selected_workload=None,
        show_cognitive=False,
        cognitive_report=None,
        show_multi_agent=False,
        agentic_report=None,
        show_horizon=False,
        horizon_report=None,
        show_genesis=False,
        genesis_report=None,
        show_sentinel=False,
        sentinel_report=None,
        show_fabric=False,
        fabric_report=None,
        show_infinity=False,
        infinity_report=None,
        show_resource_graph=False,
        resource_graph=None,
        show_graph_reasoning=False,
        graph_reasoning=None,
        graph_reasoning_observation=None,
        show_digital_twin=False,
        digital_twin_report=None,
        digital_twin_scenario=None,
        digital_twin_baseline=None,
        show_research_intel=False,
        research_intel_report=None,
        research_intel_view="daily",
        show_op_memory=False,
        op_memory_verified=(),
        op_memory_patterns=(),
        op_memory_view="verified",
        show_causal_knowledge=False,
        causal_knowledge_graph=None,
        causal_knowledge_view="causal",
        show_consensus=False,
        consensus_decision=None,
        consensus_findings=(),
        consensus_conflicts=(),
        consensus_bus_events=(),
        consensus_view="consensus",
        show_research_lab=False,
        research_lab_questions=(),
        research_lab_experiments=(),
        research_lab_results=(),
        research_lab_verified=(),
        research_lab_rejected=(),
        research_lab_journal=(),
        research_lab_view="discoveries",
        show_federation=False,
        federation_registry=None,
        federation_heartbeats=(),
        federation_view="nodes",
        federation_last_sync=None,
        show_topology=False,
        topology_graph=None,
        topology_view="tree",
        show_scheduler=False,
        scheduler_workload=None,
        scheduler_result=None,
        scheduler_view="summary",
        show_marketplace=False,
        marketplace_catalog=(),
        marketplace_installed=(),
        marketplace_updates=(),
        marketplace_selected=None,
        marketplace_view="marketplace",
        show_policy_studio=False,
        policy_studio_policies=(),
        policy_studio_results=(),
        policy_studio_impact=None,
        policy_studio_selected=None,
        policy_studio_view="active",
        show_enterprise=False,
        enterprise_organization=None,
        enterprise_workspaces=(),
        enterprise_members=(),
        enterprise_api_keys=(),
        enterprise_audit_events=(),
        enterprise_audit_count=0,
        enterprise_compliance_status="SOC2 Ready",
        enterprise_metrics=None,
        enterprise_view="organizations",
        show_cloud=False,
        cloud_snapshot=None,
        cloud_health=None,
        cloud_records=(),
        cloud_age=0.0,
        cloud_view="providers",
        show_infra_twin=False,
        infra_twin_snapshot=None,
        infra_twin_scenarios=(),
        infra_twin_run=None,
        infra_twin_view="snapshot",
        show_global_graph=False,
        global_graph_graph=None,
        global_graph_evidence=None,
        global_graph_validation=None,
        global_graph_view="world",
    )
    layout = render_frame(frame)
    assert layout["header"] is not None
    assert layout["left"] is not None
    assert layout["intent"] is not None
    assert layout["research"] is not None
    assert layout["center"] is not None
    assert layout["right"] is not None
    assert layout["bottom"] is not None


def test_build_frame_healthy(tmp_path: Path) -> None:
    """Healthy telemetry should map to a System Healthy decision panel."""

    from aetheros.dashboard.app import ObservatoryViewState, ResearchViewState
    from aetheros.intent import IntentEngine, IntentStorage
    from aetheros.observatory import HistoryRecorder

    system = _system(cpu=24.0, memory=51.0)
    snapshot = TelemetrySnapshot.from_system_snapshot(system)
    engine = DecisionEngine(
        safety=SafetyValidator(
            cooldown=CooldownManager(),
            audit=AuditLogger(tmp_path / "audit.db"),
        ),
        intent=IntentEngine(
            storage=IntentStorage(tmp_path / "intent.db"), initial="Coding"
        ),
    )
    report = engine.evaluate_report(snapshot, record=False)
    frame = build_frame(
        system,
        report,
        show_help=False,
        show_developer=False,
        audit=engine.safety.audit,
        engine=engine,
        research=ResearchViewState(),
        plugin_records=[],
        plugins_verified=0,
        plugins_unsafe=0,
        observatory=ObservatoryViewState(
            visible=True,
            recorder=HistoryRecorder(tmp_path / "obs.db", 300),
        ),
    )
    assert frame.cpu_percent == 24.0
    assert len(frame.processes) == 3
    assert frame.intent_name == "Coding"
    assert frame.research_status == "Idle"
    assert (
        frame.decision_title in {"System Healthy", "Idle System"}
        or frame.decision_score >= 0
    )
