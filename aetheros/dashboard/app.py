"""Operator dashboard application loop.

Collects telemetry, runs the decision pipeline (without flooding the
audit log), builds a DashboardFrame, and drives Rich Live.
"""

from __future__ import annotations

import argparse
import select
import sys
import termios
import time
import tty
from dataclasses import dataclass, field
from pathlib import Path

import psutil
from rich.live import Live

from aetheros import __version__
from aetheros.agent import (
    AgentCollector,
    AgentPublisher,
    SyntheticPeer,
    default_demo_peers,
)
from aetheros.agents import (
    Conflict,
    ConsensusDecision,
    ConsensusEngine,
    ConsensusFinding,
    DeliberationContext,
    Event,
)
from aetheros.cluster import (
    ClusterSnapshot,
    LocalJSONTransport,
    NodeRegistry,
    aggregate,
)
from aetheros.cognition import CognitiveRuntime
from aetheros.core import AetherCore
from aetheros.dashboard.formatting import (
    format_audit_summary,
    format_battery,
    format_uptime,
    plugin_console_rows,
)
from aetheros.dashboard.renderer import DashboardFrame, render_frame
from aetheros.dashboard.widgets import ProcessRow
from aetheros.decision import DecisionEngine, DecisionReport
from aetheros.decision.models import Decision, utc_now
from aetheros.explainability import ExplainabilityEngine, Explanation
from aetheros.fabric import FabricReport, FabricRuntime
from aetheros.federation import (
    FederationRegistry,
    Heartbeat,
    seed_demo_federation,
)
from aetheros.genesis import GenesisReport, GenesisRuntime
from aetheros.graph import ResourceGraph, build_resource_graph
from aetheros.horizon import HorizonReport, HorizonRuntime
from aetheros.infinity import InfinityReport, InfinityRuntime
from aetheros.intent import IntentEngine, IntentStorage
from aetheros.knowledge import (
    CausalKnowledgeGraph,
    build_knowledge_graph,
)
from aetheros.learning import LearningEngine
from aetheros.marketplace import (
    MarketplaceRegistry,
    MarketplaceUpdater,
    seed_demo_marketplace,
)
from aetheros.marketplace import (
    PluginManifest as MarketPluginManifest,
)
from aetheros.memory import MemoryEngine, MemoryQuery
from aetheros.observatory import (
    EventTimeline,
    HistoryRecorder,
    derive_observations,
    detect_events,
    render_ascii_graph,
    research_completed_event,
    safety_blocked_event,
    sparkline,
)
from aetheros.observatory.models import GraphMetric
from aetheros.orchestrator import (
    ExecutionPlan,
    ResourcePlanner,
    WorkloadProfile,
    get_workload,
    next_workload,
)
from aetheros.policy_engine import TelemetrySnapshot
from aetheros.predictive import ForecastEngine, PredictiveReport
from aetheros.reasoning import (
    Observation,
    VerifiedExplanation,
    observation_from_metrics,
)
from aetheros.reasoning import (
    reason as graph_reason,
)
from aetheros.reasoning.explain import CognitiveReport
from aetheros.research import ResearchEngine, ResearchIntelligenceEngine, ResearchReport
from aetheros.research.models import SystemResearchReport
from aetheros.research_ai import (
    AutonomousResearchEngine,
)
from aetheros.runtime import AgenticReport, AgenticRuntime
from aetheros.safety import AuditLogger, CooldownManager, SafetyValidator
from aetheros.scheduler import (
    ScheduleConstraint,
    ScheduleResult,
    Workload,
    demo_nodes,
    demo_workload,
    run_scheduler,
)
from aetheros.sdk import PluginRecord
from aetheros.sentinel import SentinelReport, SentinelRuntime
from aetheros.telemetry import TelemetryCollector
from aetheros.telemetry.models import SystemSnapshot
from aetheros.topology import (
    TopologyGraph,
    build_topology,
    demo_topology_metadata,
)
from aetheros.twin import (
    DigitalTwinReport,
    DigitalTwinSimulator,
    SimulationScenario,
    TwinSnapshot,
    builtin_scenario,
    create_snapshot,
)


@dataclass
class ResearchViewState:
    """UI state for the latest autonomous research run."""

    status: str = "Idle"
    strategies_generated: int = 0
    best_score: float = 0.0
    winning_strategy: str = "—"
    estimated_improvement: str = "—"
    report_path: str = "Press A to run research"


@dataclass
class ObservatoryViewState:
    """UI state for the real-time observatory center panel."""

    visible: bool = True
    metric: GraphMetric = "cpu"
    history_offset: int = 0
    recorder: HistoryRecorder = field(
        default_factory=lambda: HistoryRecorder(Path("data/observatory.db"), 300)
    )
    timeline: EventTimeline = field(default_factory=EventTimeline)
    seen_safety_blocks: set[str] = field(default_factory=set)


@dataclass
class ExplainabilityViewState:
    """UI state for the explainability center panel."""

    visible: bool = False
    engine: ExplainabilityEngine = field(default_factory=ExplainabilityEngine)
    last: Explanation | None = None


@dataclass
class PredictiveViewState:
    """UI state for the predictive intelligence center panel."""

    visible: bool = False
    engine: ForecastEngine = field(default_factory=ForecastEngine)
    last: PredictiveReport | None = None


@dataclass
class ClusterViewState:
    """UI state for the multi-device cluster center panel."""

    visible: bool = False
    transport: LocalJSONTransport = field(default_factory=LocalJSONTransport)
    registry: NodeRegistry | None = None
    local_agent: AgentCollector = field(default_factory=AgentCollector)
    publisher: AgentPublisher | None = None
    demo_peers: tuple[SyntheticPeer, ...] = field(default_factory=default_demo_peers)
    last: ClusterSnapshot | None = None
    online_ids: frozenset[str] = field(default_factory=frozenset)

    def ensure(self, db_path: Path) -> None:
        """Lazily wire registry + publisher against the shared transport."""

        if self.registry is None:
            self.registry = NodeRegistry(transport=self.transport, db_path=db_path)
        if self.publisher is None:
            self.publisher = AgentPublisher(transport=self.transport)


@dataclass
class OrchestratorViewState:
    """UI state for the workload planner center panel."""

    visible: bool = False
    planner: ResourcePlanner = field(default_factory=ResourcePlanner)
    workload: WorkloadProfile = field(
        default_factory=lambda: get_workload("AI Training")
    )
    last: ExecutionPlan | None = None


@dataclass
class CognitiveViewState:
    """UI state for the cognitive graph center panel."""

    visible: bool = False
    runtime: CognitiveRuntime = field(default_factory=CognitiveRuntime)
    last: CognitiveReport | None = None


@dataclass
class MultiAgentViewState:
    """UI state for the multi-agent center panel."""

    visible: bool = False
    runtime: AgenticRuntime = field(default_factory=AgenticRuntime)
    last: AgenticReport | None = None


@dataclass
class HorizonViewState:
    """UI state for the Horizon planetary intelligence panel."""

    visible: bool = False
    runtime: HorizonRuntime = field(default_factory=HorizonRuntime)
    last: HorizonReport | None = None


@dataclass
class GenesisViewState:
    """UI state for the Genesis research intelligence panel."""

    visible: bool = False
    runtime: GenesisRuntime = field(default_factory=GenesisRuntime)
    last: GenesisReport | None = None


@dataclass
class SentinelViewState:
    """UI state for the Sentinel resilience intelligence panel."""

    visible: bool = False
    runtime: SentinelRuntime = field(default_factory=SentinelRuntime)
    last: SentinelReport | None = None


@dataclass
class FabricViewState:
    """UI state for the Aether Fabric universal intelligence panel."""

    visible: bool = False
    runtime: FabricRuntime = field(default_factory=FabricRuntime)
    last: FabricReport | None = None


@dataclass
class InfinityViewState:
    """UI state for the Infinity platform overview panel."""

    visible: bool = False
    runtime: InfinityRuntime = field(default_factory=InfinityRuntime)
    last: InfinityReport | None = None


@dataclass
class ResourceGraphViewState:
    """UI state for the Resource Graph Engine panel."""

    visible: bool = False
    last: ResourceGraph | None = None


@dataclass
class GraphReasoningViewState:
    """UI state for the Graph Reasoning Engine panel."""

    visible: bool = False
    last: VerifiedExplanation | None = None
    observation: Observation | None = None


@dataclass
class DigitalTwinViewState:
    """UI state for Digital Twin 2.0 host panel."""

    visible: bool = False
    last: DigitalTwinReport | None = None
    scenario: SimulationScenario | None = None
    baseline: TwinSnapshot | None = None
    scenario_index: int = 0


@dataclass
class ResearchIntelligenceViewState:
    """UI state for P9 Research Intelligence panel (shortcut X)."""

    visible: bool = False
    last: SystemResearchReport | None = None
    view_index: int = 0
    views: tuple[str, ...] = (
        "daily",
        "weekly",
        "bottlenecks",
        "discoveries",
        "simulation",
    )

    @property
    def view(self) -> str:
        return self.views[self.view_index % len(self.views)]


@dataclass
class OperationalMemoryViewState:
    """UI state for P2 Operational Memory panel (shortcut L)."""

    visible: bool = False
    engine: MemoryEngine = field(default_factory=MemoryEngine)
    seeded: bool = False
    view_index: int = 0
    views: tuple[str, ...] = (
        "verified",
        "recent",
        "related",
        "timeline",
    )

    @property
    def view(self) -> str:
        return self.views[self.view_index % len(self.views)]

    def ensure_seeded(self) -> None:
        """Load curated verified seeds once (read-only overlay data)."""

        if not self.seeded:
            self.engine.seed_defaults()
            self.seeded = True


@dataclass
class CausalKnowledgeViewState:
    """UI state for P3 Causal Knowledge Graph panel (shortcut N)."""

    visible: bool = False
    last: CausalKnowledgeGraph | None = None
    view_index: int = 0
    views: tuple[str, ...] = (
        "causal",
        "ontology",
        "discoveries",
        "relationships",
        "evidence",
    )

    @property
    def view(self) -> str:
        return self.views[self.view_index % len(self.views)]


