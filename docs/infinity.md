# AetherOS ∞ — Infinity

The unifying generation of the Explainable Operating Intelligence Platform,
built under the [CELESTRA](CELESTRA.md) founding charter.

## Identity

| AetherOS is | AetherOS is not |
|-------------|-----------------|
| Userspace intelligence | An operating system |
| Explainable recommendations | A Linux distribution |
| Simulation-first | A kernel or driver |
| Human-in-the-loop | An autonomous controller |

## Pipeline

Telemetry → Observatory → Evidence → Reasoning → Simulation → Prediction → Explainability → Recommendation → **Human Approval**

## Dashboard

Press **I** for Infinity overview (generations, pipeline, layer status).

## API

```
GET /infinity
```

## Public API

```python
from aetheros.infinity import InfinityRuntime, GENERATIONS, PIPELINE, PRINCIPLES

report = InfinityRuntime().observe()
assert "Human-in-the-loop" in report.status
```

## Package README

See [`aetheros/infinity/README.md`](../aetheros/infinity/README.md).
