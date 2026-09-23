"""Pure policy rules over a TelemetrySnapshot.

Each detector returns a PolicyRecommendation or None.
Nothing here prints, executes commands, or changes the OS.
"""

from __future__ import annotations

from aetheros.policy_engine.models import PolicyRecommendation, TelemetrySnapshot

# Thresholds (percent). Tunable later via config — kept here for Phase 2 clarity.
CPU_WARNING = 85.0
CPU_CRITICAL = 95.0
MEMORY_WARNING = 90.0
MEMORY_CRITICAL = 95.0
DISK_WARNING = 90.0
DISK_CRITICAL = 95.0
IDLE_CPU_MAX = 15.0
IDLE_MEMORY_MAX = 40.0


def detect_cpu_overload(snapshot: TelemetrySnapshot) -> PolicyRecommendation | None:
    """Detect high overall CPU usage.

    Args:
        snapshot: Flat telemetry sample.

    Returns:
        A warning/critical recommendation, or None if CPU is fine.
    """

    cpu = snapshot.cpu_percent
    if cpu > CPU_CRITICAL:
        return PolicyRecommendation(
            level="critical",
            title="CPU Overload",
            reason=f"CPU usage has exceeded {CPU_CRITICAL:.0f}% (now {cpu:.1f}%).",
            recommended_action="Reduce background workload.",
            confidence=98,
        )
    if cpu > CPU_WARNING:
        return PolicyRecommendation(
            level="warning",
            title="High CPU Usage",
            reason=f"CPU usage has exceeded {CPU_WARNING:.0f}% (now {cpu:.1f}%).",
            recommended_action="Identify heavy processes and close unused apps.",
            confidence=90,
        )
    return None


def detect_memory_pressure(snapshot: TelemetrySnapshot) -> PolicyRecommendation | None:
    """Detect high memory (RAM) pressure.

    Args:
        snapshot: Flat telemetry sample.

    Returns:
        A warning/critical recommendation, or None if memory is fine.
    """

    mem = snapshot.memory_percent
    if mem > MEMORY_CRITICAL:
        return PolicyRecommendation(
            level="critical",
            title="Critical Memory Pressure",
            reason=f"Memory usage has exceeded {MEMORY_CRITICAL:.0f}% (now {mem:.1f}%).",
            recommended_action="Free RAM by closing unused applications.",
            confidence=97,
        )
    if mem > MEMORY_WARNING:
        return PolicyRecommendation(
            level="warning",
            title="High Memory Usage",
            reason=f"Memory usage has exceeded {MEMORY_WARNING:.0f}% (now {mem:.1f}%).",
            recommended_action="Review memory-heavy processes and free unused RAM.",
            confidence=90,
        )
    return None


def detect_disk_pressure(snapshot: TelemetrySnapshot) -> PolicyRecommendation | None:
    """Detect high disk utilization on watched mounts.

    Args:
        snapshot: Flat telemetry sample.

    Returns:
        A warning/critical recommendation, or None if disk space is fine.
    """

    disk = snapshot.disk_percent
    if disk > DISK_CRITICAL:
        return PolicyRecommendation(
            level="critical",
            title="Critical Disk Pressure",
            reason=f"Disk usage has exceeded {DISK_CRITICAL:.0f}% (now {disk:.1f}%).",
            recommended_action="Free disk space before the volume fills completely.",
            confidence=99,
        )
    if disk > DISK_WARNING:
        return PolicyRecommendation(
            level="warning",
            title="High Disk Usage",
            reason=f"Disk usage has exceeded {DISK_WARNING:.0f}% (now {disk:.1f}%).",
            recommended_action="Clear caches and remove unneeded large files.",
            confidence=92,
        )
    return None


def detect_idle_state(snapshot: TelemetrySnapshot) -> PolicyRecommendation | None:
    """Detect a lightly loaded (idle) system.

    Idle is informational (level=normal), not an alarm.

    Args:
        snapshot: Flat telemetry sample.

    Returns:
        A normal-level idle recommendation, or None if the system is busy.
    """

    if snapshot.cpu_percent < IDLE_CPU_MAX and snapshot.memory_percent < IDLE_MEMORY_MAX:
        return PolicyRecommendation(
            level="normal",
            title="Idle System",
            reason=(
                f"CPU is below {IDLE_CPU_MAX:.0f}% and memory is below "
                f"{IDLE_MEMORY_MAX:.0f}%."
            ),
            recommended_action="No action needed; system has spare capacity.",
            confidence=85,
        )
    return None