@dataclass
class ConsensusViewState:
    """UI state for P4 Multi-Agent Consensus panel (shortcut J)."""

    visible: bool = False
    engine: ConsensusEngine = field(default_factory=ConsensusEngine)
    last: ConsensusDecision | None = None
    findings: tuple[ConsensusFinding, ...] = ()
    conflicts: tuple[Conflict, ...] = ()
    bus_events: tuple[Event, ...] = ()
    view_index: int = 0
    views: tuple[str, ...] = (
        "consensus",
        "status",
        "findings",
        "bus",
        "conflicts",
    )

    @property
    def view(self) -> str:
        return self.views[self.view_index % len(self.views)]


@dataclass
class ResearchLabViewState:
    """UI state for P5 Autonomous Research Lab panel (shortcut B)."""

    visible: bool = False
    engine: AutonomousResearchEngine = field(default_factory=AutonomousResearchEngine)
    seeded: bool = False
    view_index: int = 0
    views: tuple[str, ...] = (
        "discoveries",
        "questions",
        "experiments",
        "rejected",
        "journal",
    )

    @property
    def view(self) -> str:
        return self.views[self.view_index % len(self.views)]


@dataclass
class FederationViewState:
    """UI state for v4 P1 Federation Protocol panel (shortcut U)."""

    visible: bool = False
    registry: FederationRegistry = field(default_factory=FederationRegistry)
    heartbeats: tuple[Heartbeat, ...] = ()
    last_sync: object | None = None
    seeded: bool = False
    view_index: int = 0
    views: tuple[str, ...] = (
        "nodes",
        "registry",
        "heartbeats",
        "protocol",
    )

    @property
    def view(self) -> str:
        return self.views[self.view_index % len(self.views)]


@dataclass
class TopologyViewState:
    """UI state for v4 P2 Cluster Topology panel (shortcut Z)."""

    visible: bool = False
    graph: TopologyGraph | None = None
    seeded: bool = False
    view_index: int = 0
    views: tuple[str, ...] = (
        "tree",
        "world",
        "regions",
        "clusters",
        "health",
    )

    @property
    def view(self) -> str:
        return self.views[self.view_index % len(self.views)]


@dataclass
class SchedulerViewState:
    """UI state for v4 P3 Distributed Scheduler panel (shortcut /)."""

    visible: bool = False
    workload: Workload | None = None
    result: ScheduleResult | None = None
    seeded: bool = False
    view_index: int = 0
    views: tuple[str, ...] = (
        "summary",
        "workloads",
        "candidates",
        "scores",
        "simulation",
        "tradeoffs",
    )

    @property
    def view(self) -> str:
        return self.views[self.view_index % len(self.views)]


@dataclass
class MarketplaceViewState:
    """UI state for v5 P3 Extension Marketplace panel (shortcut E)."""

    visible: bool = False
    registry: MarketplaceRegistry = field(default_factory=MarketplaceRegistry)
    catalog: tuple[MarketPluginManifest, ...] = ()
    seeded: bool = False
    view_index: int = 0
    views: tuple[str, ...] = (
        "marketplace",
        "installed",
        "updates",
        "permissions",
        "details",
    )

    @property
    def view(self) -> str:
        return self.views[self.view_index % len(self.views)]


def max_cooldown_seconds(engine: DecisionEngine) -> float:
    """Return the longest active cooldown across known categories."""

    titles = (
        "CPU Overload",
        "High Memory Usage",
        "Critical Disk Pressure",
        "Idle System",
    )
    return max(
        (engine.safety.cooldown.remaining_seconds(title) for title in titles),
        default=0.0,
    )


def _healthy_decision(engine: DecisionEngine) -> Decision:
    """Build a lightweight healthy-state decision shaped by intent."""

    profile = engine.intent.current_intent()
    # Modest baseline so the UI always shows an intent-aware score.
    base = 12 + (profile.latency_weight + profile.efficiency_weight) // 2
    score = int(max(0, min(100, base)))
    return Decision(
        title="System Healthy",
        severity="normal",
        confidence=80,
        priority_score=score,
        explanation=(
            "No critical resource pressure detected.\n"
            f"Active intent: {profile.name} — {profile.description}"
        ),
        action=engine.intent.guidance_text(),
        timestamp=utc_now(),
    )


def tick_cluster(
    cluster: ClusterViewState,
    snapshot: TelemetrySnapshot,
) -> ClusterSnapshot | None:
    """Publish local + demo peer telemetry and aggregate the cluster view."""

    if cluster.registry is None or cluster.publisher is None:
        return None
    local = cluster.local_agent.from_telemetry(snapshot)
    cluster.publisher.publish(local)
    for peer in cluster.demo_peers:
        cluster.publisher.publish(peer.next_snapshot())
    cluster.registry.ingest()
    report = aggregate(cluster.registry)
    cluster.last = report
    cluster.online_ids = frozenset(
        n.node_id for n in report.nodes if cluster.registry.is_online(n.node_id)
    )
    return report


