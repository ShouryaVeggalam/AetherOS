# Contributing to AetherOS

Thank you for helping **CELESTRA** build an explainable, userspace operating
intelligence platform. Read the founding charter: [docs/CELESTRA.md](docs/CELESTRA.md).

AetherOS is an **alpha** research project. Contributions should preserve these
invariants:

1. Observe before acting.
2. Explain every recommendation.
3. Simulation before intervention.
4. Humans always remain in control.

No contribution may introduce remote command execution, SSH automation, sudo usage, or automatic OS mutation.

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

```bash
git clone https://github.com/shouryaveggalam/AetherOS.git
cd AetherOS
python3.12 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
```

Verify:

```bash
python -m aetheros
pytest --cov=aetheros --cov-fail-under=90
```

---

## Coding standards

- **Python 3.12** with full type hints on public APIs
- Prefer **immutable dataclasses** (`frozen=True`) for snapshots and plans
- Keep functions short; separate collection, analysis, and Rich rendering
- **No** NumPy / pandas / scikit-learn in predictive paths (pure Python statistics)
- **No** subprocess shelling for system control
- Format with **Black**; lint with **Ruff**

```bash
ruff check .
black .
black --check .
```

Line length: **88** (Black default).

---

## Commit format

Use concise, imperative subjects (≈50 characters), with optional body for *why*:

```text
Add cluster heartbeat online window tests

Explain online classification when last_seen is stale.
```

Preferred prefixes: `Add`, `Fix`, `Update`, `Document`, `Test`, `Refactor`.

Do not commit:

- `.venv/`, `*.db`, secrets, credentials
- Generated `reports/*.md` unless intentionally documenting a fixture
- Binary demo GIFs larger than necessary (prefer compressed assets under `docs/screenshots/`)

---

## Pull request process

1. Branch from `main` (or the active release branch).
2. Keep PRs focused — one concern per PR when possible.
3. Update docs / CHANGELOG when behavior changes.
4. Ensure CI is green:
   - `ruff check .`
   - `black --check .`
   - `pytest --cov=aetheros --cov-fail-under=90`
5. Describe operator-visible impact and safety implications in the PR body.

Maintainers may request changes for clarity, test gaps, or safety regressions.

---

## Testing requirements

- Add or extend unit tests for every non-trivial module change
- Prefer pure fixtures over live OS reads when testing logic
- Integration tests that call `psutil` must remain **read-only**
- Coverage must remain **≥ 90%** on `aetheros/`

```bash
pytest -q --cov=aetheros --cov-report=term-missing --cov-fail-under=90
```

---

## Security & safety review

Call out explicitly if your PR touches:

- Safety validator / audit log
- Cluster transport
- Plugin sandbox
- Orchestrator constraints

Default posture: **recommendation-only**.

---

## Code of Conduct

Participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

---

## Questions

Open a GitHub Discussion or issue with the `question` label. For architecture context, start with [docs/architecture.md](docs/architecture.md).
