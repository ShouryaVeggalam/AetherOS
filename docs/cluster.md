# Cluster

Multi-device intelligence turns AetherOS into a **distributed observation plane**. Each machine runs a lightweight agent that publishes telemetry; the dashboard aggregates a unified, read-only view.

## Responsibilities

### `aetheros/cluster`

| Module | Role |
|--------|------|
| `models.py` | `ClusterNode`, `Heartbeat`, `ClusterSnapshot` |
| `transport.py` | JSON `publish` / `subscribe` (WebSocket-ready shape) |
| `registry.py` | Node upsert + SQLite latest state |
| `heartbeat.py` | Online / offline window |
| `aggregator.py` | Averages, highest load, alerts |
| `node.py` | Health classification (color only) |
| `renderer.py` | Cluster Overview panel |

### `aetheros/agent` (not `aetheros.agents`)

Lightweight **cluster node publisher** — local samples + demo peers. Distinct from
the multi-agent deliberation package (`aetheros.agents`); see [agents.md](agents.md).

| Module | Role |
|--------|------|
| `collector.py` | Local read-only samples |
| `publisher.py` | Telemetry + heartbeat publish; demo peers for single-host demos |

## Transport rules

- Messages are JSON-serialized
- Local in-process bus today (`LocalJSONTransport`)
- Designed so a WebSocket transport can be added later
- **No SSH**, **no remote shell**, **no network command execution**

## Health (display only)

| State | Meaning |
|-------|---------|
| Healthy | Online and within normal load bands |
| Warning | Elevated CPU / memory / disk |
| Critical | Extreme load |
| Offline | Outside heartbeat window |

Health colors never trigger automatic remediation.

## Dashboard

| Key | Action |
|-----|--------|
| `C` | Cluster Overview |
| `ESC` | Leave overlay |

On a single host, demo peers (Desktop / Pi / Cloud) publish synthetic telemetry so the multi-node UI can be exercised without remote machines.

## Related

Workload placement across cluster nodes: `aetheros/orchestrator` (shortcut `W`).