def build_frame(
    system: SystemSnapshot,
    report: DecisionReport,
    *,
    show_help: bool,
    show_developer: bool,
    audit: AuditLogger,
    engine: DecisionEngine,
    research: ResearchViewState,
    plugin_records: list[PluginRecord],
    plugins_verified: int,
    plugins_unsafe: int,
    observatory: ObservatoryViewState,
    explainability: ExplainabilityViewState | None = None,
    predictive: PredictiveViewState | None = None,
    cluster: ClusterViewState | None = None,
    orchestrator: OrchestratorViewState | None = None,
    cognition: CognitiveViewState | None = None,
    multi_agent: MultiAgentViewState | None = None,
    horizon: HorizonViewState | None = None,
    genesis: GenesisViewState | None = None,
    sentinel: SentinelViewState | None = None,
    fabric: FabricViewState | None = None,
    infinity: InfinityViewState | None = None,
    resource_graph: ResourceGraphViewState | None = None,
    graph_reasoning: GraphReasoningViewState | None = None,
    digital_twin: DigitalTwinViewState | None = None,
    research_intel: ResearchIntelligenceViewState | None = None,
    op_memory: OperationalMemoryViewState | None = None,
    causal_knowledge: CausalKnowledgeViewState | None = None,
    consensus: ConsensusViewState | None = None,
    research_lab: ResearchLabViewState | None = None,
    federation: FederationViewState | None = None,
    topology: TopologyViewState | None = None,
    scheduler: SchedulerViewState | None = None,
    marketplace: MarketplaceViewState | None = None,
) -> DashboardFrame:
    """Map pipeline output into a DashboardFrame for the renderer."""

    snapshot = report.snapshot
    processes = tuple(
        ProcessRow(
            pid=proc.pid,
            name=proc.name,
            cpu_percent=proc.cpu_percent,
            memory_percent=proc.memory_percent,
        )
        for proc in system.processes[:5]
    )

    decision = report.decision
    display_decision: Decision
    if decision is None or (
        decision.severity == "normal" and decision.priority_score < 30
    ):
        healthy = _healthy_decision(engine)
        if decision is not None and decision.priority_score >= healthy.priority_score:
            healthy = Decision(
                title="System Healthy",
                severity="normal",
                confidence=decision.confidence,
                priority_score=decision.priority_score,
                explanation=decision.explanation or healthy.explanation,
                action=engine.intent.guidance_text(decision),
                timestamp=decision.timestamp,
            )
        display_decision = healthy
        decision_title = healthy.title
        decision_score = healthy.priority_score
        decision_status = "Healthy"
        decision_style = "green"
        explanation = healthy.explanation
    else:
        display_decision = decision
        decision_title = decision.title
        decision_score = decision.priority_score
        decision_status = decision.severity.upper()
        decision_style = {
            "critical": "red",
            "warning": "yellow",
            "normal": "green",
        }.get(decision.severity, "cyan")
        explanation = decision.explanation

    if report.rejected and not report.approved:
        safety_status, safety_style = "BLOCKED", "red"
    elif report.rejected and report.approved:
        safety_status, safety_style = "MIXED", "yellow"
    elif report.approved:
        safety_status, safety_style = "APPROVED", "green"
    else:
        safety_status, safety_style = "APPROVED", "green"

    try:
        uptime = time.time() - psutil.boot_time()
        uptime_text = format_uptime(uptime)
    except (OSError, PermissionError):
        uptime_text = "n/a"

    profile = engine.intent.current_intent()
    window = observatory.recorder.get_last_seconds(60)
    if not window:
        window = observatory.recorder.points()
    cpu_spark = sparkline(observatory.recorder.series("cpu", window), width=40)
    mem_spark = sparkline(observatory.recorder.series("memory", window), width=40)
    disk_spark = sparkline(observatory.recorder.series("disk", window), width=40)
    detail_values = observatory.recorder.window(
        offset=observatory.history_offset,
        width=42,
        metric=observatory.metric,
    )
    detail_graph = render_ascii_graph(
        detail_values,
        width=42,
        height=4,
        label=observatory.metric.upper(),
    )
    observations = derive_observations(
        observatory.recorder.points(),
        observatory.timeline.recent(20),
    )

    show_explain = bool(explainability and explainability.visible)
    show_predict = bool(predictive and predictive.visible)
    show_cluster = bool(cluster and cluster.visible)
    show_orchestrator = bool(orchestrator and orchestrator.visible)
    show_cognitive = bool(cognition and cognition.visible)
    show_multi_agent = bool(multi_agent and multi_agent.visible)
    show_horizon = bool(horizon and horizon.visible)
    show_genesis = bool(genesis and genesis.visible)
    show_sentinel = bool(sentinel and sentinel.visible)
    show_fabric = bool(fabric and fabric.visible)
    show_infinity = bool(infinity and infinity.visible)
    show_resource_graph = bool(resource_graph and resource_graph.visible)
    show_graph_reasoning = bool(graph_reasoning and graph_reasoning.visible)
    show_digital_twin = bool(digital_twin and digital_twin.visible)
    show_research_intel = bool(research_intel and research_intel.visible)
    show_op_memory = bool(op_memory and op_memory.visible)
    show_causal_knowledge = bool(causal_knowledge and causal_knowledge.visible)
    show_consensus = bool(consensus and consensus.visible)
    show_research_lab = bool(research_lab and research_lab.visible)
    show_federation = bool(federation and federation.visible)
    show_topology = bool(topology and topology.visible)
    show_scheduler = bool(scheduler and scheduler.visible)
    show_marketplace = bool(marketplace and marketplace.visible)
    overlay = (
        show_explain
        or show_predict
        or show_cluster
        or show_orchestrator
        or show_cognitive
        or show_multi_agent
        or show_horizon
        or show_genesis
        or show_sentinel
        or show_fabric
        or show_infinity
        or show_resource_graph
        or show_graph_reasoning
        or show_digital_twin
        or show_research_intel
        or show_op_memory
        or show_causal_knowledge
        or show_consensus
        or show_research_lab
        or show_federation
        or show_topology
        or show_scheduler
        or show_marketplace
    )
    ai_explanation: Explanation | None = None
    if show_explain and explainability is not None:
        ai_explanation = explainability.engine.explain(
            display_decision,
            snapshot,
            history=observatory.recorder.points(),
            intent=profile,
            processes=system.processes,
        )
        explainability.last = ai_explanation

    predictive_report: PredictiveReport | None = None
    if show_predict and predictive is not None:
        points = observatory.recorder.points()
        if points:
            predictive_report = predictive.engine.predict(points)
            predictive.last = predictive_report

    cluster_snapshot: ClusterSnapshot | None = None
    cluster_online: frozenset[str] = frozenset()
    if cluster is not None:
        cluster_snapshot = cluster.last
        cluster_online = cluster.online_ids

    execution_plan: ExecutionPlan | None = None
    selected_workload: WorkloadProfile | None = None
    if orchestrator is not None:
        selected_workload = orchestrator.workload
        if show_orchestrator and cluster is not None and cluster.last is not None:
            execution_plan = orchestrator.planner.plan(
                orchestrator.workload,
                cluster.last.nodes,
                online_ids=cluster.online_ids,
            )
            orchestrator.last = execution_plan

    cognitive_report: CognitiveReport | None = None
    if show_cognitive and cognition is not None:
        cognitive_report = cognition.runtime.reason(
            snapshot,
            profile,
            history=observatory.recorder.points(),
        )
        cognition.last = cognitive_report

    agentic_report: AgenticReport | None = None
    if show_multi_agent and multi_agent is not None:
        agentic_report = multi_agent.runtime.deliberate_sync(
            snapshot,
            profile,
            history=observatory.recorder.points(),
            cluster=cluster.last if cluster is not None else None,
        )
        multi_agent.last = agentic_report

    horizon_report: HorizonReport | None = None
    if show_horizon and horizon is not None:
        horizon_report = horizon.runtime.observe()
        horizon.last = horizon_report

    genesis_report: GenesisReport | None = None
    if show_genesis and genesis is not None:
        if genesis.last is None:
            genesis.last = genesis.runtime.research(experiment_runs=12)
        genesis_report = genesis.last

    sentinel_report: SentinelReport | None = None
    if show_sentinel and sentinel is not None:
        cluster_avg = None
        if cluster is not None and cluster.last is not None:
            cluster_avg = cluster.last.average_cpu
        sentinel_report = sentinel.runtime.observe(
            snapshot,
            history=observatory.recorder.points(),
            cluster_avg_cpu=cluster_avg,
        )
        sentinel.last = sentinel_report

    fabric_report: FabricReport | None = None
    if show_fabric and fabric is not None:
        fabric_report = fabric.runtime.observe()
        fabric.last = fabric_report

    infinity_report: InfinityReport | None = None
    if show_infinity and infinity is not None:
        if infinity.last is None:
            infinity.last = infinity.runtime.observe(snapshot)
        infinity_report = infinity.last

    resource_graph_report: ResourceGraph | None = None
    if show_resource_graph and resource_graph is not None:
        resource_graph.last = build_resource_graph(
            system,
            intent_name=profile.name,
        )
        resource_graph_report = resource_graph.last

    graph_reasoning_report: VerifiedExplanation | None = None
    graph_reasoning_observation: Observation | None = None
    if show_graph_reasoning and graph_reasoning is not None:
        host_graph = build_resource_graph(system, intent_name=profile.name)
        obs = observation_from_metrics(
            cpu=snapshot.cpu_percent,
            memory=snapshot.memory_percent,
            disk=snapshot.disk_percent,
        )
        graph_reasoning.observation = obs
        graph_reasoning.last = graph_reason(
            host_graph,
            obs,
            history=observatory.recorder.points(),
        )
        graph_reasoning_report = graph_reasoning.last
        graph_reasoning_observation = obs

    digital_twin_report: DigitalTwinReport | None = None
    digital_twin_scenario: SimulationScenario | None = None
    digital_twin_baseline: TwinSnapshot | None = None
    if show_digital_twin and digital_twin is not None:
        host_graph = build_resource_graph(system, intent_name=profile.name)
        twin_snap = create_snapshot(
            host_graph,
            snapshot,
            intent=profile.name,
        )
        kinds = (
            "CPU_OVERLOAD",
            "MEMORY_PRESSURE",
            "BATTERY_LOW",
            "DISK_SATURATION",
            "NODE_OFFLINE",
        )
        idx = digital_twin.scenario_index % len(kinds)
        scene = builtin_scenario(kinds[idx])
        digital_twin.scenario = scene
        digital_twin.baseline = twin_snap
        digital_twin.last = DigitalTwinSimulator().run(twin_snap, scene)
        digital_twin_report = digital_twin.last
        digital_twin_scenario = scene
        digital_twin_baseline = twin_snap

    research_intel_report: SystemResearchReport | None = None
    research_intel_view = "daily"
    if show_research_intel and research_intel is not None:
        research_intel_view = research_intel.view
        kind_map = {
            "daily": "daily",
            "weekly": "weekly",
            "bottlenecks": "research_summary",
            "discoveries": "research_summary",
            "simulation": "simulation_summary",
        }
        host_graph = build_resource_graph(system, intent_name=profile.name)
        history = observatory.recorder.points()
        research_intel.last = ResearchIntelligenceEngine(min_evidence=3).generate(
            graph=host_graph,
            history=history,
            context=profile.name,
            verified_reasoning=(
                ("Telemetry and resource graph evidence reviewed.",) if history else ()
            ),
            twin_summaries=(
                (f"Digital twin scenario available: {digital_twin.scenario.name}",)
                if digital_twin is not None and digital_twin.scenario is not None
                else ()
            ),
            simulation_agreement=90.0 if history else None,
            session_count=max(len(history), 0) or None,
            kind=kind_map.get(research_intel_view, "research_summary"),  # type: ignore[arg-type]
        )
        research_intel_report = research_intel.last

    op_memory_verified: tuple[object, ...] = ()
    op_memory_patterns: tuple[object, ...] = ()
    op_memory_view = "verified"
    if show_op_memory and op_memory is not None:
        op_memory.ensure_seeded()
        op_memory_view = op_memory.view
        op_memory_verified = tuple(op_memory.engine.store.list_verified(limit=50))
        query = MemoryQuery(context="system", intent="operational", metric="cpu")
        if op_memory_view == "related":
            op_memory_patterns = op_memory.engine.similar_patterns(query, limit=10)
        elif op_memory_verified:
            top = op_memory_verified[0]
            op_memory_patterns = op_memory.engine.similar_patterns(
                MemoryQuery(context=top.title, metric=""),
                limit=10,
            )
        else:
            op_memory_patterns = ()

    causal_knowledge_graph: CausalKnowledgeGraph | None = None
    causal_knowledge_view = "causal"
    if show_causal_knowledge and causal_knowledge is not None:
        causal_knowledge_view = causal_knowledge.view
        # Seed operational memory for verified pattern edges (read-only).
        if op_memory is not None:
            op_memory.ensure_seeded()
            memories = tuple(op_memory.engine.store.list_verified(limit=50))
        else:
            memories = MemoryEngine().seed_defaults()
        # Resource graph from current host snapshot when available.
        rg = None
        try:
            rg = build_resource_graph(system, intent_name=profile.name)
        except Exception:
            rg = None
        twin_summaries: tuple[str, ...] = ()
        if digital_twin is not None and digital_twin.scenario is not None:
            twin_summaries = (f"Digital twin scenario: {digital_twin.scenario.name}",)
        causal_knowledge.last = build_knowledge_graph(
            resource_graph=rg,
            memories=memories,
            twin_summaries=twin_summaries,
            context_label=profile.name,
        )
        causal_knowledge_graph = causal_knowledge.last

    consensus_decision: ConsensusDecision | None = None
    consensus_findings: tuple = ()
    consensus_conflicts: tuple = ()
    consensus_bus_events: tuple = ()
    consensus_view = "consensus"
    if show_consensus and consensus is not None:
        consensus_view = consensus.view
        snap = TelemetrySnapshot.from_system_snapshot(system)
        history = tuple(observatory.recorder.points())
        decision = consensus.engine.deliberate(
            DeliberationContext(
                snapshot=snap,
                intent=profile,
                history=history,
            )
        )
        consensus.last = decision
        consensus.findings = consensus.engine.last_findings
        consensus.conflicts = consensus.engine.last_conflicts
        consensus.bus_events = consensus.engine.bus.history(limit=40)
        consensus_decision = decision
        consensus_findings = consensus.findings
        consensus_conflicts = consensus.conflicts
        consensus_bus_events = consensus.bus_events

    research_lab_questions: tuple = ()
    research_lab_experiments: tuple = ()
    research_lab_results: tuple = ()
    research_lab_verified: tuple = ()
    research_lab_rejected: tuple = ()
    research_lab_journal: tuple = ()
    research_lab_view = "discoveries"
    if show_research_lab and research_lab is not None:
        research_lab_view = research_lab.view
        if not research_lab.seeded:
            if op_memory is not None:
                op_memory.ensure_seeded()
                memories = tuple(op_memory.engine.store.list_verified(limit=50))
            else:
                memories = MemoryEngine().seed_defaults()
            try:
                rg = build_resource_graph(system, intent_name=profile.name)
                snap = TelemetrySnapshot.from_system_snapshot(system)
                twin = create_snapshot(rg, snap, intent=profile.name)
                research_lab.engine.run(
                    twin,
                    memories=memories,
                    evidence_texts=(profile.name, profile.description),
                    iterations=8,
                    limit_questions=3,
                )
            except Exception:
                pass
            research_lab.seeded = True
        research_lab_questions = research_lab.engine.last_questions
        research_lab_experiments = research_lab.engine.last_experiments
        research_lab_results = research_lab.engine.last_results
        research_lab_verified = research_lab.engine.store.list_verified(limit=20)
        research_lab_rejected = research_lab.engine.store.list_rejected(limit=20)
        research_lab_journal = research_lab.engine.journal.entries(limit=40)

    marketplace_catalog: tuple = ()
    marketplace_installed: tuple = ()
    marketplace_updates: tuple = ()
    marketplace_selected = None
    marketplace_view = "marketplace"
    if show_marketplace and marketplace is not None:
        marketplace_view = marketplace.view
        if not marketplace.seeded:
            seed_demo_marketplace(marketplace.registry)
            marketplace.seeded = True
        marketplace.catalog = marketplace.registry.list_plugins()
        marketplace_catalog = marketplace.catalog
        marketplace_installed = marketplace.registry.list_installed()
        marketplace_updates = MarketplaceUpdater(marketplace.registry).check_all()
        marketplace_selected = marketplace.registry.get_plugin("nvidia-intelligence")

    federation_registry = None
    federation_heartbeats: tuple = ()
    federation_view = "nodes"
    federation_last_sync = None
    if show_federation and federation is not None:
        federation_view = federation.view
        if not federation.seeded:
            snap = TelemetrySnapshot.from_system_snapshot(system)
            beats, sync = seed_demo_federation(
                federation.registry,
                local_telemetry=snap,
            )
            federation.heartbeats = beats
            federation.last_sync = sync
            federation.seeded = True
        federation.registry.refresh_statuses()
        federation_registry = federation.registry.view()
        federation_heartbeats = federation.heartbeats
        federation_last_sync = federation.last_sync

    topology_graph = None
    topology_view = "tree"
    if show_topology and topology is not None:
        topology_view = topology.view
        if not topology.seeded:
            # Prefer live federation registry when available; else seed demos.
            if federation is not None:
                if not federation.seeded:
                    from aetheros.federation import seed_demo_federation

                    snap = TelemetrySnapshot.from_system_snapshot(system)
                    seed_demo_federation(federation.registry, local_telemetry=snap)
                    federation.seeded = True
                federation.registry.refresh_statuses()
                topology.graph = build_topology(
                    federation.registry,
                    metadata=demo_topology_metadata(),
                )
            else:
                from aetheros.federation import FederationRegistry, seed_demo_federation

                reg = FederationRegistry()
                seed_demo_federation(reg)
                topology.graph = build_topology(reg, metadata=demo_topology_metadata())
            topology.seeded = True
        topology_graph = topology.graph

    scheduler_workload = None
    scheduler_result = None
    scheduler_view = "summary"
    if show_scheduler and scheduler is not None:
        scheduler_view = scheduler.view
        if not scheduler.seeded:
            wl = demo_workload()
            nodes = demo_nodes()
            constraints = (
                ScheduleConstraint(kind="REQUIRE_GPU", value=1.0),
                ScheduleConstraint(kind="AVOID_OVERLOAD", value=85.0),
            )
            scheduler.workload = wl
            scheduler.result = run_scheduler(wl, nodes, constraints=constraints)
            scheduler.seeded = True
        scheduler_workload = scheduler.workload
        scheduler_result = scheduler.result

    return DashboardFrame(
        version=__version__,
        cpu_percent=snapshot.cpu_percent,
        memory_percent=snapshot.memory_percent,
        disk_percent=snapshot.disk_percent,
        battery_text=format_battery(system),
        uptime_text=uptime_text,
        processes=processes,
        decision_title=decision_title,
        decision_score=decision_score,
        decision_status=decision_status,
        decision_explanation=explanation,
        decision_style=decision_style,
        safety_status=safety_status,
        safety_style=safety_style,
        approved_count=len(report.approved),
        blocked_count=len(report.rejected),
        cooldown_seconds=max_cooldown_seconds(engine),
        last_audit_summary=format_audit_summary(audit.latest()),
        show_help=show_help,
        show_developer=show_developer,
        intent_name=profile.name,
        intent_description=profile.description,
        intent_cpu=profile.cpu_weight,
        intent_memory=profile.memory_weight,
        intent_disk=profile.disk_weight,
        intent_latency=profile.latency_weight,
        intent_efficiency=profile.efficiency_weight,
        research_status=research.status,
        research_strategies=research.strategies_generated,
        research_best_score=research.best_score,
        research_winner=research.winning_strategy,
        research_improvement=research.estimated_improvement,
        research_report_path=research.report_path,
        plugin_rows=plugin_console_rows(plugin_records),
        plugins_verified=plugins_verified,
        plugins_unsafe=plugins_unsafe,
        show_observatory=observatory.visible and not overlay,
        observatory_metric=observatory.metric,
        observatory_cpu_spark=cpu_spark,
        observatory_memory_spark=mem_spark,
        observatory_disk_spark=disk_spark,
        observatory_detail_graph=detail_graph,
        observatory_events=observatory.timeline.visible(limit=8),
        observatory_observations=observations,
        observatory_offset=observatory.history_offset,
        observatory_samples=len(observatory.recorder),
        observatory_capacity=observatory.recorder.capacity,
        observatory_window_label="Last 60 Seconds",
        show_explainability=show_explain
        and not show_cognitive
        and not show_multi_agent
        and not show_horizon
        and not show_genesis
        and not show_sentinel
        and not show_fabric
        and not show_infinity
        and not show_resource_graph
        and not show_graph_reasoning
        and not show_digital_twin
        and not show_research_intel
        and not show_op_memory
        and not show_causal_knowledge
        and not show_consensus
        and not show_research_lab
        and not show_federation
        and not show_topology
        and not show_scheduler
        and not show_marketplace,
        explanation=ai_explanation,
        show_predictive=show_predict
        and not show_cognitive
        and not show_multi_agent
        and not show_horizon
        and not show_genesis
        and not show_sentinel
        and not show_fabric
        and not show_infinity
        and not show_resource_graph
        and not show_graph_reasoning
        and not show_digital_twin
        and not show_research_intel
        and not show_op_memory
        and not show_causal_knowledge
        and not show_consensus
        and not show_research_lab
        and not show_federation
        and not show_topology
        and not show_scheduler
        and not show_marketplace,
        predictive_report=predictive_report,
        show_cluster=show_cluster
        and not show_cognitive
        and not show_multi_agent
        and not show_horizon
        and not show_genesis
        and not show_sentinel
        and not show_fabric
        and not show_infinity
        and not show_resource_graph
        and not show_graph_reasoning
        and not show_digital_twin
        and not show_research_intel
        and not show_op_memory
        and not show_causal_knowledge
        and not show_consensus
        and not show_research_lab
        and not show_federation
        and not show_topology
        and not show_scheduler
        and not show_marketplace,
        cluster_snapshot=cluster_snapshot,
        cluster_online_ids=cluster_online,
        show_orchestrator=show_orchestrator
        and not show_cognitive
        and not show_multi_agent
        and not show_horizon
        and not show_genesis
        and not show_sentinel
        and not show_fabric
        and not show_infinity
        and not show_resource_graph
        and not show_graph_reasoning
        and not show_digital_twin
        and not show_research_intel
        and not show_op_memory
        and not show_causal_knowledge
        and not show_consensus
        and not show_research_lab
        and not show_federation
        and not show_topology
        and not show_scheduler
        and not show_marketplace,
        execution_plan=execution_plan,
        selected_workload=selected_workload,
        show_cognitive=show_cognitive
        and not show_multi_agent
        and not show_horizon
        and not show_genesis
        and not show_sentinel
        and not show_fabric
        and not show_infinity
        and not show_resource_graph
        and not show_graph_reasoning
        and not show_digital_twin
        and not show_research_intel
        and not show_op_memory
        and not show_causal_knowledge
        and not show_consensus
        and not show_research_lab
        and not show_federation
        and not show_topology
        and not show_scheduler
        and not show_marketplace,
        cognitive_report=cognitive_report,
        show_multi_agent=show_multi_agent
        and not show_horizon
        and not show_genesis
        and not show_sentinel
        and not show_fabric
        and not show_infinity
        and not show_resource_graph
        and not show_graph_reasoning
        and not show_digital_twin
        and not show_research_intel
        and not show_op_memory
        and not show_causal_knowledge
        and not show_consensus
        and not show_research_lab
        and not show_federation
        and not show_topology
        and not show_scheduler
        and not show_marketplace,
        agentic_report=agentic_report,
        show_horizon=show_horizon
        and not show_genesis
        and not show_sentinel
        and not show_fabric
        and not show_infinity
        and not show_resource_graph
        and not show_graph_reasoning
        and not show_digital_twin
        and not show_research_intel
        and not show_op_memory
        and not show_causal_knowledge
        and not show_consensus
        and not show_research_lab
        and not show_federation
        and not show_topology
        and not show_scheduler
        and not show_marketplace,
        horizon_report=horizon_report,
        show_genesis=show_genesis
        and not show_sentinel
        and not show_fabric
        and not show_infinity
        and not show_resource_graph
        and not show_graph_reasoning
        and not show_digital_twin
        and not show_research_intel
        and not show_op_memory
        and not show_causal_knowledge
        and not show_consensus
        and not show_research_lab
        and not show_federation
        and not show_topology
        and not show_scheduler
        and not show_marketplace,
        genesis_report=genesis_report,
        show_sentinel=show_sentinel
        and not show_fabric
        and not show_infinity
        and not show_resource_graph
        and not show_graph_reasoning
        and not show_digital_twin
        and not show_research_intel
        and not show_op_memory
        and not show_causal_knowledge
        and not show_consensus
        and not show_research_lab
        and not show_federation
        and not show_topology
        and not show_scheduler
        and not show_marketplace,
        sentinel_report=sentinel_report,
        show_fabric=show_fabric
        and not show_infinity
        and not show_resource_graph
        and not show_graph_reasoning
        and not show_digital_twin
        and not show_research_intel
        and not show_op_memory
        and not show_causal_knowledge
        and not show_consensus
        and not show_research_lab
        and not show_federation
        and not show_topology
        and not show_scheduler
        and not show_marketplace,
        fabric_report=fabric_report,
        show_infinity=show_infinity
        and not show_resource_graph
        and not show_graph_reasoning
        and not show_digital_twin
        and not show_research_intel
        and not show_op_memory
        and not show_causal_knowledge
        and not show_consensus
        and not show_research_lab
        and not show_federation
        and not show_topology
        and not show_scheduler
        and not show_marketplace,
        infinity_report=infinity_report,
        show_resource_graph=show_resource_graph
        and not show_graph_reasoning
        and not show_digital_twin
        and not show_research_intel
        and not show_op_memory
        and not show_causal_knowledge
        and not show_consensus
        and not show_research_lab
        and not show_federation
        and not show_topology
        and not show_scheduler
        and not show_marketplace,
        resource_graph=resource_graph_report,
        show_graph_reasoning=show_graph_reasoning
        and not show_digital_twin
        and not show_research_intel
        and not show_op_memory
        and not show_causal_knowledge
        and not show_consensus
        and not show_research_lab
        and not show_federation
        and not show_topology
        and not show_scheduler
        and not show_marketplace,
        graph_reasoning=graph_reasoning_report,
        graph_reasoning_observation=graph_reasoning_observation,
        show_digital_twin=show_digital_twin
        and not show_research_intel
        and not show_op_memory
        and not show_causal_knowledge
        and not show_consensus
        and not show_research_lab
        and not show_federation
        and not show_topology
        and not show_scheduler
        and not show_marketplace,
        digital_twin_report=digital_twin_report,
        digital_twin_scenario=digital_twin_scenario,
        digital_twin_baseline=digital_twin_baseline,
        show_research_intel=show_research_intel
        and not show_op_memory
        and not show_causal_knowledge
        and not show_consensus
        and not show_research_lab
        and not show_federation
        and not show_topology
        and not show_scheduler
        and not show_marketplace,
        research_intel_report=research_intel_report,
        research_intel_view=research_intel_view,
        show_op_memory=show_op_memory
        and not show_causal_knowledge
        and not show_consensus
        and not show_research_lab
        and not show_federation
        and not show_topology
        and not show_scheduler
        and not show_marketplace,
        op_memory_verified=op_memory_verified,
        op_memory_patterns=op_memory_patterns,
        op_memory_view=op_memory_view,
        show_causal_knowledge=show_causal_knowledge
        and not show_consensus
        and not show_research_lab
        and not show_federation
        and not show_topology
        and not show_scheduler
        and not show_marketplace,
        causal_knowledge_graph=causal_knowledge_graph,
        causal_knowledge_view=causal_knowledge_view,
        show_consensus=show_consensus
        and not show_research_lab
        and not show_federation
        and not show_topology
        and not show_scheduler
        and not show_marketplace,
        consensus_decision=consensus_decision,
        consensus_findings=consensus_findings,
        consensus_conflicts=consensus_conflicts,
        consensus_bus_events=consensus_bus_events,
        consensus_view=consensus_view,
        show_research_lab=show_research_lab
        and not show_federation
        and not show_topology
        and not show_scheduler
        and not show_marketplace,
        research_lab_questions=research_lab_questions,
        research_lab_experiments=research_lab_experiments,
        research_lab_results=research_lab_results,
        research_lab_verified=research_lab_verified,
        research_lab_rejected=research_lab_rejected,
        research_lab_journal=research_lab_journal,
        research_lab_view=research_lab_view,
        show_federation=show_federation
        and not show_topology
        and not show_scheduler
        and not show_marketplace,
        show_topology=show_topology and not show_scheduler and not show_marketplace,
        topology_graph=topology_graph,
        topology_view=topology_view,
        federation_registry=federation_registry,
        federation_heartbeats=federation_heartbeats,
        federation_view=federation_view,
        federation_last_sync=federation_last_sync,
        show_scheduler=show_scheduler and not show_marketplace,
        scheduler_workload=scheduler_workload,
        scheduler_result=scheduler_result,
        scheduler_view=scheduler_view,
        show_marketplace=show_marketplace,
        marketplace_catalog=marketplace_catalog,
        marketplace_installed=marketplace_installed,
        marketplace_updates=marketplace_updates,
        marketplace_selected=marketplace_selected,
        marketplace_view=marketplace_view,
    )


