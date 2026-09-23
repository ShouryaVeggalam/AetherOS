"""Read-only telemetry collector backed by psutil.

This module never changes system state. It only *reads* CPU, memory,
disk, battery, and process information from the OS via userspace APIs.
"""

from __future__ import annotations

import os
from typing import Sequence

import psutil

from aetheros.telemetry.models import (
    BatterySnapshot,
    CpuSnapshot,
    DiskSnapshot,
    MemorySnapshot,
    ProcessSnapshot,
    SystemSnapshot,
    utc_now,
)


class TelemetryCollector:
    """Collects a single SystemSnapshot from the host.

    Args:
        disk_mounts: Mount points to measure. Defaults to root ("/").
        process_limit: Max number of processes to include, ranked by
            CPU usage. Use a limit so snapshots stay small and fast.
    """

    def __init__(
        self,
        disk_mounts: Sequence[str] | None = None,
        process_limit: int = 15,
    ) -> None:
        """Store collection settings."""

        self._disk_mounts: tuple[str, ...] = tuple(disk_mounts or ("/",))
        self._process_limit = process_limit
        # Prime CPU percent counters so the first real sample is meaningful.
        # psutil needs two samples spaced in time to compute CPU %.
        psutil.cpu_percent(interval=None)
        for proc in psutil.process_iter(["pid"]):
            try:
                proc.cpu_percent(interval=None)
            except (psutil.Error, ProcessLookupError, PermissionError):
                continue

    def collect(self) -> SystemSnapshot:
        """Gather one full telemetry snapshot.

        Returns:
            An immutable SystemSnapshot of the current host state.
        """

        return SystemSnapshot(
            collected_at=utc_now(),
            cpu=self._collect_cpu(),
            memory=self._collect_memory(),
            disks=self._collect_disks(),
            processes=self._collect_processes(),
            battery=self._collect_battery(),
        )

    def _collect_cpu(self) -> CpuSnapshot:
        """Read overall and per-core CPU usage plus load average."""

        overall = float(psutil.cpu_percent(interval=None))
        per_core = tuple(float(v) for v in psutil.cpu_percent(interval=None, percpu=True))
        try:
            load_1, load_5, load_15 = os.getloadavg()
            load_avg = (float(load_1), float(load_5), float(load_15))
        except (AttributeError, OSError):
            # Windows / rare platforms without getloadavg.
            load_avg = (0.0, 0.0, 0.0)
        return CpuSnapshot(percent=overall, per_cpu_percent=per_core, load_avg=load_avg)

    def _collect_memory(self) -> MemorySnapshot:
        """Read physical RAM and swap usage."""

        virtual = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return MemorySnapshot(
            total_bytes=int(virtual.total),
            available_bytes=int(virtual.available),
            used_bytes=int(virtual.used),
            percent=float(virtual.percent),
            swap_total_bytes=int(swap.total),
            swap_used_bytes=int(swap.used),
            swap_percent=float(swap.percent),
        )

    def _collect_disks(self) -> tuple[DiskSnapshot, ...]:
        """Read disk usage for each configured mount point."""

        snapshots: list[DiskSnapshot] = []
        for mount in self._disk_mounts:
            try:
                usage = psutil.disk_usage(mount)
            except (OSError, PermissionError):
                continue
            snapshots.append(
                DiskSnapshot(
                    mountpoint=mount,
                    total_bytes=int(usage.total),
                    used_bytes=int(usage.used),
                    free_bytes=int(usage.free),
                    percent=float(usage.percent),
                )
            )
        return tuple(snapshots)

    def _collect_battery(self) -> BatterySnapshot | None:
        """Read battery status when hardware exposes one."""

        battery = psutil.sensors_battery()
        if battery is None:
            return None
        secs = float(battery.secsleft) if battery.secsleft >= 0 else None
        return BatterySnapshot(
            percent=float(battery.percent),
            is_plugged_in=bool(battery.power_plugged),
            secs_left=secs,
        )

    def _collect_processes(self) -> tuple[ProcessSnapshot, ...]:
        """List top processes by CPU percent, capped by process_limit."""

        rows: list[ProcessSnapshot] = []
        for proc in psutil.process_iter(
            ["pid", "name", "username", "status", "memory_percent"]
        ):
            try:
                info = proc.info
                cpu = float(proc.cpu_percent(interval=None) or 0.0)
                rows.append(
                    ProcessSnapshot(
                        pid=int(info["pid"]),
                        name=str(info["name"] or "unknown"),
                        username=info.get("username"),
                        cpu_percent=cpu,
                        memory_percent=float(info.get("memory_percent") or 0.0),
                        status=str(info.get("status") or "unknown"),
                    )
                )
            except (psutil.Error, ProcessLookupError, PermissionError):
                # Process may exit between iteration and read — skip it.
                continue

        rows.sort(key=lambda item: item.cpu_percent, reverse=True)
        return tuple(rows[: self._process_limit])
