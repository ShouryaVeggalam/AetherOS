# Cognition Core (v3.0 P1)

Isolated deterministic intelligence layer that converts **graph evidence** into
structured operational understanding.

**Not an LLM.** Recommendation-only. Does not modify host OS state.

Legacy ``CognitiveRuntime`` (dashboard **K**) remains unchanged. This document
covers ``CognitionEngine`` and the v3 models in ``aetheros.cognition.models``.

---

## Architecture

```mermaid
flowchart LR
  RG[ResourceGraph] --> Observe
  Ctx[GraphContext] --> Observe
  Twin[DigitalTwin] --> Observe
  Hist[TelemetryHistory] --> Observe
  Mem[OperationalMemory] --> Observe
  Observe --> Evidence
  Evidence --> Reason
  Reason --> Hypotheses
  Hypotheses --> Verify
  Verify --> Verified
  Verified --> Plan
  Plan --> State[CognitionState]
```

| Module | Role |
|--------|------|
| `models.py` | `Evidence`, `Hypothesis` (Core), `CognitionState`, plans |
| `evidence.py` | Collect evidence from graph / context / twin / history |
| `memory.py` | `OperationalMemory` — verified system patterns only |
| `hypotheses.py` | `generate_core_hypotheses` (additive) |
| `verifier.py` | `verify_core_hypotheses` — graph + history + simulation gates |
| `planner.py` | `generate_cognition_plans` — Performance / Efficiency / Balanced |
| `engine.py` | `CognitionEngine.observe/reason/verify/plan` |
| `formatter.py` | Rich `CognitionCorePanel` |

---

## Evidence lifecycle

```mermaid
sequenceDiagram
  participant E as CognitionEngine
  participant C as collect_evidence
  participant H as generate_core_hypotheses
  participant V as verify_core_hypotheses
  participant P as generate_cognition_plans
  E->>C: observe(graph, history, context, twin)
  C-->>E: Evidence[]
  E->>H: reason()
  H-->>E: Hypothesis[]
  E->>V: verify(simulation_agreement)
  V-->>E: VerifiedCoreExplanation[]
  E->>P: plan()
  P-->>E: CognitionPlan[]
  E-->>E: state() → CognitionState
```

1. **Observe** — mint `Evidence` only from real inputs (empty ⇒ empty).
2. **Reason** — propose `Hypothesis` candidates referencing evidence ids.
3. **Verify** — accept only with graph and/or history support; optional simulation agreement floor.
4. **Plan** — emit simulation-backed Performance / Efficiency / Balanced plans; never execute.

---

## Public API

```python
from aetheros.cognition import CognitionEngine, CoreHypothesis, Evidence

engine = CognitionEngine()
state = engine.run(
    graph=resource_graph,
    history=telemetry_points,
    context="CODING",
    twin_summaries=("CPU_OVERLOAD agrees with load",),
    simulation_agreement=90.0,
)
```

| Method | Output |
|--------|--------|
| `observe(...)` | `tuple[Evidence, ...]` |
| `reason()` | `tuple[CoreHypothesis, ...]` |
| `verify(...)` | `tuple[VerifiedCoreExplanation, ...]` |
| `plan()` | `tuple[CognitionPlan, ...]` |
| `state()` / `run(...)` | `CognitionState` |

Naming note: package export ``Hypothesis`` remains the **legacy** type used by
``CognitiveRuntime``. v3 hypotheses are exported as ``CoreHypothesis``
(``aetheros.cognition.models.Hypothesis``).

---

## Memory

``OperationalMemory`` stores verified **system** patterns only, for example:

> Morning coding sessions typically increase CPU before memory pressure.

No user content. No conversations.

---

## Non-goals

- No LLM calls
- No dashboard redesign in P1
- No changes to ``CognitiveRuntime`` behavior
- No OS execution of plans
