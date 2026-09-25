# Aether Lab — Cognitive Architecture (CELESTRA X)

**Package:** [`labs/aether/`](../labs/aether/)  
**HTTP:** `/aether/*`  
**Modules:** Attention · Decomposition · Planning · Reflection · Critique

---

## Philosophy

Aether is the **executive cognitive system** of CELESTRA. Foundation models remain interchangeable inference engines.

```mermaid
sequenceDiagram
    participant Op as Operator
    participant API as /aether
    participant Cog as CognitionEngine
    participant Att as Attention
    participant Dec as Decomposition
    participant Plan as Planning
    participant Ref as Reflection
    participant Crit as Critique

    Op->>API: POST /aether/cognition
    API->>Cog: run(objective)
    Cog->>Att: allocate
    Cog->>Dec: decompose → TaskGraph DAG
    Cog->>Plan: build CognitionPlan
    API-->>Op: attention + graph + plan
    Op->>API: POST /aether/reflect
    API->>Ref: weaknesses / assumptions / improvements
    Ref->>Plan: revise (append-only)
    Op->>API: POST /aether/critique
    API->>Crit: scored verdict
```

---

## Module map

| Module | Responsibility |
|--------|----------------|
| **Attention** | Adaptive weights + reasoning/retrieval budgets |
| **Decomposition** | Strategic → Tactical → Operational → Execution DAG |
| **Planning** | CognitionPlan from attention + graph; revise path |
| **Reflection** | Logical gaps, assumptions, ambiguity, missing evidence |
| **Critique** | correctness · completeness · consistency · evidence · calibration |

---

## Decomposition levels

```mermaid
flowchart TD
    S[Strategic root] --> T1[Tactical]
    S --> T2[Tactical]
    T1 --> O1[Operational]
    T1 --> O2[Operational]
    O1 --> E1[Execution]
    O2 --> E2[Execution]
```

Sibling tasks carry sequential dependencies; parent edges enforce hierarchy. Topological order is Kahn-stable and cycle-checked.

---

## Reflection → Critique loop

1. Operator supplies `reasoning_summary` + optional evidence  
2. Reflection extracts weaknesses / assumptions / improvements  
3. Optional revised plan appended (`status=revised`, `parent_plan_id`)  
4. Critique returns machine-readable scores + `pass|revise|reject`

---

## Observatory

| Page | Feature |
|------|---------|
| Cognition | Stage replay |
| Attention Map | Channel heatmap |
| Task Graph | Hierarchical DAG |
| Reflection | Assumption explorer + timeline |
| Critique | Criterion scores |

Path: `labs/aether/observatory/web`

---

## Exit criteria

- [x] Frozen typed models including `TaskGraph`
- [x] Deterministic Attention + Decomposition + Planning
- [x] Reflection + Critique with append-only stores
- [x] FastAPI `/aether` OpenAPI routes
- [x] Observatory pages for all five views
- [x] Unit + API tests (≥95% on cognitive core)
