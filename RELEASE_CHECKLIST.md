# AetherOS v5.0.0 Release Checklist

**Codename:** Nexus · **Status:** Production · **License:** MIT

Use this checklist before tagging `v5.0.0`. Do **not** publish the GitHub Release
automatically; create a draft (or push the annotated tag) only after human approval.

## Pre-flight

- [x] Repository audit complete (docs, CI, version pins, safety invariants)
- [x] No new product features on the release branch
- [x] No runtime behavior changes intended for this packaging commit
- [x] No API breaking changes intended
- [x] No database migrations

## Documentation audit

- [x] [README.md](README.md) — Nexus hero, badges, install, architecture, screenshots, roadmap, contributing
- [x] [LICENSE](LICENSE) — MIT
- [x] [CHANGELOG.md](CHANGELOG.md) — `[5.0.0]` Nexus section
- [x] [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- [x] [SECURITY.md](SECURITY.md) — 5.0.x supported
- [x] [CONTRIBUTING.md](CONTRIBUTING.md)
- [x] [docs/architecture.md](docs/architecture.md) + [docs/architecture/](docs/architecture/) Mermaid diagrams
- [x] [docs/benchmarks.md](docs/benchmarks.md) — reproducible methodology
- [x] [docs/releases/v5.0.0.md](docs/releases/v5.0.0.md)
- [x] [docs/screenshots/README.md](docs/screenshots/README.md) — demo GIF placeholder

## Quality gates

- [x] `ruff check .` (with `node_modules` / `.next` excluded)
- [x] `black --check .`
- [x] `python -m compileall -q aetheros services`
- [x] `python scripts/check_import_cycles.py`
- [x] `pytest --cov=aetheros --cov-fail-under=90` (~95.24% measured)
- [x] Coverage XML retained for release artifacts
- [x] `python scripts/run_benchmarks.py` refreshed
- [x] `python -m build` succeeds (verify before tag push)

## GitHub packaging

- [x] CI workflow: lint · format · type surface · tests · coverage
- [x] Release workflow: draft GitHub Release on `v*` tags
- [x] Issue templates + PR template
- [x] `.github/FUNDING.yml`
- [x] Repository labels configuration
- [ ] Human review of draft release body titled **AetherOS v5.0 — Nexus**

## Versioning

- [x] `pyproject.toml` version `5.0.0`
- [x] `aetheros.__version__ == "5.0.0"`
- [x] CHANGELOG has `[5.0.0]` section
- [ ] Annotated tag prepared locally: `v5.0.0` (human publishes)

## Tag & draft release (manual)

```bash
# After final green CI on the release commit:
git tag -a v5.0.0 -m "AetherOS v5.0.0 — Nexus"
# Review docs/releases/v5.0.0.md then push when approved:
# git push origin v5.0.0
# GitHub Actions creates a DRAFT release titled: AetherOS v5.0 — Nexus
```

Do not enable automatic production publish without maintainer approval.

## Post-tag

- [ ] Confirm draft release assets (wheel + sdist)
- [ ] Verify README badges and links on GitHub
- [ ] Optional: announce Horizon roadmap follow-ups
