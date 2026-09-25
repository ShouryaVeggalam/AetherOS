# ADR-0001 — Architecture freeze for v2.0 Intelligence

- **Status:** Accepted
- **Date:** 2026-09-25
- **Deciders:** CELESTRA / AetherOS release engineering

## Context

P1–P9 delivered cycle detection, integrity, hardening, Resource Graph, Graph Bridge,
Graph Reasoning, Digital Twin, Context Intelligence, and Research Intelligence.
Release engineering requires a frozen architecture so v2.0.0 RC does not drift.

## Decision

For the `v2.0.x` line:

1. No new product subsystems land without a new ADR.
2. Runtime behavior remains userspace, read-only, human-in-the-loop.
3. Dashboard chrome is not redesigned; additive hotkeys only.
4. Database schemas for existing stores are not migrated except isolated
   read-only research tables (none required for this RC).
5. Foundation models / GII services remain optional adapters — not core OS mutation.

## Consequences

- Release work is documentation, tests, benchmarks, CI gates, and packaging only.
- Feature work targets `v2.1+` after explicit ADR acceptance.
