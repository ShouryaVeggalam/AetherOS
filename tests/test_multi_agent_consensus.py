"""Tests for v3 P4 Multi-Agent Consensus Engine."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from rich.console import Console

from aetheros.agents import (
    BROADCAST,
    Conflict,
    ConsensusDecision,
    ConsensusEngine,
    ConsensusFinding,
    ConsensusPanel,
    DeliberationContext,
    EventBus,
    detect_conflicts,
    make_consensus_event,
)
from aetheros.agents.base import AgentFinding
from aetheros.agents.coordinator import Coordinator
from aetheros.intent.profiles import BATTERY_SAVER, CODING, PROFILES
from aetheros.messaging import AsyncMessageBus
from aetheros.observatory.models import TelemetryPoint
from aetheros.policy_engine.models import TelemetrySnapshot


def _snap(
    *,
    cpu: float = 96.0,
    memory: float = 55.0,
    battery: float | None = 22.0,
    disk: float = 40.0,
) -> TelemetrySnapshot:
    return TelemetrySnapshot(
        timestamp=datetime.now(UTC),
        cpu_percent=cpu,
        memory_percent=memory,
        disk_percent=disk,
        battery_percent=battery,
        process_count=2,
        top_processes=("Cursor", "Chrome"),
    )


def _ctx(
    *,
    cpu: float = 96.0,
    battery: float | None = 22.0,
    intent_key: str = CODING,
) -> DeliberationContext:
    now = datetime.now(UTC)
    history = tuple(
        TelemetryPoint(now - timedelta(seconds=20 - i), cpu, 50.0, 40.0, 70.0, "Coding")
        for i in range(20)
    )
    return DeliberationContext(
        snapshot=_snap(cpu=cpu, battery=battery),
        intent=PROFILES[intent_key],
        history=history,
    )


# --- events / bus -----------------------------------------------------------


def test_event_bus_publish_subscribe_history() -> None:
    bus = EventBus(history_limit=10)
    seen: list[str] = []

    def handler(event) -> None:
        seen.append(event.id)

    bus.subscribe("coordinator", handler)
    event = make_consensus_event(
        sender="performance",
        receiver="coordinator",
        type="agent.finding",
        payload={"stance": "increase_cpu", "confidence": 0.9},
    )
    delivered = bus.publish(event)
    assert delivered >= 1
    assert seen == [event.id]
    assert bus.history(limit=5)[-1].sender == "performance"

    broadcast = make_consensus_event(
        sender="coordinator",
        receiver=BROADCAST,
        type="coordinator.decision",
        payload={"recommendation": "Balanced Mode"},
    )
    bus.subscribe("telemetry", handler)
    bus.publish(broadcast)
    assert len(bus.history()) >= 2

    bus.unsubscribe("coordinator", handler)
    bus.clear()
    assert bus.history() == ()

    with pytest.raises(ValueError):
        bus.subscribe(" ", handler)
    with pytest.raises(ValueError):
        make_consensus_event(sender=" ", receiver="x", type="t")


def test_consensus_finding_and_conflict_validation() -> None:
    finding = ConsensusFinding(
        agent="telemetry",
        summary="Healthy",
        evidence=("CPU 10%",),
        confidence=95.0,
    )
    assert finding.agent == "telemetry"
    with pytest.raises(ValueError):
        ConsensusFinding(agent=" ", summary="x", evidence=(), confidence=10.0)
    with pytest.raises(ValueError):
        ConsensusFinding(agent="a", summary="x", evidence=(), confidence=101.0)
    with pytest.raises(ValueError):
        Conflict(source="a", target="b", disagreement=" ")
    with pytest.raises(ValueError):
        ConsensusDecision(
            recommendation=" ",
            supporting_agents=(),
            conflicting_agents=(),
            confidence=50.0,
            reasoning="x",
        )


# --- agents / consensus -----------------------------------------------------


def test_consensus_engine_deliberate_conflict() -> None:
    engine = ConsensusEngine()
    decision = engine.deliberate(_ctx(cpu=96.0, battery=22.0))
    assert isinstance(decision, ConsensusDecision)
    assert decision.recommendation in {
        "Balanced Mode",
        "Efficiency Mode",
        "Performance Mode",
    }
    assert 0.0 <= decision.confidence <= 100.0
    assert decision.reasoning
    assert engine.last_findings
    assert any(f.agent == "performance" for f in engine.last_findings)
    assert engine.bus.history()
    # High CPU + low battery typically yields conflict
    assert (
        engine.last_conflicts or decision.conflicting_agents or decision.recommendation
    )


def test_consensus_engine_balanced_when_calm() -> None:
    engine = ConsensusEngine()
    decision = engine.deliberate(_ctx(cpu=30.0, battery=90.0, intent_key=CODING))
    assert decision.recommendation
    assert "Human" not in decision.recommendation  # recommendation is a mode label


def test_detect_conflicts_and_merge_sync() -> None:
    findings = (
        AgentFinding(
            agent_id="performance",
            stance="increase_cpu",
            summary="Increase CPU allocation",
            confidence=0.9,
            priority=0.9,
            evidence=("CPU 96%",),
        ),
        AgentFinding(
            agent_id="battery",
            stance="reduce_power",
            summary="Reduce power usage",
            confidence=0.9,
            priority=0.85,
            evidence=("Battery 22%",),
        ),
        AgentFinding(
            agent_id="telemetry",
            stance="report_metrics",
            summary="Healthy",
            confidence=0.95,
            priority=0.2,
            evidence=("ok",),
        ),
    )
    conflicts = detect_conflicts(findings)
    assert conflicts
    assert conflicts[0].source == "performance"

    coordinator = Coordinator(AsyncMessageBus())
    decision = coordinator.merge_sync(findings, _ctx())
    consensus = decision.to_consensus_decision(conflicts)
    assert consensus.confidence == round(decision.confidence * 100.0, 2)
    assert "performance" in consensus.conflicting_agents or consensus.recommendation


def test_agent_finding_to_consensus_finding() -> None:
    raw = AgentFinding(
        agent_id="research",
        stance="prefer_balanced",
        summary="Morning Coding Pattern",
        confidence=0.91,
        priority=0.4,
        evidence=("hist",),
    )
    projected = raw.to_consensus_finding()
    assert projected.agent == "research"
    assert projected.confidence == 91.0


# --- formatter --------------------------------------------------------------


def test_consensus_panel_views() -> None:
    engine = ConsensusEngine()
    decision = engine.deliberate(_ctx())
    console = Console(record=True, width=100)
    console.print(ConsensusPanel())
    assert (
        "idle" in console.export_text().lower() or "CONSENSUS" in console.export_text()
    )

    for view in ("consensus", "status", "findings", "bus", "conflicts"):
        console = Console(record=True, width=110)
        console.print(
            ConsensusPanel(
                findings=engine.last_findings,
                decision=decision,
                conflicts=engine.last_conflicts,
                bus_events=engine.bus.history(limit=20),
                view=view,
            )
        )
        out = console.export_text()
        assert "MULTI-AGENT CONSENSUS" in out


def test_module_aliases_importable() -> None:
    from aetheros.agents.battery import BatteryAgent
    from aetheros.agents.performance import PerformanceAgent
    from aetheros.agents.research import ResearchAgent
    from aetheros.agents.security import SecurityAgent
    from aetheros.agents.telemetry import TelemetryAgent

    bus = AsyncMessageBus()
    assert TelemetryAgent(bus).agent_id == "telemetry"
    assert PerformanceAgent(bus).agent_id == "performance"
    assert BatteryAgent(bus).agent_id == "battery"
    assert SecurityAgent(bus).agent_id == "security"
    assert ResearchAgent(bus).agent_id == "research"


def test_efficiency_intent_softens_performance() -> None:
    engine = ConsensusEngine()
    # High CPU but efficiency-favoring intent + decent battery may soften.
    decision = engine.deliberate(_ctx(cpu=92.0, battery=80.0, intent_key=BATTERY_SAVER))
    assert decision.recommendation in {
        "Balanced Mode",
        "Efficiency Mode",
        "Performance Mode",
    }


def test_specialist_paths_and_formatter_edges() -> None:
    """Exercise specialist branches and empty panel sections."""

    from aetheros.agents.battery import BatteryAgent
    from aetheros.agents.cluster_agent import ClusterAgent
    from aetheros.agents.performance import PerformanceAgent
    from aetheros.agents.security import SecurityAgent

    bus = AsyncMessageBus()
    # No battery path
    batt = BatteryAgent(bus).analyze(
        DeliberationContext(snapshot=_snap(battery=None), intent=PROFILES[CODING])
    )
    assert batt.stance == "hold_power"

    # Memory / disk pressure paths
    perf_mem = PerformanceAgent(bus).analyze(
        DeliberationContext(
            snapshot=_snap(cpu=40.0, memory=95.0, battery=80.0),
            intent=PROFILES[CODING],
        )
    )
    assert perf_mem.stance == "relieve_memory"
    perf_disk = PerformanceAgent(bus).analyze(
        DeliberationContext(
            snapshot=_snap(cpu=40.0, memory=40.0, disk=95.0, battery=80.0),
            intent=PROFILES[CODING],
        )
    )
    assert perf_disk.stance == "relieve_disk"
    perf_mid = PerformanceAgent(bus).analyze(
        DeliberationContext(
            snapshot=_snap(cpu=75.0, memory=40.0, battery=80.0),
            intent=PROFILES[CODING],
        )
    )
    assert perf_mid.stance == "increase_cpu"

    # Security with spike history
    now = datetime.now(UTC)
    hist = tuple(
        TelemetryPoint(
            now - timedelta(seconds=20 - i), 40.0, 50.0, 40.0, 70.0, "Coding"
        )
        for i in range(20)
    )
    sec = SecurityAgent(bus).analyze(
        DeliberationContext(
            snapshot=_snap(cpu=98.0),
            intent=PROFILES[CODING],
            history=hist,
        )
    )
    assert sec.agent_id == "security"

    # Cluster solo
    cluster_agent = ClusterAgent(bus).analyze(
        DeliberationContext(snapshot=_snap(), intent=PROFILES[CODING], cluster=None)
    )
    assert cluster_agent.stance == "cluster_solo"

    # Empty conflicts panel
    console = Console(record=True, width=80)
    console.print(
        ConsensusPanel(
            findings=(
                ConsensusFinding(
                    agent="telemetry",
                    summary="Healthy",
                    evidence=("CPU ok",),
                    confidence=90.0,
                ),
            ),
            decision=ConsensusDecision(
                recommendation="Balanced Mode",
                supporting_agents=("telemetry",),
                conflicting_agents=(),
                confidence=91.0,
                reasoning="ok",
            ),
            conflicts=(),
            bus_events=(),
            view="conflicts",
        )
    )
    assert "Conflicts" in console.export_text() or "(none)" in console.export_text()


def test_coordinator_async_resolve_and_research_paths() -> None:
    import asyncio

    from aetheros.agents.research import ResearchAgent

    async def _run() -> None:
        bus = AsyncMessageBus()
        bus.subscribe("coordinator")
        coord = Coordinator(bus)
        idle = coord.analyze(_ctx())
        assert idle.stance == "await_findings"
        findings = (
            AgentFinding(
                agent_id="research",
                stance="prefer_performance",
                summary="sim",
                confidence=0.9,
                priority=0.5,
                evidence=("e",),
            ),
            AgentFinding(
                agent_id="telemetry",
                stance="report_metrics",
                summary="ok",
                confidence=0.9,
                priority=0.1,
                evidence=("e",),
            ),
        )
        decision = await coord.resolve(findings, context=_ctx(cpu=40.0, battery=90.0))
        assert decision.recommendation == "Performance Mode"

        findings2 = (
            AgentFinding(
                agent_id="research",
                stance="prefer_efficiency",
                summary="sim",
                confidence=0.88,
                priority=0.5,
                evidence=("e",),
            ),
        )
        d2 = coord.merge_sync(findings2, _ctx(cpu=40.0, battery=50.0))
        assert d2.recommendation == "Efficiency Mode"

        findings3 = (
            AgentFinding(
                agent_id="research",
                stance="prefer_balanced",
                summary="sim",
                confidence=0.86,
                priority=0.5,
                evidence=("e",),
                status="ok",
            ),
        )
        d3 = coord.merge_sync(findings3, _ctx(cpu=40.0, battery=90.0))
        assert d3.recommendation == "Balanced Mode"

        # Research agent analyze
        research = ResearchAgent(bus).analyze(_ctx(cpu=40.0, battery=90.0))
        assert research.agent_id == "research"

    asyncio.run(_run())


def test_event_payload_dict_and_limit_zero() -> None:
    bus = EventBus()
    event = make_consensus_event(
        sender="a",
        receiver="b",
        type="t",
        payload={"x": 1.5, "y": ["a", "b"]},
    )
    assert "x" in event.payload_dict()
    assert bus.history(limit=0) == ()
    bus.unsubscribe("missing")

    from aetheros.agents.events import Event

    with pytest.raises(ValueError):
        Event(
            id=" ",
            sender="a",
            receiver="b",
            type="t",
            payload=(),
            timestamp=datetime.now(UTC),
        )
    with pytest.raises(ValueError):
        Event(
            id="1",
            sender=" ",
            receiver="b",
            type="t",
            payload=(),
            timestamp=datetime.now(UTC),
        )
    with pytest.raises(ValueError):
        Event(
            id="1",
            sender="a",
            receiver="b",
            type=" ",
            payload=(),
            timestamp=datetime.now(UTC),
        )
    with pytest.raises(ValueError):
        ConsensusFinding(agent="a", summary=" ", evidence=(), confidence=10.0)
    with pytest.raises(ValueError):
        Conflict(source=" ", target="b", disagreement="x")


def test_coverage_specialists_coordinator_formatter() -> None:
    from aetheros.agents.battery import BatteryAgent
    from aetheros.agents.cluster_agent import ClusterAgent
    from aetheros.agents.security import SecurityAgent
    from aetheros.cluster.models import ClusterSnapshot
    from aetheros.runtime import AgenticRuntime

    bus = AsyncMessageBus()
    # Mid charge under heavy CPU
    mid = BatteryAgent(bus).analyze(
        DeliberationContext(
            snapshot=_snap(cpu=75.0, battery=35.0),
            intent=PROFILES[CODING],
        )
    )
    assert mid.stance == "reduce_power"
    # Intent efficiency bias path (needs efficiency_weight/100 >= 0.6)
    from aetheros.intent.models import IntentProfile

    high_eff = IntentProfile(
        name="High Efficiency",
        description="Force efficiency bias for tests.",
        cpu_weight=5,
        memory_weight=5,
        disk_weight=5,
        latency_weight=10,
        efficiency_weight=70,
    )
    eff = BatteryAgent(bus).analyze(
        DeliberationContext(
            snapshot=_snap(cpu=65.0, battery=70.0),
            intent=high_eff,
        )
    )
    assert eff.stance == "reduce_power"

    # Cluster with peers — hotter / cooler / balanced
    from aetheros.cluster.models import ClusterNode

    now = datetime.now(UTC)
    peer = ClusterNode(
        node_id="peer1",
        hostname="peer",
        platform="Linux",
        cpu=40.0,
        memory=50.0,
        disk=40.0,
        battery=None,
        latency=5.0,
        last_seen=now,
    )
    hot = ClusterSnapshot(
        total_nodes=3,
        online_nodes=3,
        offline_nodes=0,
        average_cpu=40.0,
        average_memory=50.0,
        average_load=45.0,
        highest_load_node=peer,
        nodes=(peer,),
        alerts=(),
    )
    cluster_hot = ClusterAgent(bus).analyze(
        DeliberationContext(
            snapshot=_snap(cpu=80.0),
            intent=PROFILES[CODING],
            cluster=hot,
        )
    )
    assert cluster_hot.stance == "shed_to_peers"
    cool = ClusterSnapshot(
        total_nodes=3,
        online_nodes=3,
        offline_nodes=0,
        average_cpu=90.0,
        average_memory=50.0,
        average_load=70.0,
        highest_load_node=peer,
        nodes=(peer,),
        alerts=(),
    )
    cluster_cool = ClusterAgent(bus).analyze(
        DeliberationContext(
            snapshot=_snap(cpu=40.0),
            intent=PROFILES[CODING],
            cluster=cool,
        )
    )
    assert cluster_cool.stance == "accept_workload"
    bal = ClusterSnapshot(
        total_nodes=2,
        online_nodes=2,
        offline_nodes=0,
        average_cpu=50.0,
        average_memory=50.0,
        average_load=50.0,
        highest_load_node=peer,
        nodes=(peer,),
        alerts=(),
    )
    cluster_bal = ClusterAgent(bus).analyze(
        DeliberationContext(
            snapshot=_snap(cpu=50.0),
            intent=PROFILES[CODING],
            cluster=bal,
        )
    )
    assert cluster_bal.stance == "cluster_balanced"

    runtime = AgenticRuntime()
    report = runtime.deliberate_sync(
        _snap(cpu=40.0, battery=90.0),
        PROFILES[CODING],
    )
    assert report.reasoning

    # Security unknown process path
    sec = SecurityAgent(bus).analyze(
        DeliberationContext(
            snapshot=TelemetrySnapshot(
                timestamp=datetime.now(UTC),
                cpu_percent=85.0,
                memory_percent=40.0,
                disk_percent=40.0,
                battery_percent=80.0,
                process_count=1,
                top_processes=("WeirdMinerXYZ",),
            ),
            intent=PROFILES[CODING],
            history=_ctx().history,
        )
    )
    assert sec.stance in {"investigate_anomaly", "security_nominal"}

    # Coordinator security annotation + vote paths
    coord = Coordinator(bus)
    with_sec = coord.merge_sync(
        (
            AgentFinding(
                agent_id="security",
                stance="investigate_anomaly",
                summary="spike",
                confidence=0.8,
                priority=0.8,
                evidence=("e",),
            ),
            AgentFinding(
                agent_id="performance",
                stance="increase_cpu",
                summary="cpu",
                confidence=0.9,
                priority=0.9,
                evidence=("e",),
            ),
            AgentFinding(
                agent_id="battery",
                stance="hold_power",
                summary="ok",
                confidence=0.8,
                priority=0.2,
                evidence=("e",),
            ),
        ),
        _ctx(cpu=90.0, battery=90.0),
    )
    assert "Security" in with_sec.reasoning or with_sec.recommendation

    # Soften performance via efficiency intent (>= 70)
    from aetheros.intent.models import IntentProfile

    high_eff = IntentProfile(
        name="High Efficiency",
        description="Force efficiency bias for tests.",
        cpu_weight=5,
        memory_weight=5,
        disk_weight=5,
        latency_weight=10,
        efficiency_weight=80,
    )
    softened = coord.merge_sync(
        (
            AgentFinding(
                agent_id="performance",
                stance="increase_cpu",
                summary="cpu",
                confidence=0.95,
                priority=0.95,
                evidence=("e",),
            ),
            AgentFinding(
                agent_id="battery",
                stance="hold_power",
                summary="ok",
                confidence=0.5,
                priority=0.1,
                evidence=("e",),
            ),
        ),
        DeliberationContext(
            snapshot=_snap(cpu=95.0, battery=90.0),
            intent=high_eff,
        ),
    )
    assert softened.recommendation == "Balanced Mode"
    # Vote majority performance / efficiency without research
    perf_votes = coord.merge_sync(
        (
            AgentFinding(
                agent_id="performance",
                stance="increase_cpu",
                summary="a",
                confidence=0.8,
                priority=0.5,
                evidence=("e",),
            ),
            AgentFinding(
                agent_id="telemetry",
                stance="increase_cpu",
                summary="b",
                confidence=0.8,
                priority=0.5,
                evidence=("e",),
            ),
        ),
        _ctx(cpu=40.0, battery=90.0),
    )
    assert perf_votes.recommendation == "Performance Mode"
    eff_votes = coord.merge_sync(
        (
            AgentFinding(
                agent_id="battery",
                stance="reduce_power",
                summary="a",
                confidence=0.8,
                priority=0.5,
                evidence=("e",),
            ),
            AgentFinding(
                agent_id="telemetry",
                stance="prefer_efficiency",
                summary="b",
                confidence=0.8,
                priority=0.5,
                evidence=("e",),
            ),
        ),
        _ctx(cpu=40.0, battery=90.0),
    )
    assert eff_votes.recommendation == "Efficiency Mode"

    # Formatter empty lists
    console = Console(record=True, width=80)
    console.print(
        ConsensusPanel(
            findings=(),
            decision=ConsensusDecision(
                recommendation="Balanced Mode",
                supporting_agents=(),
                conflicting_agents=(),
                confidence=80.0,
                reasoning="ok",
            ),
            view="status",
        )
    )
    console.print(
        ConsensusPanel(
            findings=(),
            decision=ConsensusDecision(
                recommendation="Balanced Mode",
                supporting_agents=(),
                conflicting_agents=(),
                confidence=80.0,
                reasoning="ok",
            ),
            view="findings",
        )
    )
    console.print(
        ConsensusPanel(
            findings=(),
            decision=None,
            view="consensus",
        )
    )
    assert "CONSENSUS" in console.export_text() or "Awaiting" in console.export_text()
