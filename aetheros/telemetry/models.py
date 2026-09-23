"""Typed snapshot models for system telemetry.

These dataclasses are plain data containers: they hold measurements
collected from the OS. Nothing here talks to hardware or changes state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True, slots=True)
class CpuSnapshot:
    """CPU utilization at one moment in time.

    Attributes:
        percent: Overall CPU usage from 0.0 to 100.0.
        per_cpu_percent: Usage for each logical core.
        load_avg: 1-, 5-, and 15-minute load averages (Unix).
    """

    percent: float
    per_cpu_percent: tuple[float, ...]
    load_avg: tuple[float, float, float]


@dataclass(frozen=True, slots=True)
class MemorySnapshot:
    """Physical and swap memory usage.

    Attributes:
        total_bytes: Total physical RAM in bytes.
        available_bytes: RAM available for new allocations.
        used_bytes: RAM currently in use.
        percent: Used RAM as a percentage of total.
        swap_total_bytes: Total swap space in bytes.
        swap_used_bytes: Swap currently in use.
        swap_percent: Used swap as a percentage of total.
    """

    total_bytes: int
    available_bytes: int
    used_bytes: int
    percent: float
    swap_total_bytes: int
    swap_used_bytes: int
    swap_percent: float


@dataclass(frozen=True, slots=True)
class DiskSnapshot:
    """Disk capacity for one mount point.

    Attributes:
        mountpoint: Filesystem path being measured (e.g. "/").
        total_bytes: Total capacity of the volume.
        used_bytes: Bytes currently used.
        free_bytes: Bytes still free.
        percent: Used space as a percentage of total.
    """

    mountpoint: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    percent: float


@dataclass(frozen=True, slots=True)
class BatterySnapshot:
    """Battery status when a battery is present.

    On desktops, VMs, and many WSL setups this will be absent.
    Reading battery state is safe and read-only.

    Attributes:
        percent: Charge remaining from 0.0 to 100.0.
        is_plugged_in: True when AC power is connected.
        secs_left: Estimated seconds of runtime, or None if unknown.
    """

    percent: float
    is_plugged_in: bool
    secs_left: float | None


@dataclass(frozen=True, slots=True)
class ProcessSnapshot:
    """A single running process.

    Attributes:
        pid: Process ID assigned by the OS.
        name: Short process name.
        username: Owner of the process, if available.
        cpu_percent: Approximate CPU share for this process.
        memory_percent: Approximate RAM share for this process.
        status: Process state string (e.g. "running", "sleeping").
    """

    pid: int
    name: str
    username: str | None
    cpu_percent: float
    memory_percent: float
    status: str


@dataclass(frozen=True, slots=True)
class SystemSnapshot:
    """Full telemetry sample taken at one instant.

    Attributes:
        collected_at: UTC timestamp when the sample was taken.
        cpu: CPU measurements.
        memory: Memory measurements.
        disks: Disk measurements for watched mount points.
        processes: Selected running processes.
        battery: Battery info, or None if unavailable.
    """

    collected_at: datetime
    cpu: CpuSnapshot
    memory: MemorySnapshot
    disks: tuple[DiskSnapshot, ...]
    processes: tuple[ProcessSnapshot, ...]
    battery: BatterySnapshot | None = None


def utc_now() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""

    return datetime.now(timezone.utc)
