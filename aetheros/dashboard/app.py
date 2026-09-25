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
from datetime import UTC, datetime
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
from aetheros.cluster import (
    ClusterSnapshot,
    LocalJSONTransport,
    NodeRegistry,
    aggregate,
)
from aetheros.cognition import CognitiveRuntime
from aetheros.core import AetherCore
from aetheros.dashboard.renderer import DashboardFrame, render_frame
from aetheros.dashboard.widgets import ProcessRow
from aetheros.decision import DecisionEngine, DecisionReport
from aetheros.decision.models import Decision, utc_now
from aetheros.explainability import ExplainabilityEngine, Explanation
from aetheros.fabric import FabricReport, FabricRuntime
from aetheros.genesis import GenesisReport, GenesisRuntime
from aetheros.horizon import HorizonReport, HorizonRuntime
from aetheros.infinity import InfinityReport, InfinityRuntime
from aetheros.intent import IntentEngine, IntentStorage
from aetheros.learning import LearningEngine
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
from aetheros.reasoning.explain import CognitiveReport
from aetheros.research import ResearchEngine, ResearchReport
from aetheros.runtime import AgenticReport, AgenticRuntime
from aetheros.safety import AuditLogger, CooldownManager, SafetyValidator
from aetheros.sdk import PluginRecord
from aetheros.sentinel import SentinelReport, SentinelRuntime
from aetheros.telemetry import TelemetryCollector
from aetheros.telemetry.models import SystemSnapshot


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


def format_uptime(seconds: float) -> str:
    """Format boot uptime as a short human string."""

    total = int(seconds)
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    if days:
        return f"{days}d {hours}h {minutes}m"
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    return f"{minutes}m {secs}s"


def format_battery(system: SystemSnapshot) -> str:
    """Format battery status for the telemetry panel."""

    if system.battery is None:
        return "n/a"
    plugged = "AC" if system.battery.is_plugged_in else "battery"
    return f"{system.battery.percent:.0f}% ({plugged})"


def format_audit_summary(entry: dict[str, object] | None) -> str:
    """Turn the latest audit row into a one-line summary."""

    if entry is None:
        return "No audit entries yet."
    title = str(entry["title"])
    approved = bool(entry["approved"])
    stamp = str(entry["timestamp"])
    verb = "approved" if approved else "blocked"
    ago = _relative_time(stamp)
    return f"{title} {verb} {ago}."


def _relative_time(iso_timestamp: str) -> str:
    """Approximate relative time from an ISO timestamp string."""

    try:
        parsed = datetime.fromisoformat(iso_timestamp)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
    except ValueError:
        return "recently"
    delta = datetime.now(UTC) - parsed.astimezone(UTC)
    seconds = max(0, int(delta.total_seconds()))
    if seconds < 60:
        return f"{seconds}s ago"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"


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


def plugin_console_rows(
    records: list[PluginRecord],
) -> tuple[tuple[str, str, str, str, str], ...]:
    """Map plugin records into developer-console table rows."""

    rows: list[tuple[str, str, str, str, str]] = []
    for record in records:
        if not record.verified:
            status = "Rejected"
            safety = "Unsafe"
        elif record.enabled:
            status = "Enabled"
            safety = "Verified"
        else:
            status = "Disabled"
            safety = "Verified"
        rows.append((record.name, record.version, status, record.author, safety))
    return tuple(rows)


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
        and not show_infinity,
        explanation=ai_explanation,
        show_predictive=show_predict
        and not show_cognitive
        and not show_multi_agent
        and not show_horizon
        and not show_genesis
        and not show_sentinel
        and not show_fabric
        and not show_infinity,
        predictive_report=predictive_report,
        show_cluster=show_cluster
        and not show_cognitive
        and not show_multi_agent
        and not show_horizon
        and not show_genesis
        and not show_sentinel
        and not show_fabric
        and not show_infinity,
        cluster_snapshot=cluster_snapshot,
        cluster_online_ids=cluster_online,
        show_orchestrator=show_orchestrator
        and not show_cognitive
        and not show_multi_agent
        and not show_horizon
        and not show_genesis
        and not show_sentinel
        and not show_fabric
        and not show_infinity,
        execution_plan=execution_plan,
        selected_workload=selected_workload,
        show_cognitive=show_cognitive
        and not show_multi_agent
        and not show_horizon
        and not show_genesis
        and not show_sentinel
        and not show_fabric
        and not show_infinity,
        cognitive_report=cognitive_report,
        show_multi_agent=show_multi_agent
        and not show_horizon
        and not show_genesis
        and not show_sentinel
        and not show_fabric
        and not show_infinity,
        agentic_report=agentic_report,
        show_horizon=show_horizon
        and not show_genesis
        and not show_sentinel
        and not show_fabric
        and not show_infinity,
        horizon_report=horizon_report,
        show_genesis=show_genesis
        and not show_sentinel
        and not show_fabric
        and not show_infinity,
        genesis_report=genesis_report,
        show_sentinel=show_sentinel and not show_fabric and not show_infinity,
        sentinel_report=sentinel_report,
        show_fabric=show_fabric and not show_infinity,
        fabric_report=fabric_report,
        show_infinity=show_infinity,
        infinity_report=infinity_report,
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
                    elif lowered == "]":
                        if orchestrator.visible:
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
                    elif lowered == "e":
                        explainability.visible = not explainability.visible
                        if explainability.visible:
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
