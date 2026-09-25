# Horizon — Planetary Intelligence Network (v6.0)

AetherOS Horizon is a simulation-first global knowledge graph spanning
cloud regions, edge devices, robotics, IoT, satellites, and HPC.

## Constraints

- Read-only / recommendation-only
- No shell execution, no sudo, no kernel or hardware control
- Latency estimates never probe the network
- Resilience and capacity are what-if simulations only
- Humans approve any follow-up action

## Packages

| Package | Role |
|---------|------|
| `aetheros.horizon` | World graph, latency, resilience, capacity, runtime |
| `aetheros.edge` | Gateway, sensors, mobile, IoT inventories |
| `aetheros.robotics` | Fleet, autonomy profiles, telemetry |

## World hierarchy

Earth → Region → Country → Datacenter → Cluster → Node → Process

Overlays: edge gateways, sensors, robots, satellites, HPC.

Planetary-scale **census** counts (e.g. 184,220 nodes) are separate from
the navigable NetworkX **sample** graph used for algorithms.

## Dashboard

Press **H** for Horizon. Help moved to **?**.

## API

```
GET /world
GET /regions
GET /latency
GET /resilience
GET /capacity
GET /graph
```

```bash
uvicorn aetheros.api.app:app --reload
```
