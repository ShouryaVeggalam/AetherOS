# Module index

Every first-class package under `aetheros/` with its role and doc entry point.

Engineering charter: [CELESTRA.md](CELESTRA.md).

| Package | Docs | Notes |
|---------|------|-------|
| `agent` | [cluster.md](cluster.md) | Cluster node publisher (**not** multi-agent) |
| `agents` | [agents.md](agents.md) · [multi_agent_consensus.md](multi_agent_consensus.md) | Multi-agent specialists + v3 P4 consensus |
| `advice` | [architecture.md](architecture.md) | Shared Decision contract (cycle-neutral) |
| `api` | OpenAPI `/docs` | Read-only FastAPI surface |
| `atlas` | [architecture.md](architecture.md) | v5 facade → Horizon/Twin |
| `cli` | README | Demo CLIs |
| `cluster` | [cluster.md](cluster.md) | Multi-device registry |
| `cognition` | [cognition.md](cognition.md) · [cognition_core.md](cognition_core.md) | Causal / hypothesis / verify + v3 Cognition Core |
| `context` | [context_engine.md](context_engine.md) | Context Intelligence Engine (P8) |
| `research` | [research_engine.md](research_engine.md) | Strategy research + P9 Research Intelligence |
| `research_ai` | [autonomous_research.md](autonomous_research.md) | v3 P5 Autonomous Research Engine (twin experiments) |
| `core` | SDK docs | Plugin host |
| `dashboard` | README | Rich Live UI |
| `decision` | architecture | Prioritizer |
| `edge` | [horizon.md](horizon.md) | Edge inventory |
| `explainability` | [explainability.md](explainability.md) | Evidence chains |
| `fabric` | [fabric.md](fabric.md) | Universal federation |
| `federation` | [federation_protocol.md](federation_protocol.md) | v4.0 P1 Federation Protocol (read-only node snapshots) |
| `topology` | [cluster_topology.md](cluster_topology.md) | v4.0 P2 Cluster Topology Engine (World → Nodes) |
| `scheduler` | [distributed_scheduler.md](distributed_scheduler.md) | v4.0 P3 Distributed Scheduler (Digital Twin simulation only) |
| `atlas` | [atlas_dashboard.md](atlas_dashboard.md) · [horizon.md](horizon.md) | v4.0 P5 Atlas Dashboard (+ v5 Horizon/Twin facade) |
| `genesis` | [genesis.md](genesis.md) | Research knowledge |
| `graph` | [resource_graph.md](resource_graph.md) · [sentinel.md](sentinel.md) | Resource Graph Engine + Sentinel deps |
| `reasoning` | [reasoning.md](reasoning.md) · [cognition.md](cognition.md) | Graph Reasoning Engine + cognitive helpers |
| `bridge` | [graph_bridge.md](graph_bridge.md) | Graph Intelligence Bridge (P5) |
| `horizon` | [horizon.md](horizon.md) | Planetary intelligence |
| `infinity` | [infinity.md](infinity.md) | ∞ unifying layer |
| `intent` | architecture | Operator profiles |
| `kernel` | package README | Userspace context only |
| `knowledge` | [ontology-catalogs.md](ontology-catalogs.md) · [causal_knowledge_graph.md](causal_knowledge_graph.md) | Ontology catalogs + v3 P3 Causal Knowledge Graph |
| `learning` | architecture | Pattern summaries |
| `memory` | [operational_memory.md](operational_memory.md) | v3 P2 long-term operational memory (verified patterns only) |
| `messaging` | [agents.md](agents.md) | Async agent bus |
| `observatory` | [observatory.md](observatory.md) | Temporal memory |
| `ontology` | [ontology-catalogs.md](ontology-catalogs.md) | Genesis entity relations |
| `orchestrator` | architecture | Workload planner |
| `policy` | package README | Alias → policy_engine |
| `policy_engine` | architecture | Rules |
| `predictive` | architecture | Forecasts |
| `protocol` | [fabric.md](fabric.md) | Fabric wire protocol |
| `research` | architecture | Strategy research |
| `robotics` | [horizon.md](horizon.md) | Fleet inventory |
| `runtime` | [agents.md](agents.md) | Agentic runtime |
| `safety` | architecture | Audit + cooldown |
| `sdk` / `plugins` | [sdk README](../aetheros/sdk/README.md) | Sandboxed plugins (load-time trust) |
| `sentinel` | [sentinel.md](sentinel.md) | Resilience fabric |
| `simulation` | [simulation.md](simulation.md) | Host strategy what-if |
| `storage` | [architecture.md](architecture.md) | Shared SQLite helpers |
| `telemetry` | architecture | Host metrics |
| `twin` | [digital_twin.md](digital_twin.md) · [fabric.md](fabric.md) | Digital Twin 2.0 (host) + global twin |
| `services/intelligence` | [PHASE16.md](PHASE16.md) | CELESTRA GII v9 — Cognition Engine (`/v9`) |
| `labs/aether` | [aether_lab.md](aether_lab.md) | CELESTRA X Aether Lab — Attention → Decompose → Plan → Reflect → Critique (`/aether`) |
| Release eng. | [release_checklist.md](release_checklist.md) · [releases/v2.0.0.md](releases/v2.0.0.md) · [benchmarks.md](benchmarks.md) · [adr/](adr/) | P10 RC artifacts |

## Documentation standard

New modules should include:

- Package `README.md` (purpose, Mermaid, public API)
- Entry in this index
- Unit tests under `tests/`
- Type hints + docstrings on public surfaces
