# Changelog

All notable changes to AetherOS are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Fixed

## [6.0.0] — 2026-09-26 — Horizon

Open-source launch of the **Horizon** line: planetary observation and advice without actuation.
Full notes: [docs/releases/v6.0.0.md](docs/releases/v6.0.0.md).

### Added

- v6.0 P5 Horizon Observatory — `aetheros.horizon` presentation layer (Rich · read-only)
- Entry: `aetheros-horizon` · pages Overview / Cloud / Topology / Knowledge / Scheduler / Twin / Consensus / Research / Health
- Docs: `docs/horizon_observatory.md`
- Research paper draft: `docs/papers/aetheros_explainable_operating_intelligence.md` (+ PDF)
- v6.0 P4 Planetary Scheduler — `aetheros.planetary` (constraints · scoring · twin sim · top-5)
- Dashboard **W** → Worldwide Scheduler (Map / Regions / Candidates / Trade-offs / Simulation); **%** → Workload Planner
- Docs: `docs/planetary_scheduler.md`
- v6.0 P3 Global Knowledge Graph — `aetheros.global_graph` (ontology · evidence · traversal)
- Dashboard **K** → Global Graph (World / Regions / Clusters / Knowledge / Discoveries / Evidence); **^** → Cognitive
- Docs: `docs/global_knowledge_graph.md`
- v6.0 P2 Infrastructure Digital Twin — `aetheros.infra_twin` (clone · scenarios · evaluate · diff)
- Dashboard **I** → Infrastructure Twin (Snapshot / Library / Simulation / Diff / Availability); **~** → Infinity
- Docs: `docs/infrastructure_twin.md`
- v6.0 P1 Cloud Federation Engine — `aetheros.cloud` (AWS · Azure · GCP · Kubernetes · Docker · Edge)
- Dashboard **C** → Cloud Federation (Providers / Regions / Resources / Health / Snapshots); **;** → Cluster overview
- Docs: `docs/cloud_federation.md`
- Open-source launch packaging: rewritten README, `docs/installation.md`, Horizon architecture diagram, demo GIF placeholders, Contributing / Security / CoC, issue & PR templates, CI docs-surface job, release workflow Horizon titles, `docs/benchmarks.md` Horizon placeholders

### Changed

- Root README repositioned for v6 Horizon (quick start, demo gallery, architecture mermaid)
- CI: docs-surface job validates launch documentation files exist
- Release workflow: `v6*` tags draft as **Horizon** with notes link to `docs/releases/v6.0.0.md`

### Fixed

## [5.0.0] — 2026-09-26 — Nexus

Production release of the AetherOS Explainable Operating Intelligence Platform.

### Added

