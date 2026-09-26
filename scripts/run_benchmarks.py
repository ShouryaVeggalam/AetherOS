#!/usr/bin/env python3
"""Reproducible micro-benchmarks for AetherOS v5.0 Nexus release engineering.

Measures userspace CPU time only — no network, no privileged calls.
Writes JSON to reports/benchmarks.json and prints a Markdown table.
"""

from __future__ import annotations

import json
import statistics
import time
import tracemalloc
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from aetheros.graph import build_resource_graph
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.reasoning import observation_from_metrics
from aetheros.reasoning import reason as graph_reason
from aetheros.telemetry import TelemetryCollector
from aetheros.twin import DigitalTwinSimulator, builtin_scenario, create_snapshot


@dataclass(frozen=True, slots=True)
class BenchResult:
    name: str
    iterations: int
    mean_ms: float
    p95_ms: float
    min_ms: float
    max_ms: float
    peak_kib: float | None = None


def _timed(fn, *, iterations: int = 25, warmup: int = 3) -> BenchResult:
    for _ in range(warmup):
        fn()
    samples: list[float] = []
    tracemalloc.start()
    for _ in range(iterations):
        start = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - start) * 1000.0)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    ordered = sorted(samples)
    p95 = ordered[max(0, int(len(ordered) * 0.95) - 1)]
    return BenchResult(
        name=fn.__name__,
        iterations=iterations,
        mean_ms=round(statistics.fmean(samples), 3),
        p95_ms=round(p95, 3),
        min_ms=round(min(samples), 3),
        max_ms=round(max(samples), 3),
        peak_kib=round(peak / 1024.0, 1),
    )


def bench_startup_import() -> BenchResult:
    """Time a fresh subprocess import of aetheros (measured separately)."""

    import subprocess
    import sys

    samples: list[float] = []
    for _ in range(8):
        start = time.perf_counter()
        subprocess.run(
            [sys.executable, "-c", "import aetheros"],
            check=True,
            capture_output=True,
        )
        samples.append((time.perf_counter() - start) * 1000.0)
    ordered = sorted(samples)
    return BenchResult(
        name="startup_import",
        iterations=len(samples),
        mean_ms=round(statistics.fmean(samples), 3),
        p95_ms=round(ordered[max(0, int(len(ordered) * 0.95) - 1)], 3),
        min_ms=round(min(samples), 3),
        max_ms=round(max(samples), 3),
        peak_kib=None,
    )


def main() -> int:
    collector = TelemetryCollector(process_limit=5)
    system = collector.collect()
    snapshot = TelemetrySnapshot.from_system_snapshot(system)

    def telemetry_refresh() -> None:
        collector.collect()

    def graph_build() -> None:
        build_resource_graph(system, intent_name="Balanced")

    graph = build_resource_graph(system, intent_name="Balanced")
    obs = observation_from_metrics(
        cpu=snapshot.cpu_percent,
        memory=snapshot.memory_percent,
        disk=snapshot.disk_percent,
    )

    def reasoning_latency() -> None:
        graph_reason(graph, obs, history=())

    twin_snap = create_snapshot(graph, snapshot, intent="Balanced")
    scenario = builtin_scenario("CPU_OVERLOAD")
    simulator = DigitalTwinSimulator()

    def simulation_latency() -> None:
        simulator.run(twin_snap, scenario)

    results = [
        _timed(telemetry_refresh, iterations=30),
        _timed(graph_build, iterations=40),
        _timed(reasoning_latency, iterations=40),
        _timed(simulation_latency, iterations=30),
        bench_startup_import(),
    ]

    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "version": __import__("aetheros").__version__,
        "methodology": {
            "timer": "time.perf_counter",
            "memory": "tracemalloc peak (per timed suite; None for subprocess)",
            "warmup": 3,
            "host": "userspace only; no privileged APIs",
        },
        "results": [asdict(r) for r in results],
    }
    out = Path("reports/benchmarks.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print("| Benchmark | Mean (ms) | p95 (ms) | Peak KiB | N |")
    print("|-----------|----------:|---------:|---------:|--:|")
    for r in results:
        peak = "—" if r.peak_kib is None else f"{r.peak_kib:.1f}"
        print(
            f"| {r.name} | {r.mean_ms:.3f} | {r.p95_ms:.3f} | {peak} | {r.iterations} |"
        )
    print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
