# Changelog

All notable changes to AetherOS are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- CELESTRA founding engineering charter (`docs/CELESTRA.md`) with feature acceptance gate
- Contributor gate linked from `CONTRIBUTING.md`

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

[Unreleased]: https://github.com/shouryaveggalam/AetherOS/compare/v1.5.0-alpha...HEAD
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
