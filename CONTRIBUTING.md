# Contributing to AetherOS

Thank you for helping **CELESTRA** build an explainable, userspace operating
intelligence platform. Read the founding charter: [docs/CELESTRA.md](docs/CELESTRA.md).

AetherOS is a **research- and operations-grade** platform. Contributions must preserve:

1. Observe before acting.
2. Explain every recommendation.
3. Simulation before intervention advice.
4. Humans always remain in control.

**No contribution may introduce** remote command execution, SSH automation, sudo
usage, Terraform/kubectl apply, cloud provisioning, or automatic OS mutation.

---

## Feature acceptance gate

Before opening a PR, confirm each item:

1. **Problem** — What operator or research problem does this solve?
2. **Evidence** — What measurable inputs support the claim?
3. **Explainability** — Can a human reconstruct why the output appeared?
4. **Testability** — Will CI fail if the behavior regresses?
5. **Reproducibility** — Can another engineer rebuild the result from docs + code?

Systems quality outranks flashy UI.

---

## Development setup

Full install: [docs/installation.md](docs/installation.md)

```bash
git clone https://github.com/ShouryaVeggalam/AetherOS.git
cd AetherOS
python3.12 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
```

Verify:

```bash
python -m aetheros --help 2>/dev/null || python -m aetheros &
pytest --cov=aetheros --cov-fail-under=90
ruff check .
black --check .
python scripts/check_import_cycles.py
```

---

## Coding standards

- **Python 3.12** with type hints on public APIs
- Prefer **immutable dataclasses** (`frozen=True`) for snapshots and plans
- Separate collection, analysis, and Rich rendering
- **No** NumPy / pandas / scikit-learn in predictive core paths (pure Python stats)
- **No** subprocess shelling for system control
- Format with **Black** (line length 88); lint with **Ruff**
- Generation boundaries: lower layers must not import higher layers

```bash
ruff check .
black .
black --check .
```

---

## Tests

```bash
pytest --cov=aetheros --cov-report=term-missing --cov-fail-under=90
```

- Prefer focused unit tests for models / scoring / constraints
- Presentation layers (Atlas / Horizon) should render idle + demo snapshots
- Twin / scheduler tests must assert **baselines are not mutated**

Benchmarks (optional, not a merge gate unless claimed in docs):

```bash
python scripts/run_benchmarks.py
```

---

## Documentation

When behavior or packaging changes:

- Update module docs under `docs/` and [docs/MODULES.md](docs/MODULES.md)
- Add a [CHANGELOG.md](CHANGELOG.md) entry under `[Unreleased]`
- Keep README keyboard maps accurate for dashboard / Horizon hotkeys
- Do not invent benchmark numbers — use methodology + `[TBD]` or harness output

Architecture diagrams: [docs/architecture/](docs/architecture/)

---

## Commit messages

Use concise, imperative subjects (≈50 characters), optional body for *why*:

```text
Add planetary ENERGY_PRIORITY constraint tests

Reject sites below efficiency threshold before scoring.
```

Preferred prefixes: `Add`, `Fix`, `Update`, `Document`, `Test`, `Refactor`.

---

## Pull requests

1. Branch from `main` (or the active release branch named by maintainers).
2. Keep PRs focused — one concern per PR when practical.
3. Fill [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md).
4. Ensure CI is green (lint · format · import cycles · tests · coverage · build).
5. Request review; address feedback with follow-up commits (avoid force-push to shared review branches unless asked).

---

## Issues

Use templates under [.github/ISSUE_TEMPLATE/](.github/ISSUE_TEMPLATE/):

- Bug report
- Feature request
- Documentation

**Security issues are not public bugs** — see [SECURITY.md](SECURITY.md).

---

## Community

- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- Be precise, kind, and evidence-driven in reviews

---

## License

By contributing, you agree that your contributions are licensed under the MIT
License (see [LICENSE](LICENSE)).