def apply_research_result(
    state: ResearchViewState,
    report: ResearchReport,
) -> ResearchViewState:
    """Update research UI state from a completed ResearchReport."""

    if report.winner is None:
        state.status = "Complete"
        state.strategies_generated = len(report.candidates)
        state.winning_strategy = "None"
        state.estimated_improvement = "—"
        state.report_path = report.report_path or "—"
        return state

    winner = report.winner
    cpu_delta = winner.strategy.expected_cpu_delta
    improvement = abs(cpu_delta) if cpu_delta < 0 else cpu_delta
    state.status = "Complete"
    state.strategies_generated = len(report.candidates)
    state.best_score = winner.rank_score
    state.winning_strategy = winner.strategy.title
    state.estimated_improvement = f"+{improvement:.0f}% CPU (est.)"
    state.report_path = report.report_path or "—"
    return state


def poll_key(timeout: float = 0.05) -> str | None:
    """Non-blocking key read, including ←/→ escape sequences."""

    if not sys.stdin.isatty():
        time.sleep(timeout)
        return None
    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    if not ready:
        return None
    char = sys.stdin.read(1)
    if char != "\x1b":
        return char
    # Escape sequence — try to read CSI arrow keys.
    rest = ""
    if select.select([sys.stdin], [], [], 0.02)[0]:
        rest += sys.stdin.read(1)
    if rest == "[" and select.select([sys.stdin], [], [], 0.02)[0]:
        rest += sys.stdin.read(1)
    if rest == "[D":
        return "LEFT"
    if rest == "[C":
        return "RIGHT"
    if rest == "[A":
        return "UP"
    if rest == "[B":
        return "DOWN"
    return "ESC"


