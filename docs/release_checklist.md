# AetherOS v2.0.0 Release Checklist

**Codename:** Intelligence · **Status:** Release Candidate

Use this checklist before tagging `v2.0.0`. Do **not** publish the GitHub Release
automatically; create a draft or tag locally after human approval.

## Pre-flight

- [ ] Architecture frozen ([ADR-0001](adr/0001-architecture-freeze-v2.md))
- [ ] Public API policy acknowledged ([ADR-0002](adr/0002-public-api-stability.md))
- [ ] No new product features on the RC branch
- [ ] No dashboard redesign; no DB migrations; no API rewrites

## Documentation audit

- [ ] [README.md](../README.md)
- [ ] [CONTRIBUTING.md](../CONTRIBUTING.md)
- [ ] [LICENSE](../LICENSE)
- [ ] [CHANGELOG.md](../CHANGELOG.md)
- [ ] [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md)
- [ ] [SECURITY.md](../SECURITY.md)
- [ ] [docs/architecture.md](architecture.md)
- [ ] [docs/CELESTRA.md](CELESTRA.md)
- [ ] [docs/context_engine.md](context_engine.md)
- [ ] [docs/digital_twin.md](digital_twin.md)
- [ ] [docs/graph_bridge.md](graph_bridge.md)
- [ ] [docs/reasoning.md](reasoning.md)
- [ ] [docs/research_engine.md](research_engine.md)
- [ ] [docs/benchmarks.md](benchmarks.md)
- [ ] [docs/releases/v2.0.0.md](releases/v2.0.0.md)
- [ ] [docs/adr/](adr/)

## Quality gates

- [ ] `ruff check .`
- [ ] `black --check .`
- [ ] `python scripts/check_import_cycles.py`
- [ ] `python -m compileall -q aetheros`
- [ ] `pytest --cov=aetheros --cov-fail-under=90`
- [ ] Core packages (graph, bridge, reasoning, twin, context, research) ≥95%
- [ ] `python -m build` succeeds
- [ ] Benchmarks refreshed (`python scripts/run_benchmarks.py`)

## Versioning

- [ ] `pyproject.toml` version `2.0.0`
- [ ] `aetheros.__version__ == "2.0.0"`
- [ ] CHANGELOG has `[2.0.0]` section
- [ ] Annotated tag prepared: `v2.0.0` (human publishes)

## GitHub Release (manual)

```bash
git tag -a v2.0.0 -m "AetherOS v2.0.0 — Intelligence (RC)"
# Review docs/releases/v2.0.0.md then push tag when approved:
# git push origin v2.0.0
# Create a DRAFT GitHub Release titled: AetherOS v2.0 — Intelligence
```

Do not enable automatic production publish for this RC.
