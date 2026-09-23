"""Candidate strategy generator for autonomous research.

Produces at least five read-only optimization strategies shaped by
telemetry, intent, and historical patterns.
"""

from __future__ import annotations

from aetheros.intent.models import IntentProfile
from aetheros.learning.models import HistoricalPattern
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.research.models import CandidateStrategy


def generate_strategies(
    snapshot: TelemetrySnapshot,
    intent: IntentProfile,
    patterns: tuple[HistoricalPattern, ...] | list[HistoricalPattern],
) -> tuple[CandidateStrategy, ...]:
    """Generate at least five candidate strategies.

    Args:
        snapshot: Current telemetry sample.
        intent: Active user intent.
        patterns: Historical patterns from the learning engine.

    Returns:
        An immutable tuple of CandidateStrategy values.
    """

    cpu_pressure = max(0.0, snapshot.cpu_percent - 50.0) / 50.0
    mem_pressure = max(0.0, snapshot.memory_percent - 50.0) / 50.0
    pattern_cpu = max((p.cpu_bias for p in patterns), default=0.0)

    # Deltas are signed: negative CPU/memory = projected relief.
    interactive_cpu = -8.0 - (intent.latency_weight * 0.25) - (cpu_pressure * 4.0)
    background_cpu = -10.0 - (intent.efficiency_weight * 0.2) - (pattern_cpu * 0.1)
    balanced_cpu = -5.0 - (cpu_pressure * 2.0)
    memory_delta = -6.0 - (intent.memory_weight * 0.2) - (mem_pressure * 5.0)
    power_cpu = -4.0 - (intent.efficiency_weight * 0.15)

    strategies = (
        CandidateStrategy(
            title="Reduce Background Workload",
            description="Trim non-essential background activity to free CPU headroom.",
            expected_cpu_delta=round(background_cpu, 1),
            expected_memory_delta=round(-3.0 - mem_pressure * 2.0, 1),
            expected_efficiency_delta=round(8.0 + intent.efficiency_weight * 0.15, 1),
        ),
        CandidateStrategy(
            title="Interactive Priority Boost",
            description="Favor interactive responsiveness for the active intent.",
            expected_cpu_delta=round(interactive_cpu, 1),
            expected_memory_delta=round(-2.0 - intent.latency_weight * 0.05, 1),
            expected_efficiency_delta=round(5.0 + intent.latency_weight * 0.1, 1),
        ),
        CandidateStrategy(
            title="Increase Interactive Priority",
            description="Raise emphasis on foreground interactive tasks.",
            expected_cpu_delta=round(interactive_cpu * 0.85, 1),
            expected_memory_delta=-2.0,
            expected_efficiency_delta=4.0,
        ),
        CandidateStrategy(
            title="Balanced Resource Allocation",
            description="Spread relief evenly across CPU, memory, and efficiency.",
            expected_cpu_delta=round(balanced_cpu, 1),
            expected_memory_delta=round(-4.0 - mem_pressure * 2.0, 1),
            expected_efficiency_delta=6.0,
        ),
        CandidateStrategy(
            title="Memory Optimization",
            description="Target memory pressure while keeping CPU mostly stable.",
            expected_cpu_delta=-2.0,
            expected_memory_delta=round(memory_delta, 1),
            expected_efficiency_delta=5.0,
        ),
        CandidateStrategy(
            title="Power Efficient Mode",
            description="Prefer efficiency and lower sustained power draw.",
            expected_cpu_delta=round(power_cpu, 1),
            expected_memory_delta=-3.0,
            expected_efficiency_delta=round(12.0 + intent.efficiency_weight * 0.2, 1),
        ),
    )
    return strategies
