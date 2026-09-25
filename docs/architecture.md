# Architecture — AetherOS ∞

AetherOS is an **Explainable Operating Intelligence Platform**. It is not an
operating system, kernel, driver, or autonomous controller.

Engineering decisions follow the **CELESTRA** founding charter:
[CELESTRA.md](CELESTRA.md) (human-centered, explainable, simulation-first,
read-only, open architecture, enterprise-grade).

## Design invariants

1. Observe before acting.
2. Explain every recommendation.
3. Simulation before intervention.
4. Humans remain in control.
5. Immutable telemetry.
6. Research-grade architecture.
7. Modular by design — no circular dependencies into higher layers.

## Intelligence pipeline

```mermaid
flowchart TD
    T[Telemetry] --> O[Observatory]
    O --> Ev[Evidence]
    Ev --> R[Reasoning]
    R --> S[Simulation]
    S --> P[Prediction]
    P --> X[Explainability]
    X --> Rec[Recommendation]
    Rec --> H[Human Approval]
```

## Generation map

```mermaid
flowchart LR
    V1[v1 Operating] --> V2[v2 Resource]
    V2 --> V3[v3 Cognitive]
    V3 --> V4[v4 Agents]
    V4 --> V5[v5 Atlas]
    V5 --> V6[v6 Horizon]
    V6 --> V7[v7 Genesis]
    V7 --> V8[v8 Sentinel]
    V8 --> V9[v9 Fabric]
    V9 --> INF[∞ Infinity]
```

## Module map

| Package | Generation | Responsibility |
|---------|------------|----------------|
| `telemetry` | v1 | Host metrics (read-only) |
| `policy` / `policy_engine` | v1 | Advice-only rules |
| `safety` | v1 | Approval, cooldowns, audit |
| `decision` | v1 | Prioritized recommendations |
| `observatory` | v1 | Temporal memory |
| `explainability` | v1 | Evidence + confidence |
| `predictive` | v1+ | Statistical forecasts |
| `cluster` / `agent` | v1+ | Multi-device bus |
| `orchestrator` | v1+ | Workload placement advice |
| `kernel` | v2 | **Userspace** resource context (not OS kernel) |
| `knowledge` / `ontology` | v2–v7 | Catalogs — see [ontology-catalogs.md](ontology-catalogs.md) |
| `cognition` / `reasoning` | v3 | Causal / hypothesis / verify |
| `agents` / `messaging` | v4 | Multi-agent bus |
| `atlas` | v5 | Facade over Horizon + Twin |
| `horizon` / `edge` / `robotics` | v6 | Planetary intelligence |
| `genesis` | v7 | Research knowledge engine |
| `sentinel` / `graph` | v8 + P4 | Resilience deps + Resource Graph Engine |
| `fabric` / `protocol` / `twin` | v9 | Universal federation |
| `simulation` | [simulation.md](simulation.md) | Host what-if (simulator family) |
| `storage` | architecture | Shared SQLite connect/schema helpers |
| `infinity` | ∞ | Unifying pipeline + status |
| `api` / `dashboard` | all | Read-only API + Rich UI |
| `sdk` / `plugins` | all | Sandboxed plugins |
| `services/intelligence` | GII v9 | Cognition Engine — see [PHASE16.md](PHASE16.md) |

## Compatibility aliases

- `aetheros.policy` → `aetheros.policy_engine`
- `aetheros.atlas` → Horizon world graph + Global Twin
- `aetheros.kernel` → userspace resource context only
- `aetheros.advice.Decision` → shared by decision + intent (no package cycle)
- `aetheros.reasoning.explain` → re-exports `cognition.report` (compat)
- `aetheros.runtime.AgenticReport` → owned by `agents.report` (compat)

## Related docs

- [CELESTRA charter](CELESTRA.md)
- [Infinity](infinity.md)
- [Module index](MODULES.md)
- [Ontology catalogs](ontology-catalogs.md) · [Simulation family](simulation.md)
- [Plugins / trust](plugins.md) · [agent vs agents](agents.md#naming-agent-vs-agents)
- [Resource Graph](resource_graph.md)
- [Graph Intelligence Bridge](graph_bridge.md)
- [Graph Reasoning](reasoning.md)
- [Digital Twin 2.0](digital_twin.md)
- [Context Engine](context_engine.md)
- [Cognition Core v3](cognition_core.md)
- [Operational Memory v3 P2](operational_memory.md)
- [Causal Knowledge Graph v3 P3](causal_knowledge_graph.md)
- [Multi-Agent Consensus v3 P4](multi_agent_consensus.md)
- [Research Intelligence P9](research_engine.md)
- [Phase 16 GII](PHASE16.md)
- [Fabric](fabric.md) · [Sentinel](sentinel.md) · [Genesis](genesis.md) · [Horizon](horizon.md)
- [Agents](agents.md) · [Cognition](cognition.md) · [Observatory](observatory.md)
