## Summary

<!-- What does this PR change, and why? -->

## Type

- [ ] Bug fix
- [ ] Documentation / release packaging
- [ ] Tests / CI
- [ ] Refactor (no behavior change)
- [ ] Feature (must pass CELESTRA gate — prefer a tracking issue first)

## Safety invariants

- [ ] Userspace only (no kernel modules / drivers)
- [ ] Read-only / recommendation-only (no shell, sudo, Terraform apply, kubectl apply, or host mutation)
- [ ] Human-in-the-loop preserved
- [ ] Twin / scheduler paths do not mutate live baselines
- [ ] No database migrations (or migrations are documented and additive)
- [ ] No intentional public API breaking changes (or changelog + migration notes)

## Test plan

- [ ] `ruff check .`
- [ ] `black --check .`
- [ ] `python scripts/check_import_cycles.py`
- [ ] `pytest --cov=aetheros --cov-fail-under=90`
- [ ] Docs updated (`CHANGELOG.md` / module docs / README hotkeys) when behavior or packaging changes
- [ ] Benchmarks: methodology only — no invented numbers

## Operator-visible impact

<!-- Dashboard hotkeys, Horizon pages, API routes, CLI entry points, etc. -->

## Related

<!-- Fixes #NNN · Refs docs/releases/v6.0.0.md · Refs docs/CELESTRA.md -->
