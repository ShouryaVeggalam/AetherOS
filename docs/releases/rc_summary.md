# AetherOS v2.0.0 RC — Summary

Generated during P10 release engineering.

## Semantic version

| Field | Value |
|-------|-------|
| Version | `2.0.0` |
| Codename | Intelligence |
| Status | Release Candidate |
| `aetheros.__version__` | `2.0.0` |
| `pyproject.toml` | `2.0.0` |
| Prepared tag | `v2.0.0` (not pushed by automation) |

## Quality gates (local)

| Gate | Result |
|------|--------|
| Ruff | Pass |
| Black | Pass |
| `compileall` | Pass |
| Import cycles | Pass |
| Pytest | Pass |
| Coverage overall | **92.36%** (≥90%) |
| Core graph | 97.1% |
| Core bridge | 98.0% |
| Core reasoning | 98.0% |
| Core twin | 96.8% |
| Core context | 98.1% |
| Core research | 97.3% |
| Build | Run `python -m build` before tagging |

## Artifacts

- `reports/coverage.xml` — machine-readable coverage
- `reports/benchmarks.json` — benchmark raw data
- `docs/benchmarks.md` — methodology + table
- `docs/releases/v2.0.0.md` — release notes
- `docs/release_checklist.md` — human checklist
- `SECURITY.md` — security policy
- `docs/adr/` — architecture freeze + API stability

## Publish procedure (manual)

```bash
# After checklist complete:
git tag -a v2.0.0 -m "AetherOS v2.0.0 — Intelligence (RC)"
git push origin v2.0.0
# GitHub Actions creates a DRAFT release only (draft: true).
# Human publishes the draft when ready.
```

## Non-goals completed

No new product features · no UI redesign · no DB migrations · no API rewrites.
