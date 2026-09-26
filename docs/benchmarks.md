# Benchmarks — AetherOS v5.0 Nexus

Reproducible userspace micro-benchmarks for the **v5.0.0** production release.

**Do not** treat these as hardware certifications. Numbers vary by host load,
Python build, and `psutil` collection cost.

## How to reproduce

```bash
pip install -e ".[dev]"
python scripts/run_benchmarks.py
# → prints Markdown table
# → writes reports/benchmarks.json
```

Optional: pin affinity / quiet the host before measuring.

```bash
# Example (Linux): reduce noise
nice -n 10 python scripts/run_benchmarks.py
```

### Methodology

| Control | Value |
|---------|-------|
| Timer | `time.perf_counter` |
| Warmup | 3 iterations (discarded) per in-process bench |
| Memory | `tracemalloc` peak KiB (in-process only) |
| Privileges | None — userspace only |
| Network | Not measured |
| Disk IO | Not intentionally stressed |
| Seed data | Live local telemetry via `TelemetryCollector` |
| Coverage gate | Orthogonal — `pytest --cov=aetheros --cov-fail-under=90` |

Raw JSON artifact: [`reports/benchmarks.json`](../reports/benchmarks.json)
(generated locally; regenerate before tagging).

### What each probe measures

| Benchmark | Code path (conceptual) | Notes |
|-----------|------------------------|-------|
| Telemetry refresh | Collector → snapshot | Dominated by OS counter sampling |
| Graph build | Snapshot → Resource Graph | Pure Python / NetworkX sample |
| Reasoning latency | Graph → hypotheses / verify | Evidence-backed; no LLM |
| Simulation latency | Twin scenario evaluate | In-process what-if only |
| Startup import | `import aetheros` | Subprocess spawn + import graph |

## Reference results (Nexus host)

Captured during v5.0.0 release engineering on a CI-like Linux agent
(`python3.12 scripts/run_benchmarks.py`, 2026-09-26).

| Benchmark | Mean (ms) | p95 (ms) | Peak KiB | N |
|-----------|----------:|---------:|---------:|--:|
| Telemetry refresh | 9.287 | 9.378 | 86.0 | 30 |
| Graph build | 0.256 | 0.292 | 5.3 | 40 |
| Reasoning latency | 0.286 | 0.316 | 36.4 | 40 |
| Simulation latency | 0.332 | 0.368 | 33.1 | 30 |
| Startup import (`import aetheros`) | 112.371 | 119.889 | — | 8 |

> Re-run `scripts/run_benchmarks.py` on your host and replace this table before
> publishing marketing claims. Keep methodology columns identical for comparison.

## Quality companion metrics

| Metric | Gate | Nexus measurement |
|--------|------|-------------------|
| Line coverage (`aetheros/`) | ≥ 90% | ~95.24% (full suite) |
| Import cycles | Zero cycles into higher layers | `scripts/check_import_cycles.py` |
| Lint / format | Clean | `ruff check .` · `black --check .` |

```bash
pytest --cov=aetheros --cov-report=term-missing --cov-report=xml --cov-fail-under=90
```

## Interpretation

- **Telemetry refresh** dominates because it samples live OS counters.
- **Graph build / reasoning / twin simulation** are typically sub-millisecond on modest hosts when operating on a single snapshot.
- **Startup import** includes interpreter spawn + package import graph (grows with platform surface; still userspace-only).

## Non-goals

- No GPU / distributed cluster stress tests in v5.0.0.
- No LLM latency (foundation models are out of core AetherOS).
- No marketplace network install timing (catalog is local/fixture-oriented).
- No enterprise multi-tenant load tests in this micro-bench suite.
- No PDF or dashboard chrome performance claims.
