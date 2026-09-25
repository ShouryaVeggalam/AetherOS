# Sentinel Intelligence Fabric (v8.0)

Sentinel is the resilience intelligence layer: detect anomalies, explain
root causes, predict cascades, and recommend recovery — without executing
any recovery actions.

## Constraints

- Recommendation only
- No shell / sudo / kernel / hardware control
- Cascade and recovery are simulations
- Humans approve decisions

## Packages

| Package | Role |
|---------|------|
| `aetheros.graph` | Service + infra dependency topology (NetworkX) |
| `aetheros.sentinel` | Anomaly, root cause, cascade, recovery, resilience score |

## Dashboard

Press **S** for Sentinel.

## API

```
GET /sentinel
GET /sentinel/anomalies
GET /sentinel/graph
```
