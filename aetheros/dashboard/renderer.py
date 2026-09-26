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

from aetheros.agents import ConsensusPanel, MultiAgentPanel
from aetheros.agents.base import Conflict, ConsensusFinding
from aetheros.agents.coordinator import ConsensusDecision
from aetheros.agents.events import Event
from aetheros.cloud import (
    CloudFederationPanel,
    FederationHealth,
    InfrastructureSnapshot,
    ProviderRecord,
)
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
from aetheros.enterprise import (
    APIKey as EnterpriseAPIKey,
)
from aetheros.enterprise import (
    AuditEvent as EnterpriseAuditEvent,
)
from aetheros.enterprise import (
    EnterprisePanel,
    Organization,
    UsageMetrics,
)
from aetheros.enterprise import (
    Member as EnterpriseMember,
)
from aetheros.enterprise import (
    Workspace as EnterpriseWorkspace,
)
from aetheros.explainability import ExplainabilityPanel, Explanation
from aetheros.fabric import FabricPanel, FabricReport
from aetheros.federation import FederationPanel
from aetheros.federation.models import Heartbeat, RegistryView
from aetheros.genesis import GenesisPanel, GenesisReport
from aetheros.graph import ResourceGraph, ResourceGraphPanel
from aetheros.horizon import HorizonPanel, HorizonReport
from aetheros.infinity import InfinityPanel, InfinityReport
from aetheros.infra_twin import (
    InfrastructureSnapshot as TwinInfraSnapshot,
)
from aetheros.infra_twin import (
    InfrastructureTwinPanel,
    TwinRun,
)
from aetheros.infra_twin import (
    TwinScenario as InfraTwinScenario,
)
from aetheros.knowledge import CausalKnowledgeGraph, CausalKnowledgePanel
from aetheros.marketplace import (
    InstalledPlugin,
    MarketplacePanel,
    UpdateRecommendation,
)
from aetheros.marketplace import PluginManifest as MarketPluginManifest
from aetheros.memory import MemoryRecord, OperationalMemoryPanel, Pattern
from aetheros.observatory import ObservatoryPanel
from aetheros.observatory.models import GraphMetric, SystemEvent
from aetheros.orchestrator import (
    ExecutionPlan,
    WorkloadPlannerPanel,
    WorkloadProfile,
)
from aetheros.policy import (
    EvaluationResult,
    PolicyStudioPanel,
    SimulationImpact,
)
from aetheros.policy import (
    Policy as StudioPolicy,
)
from aetheros.predictive import PredictivePanel, PredictiveReport
from aetheros.reasoning.explain import CognitiveReport
from aetheros.reasoning.formatter import GraphReasoningPanel
from aetheros.reasoning.models import Observation, VerifiedExplanation
from aetheros.research.formatter import ResearchIntelligencePanel
from aetheros.research.models import SystemResearchReport
from aetheros.research_ai import (
    Discovery as ResearchLabDiscovery,
)
from aetheros.research_ai import (
    Experiment as ResearchLabExperiment,
)
from aetheros.research_ai import (
    JournalEntry,
    ResearchLabPanel,
    ResearchQuestion,
)
from aetheros.research_ai import (
    Result as ResearchLabResult,
)
from aetheros.runtime import AgenticReport
from aetheros.scheduler import ScheduleResult, SchedulerPanel, Workload
from aetheros.sentinel import SentinelPanel, SentinelReport
from aetheros.topology import TopologyGraph, TopologyPanel
from aetheros.twin import (
    DigitalTwinPanel,
    DigitalTwinReport,
    SimulationScenario,
    TwinSnapshot,
)


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
    show_resource_graph: bool
    resource_graph: ResourceGraph | None
    show_graph_reasoning: bool
    graph_reasoning: VerifiedExplanation | None
    graph_reasoning_observation: Observation | None
    show_digital_twin: bool
    digital_twin_report: DigitalTwinReport | None
    digital_twin_scenario: SimulationScenario | None
    digital_twin_baseline: TwinSnapshot | None
    show_research_intel: bool
    research_intel_report: SystemResearchReport | None
    research_intel_view: str
    show_op_memory: bool
    op_memory_verified: tuple[MemoryRecord, ...]
    op_memory_patterns: tuple[Pattern, ...]
    op_memory_view: str
    show_causal_knowledge: bool
    causal_knowledge_graph: CausalKnowledgeGraph | None
    causal_knowledge_view: str
    show_consensus: bool
    consensus_decision: ConsensusDecision | None
    consensus_findings: tuple[ConsensusFinding, ...]
    consensus_conflicts: tuple[Conflict, ...]
    consensus_bus_events: tuple[Event, ...]
    consensus_view: str
    show_research_lab: bool
    research_lab_questions: tuple[ResearchQuestion, ...]
    research_lab_experiments: tuple[ResearchLabExperiment, ...]
    research_lab_results: tuple[ResearchLabResult, ...]
    research_lab_verified: tuple[ResearchLabDiscovery, ...]
    research_lab_rejected: tuple[ResearchLabDiscovery, ...]
    research_lab_journal: tuple[JournalEntry, ...]
    research_lab_view: str
    show_federation: bool
    federation_registry: RegistryView | None
    federation_heartbeats: tuple[Heartbeat, ...]
    federation_view: str
    federation_last_sync: object | None
    show_topology: bool
    topology_graph: TopologyGraph | None
    topology_view: str
    show_scheduler: bool
    scheduler_workload: Workload | None
    scheduler_result: ScheduleResult | None
    scheduler_view: str
    show_marketplace: bool
    marketplace_catalog: tuple[MarketPluginManifest, ...]
    marketplace_installed: tuple[InstalledPlugin, ...]
    marketplace_updates: tuple[UpdateRecommendation, ...]
    marketplace_selected: MarketPluginManifest | None
    marketplace_view: str
    show_policy_studio: bool
    policy_studio_policies: tuple[StudioPolicy, ...]
    policy_studio_results: tuple[EvaluationResult, ...]
    policy_studio_impact: SimulationImpact | None
    policy_studio_selected: StudioPolicy | None
    policy_studio_view: str
    show_enterprise: bool
    enterprise_organization: Organization | None
    enterprise_workspaces: tuple[EnterpriseWorkspace, ...]
    enterprise_members: tuple[EnterpriseMember, ...]
    enterprise_api_keys: tuple[EnterpriseAPIKey, ...]
    enterprise_audit_events: tuple[EnterpriseAuditEvent, ...]
    enterprise_audit_count: int
    enterprise_compliance_status: str
    enterprise_metrics: UsageMetrics | None
    enterprise_view: str
    show_cloud: bool
    cloud_snapshot: InfrastructureSnapshot | None
    cloud_health: FederationHealth | None
    cloud_records: tuple[ProviderRecord, ...]
    cloud_age: float
    cloud_view: str
    show_infra_twin: bool
    infra_twin_snapshot: TwinInfraSnapshot | None
    infra_twin_scenarios: tuple[InfraTwinScenario, ...]
    infra_twin_run: TwinRun | None
    infra_twin_view: str


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
    if frame.show_infra_twin:
        layout["center"].update(
            InfrastructureTwinPanel(
                snapshot=frame.infra_twin_snapshot,
                scenarios=frame.infra_twin_scenarios,
                run=frame.infra_twin_run,
                view=frame.infra_twin_view,
            )
        )
    elif frame.show_cloud:
        layout["center"].update(
            CloudFederationPanel(
                snapshot=frame.cloud_snapshot,
                health=frame.cloud_health,
                records=frame.cloud_records,
                snapshot_age_seconds=frame.cloud_age,
                view=frame.cloud_view,
            )
        )
    elif frame.show_enterprise:
        layout["center"].update(
            EnterprisePanel(
                organization=frame.enterprise_organization,
                workspaces=frame.enterprise_workspaces,
                members=frame.enterprise_members,
                api_keys=frame.enterprise_api_keys,
                audit_events=frame.enterprise_audit_events,
                audit_count=frame.enterprise_audit_count,
                compliance_status=frame.enterprise_compliance_status,
                metrics=frame.enterprise_metrics,
                view=frame.enterprise_view,
            )
        )
    elif frame.show_policy_studio:
        layout["center"].update(
            PolicyStudioPanel(
                policies=frame.policy_studio_policies,
                results=frame.policy_studio_results,
                impact=frame.policy_studio_impact,
                selected=frame.policy_studio_selected,
                view=frame.policy_studio_view,
            )
        )
    elif frame.show_marketplace:
        layout["center"].update(
            MarketplacePanel(
                catalog=frame.marketplace_catalog,
                installed=frame.marketplace_installed,
                updates=frame.marketplace_updates,
                selected=frame.marketplace_selected,
                view=frame.marketplace_view,
            )
        )
    elif frame.show_scheduler:
        layout["center"].update(
            SchedulerPanel(
                workload=frame.scheduler_workload,
                result=frame.scheduler_result,
                view=frame.scheduler_view,
            )
        )
    elif frame.show_topology:
        layout["center"].update(
            TopologyPanel(
                graph=frame.topology_graph,
                view=frame.topology_view,
            )
        )
    elif frame.show_federation:
        layout["center"].update(
            FederationPanel(
                registry=frame.federation_registry,
                heartbeats=frame.federation_heartbeats,
                view=frame.federation_view,
                last_sync=frame.federation_last_sync,  # type: ignore[arg-type]
            )
        )
    elif frame.show_research_lab:
        layout["center"].update(
            ResearchLabPanel(
                questions=frame.research_lab_questions,
                experiments=frame.research_lab_experiments,
                results=frame.research_lab_results,
                verified=frame.research_lab_verified,
                rejected=frame.research_lab_rejected,
                journal=frame.research_lab_journal,
                view=frame.research_lab_view,
            )
        )
    elif frame.show_consensus:
        layout["center"].update(
            ConsensusPanel(
                findings=frame.consensus_findings,
                decision=frame.consensus_decision,
                conflicts=frame.consensus_conflicts,
                bus_events=frame.consensus_bus_events,
                view=frame.consensus_view,
            )
        )
    elif frame.show_causal_knowledge:
        layout["center"].update(
            CausalKnowledgePanel(
                graph=frame.causal_knowledge_graph,
                view=frame.causal_knowledge_view,
            )
        )
    elif frame.show_op_memory:
        layout["center"].update(
            OperationalMemoryPanel(
                verified=frame.op_memory_verified,
                patterns=frame.op_memory_patterns,
                view=frame.op_memory_view,
            )
        )
    elif frame.show_research_intel:
        layout["center"].update(
            ResearchIntelligencePanel(
                report=frame.research_intel_report,
                view=frame.research_intel_view,
            )
        )
    elif frame.show_digital_twin:
        layout["center"].update(
            DigitalTwinPanel(
                report=frame.digital_twin_report,
                scenario=frame.digital_twin_scenario,
                baseline=frame.digital_twin_baseline,
            )
        )
    elif frame.show_graph_reasoning:
        layout["center"].update(
            GraphReasoningPanel(
                explanation=frame.graph_reasoning,
                observation=frame.graph_reasoning_observation,
            )
        )
    elif frame.show_resource_graph:
        layout["center"].update(ResourceGraphPanel(graph=frame.resource_graph))
    elif frame.show_infinity:
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
