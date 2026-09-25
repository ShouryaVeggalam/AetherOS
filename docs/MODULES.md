# Module index

Every first-class package under `aetheros/` with its role and doc entry point.

Engineering charter: [CELESTRA.md](CELESTRA.md).

| Package | Docs | Notes |
|---------|------|-------|
| `agent` | [cluster.md](cluster.md) | Lightweight cluster publisher |
| `agents` | [agents.md](agents.md) | Multi-agent specialists + coordinator |
| `api` | OpenAPI `/docs` | Read-only FastAPI surface |
| `atlas` | [architecture.md](architecture.md) | v5 facade → Horizon/Twin |
| `cli` | README | Demo CLIs |
| `cluster` | [cluster.md](cluster.md) | Multi-device registry |
| `cognition` | [cognition.md](cognition.md) | Causal / hypothesis / verify |
| `core` | SDK docs | Plugin host |
| `dashboard` | README | Rich Live UI |
| `decision` | architecture | Prioritizer |
| `edge` | [horizon.md](horizon.md) | Edge inventory |
| `explainability` | [explainability.md](explainability.md) | Evidence chains |
| `fabric` | [fabric.md](fabric.md) | Universal federation |
| `genesis` | [genesis.md](genesis.md) | Research knowledge |
| `graph` | [sentinel.md](sentinel.md) | Service dependency graph |
| `horizon` | [horizon.md](horizon.md) | Planetary intelligence |
| `infinity` | [infinity.md](infinity.md) | ∞ unifying layer |
| `intent` | architecture | Operator profiles |
| `kernel` | package README | Userspace context only |
| `knowledge` | [cognition.md](cognition.md) | Ontology concepts |
| `learning` | architecture | Pattern summaries |
| `messaging` | [agents.md](agents.md) | Async agent bus |
| `observatory` | [observatory.md](observatory.md) | Temporal memory |
| `ontology` | [genesis.md](genesis.md) | Computing ontology |
| `orchestrator` | architecture | Workload planner |
| `policy` | package README | Alias → policy_engine |
| `policy_engine` | architecture | Rules |
| `predictive` | architecture | Forecasts |
| `protocol` | [fabric.md](fabric.md) | Fabric wire protocol |
| `reasoning` | [cognition.md](cognition.md) | Abductive/deductive/causal |
| `research` | architecture | Strategy research |
| `robotics` | [horizon.md](horizon.md) | Fleet inventory |
| `runtime` | [agents.md](agents.md) | Agentic runtime |
| `safety` | architecture | Audit + cooldown |
| `sdk` / `plugins` | architecture | Sandboxed plugins |
| `sentinel` | [sentinel.md](sentinel.md) | Resilience fabric |
| `simulation` | architecture | What-if engine |
| `telemetry` | architecture | Host metrics |
| `twin` | [fabric.md](fabric.md) | Global digital twin |

## Documentation standard

New modules should include:

- Package `README.md` (purpose, Mermaid, public API)
- Entry in this index
- Unit tests under `tests/`
- Type hints + docstrings on public surfaces
