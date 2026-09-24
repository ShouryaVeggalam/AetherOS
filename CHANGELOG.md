# Changelog

All notable changes to AetherOS are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned

- Recorded demo GIFs under `docs/screenshots/`
- Optional WebSocket cluster transport (read-only)

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
