# Explainability

The Explainable Intelligence Engine produces **evidence-based** explanations for decisions. It never invents reasons that cannot be traced to telemetry, history, intent, or simulation results.

## Responsibilities

| Module | Role |
|--------|------|
| `models.py` | `Evidence`, `ReasoningChain`, `Explanation` |
| `evidence.py` | Collect facts from live and historical inputs |
| `confidence.py` | Score 0–100 from quality signals |
| `reasoning.py` | `ExplainabilityEngine` orchestration |
| `formatter.py` | Rich explanation panel |

## Evidence sources

- **Telemetry** — CPU, memory, disk, battery, top process CPU when available
- **History** — window averages, pressure streaks, session averages
- **Intent** — active profile and latency/efficiency bias
- **Simulation** — projected CPU, stability, improvement from `SimulationResult`

Missing inputs yield fewer evidence items — never fabricated metrics.

## Confidence

Confidence blends:

- telemetry completeness
- history length (toward 300-sample capacity)
- simulation agreement (when present)
- intent certainty from weight contrast

Factors without data contribute zero.

## Dashboard

| Key | Action |
|-----|--------|
| `E` | Toggle Explainability panel |
| `ESC` | Leave overlay |

## Contract

If a claim cannot be sourced from collected evidence, it must not appear in the explanation.
