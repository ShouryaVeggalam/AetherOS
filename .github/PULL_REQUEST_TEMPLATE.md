## Summary

<!-- What does this PR change, and why? -->

## Type

- [ ] Bug fix
- [ ] Documentation / release packaging
- [ ] Tests / CI
- [ ] Refactor (no behavior change)
- [ ] Feature (must pass CELESTRA gate — prefer separate issue first)

## Safety invariants

- [ ] Userspace only (no kernel modules / drivers)
- [ ] Read-only / recommendation-only (no shell, sudo, or host mutation)
- [ ] Human-in-the-loop preserved
- [ ] No database migrations (or migrations are documented and additive)
- [ ] No intentional public API breaking changes (or changelog + migration notes)

## Test plan

- [ ] `ruff check .`
- [ ] `black --check .`
- [ ] `python scripts/check_import_cycles.py`
- [ ] `pytest --cov=aetheros --cov-fail-under=90`
- [ ] Docs updated (`CHANGELOG.md` / module docs) when behavior or packaging changes

## Operator-visible impact

<!-- Dashboard hotkeys, API routes, CLI entry points, etc. -->

## Related

<!-- Fixes #NNN · Refs docs/releases/v5.0.0.md -->
