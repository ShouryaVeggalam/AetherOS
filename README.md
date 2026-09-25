# AetherOS ∞

**Explainable Operating Intelligence Platform**

AetherOS observes, understands, predicts, simulates, and explains computing
systems while remaining entirely **userspace**, **read-only**, and
**human-in-the-loop**.

It is **not** an operating system, Linux distribution, kernel, device driver,
or autonomous controller. Humans always approve actions. No shell execution,
no kernel mutation, no sudo.

[![Python 3.12](https://img.shields.io/badge/python-3.12-black?style=flat-square)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-black?style=flat-square)](LICENSE)
[![Coverage 90%+](https://img.shields.io/badge/coverage-90%25%2B-black?style=flat-square)](pytest.ini)
[![Rich UI](https://img.shields.io/badge/UI-Rich-black?style=flat-square)](https://github.com/Textualize/rich)
[![Linux](https://img.shields.io/badge/os-Linux-black?style=flat-square)](#installation)
[![WSL2](https://img.shields.io/badge/os-WSL2-black?style=flat-square)](#installation)
[![Status: Intelligence RC](https://img.shields.io/badge/status-v2.0.0--intelligence--RC-black?style=flat-square)](docs/releases/v2.0.0.md)

---

## Introduction

AetherOS turns a terminal into an **operator console for system intelligence**.

It collects local telemetry, evaluates policy, validates safety, ranks decisions, records history, forecasts load, aggregates multi-device views, and recommends workload placement — then **explains every recommendation with evidence**.

Nothing is executed on your behalf. There is no kernel module, no sudo path, and no remote shell.

**Release:** `v2.0.0` · **Codename:** Intelligence · **Status:** Release Candidate · **Team:** [CELESTRA](docs/CELESTRA.md)

Docs: [CELESTRA](docs/CELESTRA.md) · [Architecture](docs/architecture.md) · [Release notes](docs/releases/v2.0.0.md) · [Modules](docs/MODULES.md) · [Benchmarks](docs/benchmarks.md) · [Security](SECURITY.md)

---

## Why AetherOS exists

Modern systems are observable. Few are *intelligible*.

Operators drown in metrics without a trustworthy narrative. Autopilots that mutate hosts without explanation create risk. AetherOS sits in between:

- **Observe** resource pressure in real time
- **Analyze** with explicit policy and safety gates
- **Simulate** outcomes without touching the OS
- **Explain** recommendations with traceable evidence
- **Recommend** — humans stay in control

---

## Features

| Capability | What it does |
|------------|--------------|
| **Telemetry** | CPU, memory, disk, battery, processes — read-only via `psutil` |
| **Policy & Safety** | Advice-only rules with audit log and cooldowns |
| **Decision Engine** | Prioritized operator recommendations |
| **Observatory** | SQLite temporal memory, sparklines, event timeline |
| **Explainability** | Evidence chains and confidence from real inputs |
| **Predictive** | Statistical 5 / 15 / 60 minute forecasts (no ML libraries) |
| **Cluster** | Multi-node JSON bus, aggregator, health colors |
| **Orchestrator** | Workload placement scores — recommendation only |
| **Cognition / Agents** | Causal reasoning and multi-agent deliberation |
| **Horizon / Genesis / Sentinel / Fabric** | Planetary, research, resilience, federation layers |
| **Infinity (∞)** | Unifying generation map, pipeline, and layer status |
| **Plugin SDK** | Sandboxed userspace plugins |

---

## Architecture

### Intelligence pipeline

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

### Intelligence loop

```mermaid
flowchart LR
    A[Observe] --> B[Analyze]
    B --> C[Simulate]
    C --> D[Explain]
    D --> E[Recommend]
    E -.->|human decides| A
```

Deeper notes: [docs/architecture.md](docs/architecture.md)

---

## Screenshots

> Place recorded terminal captures in `docs/screenshots/`. Paths below are ready for GitHub rendering.

![Operator Dashboard](docs/screenshots/dashboard.gif)

![Observatory](docs/screenshots/observatory.gif)

![Cluster Overview](docs/screenshots/cluster.gif)

![Predictive Intelligence](docs/screenshots/predictive.gif)

Asset guide: [docs/screenshots/README.md](docs/screenshots/README.md)

---

## Installation

Requires **Python 3.12+**. Supported on **Ubuntu**, **WSL2**, and **macOS**.

```bash
git clone https://github.com/shouryaveggalam/AetherOS.git
cd AetherOS

python3.12 -m venv .venv
# macOS / Linux / WSL2
source .venv/bin/activate

pip install -U pip
pip install -e ".[dev]"
```

### Quick Start

```bash
# Recommended
python -m aetheros

# Or the console script
aetheros

# Or the thin launcher
python main.py
```

Press `Q` to quit. The dashboard is a Rich Live terminal UI.

### Troubleshooting

| Symptom | Fix |
|---------|-----|
| `python: command not found` | Use `python3.12` explicitly |
| Blank / broken TUI in CI SSH | Run in a real TTY (Terminal.app, Windows Terminal, gnome-terminal) |
| `PermissionError` from `psutil` on macOS | Grant Full Disk Access to the terminal, or re-run locally outside sandboxes |
| No battery metrics | Expected on many desktops / VMs — AetherOS treats battery as optional |
| Import errors after pull | Re-run `pip install -e ".[dev]"` |
| Coverage / CI red | `pytest --cov=aetheros --cov-fail-under=90` |

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Q` | Quit |
| `I` | Infinity (∞ platform overview) |
| `F` | Fabric |
| `S` | Sentinel |
| `G` | Genesis |
| `H` | Horizon |
| `M` | Multi-Agent |
| `K` | Cognitive Graph |
| `O` | Observatory |
| `E` | Explainability |
| `P` | Predictive Intelligence |
| `C` | Cluster overview |
| `W` | Workload Planner |
| `]` | Cycle workload (planner) |
| `←` / `→` | Scroll observatory history |
| `T` | Cycle CPU / Memory / Disk graph |
| `A` | Run autonomous research |
| `D` | Developer / plugin console |
| `?` | Help |
| `1`–`6` | Switch intent profile |
| `ESC` | Leave overlays |

---

## Project Structure

```text
AetherOS/
├── aetheros/
│   ├── telemetry/ · policy_engine/ · safety/ · decision/
│   ├── observatory/ · explainability/ · predictive/
│   ├── cognition/ · reasoning/ · agents/ · messaging/
│   ├── horizon/ · genesis/ · sentinel/ · fabric/
│   ├── infinity/               # ∞ unifying layer
│   ├── atlas/ · kernel/ · policy/   # compatibility facades
│   ├── api/ · dashboard/
│   └── …
├── docs/
├── tests/
├── main.py
└── pyproject.toml
```

---

## Philosophy

Built by **CELESTRA** under a research- and enterprise-grade charter:

1. **Observe before acting.**
2. **Explain every recommendation.**
3. **Simulation before intervention.**
4. **Humans remain in control.**

Every feature must be problem-backed, evidence-based, explainable, tested, and
reproducible. Systems quality outranks flashy UI.

AetherOS is the intelligence layer for computing — not an autopilot.

Charter: [docs/CELESTRA.md](docs/CELESTRA.md)

---

## Roadmap

| Version | Focus |
|---------|--------|
| **v2.0.0 Intelligence (RC)** | P1–P9 stack freeze, ≥90% coverage, benchmarks, ADRs |
| v10 Infinity (historical label) | Unifying platform layer + docs + `/infinity` |
| v9 Fabric | Universal federation graph + twin |
| v8 Sentinel | Resilience intelligence |
| v7 Genesis | Research knowledge engine |
| v6 Horizon | Planetary intelligence |
| v4–v5 | Agents + Atlas facade |
| v3 | Cognitive reasoning |
| v1.x | Operating intelligence foundations |

See [CHANGELOG.md](CHANGELOG.md) for history.

---

## Contributing

We welcome careful, well-tested contributions.

Read [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before opening a PR.

```bash
pip install -e ".[dev]"
ruff check .
black --check .
pytest --cov=aetheros --cov-fail-under=90
```

---

## License

MIT © 2026 Shourya Veggalam — see [LICENSE](LICENSE).
