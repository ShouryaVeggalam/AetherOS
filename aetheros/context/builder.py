"""Context builder — aggregate GraphContext from existing intelligence inputs.

Performs no prediction. Only read-only aggregation of graph, bridge, telemetry,
history, and intent evidence.
"""

from __future__ import annotations

from datetime import UTC, datetime

from aetheros.bridge.adapter import GraphBridge
from aetheros.context.history import match_historical_pattern
from aetheros.context.intent import resolve_intent
from aetheros.context.models import GraphContext, IntentContext
from aetheros.graph.models import ResourceGraph
from aetheros.graph.queries import nodes_of_type
from aetheros.observatory.models import TelemetryPoint
from aetheros.policy_engine.models import TelemetrySnapshot


def build_context(
    *,
    telemetry: TelemetrySnapshot,
    resource_graph: ResourceGraph | None = None,
    bridge: GraphBridge | None = None,
    history: tuple[TelemetryPoint, ...] = (),
    manual_intent: str | None = None,
    intent_duration_seconds: float = 0.0,
    now: datetime | None = None,
) -> GraphContext:
    """Aggregate one immutable GraphContext.

    Prefers ``bridge`` views when provided; otherwise derives from
    ``resource_graph`` / telemetry alone.
    """

    stamp = now if now is not None else datetime.now(UTC)
    graph = resource_graph
    if bridge is not None:
        graph = bridge.graph

    foreground = _foreground(bridge, graph, telemetry)
    intent = resolve_intent(
        manual_profile=manual_intent,
        foreground_process=foreground,
        history=history,
        battery_percent=telemetry.battery_percent,
        intent_duration_seconds=intent_duration_seconds,
    )
    pattern = match_historical_pattern(
        cpu=telemetry.cpu_percent,
        memory=telemetry.memory_percent,
        disk=telemetry.disk_percent,
        intent=intent.name,
        history=history,
    )
    battery_state = _battery_state(bridge, graph, telemetry)
    cluster_health = _cluster_health(bridge, graph)
    simulation_state = _simulation_state(bridge, graph)
    confidence = _context_confidence(intent, pattern, graph is not None, history)
    return GraphContext(
        timestamp=stamp,
        active_intent=intent,
        foreground_process=foreground,
        cpu_load=telemetry.cpu_percent,
        memory_load=telemetry.memory_percent,
        disk_load=telemetry.disk_percent,
        battery_state=battery_state,
        cluster_health=cluster_health,
        simulation_state=simulation_state,
        historical_pattern=pattern,
        confidence=confidence,
    )


def _foreground(
    bridge: GraphBridge | None,
    graph: ResourceGraph | None,
    telemetry: TelemetrySnapshot,
) -> str | None:
    if bridge is not None:
        ctx = bridge.current_context()
        if ctx.foreground_process:
            return ctx.foreground_process
    if graph is not None:
        processes = nodes_of_type(graph, "Process")
        if processes:
            return processes[0].name
    if telemetry.top_processes:
        return telemetry.top_processes[0]
    return None


def _battery_state(
    bridge: GraphBridge | None,
    graph: ResourceGraph | None,
    telemetry: TelemetrySnapshot,
) -> str:
    if telemetry.battery_percent is None:
        return "n/a"
    plugged = None
    if graph is not None:
        node = graph.get_node("battery")
        if node is not None:
            for key, value in node.metadata:
                if key == "plugged_in":
                    plugged = value == "true"
    if plugged is True:
        return f"Charging {telemetry.battery_percent:.0f}%"
    if plugged is False:
        return f"On battery {telemetry.battery_percent:.0f}%"
    return f"{telemetry.battery_percent:.0f}%"


def _cluster_health(bridge: GraphBridge | None, graph: ResourceGraph | None) -> str:
    if bridge is not None:
        return bridge.get_cluster_summary().health
    if graph is None:
        return "unknown"
    clusters = nodes_of_type(graph, "Cluster")
    return "present" if clusters else "unknown"


def _simulation_state(bridge: GraphBridge | None, graph: ResourceGraph | None) -> str:
    if bridge is not None:
        return "active" if bridge.simulation_state().active else "idle"
    if graph is None:
        return "idle"
    return "active" if nodes_of_type(graph, "Simulation") else "idle"


def _context_confidence(
    intent: IntentContext,
    pattern: object | None,
    has_graph: bool,
    history: tuple[TelemetryPoint, ...],
) -> int:
    score = intent.confidence * 0.55
    if pattern is not None:
        score += 20
    if has_graph:
        score += 15
    if len(history) >= 10:
        score += 10
    elif history:
        score += 5
    return int(max(0, min(100, round(score))))
