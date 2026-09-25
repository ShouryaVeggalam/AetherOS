# Benchmarks — AetherOS v2.0 Intelligence

Reproducible userspace micro-benchmarks for the Release Candidate.

**Do not** treat these as hardware certifications. Numbers vary by host load,
Python build, and `psutil` collection cost.

## How to reproduce

```bash
pip install -e ".[dev]"
python scripts/run_benchmarks.py
# → prints Markdown table
# → writes reports/benchmarks.json
```

### Methodology

| Control | Value |
|---------|-------|
| Timer | `time.perf_counter` |
| Warmup | 3 iterations (discarded) per in-process bench |
| Memory | `tracemalloc` peak KiB (in-process only) |
| Privileges | None — userspace only |
| Network | Not measured |
| Seed data | Live local telemetry via `TelemetryCollector` |

Raw JSON artifact: [`reports/benchmarks.json`](../reports/benchmarks.json) (generated locally; regenerate before tagging).

## Reference results (RC host)

Captured during P10 release engineering on the CI-like Linux agent used for this RC.

| Benchmark | Mean (ms) | p95 (ms) | Peak KiB | N |
|-----------|----------:|---------:|---------:|--:|
| Telemetry refresh | 10.492 | 12.738 | 78.6 | 30 |
| Graph build | 0.320 | 0.354 | 5.3 | 40 |
| Reasoning latency | 0.351 | 0.369 | 36.4 | 40 |
| Simulation latency | 0.407 | 0.437 | 33.1 | 30 |
| Startup import (`import aetheros`) | 24.679 | 25.604 | — | 8 |

## Interpretation

- **Telemetry refresh** dominates because it samples live OS counters.
- **Graph build / reasoning / twin simulation** are sub-millisecond on modest hosts when operating on a single snapshot.
- **Startup import** includes interpreter spawn + package import graph.

## Non-goals

- No GPU / distributed cluster stress tests in v2.0.0 RC.
- No LLM latency (foundation models are out of core AetherOS).
- No PDF or dashboard chrome performance claims.