def wait_for_interval_or_key(seconds: float) -> str | None:
    """Wait up to `seconds`, returning early if a key is pressed."""

    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        key = poll_key(timeout=min(0.05, max(0.0, deadline - time.monotonic())))
        if key:
            return key
    return None


def collect_pipeline(
    collector: TelemetryCollector,
    engine: DecisionEngine,
) -> tuple[SystemSnapshot, DecisionReport]:
    """Take one telemetry sample and run the decision pipeline."""

    system = collector.collect()
    snapshot = TelemetrySnapshot.from_system_snapshot(system)
    report = engine.evaluate_report(snapshot, record=False)
    return system, report


def ingest_observatory_sample(
    observatory: ObservatoryViewState,
    snapshot: TelemetrySnapshot,
    intent_name: str,
    report: DecisionReport | None = None,
) -> None:
    """Record a sample, detect events, and persist them."""

    previous = observatory.recorder.latest()
    current = observatory.recorder.record_telemetry(snapshot, intent_name)
    history = observatory.recorder.points()
    events = detect_events(history, current, previous)
    if report is not None:
        for rec, result in report.rejected:
            key = f"{rec.title}:{result.reason}"
            if key in observatory.seen_safety_blocks:
                continue
            observatory.seen_safety_blocks.add(key)
            events.append(safety_blocked_event(title=rec.title, reason=result.reason))
    for event in events:
        observatory.recorder.record_event(event)
        if observatory.history_offset == 0:
            observatory.timeline.add(event)
        else:
            observatory.timeline.append_keep_scroll(event)