- v5.0 P5 Enterprise Edition — `aetheros.enterprise` (orgs · RBAC · API keys · audit · compliance)
- Dashboard **E** → Enterprise (Orgs / Workspaces / Roles / Keys / Audit / Compliance / Analytics); **@** → Extensions
- Docs: `docs/enterprise.md`
- v5.0 P4 Policy Studio — `aetheros.policy` (rules · versions · simulate · advisory only)
- Dashboard **P** → Policies (Active / Versions / Builder / Evaluation / Simulation); **#** → Predictive
- Docs: `docs/policy_studio.md`
- v5.0 P3 Extension Marketplace — `aetheros.marketplace` (catalog · install · verify · enable)
- Dashboard **@** → Extensions (Marketplace / Installed / Updates / Permissions / Details); **=** → Explainability
- Docs: `docs/marketplace.md`
- v5.0 P2 Public API & Python SDK — `/api/v1` FastAPI routes + `AetherClient`
- Docs: `docs/public_api.md`, `docs/python_sdk.md`
- v5.0 P1 Plugin SDK — `plugins/sdk` (YAML manifest, capabilities, events, sandbox, loader, Rich inspector)
- Example plugin: `plugins/examples/hello_insight`
- Docs: `docs/plugin_sdk.md`
- v4.0 P5 Atlas Dashboard — `aetheros.atlas` Rich observatory (O/F/T/S/G/D/R/H navigation)
- Entry: `aetheros-atlas` / `python -m aetheros.atlas` (presentation only, read-only)
- Docs: `docs/atlas_dashboard.md`
- v4.0 P3 Distributed Scheduler — `aetheros.scheduler` (constraint → score → twin-simulate → evaluate)
- Dashboard **/** → Distributed Scheduler (Workloads / Candidates / Scores / Simulation / Trade-offs); **S** stays Sentinel
- Docs: `docs/distributed_scheduler.md`
- v4.0 P2 Cluster Topology Engine — `aetheros.topology` (World → Regions → DCs → Clusters → Nodes)
- Dashboard **Z** → Cluster Topology (Tree / World / Regions / Clusters / Health); **T** stays graph toggle
- Docs: `docs/cluster_topology.md`
- v4.0 P1 Federation Protocol — `aetheros.federation` (immutable snapshots + heartbeats)
- Dashboard **U** → Federation Protocol (Nodes / Registry / Heartbeats / Protocol); **F** stays Fabric
- Docs: `docs/federation_protocol.md`
- CELESTRA X **Aether Lab** Modules 2–4 — Decomposition (DAG), Planning, Reflection, Critique
- Cognition orchestrator (`POST /aether/cognition`) runs attention → decompose → plan
- Observatory Task Graph / Reflection / Critique / Cognition pages (Next.js 16)
- Docs: `docs/aether_lab.md` updated for full cognitive pipeline
- CELESTRA X **Aether Lab** Module 1 — Attention Engine (`labs/aether/`, `/aether`)
- Deterministic attention allocation (weights + reasoning/retrieval budgets) + draft cognition plans
- Aether Observatory Next.js 16 Attention Map (`labs/aether/observatory/web`)
- Docs: `docs/aether_lab.md`
- v3.0 P5 Autonomous Research Engine — `aetheros.research_ai` (twin-only experiments + journal)
- Dashboard **B** → Research Lab (Questions / Experiments / Discoveries / Rejected / Journal); **R** stays Graph Reasoning
- Docs: `docs/autonomous_research.md`
- v3.0 P4 Multi-Agent Consensus — sync `EventBus` + `ConsensusEngine` (human-approval recommendations)
- Dashboard **J** → Multi-Agent Consensus (Status / Findings / Bus / Consensus / Conflicts); **A** stays Research, **M** stays Multi-Agent View
- Docs: `docs/multi_agent_consensus.md`
- v3.0 P3 Causal Knowledge Graph — `aetheros.knowledge` builder/traversal/validator (verified relations only)
- Dashboard **N** → Causal Knowledge Graph (Ontology / Causal / Discoveries / Relationships / Evidence); **K** stays Cognitive
- Docs: `docs/causal_knowledge_graph.md`
- v3.0 P2 Long-Term Operational Memory — `aetheros.memory` (`MemoryEngine`, store, verifier, consolidation)
- Dashboard **L** → Operational Memory (Verified / Recent / Related / Evidence Timeline); **M** stays Multi-Agent
- Docs: `docs/operational_memory.md`
- v3.0 P1 Cognition Core — `CognitionEngine` (observe/reason/verify/plan) over graph evidence
- `Evidence` / `CoreHypothesis` / `CognitionState` / `OperationalMemory` (isolated layer)
- Docs: `docs/cognition_core.md`

### Changed

- Package version set to **5.0.0** (codename **Nexus**, production release)
- Development status classifier: Production/Stable
- Release engineering: publication-grade README, architecture diagrams, benchmarks, GitHub templates, CI coverage artifacts

### Fixed

### Planned

- Horizon roadmap deepening (planetary overlays, recorded demo GIFs)
- Optional WebSocket cluster transport (read-only)

## [2.0.0] — 2026-09-25 — Intelligence (Release Candidate)

### Added

- CELESTRA GII Module 1 — Cognition Engine (`services/intelligence/`, Phase 16 / `/v9`)
- `/v9/cognition` create/list/get and `/v9/intelligence` health
- Append-only cognition plans + `li_gii_cognition_plans` migration contract
- Docs: `docs/PHASE16.md`
- CELESTRA founding engineering charter (`docs/CELESTRA.md`) with feature acceptance gate
- Contributor gate linked from `CONTRIBUTING.md`
- Shared `aetheros.advice` contracts (`Decision`) to break decision ↔ intent imports
- `aetheros.agents.report` / `aetheros.cognition.report` owning report types (cycle breaks)
- Import-cycle guard: `scripts/check_import_cycles.py`, `tests/test_import_cycles.py`, CI step
- `CausalRelationKind` / `OntologyRelationKind` namespaced catalogs (`docs/ontology-catalogs.md`)
- Simulator family map (`docs/simulation.md`) — host / resilience / cascade / twin
- Shared SQLite helpers (`aetheros.storage`) adopted by all eight persistence stores
- Dashboard formatting helpers extracted to `aetheros.dashboard.formatting` (testable outside Live)
- Tightened plugin sandbox deny-list + trust model (`aetheros/sdk/README.md`, `docs/plugins.md`)
- Pydantic response models for `/health`, `/infinity`, `/fabric`, `/sentinel`, `/sentinel/anomalies`
- Docs clarify `aetheros.agent` (cluster publisher) vs `aetheros.agents` (multi-agent)
- Resource Graph Engine (`aetheros.graph` models/builder/validator/queries/serializer/renderer)
- Dashboard Resource Graph panel (`Y`; `G` remains Genesis)
- Docs: `docs/resource_graph.md`
- Graph Intelligence Bridge (`aetheros.bridge`) — read-only ResourceGraph adapters
- Docs: `docs/graph_bridge.md`
- `EvidenceSource` extended with `"graph"` (additive; explainability engines unchanged)
- Graph Reasoning Engine (`aetheros.reasoning` traversal/hypotheses/verifier/confidence/formatter)
- Dashboard Graph Reasoning panel (`R`; `K` remains Cognitive)
- Docs: `docs/reasoning.md`
- Digital Twin 2.0 (`aetheros.twin` snapshot/scenario/evaluator/diff + `DigitalTwinSimulator`)
- Dashboard Digital Twin panel (`V`; `D` remains Developer Console)
- Docs: `docs/digital_twin.md`
- Context Intelligence Engine (`aetheros.context` builder/intent/history/engine)
- Optional prediction/reasoning/simulation context adapters (no runtime rewrite)
- Docs: `docs/context_engine.md`
- Research Intelligence Engine P9 (`aetheros.research` analyzer/trends/bottlenecks/discoveries)
- Dashboard **X** Research Intelligence page (A remains strategy research)
- Docs: `docs/research_engine.md`
- Release engineering: `SECURITY.md`, ADRs, benchmarks, release checklist, coverage gate 90%

### Changed

- Package version set to **2.0.0** (codename **Intelligence**, Release Candidate)
- CI / pytest coverage fail-under raised from 80% to **90%**
- `reasoning.explain` re-exports cognition report helpers (compat)
- `decision.models` re-exports `aetheros.advice.Decision` (compat)
- `runtime` re-exports agentic report types from `agents.report` (compat)

### Planned

- Recorded demo GIFs under `docs/screenshots/`
- Optional WebSocket cluster transport (read-only)

## [10.0.0] — 2026-09-25

### Added

- AetherOS Infinity (∞) unifying layer (`aetheros/infinity`)
- Generation catalog (v1–v9 + ∞) and intelligence pipeline descriptors
- Compatibility facades: `aetheros.atlas`, `aetheros.kernel`, `aetheros.policy`
- Platform docs: `docs/architecture.md`, `docs/infinity.md`, `docs/MODULES.md`
- Dashboard Infinity panel (`I`)
- API: `GET /infinity`

### Changed

- Package version set to `10.0.0`
- Root identity clarified: Explainable Operating Intelligence Platform (not an OS)

### Security

- Infinity remains observation / recommendation only — no shell, sudo, or kernel mutation

## [9.0.0] — 2026-09-25

### Added

- Aether Fabric universal intelligence (`aetheros/fabric`, `aetheros/protocol`, `aetheros/twin`)
- Universal graph (device/cluster/DC/GPU/storage/network/agent/simulation/knowledge)
- Federation of immutable telemetry snapshots with eventual-consistency sync
- Global Digital Twin scenarios (region outage, GPU shortage, congestion, edge expansion)
- Dashboard Fabric panel (`F`)
- API: `/fabric`, `/federation`, `/fabric/graph`, `/twin`, `/knowledge` (plus existing `/health`)

### Changed

- Package version set to `9.0.0`
- `/health` reports `mode=simulation-only` and `control=human`

### Security

- Fabric remains simulation-only: no remote execution, no hardware control, humans approve recommendations

## [8.0.0] — 2026-09-25

### Added

- Sentinel Intelligence Fabric (`aetheros/sentinel`, `aetheros/graph`)
- Anomaly engine (CPU, memory leak, network, disk, battery, cluster imbalance)
- Root-cause ranking verified via telemetry, history, and simulation
- Cascade simulator over service/infra dependency graph
- Recovery planner (Digital Twin scored; recommendation only)
- Explainable resilience score (health / stability / redundancy / risk)
- Dashboard Sentinel panel (`S`)
- API: `/sentinel`, `/sentinel/anomalies`, `/sentinel/graph`

### Changed

- Package version set to `8.0.0`

### Security

- Sentinel never executes recovery: no OS commands, no sudo, no kernel changes

## [7.0.0] — 2026-09-25

### Added

- Genesis Intelligence Layer (`aetheros/genesis`, `aetheros/ontology`)
- Verified knowledge base (SQLite) — rejects unsupported claims
- Hypothesis → experiment → verifier → theorem research cycle
- Computing ontology (CPU/GPU/Memory/Disk/Network/Intent/Cluster/…) with CAUSES/USES/ALLOCATES/DEPENDS_ON/IMPROVES/DEGRADES
- Dashboard Genesis panel (`G`); Cognitive Graph moved to `K`
- API: `/genesis`, `/genesis/knowledge`, `/genesis/theorems`, `/genesis/ontology`

### Changed

- Package version set to `7.0.0`

### Security

- Genesis remains research-only: no OS execution, no hardware control, simulation-backed evidence only

## [6.0.0] — 2026-09-25

### Added

- Horizon Planetary Intelligence Network (`aetheros/horizon`, `aetheros/edge`, `aetheros/robotics`)
- NetworkX world graph (Earth → Region → Country → DC → Cluster → Node → Process)
- Latency engine (geography + network class; no live probes)
- Resilience simulator (region outage, DC failure, partition, power loss)
- Capacity planner (1h / 24h / 7d compute, memory, GPU, storage)
- Dashboard Horizon panel (`H`); Help moved to `?`
- Read-only API: `/world`, `/regions`, `/latency`, `/resilience`, `/capacity`, `/graph`

### Changed

- Package version set to `6.0.0`
- Dependency: `networkx>=3.2`

### Security

- Horizon remains simulation-first: no OS execution, no hardware control, no live network tests

## [4.0.0] — 2026-09-25

### Added

- Agentic Systems Intelligence (`aetheros/agents`, `aetheros/messaging`, `aetheros/runtime`)
- Async in-process message bus with immutable `AgentEvent` records
- Specialist agents: Telemetry, Performance, Battery, Security, Cluster, Research
- Coordinator conflict resolution (e.g. performance vs battery → Balanced Mode)
- Dashboard Multi-Agent View (`M`)

### Changed

- Package version set to `4.0.0`

### Security

- Agents remain recommendation-only: no OS execution, no sudo, no kernel changes

## [3.0.0] — 2026-09-24

### Added

- Cognitive Operating Intelligence (`aetheros/cognition`, `aetheros/knowledge`, `aetheros/reasoning`)
- Structured cognitive memory (SQLite) with public systems facts only
- Causal graph builder (CAUSES / USES / DEPENDS_ON / PREDICTS / EXPLAINS)
- Hypothesis engine, verifier, and simulation-backed intervention planner
- FastAPI read-only cognitive API (`aetheros.api`)
- Dashboard Cognitive Graph panel (`G`)

### Changed

- Package version set to `3.0.0`

### Security

- Cognition remains recommendation-only: no OS execution, no sudo, no kernel changes

## [1.5.0-alpha] — 2026-09-23

### Added

- Resource Orchestrator (`aetheros/orchestrator`) with workload catalog, constraints, scoring, and explainable `ExecutionPlan`
- Workload Planner dashboard panel (`W`, cycle with `]`)
- Public alpha packaging: MIT license, CONTRIBUTING, CODE OF CONDUCT, architecture docs, CI/CD workflows
- Coverage gate at 80% (`pytest-cov` + `--cov-fail-under=80`)
- Thin `main.py` launcher for documented quick start

### Changed

- Package version set to `1.5.0a1` (PEP 440) / release tag `v1.5.0-alpha`
- README rewritten for public alpha (Operating Intelligence Platform)

### Security

- Orchestrator remains recommendation-only: no SSH, no sudo, no remote execution

## [1.4.0] — 2026-09-23

### Added

- Multi-device cluster module (`aetheros/cluster`) with JSON local transport, registry, heartbeat, aggregator
- Lightweight Aether Agent (`aetheros/agent`) collector and publisher
- Cluster Overview dashboard panel (`C`)
- Demo peer publishers for single-host multi-node UI exercises

## [1.3.0] — 2026-09-23

### Added

- Predictive Intelligence Engine (`aetheros/predictive`)
- Statistical forecasting via moving averages, exponential smoothing, and manual OLS (no NumPy / pandas / sklearn)
- Anomaly detection and forecast explainability payloads
- Predictive dashboard panel (`P`)

## [1.2.0] — 2026-09-23

### Added

- Explainable Intelligence Engine (`aetheros/explainability`)
- Evidence collection from telemetry, history, intent, and simulation
- Confidence scoring from measurable quality signals
- Explainability dashboard panel (`E`)

## [1.1.0] — 2026-09-23

### Added

- Observatory (`aetheros/observatory`) with SQLite temporal memory
- History recorder (300-sample ring buffer), event detector, timeline, Rich graphs
- Observatory center panel (`O`, `T`, `←`)

## [1.0.0] — 2026-09-22

### Added

- Complete v1.0 control-plane stack: Telemetry, Policy, Safety, Decision, Dashboard
- Intent profiles, Learning patterns, Simulation engine, Autonomous Research
- Plugin SDK with sandbox and example plugins
- Rich Live operator dashboard

## [0.5.0] — 2026-09-22

### Added

- Operator dashboard (Phase 5) with telemetry, decision, and safety panels
- Intent hotkeys and research trigger

## [0.4.0] — 2026-09-22

### Added

- Decision engine with prioritization and scoring
- Safety-gated recommendation pipeline

## [0.3.0] — 2026-09-22

### Added

- Safety layer with validator, cooldown manager, and SQLite audit log

## [0.2.0] — 2026-09-22

### Added

- Policy engine with severity-ranked recommendations from telemetry snapshots

## [0.1.0] — 2026-09-22

### Added

- Initial telemetry collector and typed snapshot models
- CLI monitor prototype
- Project skeleton under `aetheros/`

[Unreleased]: https://github.com/shouryaveggalam/AetherOS/compare/v5.0.0...HEAD
[5.0.0]: https://github.com/shouryaveggalam/AetherOS/releases/tag/v5.0.0
[2.0.0]: https://github.com/shouryaveggalam/AetherOS/releases/tag/v2.0.0
[1.5.0-alpha]: https://github.com/shouryaveggalam/AetherOS/releases/tag/v1.5.0-alpha
[1.4.0]: https://github.com/shouryaveggalam/AetherOS/releases/tag/v1.4.0
[1.3.0]: https://github.com/shouryaveggalam/AetherOS/releases/tag/v1.3.0
[1.2.0]: https://github.com/shouryaveggalam/AetherOS/releases/tag/v1.2.0
[1.1.0]: https://github.com/shouryaveggalam/AetherOS/releases/tag/v1.1.0
[1.0.0]: https://github.com/shouryaveggalam/AetherOS/releases/tag/v1.0.0
[0.5.0]: https://github.com/shouryaveggalam/AetherOS/releases/tag/v0.5.0
[0.4.0]: https://github.com/shouryaveggalam/AetherOS/releases/tag/v0.4.0
[0.3.0]: https://github.com/shouryaveggalam/AetherOS/releases/tag/v0.3.0
[0.2.0]: https://github.com/shouryaveggalam/AetherOS/releases/tag/v0.2.0
[0.1.0]: https://github.com/shouryaveggalam/AetherOS/releases/tag/v0.1.0
