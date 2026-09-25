"""Experiment executor — run twin simulations on cloned snapshots only.

Pipeline: Snapshot → Clone → Apply variables → Digital Twin → Metrics.

Never touches live telemetry, Resource Graph, or host OS state.
"""

from __future__ import annotations

from datetime import UTC, datetime

from aetheros.research_ai.models import Experiment, Result
from aetheros.twin.models import TwinSnapshot
from aetheros.twin.scenario import builtin_scenario
from aetheros.twin.simulator import DigitalTwinSimulator
from aetheros.twin.snapshot import clone_snapshot


def execute_experiment(
    experiment: Experiment,
    snapshot: TwinSnapshot,
    *,
    now: datetime | None = None,
    simulator: DigitalTwinSimulator | None = None,
) -> Result:
    """Execute ``experiment`` for ``experiment.iterations`` twin clones."""

    if not snapshot.id.strip() or not experiment.snapshot_id.strip():
        raise ValueError("snapshot ids must be non-empty")

    stamp = now or datetime.now(UTC)
    engine = simulator or DigitalTwinSimulator()
    scenario = _resolve_scenario(experiment, stamp)

    cpu_vals: list[float] = []
    mem_vals: list[float] = []
    disk_vals: list[float] = []
    stab_vals: list[float] = []
    conf_vals: list[float] = []
    evidence: list[str] = []
    success = 0

    for index in range(experiment.iterations):
        cloned = clone_snapshot(
            snapshot,
            now=stamp,
            snapshot_id=f"{snapshot.id}:run:{index}",
        )
        report = engine.run(cloned, scenario, now=stamp)
        twin_result = report.result
        cpu_vals.append(twin_result.predicted_cpu)
        mem_vals.append(twin_result.predicted_memory)
        disk_vals.append(twin_result.predicted_disk)
        stab_vals.append(twin_result.stability)
        conf_vals.append(twin_result.confidence)
        # Successful iteration: twin produced usable stability signal.
        if twin_result.stability >= 35.0:
            success += 1
        if index == 0:
            evidence.append(twin_result.reasoning)
            evidence.append(f"bottleneck={twin_result.bottleneck}")
            evidence.append(f"risk={twin_result.risk}")

    metrics = (
        ("cpu_mean", _mean(cpu_vals)),
        ("memory_mean", _mean(mem_vals)),
        ("disk_mean", _mean(disk_vals)),
        ("cpu_delta", _mean(cpu_vals) - snapshot.telemetry.cpu_percent),
        ("memory_delta", _mean(mem_vals) - snapshot.telemetry.memory_percent),
        ("disk_delta", _mean(disk_vals) - snapshot.telemetry.disk_percent),
    )
    evidence.append(
        f"iterations={experiment.iterations} successful={success} "
        f"scenario={experiment.scenario}"
    )
    # Research confidence blends twin stability with reproducibility —
    # distinct from twin evaluator's per-run prediction confidence.
    repro = 100.0 * success / max(1, experiment.iterations)
    research_confidence = round(
        min(
            99.0,
            0.45 * _mean(stab_vals) + 0.40 * repro + 0.15 * max(_mean(conf_vals), 40.0),
        ),
        2,
    )
    return Result(
        metrics=metrics,
        stability=_mean(stab_vals),
        confidence=research_confidence,
        evidence=tuple(evidence),
        successful_iterations=success,
        total_iterations=experiment.iterations,
    )


def _resolve_scenario(experiment: Experiment, stamp: datetime):
    name = experiment.scenario.strip().upper()
    try:
        return builtin_scenario(name, now=stamp)
    except ValueError:
        mods = experiment.variables or (("cpu_delta", "15"),)
        return builtin_scenario("CUSTOM", now=stamp, custom_mods=mods)


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)
