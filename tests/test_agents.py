"""Unit tests for AetherOS v4 Agentic Systems Intelligence."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from rich.console import Console

from aetheros.agents import (
    BatteryAgent,
    MultiAgentPanel,
    PerformanceAgent,
    TelemetryAgent,
)
from aetheros.cluster.models import ClusterSnapshot
from aetheros.intent.profiles import BATTERY_SAVER, CODING, PROFILES
from aetheros.messaging import AsyncMessageBus, make_event
from aetheros.observatory.models import TelemetryPoint
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.runtime import AgenticRuntime


def _snap(
    *,
    cpu: float = 96.0,
    memory: float = 55.0,
    battery: float | None = 22.0,
    processes: tuple[str, ...] = ("Cursor", "Chrome"),
) -> TelemetrySnapshot:
    """Telemetry snapshot for agentic tests."""

    return TelemetrySnapshot(
        timestamp=datetime.now(UTC),
        cpu_percent=cpu,
        memory_percent=memory,
        disk_percent=40.0,
        battery_percent=battery,
        process_count=len(processes),
        top_processes=processes,
    )


def _history(cpu: float = 50.0, count: int = 20) -> tuple[TelemetryPoint, ...]:
    """History window for security spike detection."""

    now = datetime.now(UTC)
    return tuple(
        TelemetryPoint(
            now - timedelta(seconds=count - i), cpu, 50.0, 40.0, 70.0, "Coding"
        )
        for i in range(count)
    )


def test_message_bus_publish_and_history() -> None:
    """Bus should deliver events and retain history."""

    import asyncio

    async def _run() -> None:
        bus = AsyncMessageBus()
        queue = bus.subscribe("coordinator")
        event = make_event(
            sender="performance",
            receiver="coordinator",
            type="agent.finding",
            payload={"stance": "increase_cpu"},
        )
        delivered = await bus.publish(event)
        assert delivered >= 1
        received = await queue.get()
        assert received.id == event.id
        assert bus.history(limit=10)[-1].sender == "performance"

    asyncio.run(_run())


def test_performance_vs_battery_conflict() -> None:
    """Coordinator should resolve increase_cpu vs reduce_power."""

    runtime = AgenticRuntime()
    report = runtime.deliberate_sync(
        _snap(cpu=96.0, battery=20.0),
        PROFILES[BATTERY_SAVER],
        history=_history(cpu=40.0),
    )
    assert report.decision.recommendation in {
        "Balanced Mode",
        "Efficiency Mode",
        "Performance Mode",
    }
    assert report.decision.reasoning
    assert report.confidence >= 0.5
    assert (
        "performance" in report.decision.conflicting_agents
        or report.decision.recommendation != "Performance Mode"
    )
    agent_ids = {row.agent_id for row in report.agents}
    assert "coordinator" in agent_ids
    assert "performance" in agent_ids
    assert "battery" in agent_ids


def test_agents_specialize() -> None:
    """Specialists should emit distinct stances for a hot system."""

    bus = AsyncMessageBus()
    from aetheros.agents.base import DeliberationContext

    ctx = DeliberationContext(
        snapshot=_snap(cpu=95.0, battery=18.0),
        intent=PROFILES[CODING],
        history=_history(),
    )
    perf = PerformanceAgent(bus).analyze(ctx)
    batt = BatteryAgent(bus).analyze(ctx)
    telem = TelemetryAgent(bus).analyze(ctx)
    assert perf.stance == "increase_cpu"
    assert batt.stance == "reduce_power"
    assert telem.stance == "report_metrics"


def test_runtime_panel_renders() -> None:
    """AgenticRuntime + MultiAgentPanel should render without error."""

    runtime = AgenticRuntime()
    report = runtime.deliberate_sync(
        _snap(cpu=40.0, battery=80.0),
        PROFILES[CODING],
        history=_history(cpu=35.0),
        cluster=ClusterSnapshot(
            total_nodes=1,
            online_nodes=1,
            offline_nodes=0,
            average_cpu=40.0,
            average_memory=50.0,
            average_load=45.0,
            highest_load_node=None,
            nodes=(),
            alerts=(),
        ),
    )
    console = Console(record=True, width=100)
    console.print(MultiAgentPanel(report=report))
    text = console.export_text()
    assert "AGENTIC" in text or "Coordinator" in text
    assert report.recommendation
    assert len(report.findings) == 6