def run_dashboard(
    *,
    db_path: Path,
    intent_db: Path,
    reports_dir: Path,
    interval: float = 1.0,
) -> None:
    """Run the live operator dashboard until the user presses Q."""

    audit = AuditLogger(db_path)
    intent = IntentEngine(storage=IntentStorage(intent_db))
    engine = DecisionEngine(
        safety=SafetyValidator(
            cooldown=CooldownManager(),
            audit=audit,
        ),
        intent=intent,
    )
    research_engine = ResearchEngine(
        learning=LearningEngine(audit=audit),
        reports_dir=reports_dir,
    )
    research_state = ResearchViewState()
    observatory = ObservatoryViewState(visible=True)
    explainability = ExplainabilityViewState(visible=False)
    predictive = PredictiveViewState(visible=False)
    cluster = ClusterViewState(visible=False)
    cluster.ensure(Path("data/cluster.db"))
    orchestrator = OrchestratorViewState(visible=False)
    cognition = CognitiveViewState(visible=False)
    multi_agent = MultiAgentViewState(visible=False)
    horizon_view = HorizonViewState(visible=False)
    genesis_view = GenesisViewState(visible=False)
    sentinel_view = SentinelViewState(visible=False)
    fabric_view = FabricViewState(visible=False)
    infinity_view = InfinityViewState(visible=False)
    resource_graph_view = ResourceGraphViewState(visible=False)
    graph_reasoning_view = GraphReasoningViewState(visible=False)
    digital_twin_view = DigitalTwinViewState(visible=False)
    research_intel_view = ResearchIntelligenceViewState(visible=False)
    op_memory_view = OperationalMemoryViewState(visible=False)
    causal_knowledge_view = CausalKnowledgeViewState(visible=False)
    consensus_view_state = ConsensusViewState(visible=False)
    research_lab_view_state = ResearchLabViewState(visible=False)
    federation_view_state = FederationViewState(visible=False)
    topology_view_state = TopologyViewState(visible=False)
    scheduler_view_state = SchedulerViewState(visible=False)
    marketplace_view_state = MarketplaceViewState(visible=False)
    core = AetherCore()
    core.registry.state_path = Path("data/plugin_state.json")
    core.bootstrap()
    collector = TelemetryCollector(process_limit=5)
    collector.collect()

    show_help = False
    show_developer = False
    system, report = collect_pipeline(collector, engine)
    ingest_observatory_sample(
        observatory,
        report.snapshot,
        engine.intent.current_intent().name,
        report,
    )
    tick_cluster(cluster, report.snapshot)
    core.api.telemetry.set_host_snapshot(
        {
            "cpu_percent": report.snapshot.cpu_percent,
            "memory_percent": report.snapshot.memory_percent,
            "battery_percent": report.snapshot.battery_percent,
        }
    )
    summary = core.registry.safety_summary()

    def make_frame() -> DashboardFrame:
        """Build the current dashboard frame."""

        return build_frame(
            system,
            report,
            show_help=show_help,
            show_developer=show_developer,
            audit=audit,
            engine=engine,
            research=research_state,
            plugin_records=core.registry.list_plugins(),
            plugins_verified=summary["verified"],
            plugins_unsafe=summary["unsafe"],
            observatory=observatory,
            explainability=explainability,
            predictive=predictive,
            cluster=cluster,
            orchestrator=orchestrator,
            cognition=cognition,
            multi_agent=multi_agent,
            horizon=horizon_view,
            genesis=genesis_view,
            sentinel=sentinel_view,
            fabric=fabric_view,
            infinity=infinity_view,
            resource_graph=resource_graph_view,
            graph_reasoning=graph_reasoning_view,
            digital_twin=digital_twin_view,
            research_intel=research_intel_view,
            op_memory=op_memory_view,
            causal_knowledge=causal_knowledge_view,
            consensus=consensus_view_state,
            research_lab=research_lab_view_state,
            federation=federation_view_state,
            topology=topology_view_state,
            scheduler=scheduler_view_state,
            marketplace=marketplace_view_state,
        )

    frame = make_frame()
    fd = sys.stdin.fileno() if sys.stdin.isatty() else None
    old_settings = termios.tcgetattr(fd) if fd is not None else None

    try:
        if fd is not None and old_settings is not None:
            tty.setcbreak(fd)
        with Live(render_frame(frame), refresh_per_second=8, screen=True) as live:
            while True:
                key = wait_for_interval_or_key(interval)
                if key is not None:
                    lowered = key.lower() if len(key) == 1 else key
                    if lowered == "q":
                        break
                    if key == "ESC" or lowered == "\x1b":
                        observatory.visible = False
                        explainability.visible = False
                        predictive.visible = False
                        cluster.visible = False
                        orchestrator.visible = False
                        cognition.visible = False
                        multi_agent.visible = False
                        horizon_view.visible = False
                        genesis_view.visible = False
                        sentinel_view.visible = False
                        fabric_view.visible = False
                        infinity_view.visible = False
                        resource_graph_view.visible = False
                        graph_reasoning_view.visible = False
                        digital_twin_view.visible = False
                        research_intel_view.visible = False
                        op_memory_view.visible = False
                        causal_knowledge_view.visible = False
                        consensus_view_state.visible = False
                        research_lab_view_state.visible = False
                        federation_view_state.visible = False
                        topology_view_state.visible = False
                        scheduler_view_state.visible = False
                        marketplace_view_state.visible = False
                        show_help = False
                        show_developer = False
                    elif key == "?" or lowered == "?":
                        show_help = not show_help
                        if show_help:
                            show_developer = False
                            observatory.visible = False
                            explainability.visible = False
                            predictive.visible = False
                            cluster.visible = False
                            orchestrator.visible = False
                            cognition.visible = False
                            multi_agent.visible = False
                            horizon_view.visible = False
                            genesis_view.visible = False
                            sentinel_view.visible = False
                            fabric_view.visible = False
                            infinity_view.visible = False
                            resource_graph_view.visible = False
                            graph_reasoning_view.visible = False
                            digital_twin_view.visible = False
                            research_intel_view.visible = False
                            op_memory_view.visible = False
                            causal_knowledge_view.visible = False
                            consensus_view_state.visible = False
                            research_lab_view_state.visible = False
                            federation_view_state.visible = False
                            topology_view_state.visible = False
                            scheduler_view_state.visible = False
                            marketplace_view_state.visible = False
                    elif lowered == "h":
                        horizon_view.visible = not horizon_view.visible
                        if horizon_view.visible:
                            show_help = False
                            show_developer = False
                            observatory.visible = False
                            explainability.visible = False
                            predictive.visible = False
                            cluster.visible = False
                            orchestrator.visible = False
                            cognition.visible = False
                            multi_agent.visible = False
                            genesis_view.visible = False
                            sentinel_view.visible = False
                            fabric_view.visible = False
                            infinity_view.visible = False
                            resource_graph_view.visible = False
                            graph_reasoning_view.visible = False
                            digital_twin_view.visible = False
                            research_intel_view.visible = False
                            op_memory_view.visible = False
                            causal_knowledge_view.visible = False
                            consensus_view_state.visible = False
                            research_lab_view_state.visible = False
                            federation_view_state.visible = False
                            topology_view_state.visible = False
                            scheduler_view_state.visible = False
                            marketplace_view_state.visible = False
                    elif lowered == "d":
                        show_developer = not show_developer
                        if show_developer:
                            show_help = False
                            observatory.visible = False
                            explainability.visible = False
                            predictive.visible = False
                            cluster.visible = False
                            orchestrator.visible = False
                            cognition.visible = False
                            multi_agent.visible = False
                            horizon_view.visible = False
                            genesis_view.visible = False
                            sentinel_view.visible = False
                            fabric_view.visible = False
                            infinity_view.visible = False
                            resource_graph_view.visible = False
                            graph_reasoning_view.visible = False
                            digital_twin_view.visible = False
                            research_intel_view.visible = False
                            op_memory_view.visible = False
                            causal_knowledge_view.visible = False
                            consensus_view_state.visible = False
                            research_lab_view_state.visible = False
                            federation_view_state.visible = False
                            topology_view_state.visible = False
                            scheduler_view_state.visible = False
                            marketplace_view_state.visible = False
                    elif lowered == "m":
                        multi_agent.visible = not multi_agent.visible
                        if multi_agent.visible:
                            show_help = False
                            show_developer = False
                            observatory.visible = False
                            explainability.visible = False
                            predictive.visible = False
                            cluster.visible = False
                            orchestrator.visible = False
                            cognition.visible = False
                            horizon_view.visible = False
                            genesis_view.visible = False
                            sentinel_view.visible = False
                            fabric_view.visible = False
                            infinity_view.visible = False
                            resource_graph_view.visible = False
                            graph_reasoning_view.visible = False
                            digital_twin_view.visible = False
                            research_intel_view.visible = False
                            op_memory_view.visible = False
                            causal_knowledge_view.visible = False
                            consensus_view_state.visible = False
                            research_lab_view_state.visible = False
                            federation_view_state.visible = False
                            topology_view_state.visible = False
                            scheduler_view_state.visible = False
                            marketplace_view_state.visible = False
                    elif lowered == "g":
                        genesis_view.visible = not genesis_view.visible
                        if genesis_view.visible:
                            show_help = False
                            show_developer = False
                            observatory.visible = False
                            explainability.visible = False
                            predictive.visible = False
                            cluster.visible = False
                            orchestrator.visible = False
                            cognition.visible = False
                            multi_agent.visible = False
                            horizon_view.visible = False
                            sentinel_view.visible = False
                            fabric_view.visible = False
                            infinity_view.visible = False
                            resource_graph_view.visible = False
                            graph_reasoning_view.visible = False
                            digital_twin_view.visible = False
                            research_intel_view.visible = False
                            op_memory_view.visible = False
                            causal_knowledge_view.visible = False
                            consensus_view_state.visible = False
                            research_lab_view_state.visible = False
                            federation_view_state.visible = False
                            topology_view_state.visible = False
                            scheduler_view_state.visible = False
                            marketplace_view_state.visible = False
                    elif lowered == "s":
                        sentinel_view.visible = not sentinel_view.visible
                        if sentinel_view.visible:
                            show_help = False
                            show_developer = False
                            observatory.visible = False
                            explainability.visible = False
                            predictive.visible = False
                            cluster.visible = False
                            orchestrator.visible = False
                            cognition.visible = False
                            multi_agent.visible = False
                            horizon_view.visible = False
                            genesis_view.visible = False
                            fabric_view.visible = False
                            infinity_view.visible = False
                            resource_graph_view.visible = False
                            graph_reasoning_view.visible = False
                            digital_twin_view.visible = False
                            research_intel_view.visible = False
                            op_memory_view.visible = False
                            causal_knowledge_view.visible = False
                            consensus_view_state.visible = False
                            research_lab_view_state.visible = False
                            federation_view_state.visible = False
                            topology_view_state.visible = False
                            scheduler_view_state.visible = False
                            marketplace_view_state.visible = False
                    elif lowered == "f":
                        fabric_view.visible = not fabric_view.visible
                        if fabric_view.visible:
                            show_help = False
                            show_developer = False
                            observatory.visible = False
                            explainability.visible = False
                            predictive.visible = False
                            cluster.visible = False
                            orchestrator.visible = False
                            cognition.visible = False
                            multi_agent.visible = False
                            horizon_view.visible = False
                            genesis_view.visible = False
                            sentinel_view.visible = False
                            infinity_view.visible = False
                            resource_graph_view.visible = False
                            graph_reasoning_view.visible = False
                            digital_twin_view.visible = False
                            research_intel_view.visible = False
                            op_memory_view.visible = False
                            causal_knowledge_view.visible = False
                            consensus_view_state.visible = False
                            research_lab_view_state.visible = False
                            federation_view_state.visible = False
                            topology_view_state.visible = False
                            scheduler_view_state.visible = False
                            marketplace_view_state.visible = False
                    elif lowered == "i":
                        infinity_view.visible = not infinity_view.visible
                        if infinity_view.visible:
                            infinity_view.last = None
                            show_help = False
                            show_developer = False
                            observatory.visible = False
                            explainability.visible = False
                            predictive.visible = False
                            cluster.visible = False
                            orchestrator.visible = False
                            cognition.visible = False
                            multi_agent.visible = False
                            horizon_view.visible = False
                            genesis_view.visible = False
                            sentinel_view.visible = False
                            fabric_view.visible = False
                            resource_graph_view.visible = False
                            graph_reasoning_view.visible = False
                            digital_twin_view.visible = False
                            research_intel_view.visible = False
                            op_memory_view.visible = False
                            causal_knowledge_view.visible = False
                            consensus_view_state.visible = False
                            research_lab_view_state.visible = False
                            federation_view_state.visible = False
                            topology_view_state.visible = False
                            scheduler_view_state.visible = False
                            marketplace_view_state.visible = False
                    elif lowered == "y":
                        resource_graph_view.visible = not resource_graph_view.visible
                        if resource_graph_view.visible:
                            show_help = False
                            show_developer = False
                            observatory.visible = False
                            explainability.visible = False
                            predictive.visible = False
                            cluster.visible = False
                            orchestrator.visible = False
                            cognition.visible = False
                            multi_agent.visible = False
                            horizon_view.visible = False
                            genesis_view.visible = False
                            sentinel_view.visible = False
                            fabric_view.visible = False
                            infinity_view.visible = False
                            graph_reasoning_view.visible = False
                            digital_twin_view.visible = False
                            research_intel_view.visible = False
                            op_memory_view.visible = False
                            causal_knowledge_view.visible = False
                            consensus_view_state.visible = False
                            research_lab_view_state.visible = False
                            federation_view_state.visible = False
                            topology_view_state.visible = False
                            scheduler_view_state.visible = False
                            marketplace_view_state.visible = False
                    elif lowered == "r":
                        graph_reasoning_view.visible = not graph_reasoning_view.visible
                        if graph_reasoning_view.visible:
                            show_help = False
                            show_developer = False
                            observatory.visible = False
                            explainability.visible = False
                            predictive.visible = False
                            cluster.visible = False
                            orchestrator.visible = False
                            cognition.visible = False
                            multi_agent.visible = False
                            horizon_view.visible = False
                            genesis_view.visible = False
                            sentinel_view.visible = False
                            fabric_view.visible = False
                            infinity_view.visible = False
                            resource_graph_view.visible = False
                            digital_twin_view.visible = False
                            research_intel_view.visible = False
                            op_memory_view.visible = False
                            causal_knowledge_view.visible = False
                            consensus_view_state.visible = False
                            research_lab_view_state.visible = False
                            federation_view_state.visible = False
                            topology_view_state.visible = False
                            scheduler_view_state.visible = False
                            marketplace_view_state.visible = False
                    elif lowered == "v":
                        digital_twin_view.visible = not digital_twin_view.visible
                        if digital_twin_view.visible:
                            show_help = False
                            show_developer = False
                            observatory.visible = False
                            explainability.visible = False
                            predictive.visible = False
                            cluster.visible = False
                            orchestrator.visible = False
                            cognition.visible = False
                            multi_agent.visible = False
                            horizon_view.visible = False
                            genesis_view.visible = False
                            sentinel_view.visible = False
                            fabric_view.visible = False
                            infinity_view.visible = False
                            resource_graph_view.visible = False
                            graph_reasoning_view.visible = False
                            research_intel_view.visible = False
                            op_memory_view.visible = False
                            causal_knowledge_view.visible = False
                            consensus_view_state.visible = False
                            research_lab_view_state.visible = False
                            federation_view_state.visible = False
                            topology_view_state.visible = False
                            scheduler_view_state.visible = False
                            marketplace_view_state.visible = False
                    elif lowered == "x":
                        research_intel_view.visible = not research_intel_view.visible
                        if research_intel_view.visible:
                            show_help = False
                            show_developer = False
                            observatory.visible = False
                            explainability.visible = False
                            predictive.visible = False
                            cluster.visible = False
                            orchestrator.visible = False
                            cognition.visible = False
                            multi_agent.visible = False
                            horizon_view.visible = False
                            genesis_view.visible = False
                            sentinel_view.visible = False
                            fabric_view.visible = False
                            infinity_view.visible = False
                            resource_graph_view.visible = False
                            graph_reasoning_view.visible = False
                            digital_twin_view.visible = False
                            op_memory_view.visible = False
                            causal_knowledge_view.visible = False
                            consensus_view_state.visible = False
                            research_lab_view_state.visible = False
                            federation_view_state.visible = False
                            topology_view_state.visible = False
                            scheduler_view_state.visible = False
                            marketplace_view_state.visible = False

                    elif lowered == "l":
                        op_memory_view.visible = not op_memory_view.visible
                        if op_memory_view.visible:
                            show_help = False
                            show_developer = False
                            observatory.visible = False
                            explainability.visible = False
                            predictive.visible = False
                            cluster.visible = False
                            orchestrator.visible = False
                            cognition.visible = False
                            multi_agent.visible = False
                            horizon_view.visible = False
                            genesis_view.visible = False
                            sentinel_view.visible = False
                            fabric_view.visible = False
                            infinity_view.visible = False
                            resource_graph_view.visible = False
                            graph_reasoning_view.visible = False
                            digital_twin_view.visible = False
                            research_intel_view.visible = False
                            causal_knowledge_view.visible = False
                            consensus_view_state.visible = False
                            research_lab_view_state.visible = False
                            federation_view_state.visible = False
                            topology_view_state.visible = False
                            scheduler_view_state.visible = False
                            marketplace_view_state.visible = False

                    elif lowered == "n":
                        causal_knowledge_view.visible = (
                            not causal_knowledge_view.visible
                        )
                        if causal_knowledge_view.visible:
                            show_help = False
                            show_developer = False
                            observatory.visible = False
                            explainability.visible = False
                            predictive.visible = False
                            cluster.visible = False
                            orchestrator.visible = False
                            cognition.visible = False
                            multi_agent.visible = False
                            horizon_view.visible = False
                            genesis_view.visible = False
                            sentinel_view.visible = False
                            fabric_view.visible = False
                            infinity_view.visible = False
                            resource_graph_view.visible = False
                            graph_reasoning_view.visible = False
                            digital_twin_view.visible = False
                            research_intel_view.visible = False
                            op_memory_view.visible = False
                            consensus_view_state.visible = False
                            research_lab_view_state.visible = False
                            federation_view_state.visible = False
                            topology_view_state.visible = False
                            scheduler_view_state.visible = False
                            marketplace_view_state.visible = False

                    elif lowered == "j":
                        consensus_view_state.visible = not consensus_view_state.visible
                        if consensus_view_state.visible:
                            show_help = False
                            show_developer = False
                            observatory.visible = False
                            explainability.visible = False
                            predictive.visible = False
                            cluster.visible = False
                            orchestrator.visible = False
                            cognition.visible = False
                            multi_agent.visible = False
                            horizon_view.visible = False
                            genesis_view.visible = False
                            sentinel_view.visible = False
                            fabric_view.visible = False
                            infinity_view.visible = False
                            resource_graph_view.visible = False
                            graph_reasoning_view.visible = False
                            digital_twin_view.visible = False
                            research_intel_view.visible = False
                            op_memory_view.visible = False
                            causal_knowledge_view.visible = False
                            research_lab_view_state.visible = False
                            federation_view_state.visible = False
                            topology_view_state.visible = False
                            scheduler_view_state.visible = False
                            marketplace_view_state.visible = False

                    elif lowered == "b":
                        research_lab_view_state.visible = (
                            not research_lab_view_state.visible
                        )
                        if research_lab_view_state.visible:
                            research_lab_view_state.seeded = False
                            show_help = False
                            show_developer = False
                            observatory.visible = False
                            explainability.visible = False
                            predictive.visible = False
                            cluster.visible = False
                            orchestrator.visible = False
                            cognition.visible = False
                            multi_agent.visible = False
                            horizon_view.visible = False
                            genesis_view.visible = False
                            sentinel_view.visible = False
                            fabric_view.visible = False
                            infinity_view.visible = False
                            resource_graph_view.visible = False
                            graph_reasoning_view.visible = False
                            digital_twin_view.visible = False
                            research_intel_view.visible = False
                            op_memory_view.visible = False
                            causal_knowledge_view.visible = False
                            consensus_view_state.visible = False
                            federation_view_state.visible = False
                            topology_view_state.visible = False
                            scheduler_view_state.visible = False
                            marketplace_view_state.visible = False
                    elif lowered == "u":
                        federation_view_state.visible = (
                            not federation_view_state.visible
                        )
                        if federation_view_state.visible:
                            federation_view_state.seeded = False
                            topology_view_state.visible = False
                            scheduler_view_state.visible = False
                            marketplace_view_state.visible = False
                            show_help = False
                            show_developer = False
                            observatory.visible = False
                            explainability.visible = False
                            predictive.visible = False
                            cluster.visible = False
                            orchestrator.visible = False
                            cognition.visible = False
                            multi_agent.visible = False
                            horizon_view.visible = False
                            genesis_view.visible = False
                            sentinel_view.visible = False
                            fabric_view.visible = False
                            infinity_view.visible = False
                            resource_graph_view.visible = False
                            graph_reasoning_view.visible = False
                            digital_twin_view.visible = False
                            research_intel_view.visible = False
                            op_memory_view.visible = False
                            causal_knowledge_view.visible = False
                            consensus_view_state.visible = False
                            research_lab_view_state.visible = False
                    elif lowered == "k":
                        cognition.visible = not cognition.visible
                        if cognition.visible:
                            show_help = False
                            show_developer = False
                            observatory.visible = False
                            explainability.visible = False
                            predictive.visible = False
                            cluster.visible = False
                            orchestrator.visible = False
                            multi_agent.visible = False
                            horizon_view.visible = False
                            genesis_view.visible = False
                            sentinel_view.visible = False
                            fabric_view.visible = False
                            infinity_view.visible = False
                            resource_graph_view.visible = False
                            graph_reasoning_view.visible = False
                            digital_twin_view.visible = False
                            research_intel_view.visible = False
                            op_memory_view.visible = False
                            causal_knowledge_view.visible = False
                            consensus_view_state.visible = False
                            research_lab_view_state.visible = False
                            federation_view_state.visible = False
                            topology_view_state.visible = False
                            scheduler_view_state.visible = False
                            marketplace_view_state.visible = False
                    elif lowered == "w":
                        orchestrator.visible = not orchestrator.visible
                        if orchestrator.visible:
                            show_help = False
                            show_developer = False
                            observatory.visible = False
                            explainability.visible = False
                            predictive.visible = False
                            cluster.visible = False
                            cognition.visible = False
                            multi_agent.visible = False
                            horizon_view.visible = False
                            genesis_view.visible = False
                            sentinel_view.visible = False
                            fabric_view.visible = False
                            infinity_view.visible = False
                            resource_graph_view.visible = False
                            graph_reasoning_view.visible = False
                            digital_twin_view.visible = False
                            research_intel_view.visible = False
                            op_memory_view.visible = False
                            causal_knowledge_view.visible = False
                            consensus_view_state.visible = False
                            research_lab_view_state.visible = False
                            federation_view_state.visible = False
                            topology_view_state.visible = False
                            scheduler_view_state.visible = False
                            marketplace_view_state.visible = False
                    elif lowered == "]":
                        if marketplace_view_state.visible:
                            marketplace_view_state.view_index += 1
                        elif scheduler_view_state.visible:
                            scheduler_view_state.view_index += 1
                        elif topology_view_state.visible:
                            topology_view_state.view_index += 1
                        elif federation_view_state.visible:
                            federation_view_state.view_index += 1
                        elif research_lab_view_state.visible:
                            research_lab_view_state.view_index += 1
                        elif consensus_view_state.visible:
                            consensus_view_state.view_index += 1
                        elif causal_knowledge_view.visible:
                            causal_knowledge_view.view_index += 1
                        elif op_memory_view.visible:
                            op_memory_view.view_index += 1
                        elif research_intel_view.visible:
                            research_intel_view.view_index += 1
                        elif digital_twin_view.visible:
                            digital_twin_view.scenario_index += 1
                        elif orchestrator.visible:
                            orchestrator.workload = next_workload(
                                orchestrator.workload.name
                            )
                    elif lowered == "c":
                        cluster.visible = not cluster.visible
                        if cluster.visible:
                            show_help = False
                            show_developer = False
                            observatory.visible = False
                            explainability.visible = False
                            predictive.visible = False
                            orchestrator.visible = False
                            cognition.visible = False
                            multi_agent.visible = False
                            horizon_view.visible = False
                            genesis_view.visible = False
                            sentinel_view.visible = False
                            fabric_view.visible = False
                            infinity_view.visible = False
                            resource_graph_view.visible = False
                            graph_reasoning_view.visible = False
                            digital_twin_view.visible = False
                            research_intel_view.visible = False
                            op_memory_view.visible = False
                            causal_knowledge_view.visible = False
                            consensus_view_state.visible = False
                            research_lab_view_state.visible = False
                            federation_view_state.visible = False
                            topology_view_state.visible = False
                            scheduler_view_state.visible = False
                            marketplace_view_state.visible = False
                    elif lowered == "p":
                        predictive.visible = not predictive.visible
                        if predictive.visible:
                            show_help = False
                            show_developer = False
                            observatory.visible = False
                            explainability.visible = False
                            cluster.visible = False
                            orchestrator.visible = False
                            cognition.visible = False
                            multi_agent.visible = False
                            horizon_view.visible = False
                            genesis_view.visible = False
                            sentinel_view.visible = False
                            fabric_view.visible = False
                            infinity_view.visible = False
                            resource_graph_view.visible = False
                            graph_reasoning_view.visible = False
                            digital_twin_view.visible = False
                            research_intel_view.visible = False
                            op_memory_view.visible = False
                            causal_knowledge_view.visible = False
                            consensus_view_state.visible = False
                            research_lab_view_state.visible = False
                            federation_view_state.visible = False
                            topology_view_state.visible = False
                            scheduler_view_state.visible = False
                            marketplace_view_state.visible = False
                    elif lowered == "e":
                        marketplace_view_state.visible = (
                            not marketplace_view_state.visible
                        )
                        if marketplace_view_state.visible:
                            marketplace_view_state.seeded = False
                            show_help = False
                            show_developer = False
                            observatory.visible = False
                            explainability.visible = False
                            predictive.visible = False
                            cluster.visible = False
                            orchestrator.visible = False
                            cognition.visible = False
                            multi_agent.visible = False
                            horizon_view.visible = False
                            genesis_view.visible = False
                            sentinel_view.visible = False
                            fabric_view.visible = False
                            infinity_view.visible = False
                            resource_graph_view.visible = False
                            graph_reasoning_view.visible = False
                            digital_twin_view.visible = False
                            research_intel_view.visible = False
                            op_memory_view.visible = False
                            causal_knowledge_view.visible = False
                            consensus_view_state.visible = False
                            research_lab_view_state.visible = False
                            federation_view_state.visible = False
                            topology_view_state.visible = False
                            scheduler_view_state.visible = False
                    elif key == "=" or lowered == "=":
                        explainability.visible = not explainability.visible
                        if explainability.visible:
                            marketplace_view_state.visible = False
                            show_help = False
                            show_developer = False
                            observatory.visible = False
                            predictive.visible = False
                            cluster.visible = False
                            orchestrator.visible = False
                            cognition.visible = False
                            multi_agent.visible = False
                            horizon_view.visible = False
                            genesis_view.visible = False
                            sentinel_view.visible = False
                            fabric_view.visible = False
                            infinity_view.visible = False
                            resource_graph_view.visible = False
                            graph_reasoning_view.visible = False
                            digital_twin_view.visible = False
                            research_intel_view.visible = False
                            op_memory_view.visible = False
                            causal_knowledge_view.visible = False
                            consensus_view_state.visible = False
                            research_lab_view_state.visible = False
                            federation_view_state.visible = False
                            topology_view_state.visible = False
                            scheduler_view_state.visible = False

                    elif lowered == "o":
                        observatory.visible = not observatory.visible
                        if observatory.visible:
                            show_help = False
                            show_developer = False
                            explainability.visible = False
                            predictive.visible = False
                            cluster.visible = False
                            orchestrator.visible = False
                            cognition.visible = False
                            multi_agent.visible = False
                            horizon_view.visible = False
                            genesis_view.visible = False
                            sentinel_view.visible = False
                            fabric_view.visible = False
                            infinity_view.visible = False
                            resource_graph_view.visible = False
                            graph_reasoning_view.visible = False
                            digital_twin_view.visible = False
                            research_intel_view.visible = False
                            op_memory_view.visible = False
                            causal_knowledge_view.visible = False
                            consensus_view_state.visible = False
                            research_lab_view_state.visible = False
                            federation_view_state.visible = False
                            topology_view_state.visible = False
                            scheduler_view_state.visible = False
                            marketplace_view_state.visible = False
                    elif key == "LEFT":
                        observatory.history_offset = min(
                            max(0, len(observatory.recorder) - 1),
                            observatory.history_offset + 5,
                        )
                        observatory.timeline.scroll(1)
                    elif key == "RIGHT":
                        observatory.history_offset = max(
                            0, observatory.history_offset - 5
                        )
                        observatory.timeline.scroll(-1)
                    elif lowered == "z":
                        topology_view_state.visible = not topology_view_state.visible
                        if topology_view_state.visible:
                            topology_view_state.seeded = False
                            show_help = False
                            show_developer = False
                            observatory.visible = False
                            explainability.visible = False
                            predictive.visible = False
                            cluster.visible = False
                            orchestrator.visible = False
                            cognition.visible = False
                            multi_agent.visible = False
                            horizon_view.visible = False
                            genesis_view.visible = False
                            sentinel_view.visible = False
                            fabric_view.visible = False
                            infinity_view.visible = False
                            resource_graph_view.visible = False
                            graph_reasoning_view.visible = False
                            digital_twin_view.visible = False
                            research_intel_view.visible = False
                            op_memory_view.visible = False
                            causal_knowledge_view.visible = False
                            consensus_view_state.visible = False
                            research_lab_view_state.visible = False
                            federation_view_state.visible = False
                            scheduler_view_state.visible = False
                            marketplace_view_state.visible = False
                    elif key == "/" or lowered == "/":
                        scheduler_view_state.visible = not scheduler_view_state.visible
                        if scheduler_view_state.visible:
                            scheduler_view_state.seeded = False
                            show_help = False
                            show_developer = False
                            observatory.visible = False
                            explainability.visible = False
                            predictive.visible = False
                            cluster.visible = False
                            orchestrator.visible = False
                            cognition.visible = False
                            multi_agent.visible = False
                            horizon_view.visible = False
                            genesis_view.visible = False
                            sentinel_view.visible = False
                            fabric_view.visible = False
                            infinity_view.visible = False
                            resource_graph_view.visible = False
                            graph_reasoning_view.visible = False
                            digital_twin_view.visible = False
                            research_intel_view.visible = False
                            op_memory_view.visible = False
                            causal_knowledge_view.visible = False
                            consensus_view_state.visible = False
                            research_lab_view_state.visible = False
                            federation_view_state.visible = False
                            topology_view_state.visible = False
                    elif lowered == "t":
                        order: tuple[GraphMetric, ...] = ("cpu", "memory", "disk")
                        idx = order.index(observatory.metric)
                        observatory.metric = order[(idx + 1) % len(order)]
                    elif lowered == "a":
                        research_state.status = "Running"
                        live.update(render_frame(make_frame()))
                        snapshot = TelemetrySnapshot.from_system_snapshot(system)
                        research_report = research_engine.run(
                            snapshot,
                            engine.intent.current_intent(),
                            write_report=True,
                        )
                        apply_research_result(research_state, research_report)
                        winner_name = (
                            research_report.winner.strategy.title
                            if research_report.winner
                            else "None"
                        )
                        score = (
                            research_report.winner.rank_score
                            if research_report.winner
                            else 0.0
                        )
                        event = research_completed_event(
                            winner=winner_name, score=score
                        )
                        observatory.recorder.record_event(event)
                        observatory.timeline.add(event)
                    elif len(key) == 1:
                        engine.intent.set_intent_by_hotkey(key)

                system, report = collect_pipeline(collector, engine)
                ingest_observatory_sample(
                    observatory,
                    report.snapshot,
                    engine.intent.current_intent().name,
                    report,
                )
                tick_cluster(cluster, report.snapshot)
                core.api.telemetry.set_host_snapshot(
                    {
                        "cpu_percent": report.snapshot.cpu_percent,
                        "memory_percent": report.snapshot.memory_percent,
                        "battery_percent": report.snapshot.battery_percent,
                    }
                )
                summary = core.registry.safety_summary()
                live.update(render_frame(make_frame()))
    finally:
        if fd is not None and old_settings is not None:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser for the dashboard."""

    parser = argparse.ArgumentParser(
        prog="aetheros-dashboard",
        description="AetherOS ∞ — Explainable Operating Intelligence",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("data/safety_audit.db"),
        help="SQLite audit database path",
    )
    parser.add_argument(
        "--intent-db",
        type=Path,
        default=Path("data/intent.db"),
        help="SQLite intent persistence path",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=Path("reports"),
        help="Directory for research markdown reports",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Refresh interval in seconds (default: 1.0)",
    )
    return parser


def main() -> None:
    """CLI entry point for the operator dashboard."""

    args = build_parser().parse_args()
    if args.interval <= 0:
        raise SystemExit("--interval must be positive")
    run_dashboard(
        db_path=args.db,
        intent_db=args.intent_db,
        reports_dir=args.reports_dir,
        interval=args.interval,
    )


if __name__ == "__main__":
    main()
