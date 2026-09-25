"""Experiment builder — Digital Twin experiment plans from hypotheses.

Plans only. Execution happens in ``executor`` on cloned snapshots.
Default iteration count: 30.
"""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha1

from aetheros.research_ai.models import Experiment, Hypothesis, ResearchQuestion
from aetheros.twin.models import TwinSnapshot

DEFAULT_ITERATIONS = 30

# Map question cues → twin scenario kinds + variables.
_SCENARIO_MAP: tuple[tuple[tuple[str, ...], str, tuple[tuple[str, str], ...]], ...] = (
    (
        ("indexing", "compile", "disk"),
        "DISK_SATURATION",
        (("disk_delta", "25"), ("label", "indexing_load")),
    ),
    (
        ("compile", "disk"),
        "DISK_SATURATION",
        (("disk_delta", "20"), ("label", "compile_disk")),
    ),
    (
        ("charging", "thermal", "battery"),
        "BATTERY_LOW",
        (("battery_set", "15"), ("label", "thermal_charge")),
    ),
    (
        ("battery",),
        "BATTERY_LOW",
        (("battery_set", "10"), ("label", "battery_pressure")),
    ),
    (
        ("morning", "coding", "memory"),
        "MEMORY_PRESSURE",
        (("memory_delta", "15"), ("label", "morning_memory")),
    ),
    (
        ("cpu", "memory"),
        "CPU_OVERLOAD",
        (("cpu_delta", "30"), ("label", "cpu_then_memory")),
    ),
    (
        ("cpu",),
        "CPU_OVERLOAD",
        (("cpu_delta", "35"), ("label", "cpu_load")),
    ),
)


def build_experiment(
    hypothesis: Hypothesis,
    snapshot: TwinSnapshot,
    *,
    question: ResearchQuestion | None = None,
    iterations: int = DEFAULT_ITERATIONS,
    now: datetime | None = None,
) -> Experiment:
    """Create one Digital Twin experiment plan for ``hypothesis``."""

    if iterations < 1:
        raise ValueError("iterations must be >= 1")
    _ = now or datetime.now(UTC)
    haystack = " ".join(
        [
            hypothesis.statement,
            hypothesis.rationale,
            hypothesis.expected_outcome,
            question.title if question else "",
            question.objective if question else "",
        ]
    ).lower()
    scenario, variables = _select_scenario(haystack)
    eid = (
        "exp_"
        + sha1(
            f"{hypothesis.id}:{snapshot.id}:{scenario}:{iterations}".encode()
        ).hexdigest()[:12]
    )
    return Experiment(
        id=eid,
        hypothesis=hypothesis,
        scenario=scenario,
        iterations=iterations,
        snapshot_id=snapshot.id,
        variables=variables,
        metrics=("cpu", "memory", "disk", "stability", "confidence"),
    )


def _select_scenario(haystack: str) -> tuple[str, tuple[tuple[str, str], ...]]:
    for keywords, scenario, variables in _SCENARIO_MAP:
        if all(k in haystack for k in keywords):
            return scenario, variables
    # Fallback grounded scenario — still twin-only, never live.
    return "CPU_OVERLOAD", (("cpu_delta", "20"), ("label", "generic_probe"))
