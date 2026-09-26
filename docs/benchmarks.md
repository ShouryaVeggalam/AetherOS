# Benchmarks — AetherOS Horizon / Nexus

Reproducible **userspace** micro-benchmarks for AetherOS.

**Do not** treat these as hardware certifications, cloud SLAs, or marketing claims
without re-running the harness on your host. Numbers vary by load, Python build,
and `psutil` collection cost.

**Do not invent results.** If a cell is unknown, leave it as `[TBD]` or omit it.

---

## How to reproduce

```bash
pip install -e ".[dev]"
python scripts/run_benchmarks.py
# → prints Markdown table
# → writes reports/benchmarks.json
```

Quiet the host when comparing runs:

```bash
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
(generated locally; regenerate before tagging a release).

### What each probe measures

| Benchmark | Code path (conceptual) | Notes |
|-----------|------------------------|-------|
| Telemetry refresh | Collector → snapshot | Dominated by OS counter sampling |
| Graph build | Snapshot → Resource Graph | Pure Python / NetworkX sample |
| Reasoning latency | Graph → hypotheses / verify | Evidence-backed; no LLM |
| Simulation latency | Twin scenario evaluate | In-process what-if only |
| Startup import | `import aetheros` | Subprocess spawn + import graph |

---

## Reference results (Nexus host)

Captured during **v5.0.0** release engineering on a CI-like Linux agent
(`python3.12 scripts/run_benchmarks.py`, 2026-09-26).

| Benchmark | Mean (ms) | p95 (ms) | Peak KiB | N |
|-----------|----------:|---------:|---------:|--:|
| Telemetry refresh | 9.287 | 9.378 | 86.0 | 30 |
| Graph build | 0.256 | 0.292 | 5.3 | 40 |
| Reasoning latency | 0.286 | 0.316 | 36.4 | 40 |
| Simulation latency | 0.332 | 0.368 | 33.1 | 30 |
| Startup import (`import aetheros`) | 112.371 | 119.889 | — | 8 |

> Re-run `scripts/run_benchmarks.py` on your host and replace this table before
> publishing performance claims. Keep methodology columns identical for comparison.

---

## Horizon probes (placeholders)

Fill only after running a documented harness on a named host. Until then, keep `[TBD]`.

| Benchmark | Mean (ms) | p95 (ms) | Peak KiB | N | Notes |
|-----------|----------:|---------:|---------:|--:|-------|
| Cloud demo snapshot seed | [TBD] | [TBD] | [TBD] | [TBD] | `seed_demo_cloud` |
| Infra twin REGION_OUTAGE | [TBD] | [TBD] | [TBD] | [TBD] | clone → apply → evaluate |
| Planetary schedule (demo sites) | [TBD] | [TBD] | [TBD] | [TBD] | constrain → score → twin → top-5 |
| Horizon overview render | [TBD] | [TBD] | [TBD] | [TBD] | Rich frame compose |
| Global graph demo build | [TBD] | [TBD] | [TBD] | [TBD] | ontology + evidence |

---

## Quality companion metrics

| Metric | Gate | Notes |
|--------|------|-------|
| Line coverage (`aetheros/`) | ≥ 90% | Full suite via CI |
| Import cycles | Zero into higher layers | `scripts/check_import_cycles.py` |
| Lint / format | Clean | `ruff check .` · `black --check .` |

```bash
pytest --cov=aetheros --cov-report=term-missing --cov-report=xml --cov-fail-under=90
```

---

## Interpretation

- **Telemetry refresh** dominates because it samples live OS counters.
- **Graph build / reasoning / twin simulation** are typically sub-millisecond on modest hosts for a single snapshot.
- **Startup import** includes interpreter spawn + package import graph (grows with platform surface; still userspace-only).
- Horizon probes may be higher cost (multi-cloud demo census + twin) — measure before claiming.

---

## Non-goals

- No GPU / distributed cluster stress tests in this suite.
- No LLM latency (foundation models are out of core AetherOS).
- No marketplace network install timing (catalog is local/fixture-oriented).
- No enterprise multi-tenant load tests.
- No PDF or dashboard chrome FPS claims.
- No invented planetary “accuracy vs Kubernetes” numbers without an offline corpus protocol.

---

## Related

- [Installation](installation.md)
- [v6.0 Horizon release notes](releases/v6.0.0.md)
- [Research paper — Benchmarks section](papers/aetheros_explainable_operating_intelligence.md)
