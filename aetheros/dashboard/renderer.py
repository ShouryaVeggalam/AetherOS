"""Assemble dashboard widgets into the Rich Layout.

The renderer maps a DashboardFrame (plain data) onto layout regions.
It does not collect telemetry or run the decision pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.align import Align
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text

from aetheros.agents import MultiAgentPanel
from aetheros.cluster import ClusterPanel, ClusterSnapshot
from aetheros.cognition import CognitivePanel
from aetheros.dashboard.layout import build_layout
from aetheros.dashboard.widgets import (
    DecisionPanel,
    DeveloperConsolePanel,
    HeaderPanel,
    HelpPanel,
    IntentPanel,
    ProcessRow,
    ProcessTable,
    ResearchPanel,
    SafetyPanel,
    TelemetryPanel,
)
from aetheros.explainability import ExplainabilityPanel, Explanation
from aetheros.fabric import FabricPanel, FabricReport
from aetheros.genesis import GenesisPanel, GenesisReport
from aetheros.horizon import HorizonPanel, HorizonReport
from aetheros.infinity import InfinityPanel, InfinityReport
from aetheros.observatory import ObservatoryPanel
from aetheros.observatory.models import GraphMetric, SystemEvent
from aetheros.orchestrator import (
    ExecutionPlan,
    WorkloadPlannerPanel,
    WorkloadProfile,
)
from aetheros.predictive import PredictivePanel, PredictiveReport
from aetheros.reasoning.explain import CognitiveReport
from aetheros.runtime import AgenticReport
from aetheros.sentinel import SentinelPanel, SentinelReport


@dataclass(frozen=True, slots=True)
class DashboardFrame:
    """One immutable snapshot of everything the UI needs to draw."""

    version: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    battery_text: str
    uptime_text: str
    processes: tuple[ProcessRow, ...]
    decision_title: str
    decision_score: int
    decision_status: str
    decision_explanation: str
    decision_style: str
    safety_status: str
    safety_style: str
    approved_count: int
    blocked_count: int
    cooldown_seconds: float
    last_audit_summary: str
    show_help: bool
    show_developer: bool
    intent_name: str
    intent_description: str
    intent_cpu: int
    intent_memory: int
    intent_disk: int
    intent_latency: int
    intent_efficiency: int
    research_status: str
    research_strategies: int
    research_best_score: float
    research_winner: str
    research_improvement: str
    research_report_path: str
    plugin_rows: tuple[tuple[str, str, str, str, str], ...]
    plugins_verified: int
    plugins_unsafe: int
    show_observatory: bool
    observatory_metric: GraphMetric
    observatory_cpu_spark: str
    observatory_memory_spark: str
    observatory_disk_spark: str
    observatory_detail_graph: str
    observatory_events: tuple[SystemEvent, ...]
    observatory_observations: tuple[str, ...]
    observatory_offset: int
    observatory_samples: int
    observatory_capacity: int
    observatory_window_label: str
    show_explainability: bool
    explanation: Explanation | None
    show_predictive: bool
    predictive_report: PredictiveReport | None
    show_cluster: bool
    cluster_snapshot: ClusterSnapshot | None
    cluster_online_ids: frozenset[str]
    show_orchestrator: bool
    execution_plan: ExecutionPlan | None
    selected_workload: WorkloadProfile | None
    show_cognitive: bool
    cognitive_report: CognitiveReport | None
    show_multi_agent: bool
    agentic_report: AgenticReport | None
    show_horizon: bool
    horizon_report: HorizonReport | None
    show_genesis: bool
    genesis_report: GenesisReport | None
    show_sentinel: bool
    sentinel_report: SentinelReport | None
    show_fabric: bool
    fabric_report: FabricReport | None
    show_infinity: bool
    infinity_report: InfinityReport | None


def render_frame(frame: DashboardFrame) -> Layout:
    """Populate a fresh layout from one DashboardFrame."""

    layout = build_layout()
    layout["header"].update(HeaderPanel(version=frame.version))
    layout["left"].update(
        TelemetryPanel(
            cpu_percent=frame.cpu_percent,
            memory_percent=frame.memory_percent,
            disk_percent=frame.disk_percent,
            battery_text=frame.battery_text,
            uptime_text=frame.uptime_text,
        )
    )
    layout["intent"].update(
        IntentPanel(
            name=frame.intent_name,
            description=frame.intent_description,
            cpu_weight=frame.intent_cpu,
            memory_weight=frame.intent_memory,
            disk_weight=frame.intent_disk,
            latency_weight=frame.intent_latency,
            efficiency_weight=frame.intent_efficiency,
        )
    )
    if frame.show_infinity:
        layout["center"].update(InfinityPanel(report=frame.infinity_report))
    elif frame.show_fabric:
        layout["center"].update(FabricPanel(report=frame.fabric_report))
    elif frame.show_sentinel:
        layout["center"].update(SentinelPanel(report=frame.sentinel_report))
    elif frame.show_genesis:
        layout["center"].update(GenesisPanel(report=frame.genesis_report))
    elif frame.show_horizon:
        layout["center"].update(HorizonPanel(report=frame.horizon_report))
    elif frame.show_multi_agent:
        layout["center"].update(MultiAgentPanel(report=frame.agentic_report))
    elif frame.show_cognitive:
        layout["center"].update(CognitivePanel(report=frame.cognitive_report))
    elif frame.show_orchestrator:
        layout["center"].update(
            WorkloadPlannerPanel(
                plan=frame.execution_plan,
                selected=frame.selected_workload,
            )
        )
    elif frame.show_cluster:
        layout["center"].update(
            ClusterPanel(
                snapshot=frame.cluster_snapshot,
                online_ids=frame.cluster_online_ids,
            )
        )
    elif frame.show_predictive:
        layout["center"].update(PredictivePanel(report=frame.predictive_report))
    elif frame.show_explainability:
        layout["center"].update(ExplainabilityPanel(explanation=frame.explanation))
    elif frame.show_observatory:
        layout["center"].update(
            ObservatoryPanel(
                focus_metric=frame.observatory_metric,
                cpu_spark=frame.observatory_cpu_spark,
                memory_spark=frame.observatory_memory_spark,
                disk_spark=frame.observatory_disk_spark,
                detail_graph=frame.observatory_detail_graph,
                events=frame.observatory_events,
                observations=frame.observatory_observations,
                history_offset=frame.observatory_offset,
                sample_count=frame.observatory_samples,
                capacity=frame.observatory_capacity,
                window_label=frame.observatory_window_label,
            )
        )
    elif frame.show_developer:
        layout["center"].update(
            DeveloperConsolePanel(
                rows=frame.plugin_rows,
                verified=frame.plugins_verified,
                unsafe=frame.plugins_unsafe,
            )
        )
    elif frame.show_help:
        layout["center"].update(HelpPanel())
    else:
        layout["center"].update(ProcessTable(rows=frame.processes))
    layout["right"].update(
        DecisionPanel(
            title=frame.decision_title,
            priority_score=frame.decision_score,
            status=frame.decision_status,
            explanation=frame.decision_explanation,
            status_style=frame.decision_style,
        )
    )
    layout["research"].update(
        ResearchPanel(
            status=frame.research_status,
            strategies_generated=frame.research_strategies,
            best_score=frame.research_best_score,
            winning_strategy=frame.research_winner,
            estimated_improvement=frame.research_improvement,
            report_path=frame.research_report_path,
        )
    )
    layout["bottom"].update(
        SafetyPanel(
            status=frame.safety_status,
            status_style=frame.safety_style,
            approved_count=frame.approved_count,
            blocked_count=frame.blocked_count,
            cooldown_seconds=frame.cooldown_seconds,
            last_audit_summary=frame.last_audit_summary,
        )
    )
    layout["footer"].update(
        Panel(
            Align.center(
                Text(
                    "Q quit · F fabric · S sentinel · G genesis · H horizon · "
                    "M agents · K cognitive · ? help · ESC",
                    style="dim cyan",
                )
            ),
            border_style="blue",
        )
    )
    return layout
