# Agentic Systems Intelligence (v4.0)

AetherOS v4 adds a multi-agent collaboration layer. Specialists publish
immutable findings on an async message bus; a coordinator merges conflicts
into one explainable recommendation.

## Naming: `agent` vs `agents`

These are **different packages** — do not rename casually:

| Package | Role | Docs |
|---------|------|------|
| `aetheros.agent` | Cluster **node telemetry publisher** (local + demo peers) | [cluster.md](cluster.md) |
| `aetheros.agents` | Multi-agent **specialists + coordinator** (deliberation) | this page |
| `aetheros.runtime` | `AgenticRuntime` loop that drives `agents` | this page |

Dashboard imports both: cluster panel uses `agent`; Multi-Agent View (key **M**) uses `agents`.

## Constraints

- Read-only / recommendation-only
- No shell execution, no sudo, no kernel changes
- Humans approve any action
- Agents never call each other directly

## Packages

| Package | Role |
|---------|------|
| `aetheros.messaging` | Immutable events, protocol, `AsyncMessageBus` |
| `aetheros.agents` | Telemetry, Performance, Battery, Security, Cluster, Research, Coordinator |
| `aetheros.runtime` | `AgenticRuntime` deliberation entry |

## Dashboard

Press **M** for Multi-Agent View: agent status, latest messages, confidence,
and the coordinator decision.

## Conflict example

Performance may emit `increase_cpu` while Battery emits `reduce_power`.
The coordinator compares urgency × confidence and typically produces
**Balanced Mode** or **Efficiency Mode** with an explicit reasoning string.
