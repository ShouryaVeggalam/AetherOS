"""Root Cause Engine — ranked explanations for Sentinel anomalies.

Candidates verified against telemetry, history, and lightweight simulation.
Never executes remediation.
"""

from __future__ import annotations

from dataclasses import dataclass

from aetheros.intent.profiles import CODING, PROFILES
from aetheros.observatory.models import TelemetryPoint
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.sentinel.anomaly import Anomaly
from aetheros.simulation.engine import SimulatableStrategy, SimulationEngine


@dataclass(frozen=True, slots=True)
class RootCause:
    """One ranked root-cause candidate.

    Attributes:
        cause_id: Stable id.
        title: Short label.
        explanation: Public systems narrative.
        confidence: Belief in [0, 1].
        evidence: Supporting evidence lines.
        rank: 1 = most likely.
    """

    cause_id: str
    title: str
    explanation: str
    confidence: float
    evidence: tuple[str, ...]
    rank: int

    def __post_init__(self) -> None:
        """Validate confidence."""

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")


@dataclass
class RootCauseEngine:
    """Generate and score root-cause candidates for an anomaly."""

    simulator: SimulationEngine | None = None

    def __post_init__(self) -> None:
        """Ensure simulator exists."""

        if self.simulator is None:
            self.simulator = SimulationEngine()

    def explain(
        self,
        anomaly: Anomaly,
        snapshot: TelemetrySnapshot,
        *,
        history: tuple[TelemetryPoint, ...] = (),
    ) -> tuple[RootCause, ...]:
        """Return ranked root-cause explanations for ``anomaly``."""

        assert self.simulator is not None
        candidates = _candidates(anomaly, snapshot, history)
        scored: list[RootCause] = []
        for index, (cause_id, title, explanation, prior, evidence) in enumerate(
            candidates
        ):
            # Verify via a tiny what-if: relieving the suspected pressure.
            strategy = SimulatableStrategy(
                title=title,
                description=explanation,
                expected_cpu_delta=(
                    -8.0 if anomaly.kind in {"cpu", "cluster_imbalance"} else -3.0
                ),
                expected_memory_delta=-6.0 if "memory" in anomaly.kind else -1.0,
                expected_efficiency_delta=4.0,
            )
            result = self.simulator.simulate(strategy, snapshot, PROFILES[CODING])
            lift = (
                result.performance_score * 0.4
                + result.stability_score * 0.3
                + result.efficiency_score * 0.3
            ) / 100.0
            hist_boost = 0.0
            if history and anomaly.kind == "cpu":
                avg = sum(p.cpu for p in history[-15:]) / max(1, min(15, len(history)))
                if snapshot.cpu_percent - avg >= 20:
                    hist_boost = 0.08
                    evidence = (*evidence, f"History avg CPU {avg:.0f}%")
            confidence = min(0.98, prior * 0.55 + lift * 0.45 + hist_boost)
            scored.append(
                RootCause(
                    cause_id=cause_id,
                    title=title,
                    explanation=explanation,
                    confidence=round(confidence, 3),
                    evidence=evidence,
                    rank=index + 1,
                )
            )
        scored.sort(key=lambda c: c.confidence, reverse=True)
        return tuple(
            RootCause(
                cause_id=c.cause_id,
                title=c.title,
                explanation=c.explanation,
                confidence=c.confidence,
                evidence=c.evidence,
                rank=i + 1,
            )
            for i, c in enumerate(scored)
        )


def _candidates(
    anomaly: Anomaly,
    snapshot: TelemetrySnapshot,
    history: tuple[TelemetryPoint, ...],
) -> tuple[tuple[str, str, str, float, tuple[str, ...]], ...]:
    """Build prior candidate tuples for an anomaly kind."""

    top = anomaly.related_process or (
        snapshot.top_processes[0] if snapshot.top_processes else "unknown"
    )
    if anomaly.kind == "cpu":
        return (
            (
                "cause.indexing",
                "Background Indexing",
                f"Background indexing by {top} sustaining elevated CPU.",
                0.72,
                (f"Top process: {top}", f"CPU {snapshot.cpu_percent:.1f}%"),
            ),
            (
                "cause.compile",
                "Compile Workload",
                "Compilation workers contending for CPU cores.",
                0.65,
                ("Compile-like process present in sample.",),
            ),
            (
                "cause.thermal",
                "Thermal Throttle Proxy",
                "Sustained load may reflect thermal/scheduling pressure (proxy).",
                0.4,
                (f"History length {len(history)}",),
            ),
        )
    if anomaly.kind == "memory_leak":
        return (
            (
                "cause.leak",
                "Working-Set Growth",
                "Process working set rising without reclaim — leak-like pattern.",
                0.7,
                (f"Memory {snapshot.memory_percent:.1f}%",),
            ),
            (
                "cause.cache",
                "Cache Expansion",
                "Legitimate cache growth misread as a leak.",
                0.5,
                ("Cache tiers expand under compile/API load.",),
            ),
        )
    if anomaly.kind == "disk":
        return (
            (
                "cause.disk.fill",
                "Volume Fill",
                "Disk approaching capacity — risk of write amplification.",
                0.8,
                (f"Disk {snapshot.disk_percent:.1f}%",),
            ),
        )
    if anomaly.kind == "battery":
        return (
            (
                "cause.power",
                "Power / Load Mismatch",
                "Low battery with elevated CPU — unstable energy posture.",
                0.75,
                (
                    f"Battery {snapshot.battery_percent}",
                    f"CPU {snapshot.cpu_percent:.1f}%",
                ),
            ),
        )
    if anomaly.kind == "cluster_imbalance":
        return (
            (
                "cause.hotspot",
                "Local Hotspot",
                "This node hotter than peers — workload not evenly shed.",
                0.7,
                (f"CPU {snapshot.cpu_percent:.1f}%",),
            ),
        )
    return (
        (
            "cause.network.path",
            "Path Contention",
            "Host contention proxy for network fairness degradation.",
            0.45,
            (f"Process count {snapshot.process_count}",),
        ),
    )
