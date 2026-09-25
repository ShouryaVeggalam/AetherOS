"""Anomaly Engine — detect emerging infrastructure anomalies.

Returns immutable anomaly objects from telemetry + history.
Never remediates. Never executes commands.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from aetheros.observatory.models import TelemetryPoint
from aetheros.policy_engine.models import TelemetrySnapshot

AnomalyKind = Literal[
    "cpu",
    "memory_leak",
    "network",
    "disk",
    "battery",
    "cluster_imbalance",
]

AnomalySeverity = Literal["low", "medium", "high"]


@dataclass(frozen=True, slots=True)
class Anomaly:
    """One immutable detected anomaly.

    Attributes:
        anomaly_id: Stable id.
        kind: Anomaly class.
        severity: low | medium | high.
        title: Short label.
        description: Public systems explanation.
        metric: Primary metric name.
        value: Observed value.
        threshold: Threshold that was crossed.
        detected_at: UTC detection time.
        related_process: Optional top process hint.
    """

    anomaly_id: str
    kind: AnomalyKind
    severity: AnomalySeverity
    title: str
    description: str
    metric: str
    value: float
    threshold: float
    detected_at: datetime
    related_process: str | None = None


@dataclass
class AnomalyEngine:
    """Detect anomalies from a snapshot and optional history."""

    def detect(
        self,
        snapshot: TelemetrySnapshot,
        *,
        history: tuple[TelemetryPoint, ...] = (),
        cluster_avg_cpu: float | None = None,
    ) -> tuple[Anomaly, ...]:
        """Return immutable anomalies for the current sample."""

        now = snapshot.timestamp if snapshot.timestamp.tzinfo else datetime.now(UTC)
        found: list[Anomaly] = []
        top = snapshot.top_processes[0] if snapshot.top_processes else None

        if snapshot.cpu_percent >= 90.0:
            sev: AnomalySeverity = "high" if snapshot.cpu_percent >= 95.0 else "medium"
            found.append(
                Anomaly(
                    "anom.cpu",
                    "cpu",
                    sev,
                    "CPU Anomaly",
                    f"CPU at {snapshot.cpu_percent:.1f}% exceeds healthy band.",
                    "cpu",
                    snapshot.cpu_percent,
                    90.0,
                    now,
                    top,
                )
            )
        elif history and len(history) >= 5:
            avg = sum(p.cpu for p in history[-20:]) / min(20, len(history))
            jump = snapshot.cpu_percent - avg
            if jump >= 35.0:
                found.append(
                    Anomaly(
                        "anom.cpu.jump",
                        "cpu",
                        "medium" if jump < 45 else "high",
                        "CPU Jump",
                        f"CPU jumped {jump:.0f}% above recent average {avg:.0f}%.",
                        "cpu",
                        snapshot.cpu_percent,
                        avg + 35.0,
                        now,
                        top,
                    )
                )

        if snapshot.memory_percent >= 88.0:
            leak_hint = False
            if len(history) >= 8:
                early = sum(p.memory for p in history[:4]) / 4.0
                late = sum(p.memory for p in history[-4:]) / 4.0
                leak_hint = late - early >= 8.0
            kind: AnomalyKind = "memory_leak" if leak_hint else "memory_leak"
            found.append(
                Anomaly(
                    "anom.memory",
                    kind,
                    "high" if snapshot.memory_percent >= 95 else "medium",
                    "Memory Pressure" if not leak_hint else "Memory Leak Signal",
                    (
                        f"Memory at {snapshot.memory_percent:.1f}%."
                        + (
                            " Rising trend suggests leak-like growth."
                            if leak_hint
                            else ""
                        )
                    ),
                    "memory",
                    snapshot.memory_percent,
                    88.0,
                    now,
                    top,
                )
            )

        if snapshot.disk_percent >= 90.0:
            found.append(
                Anomaly(
                    "anom.disk",
                    "disk",
                    "high" if snapshot.disk_percent >= 95 else "medium",
                    "Disk Saturation",
                    f"Disk at {snapshot.disk_percent:.1f}% — saturation risk.",
                    "disk",
                    snapshot.disk_percent,
                    90.0,
                    now,
                    top,
                )
            )

        if snapshot.battery_percent is not None and snapshot.battery_percent < 20.0:
            if snapshot.cpu_percent >= 60.0:
                found.append(
                    Anomaly(
                        "anom.battery",
                        "battery",
                        "medium",
                        "Battery Instability",
                        (
                            f"Battery {snapshot.battery_percent:.0f}% with CPU "
                            f"{snapshot.cpu_percent:.0f}% — unstable energy posture."
                        ),
                        "battery",
                        float(snapshot.battery_percent),
                        20.0,
                        now,
                        top,
                    )
                )

        # Network degradation proxy: sustained high CPU + many processes.
        if snapshot.cpu_percent >= 80.0 and snapshot.process_count >= 8:
            found.append(
                Anomaly(
                    "anom.network",
                    "network",
                    "low",
                    "Network Degradation Risk",
                    (
                        "High host contention may degrade local network path "
                        "fairness (proxy signal — no live probe)."
                    ),
                    "network",
                    float(snapshot.process_count),
                    8.0,
                    now,
                    top,
                )
            )

        if cluster_avg_cpu is not None:
            delta = snapshot.cpu_percent - cluster_avg_cpu
            if delta >= 20.0:
                found.append(
                    Anomaly(
                        "anom.cluster",
                        "cluster_imbalance",
                        "medium" if delta < 35 else "high",
                        "Cluster Imbalance",
                        (
                            f"Local CPU {snapshot.cpu_percent:.0f}% vs cluster avg "
                            f"{cluster_avg_cpu:.0f}% (Δ {delta:.0f}%)."
                        ),
                        "cpu",
                        snapshot.cpu_percent,
                        cluster_avg_cpu + 20.0,
                        now,
                        top,
                    )
                )

        return tuple(found)
