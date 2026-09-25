"""Optional adapters — project GraphContext into subsystem-friendly views.

Existing prediction / reasoning / simulation modules are unchanged.
Callers may optionally pass these views instead of raw telemetry tuples.
"""

from __future__ import annotations

from dataclasses import dataclass

from aetheros.context.models import GraphContext, IntentName


@dataclass(frozen=True, slots=True)
class PredictionContextView:
    """Minimal prediction-facing projection of GraphContext."""

    cpu_load: float
    memory_load: float
    disk_load: float
    intent: IntentName
    confidence: int


@dataclass(frozen=True, slots=True)
class ReasoningContextView:
    """Minimal reasoning-facing projection of GraphContext."""

    intent: IntentName
    foreground_process: str | None
    cpu_load: float
    historical_label: str | None
    confidence: int


@dataclass(frozen=True, slots=True)
class SimulationContextView:
    """Minimal simulation-facing projection of GraphContext."""

    cpu_load: float
    memory_load: float
    disk_load: float
    battery_state: str
    simulation_state: str
    intent: IntentName


def for_prediction(ctx: GraphContext) -> PredictionContextView:
    """Adapt GraphContext for prediction consumers."""

    return PredictionContextView(
        cpu_load=ctx.cpu_load,
        memory_load=ctx.memory_load,
        disk_load=ctx.disk_load,
        intent=ctx.active_intent.name,
        confidence=ctx.confidence,
    )


def for_reasoning(ctx: GraphContext) -> ReasoningContextView:
    """Adapt GraphContext for reasoning consumers."""

    pattern = ctx.historical_pattern
    return ReasoningContextView(
        intent=ctx.active_intent.name,
        foreground_process=ctx.foreground_process,
        cpu_load=ctx.cpu_load,
        historical_label=pattern.label if pattern is not None else None,
        confidence=ctx.confidence,
    )


def for_simulation(ctx: GraphContext) -> SimulationContextView:
    """Adapt GraphContext for digital-twin / simulation consumers."""

    return SimulationContextView(
        cpu_load=ctx.cpu_load,
        memory_load=ctx.memory_load,
        disk_load=ctx.disk_load,
        battery_state=ctx.battery_state,
        simulation_state=ctx.simulation_state,
        intent=ctx.active_intent.name,
    )
