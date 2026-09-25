# ADR-0002 — Public API stability policy

- **Status:** Accepted
- **Date:** 2026-09-25
- **Deciders:** CELESTRA / AetherOS release engineering

## Context

Packages under `aetheros/` export many symbols via `__init__.py`. Downstream
operators and CI scripts depend on those names remaining stable for v2.0.

## Decision

1. Symbols listed in each package `__all__` are **public** for v2.0.x.
2. Breaking renames or removals require a minor/major bump and a CHANGELOG entry.
3. Additive exports are allowed in patch releases.
4. Internal modules without `__all__` membership are unstable.
5. Strategy `ResearchReport` and intelligence `SystemResearchReport` remain distinct.

## Consequences

- Release candidate freezes documented public surfaces.
- Tests and docs should import from package roots, not private modules, when possible.
