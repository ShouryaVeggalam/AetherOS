# Aether Fabric (v9.0)

Aether Fabric is the universal intelligence layer spanning personal
computers, servers, cloud, edge, robotics, AI clusters, and IoT.

## Constraints

- Read-only / simulation-only
- No shell, sudo, kernel, or hardware control
- Federation never executes remote actions
- Humans approve every recommendation

## Packages

| Package | Role |
|---------|------|
| `aetheros.protocol` | Events, in-process transport, serialization, versioning |
| `aetheros.fabric` | Universe census, federation, graph, sync, runtime |
| `aetheros.twin` | Global digital twin scenarios |

## Dashboard

Press **F** for Fabric.

## API

```
GET /fabric
GET /federation
GET /fabric/graph
GET /twin
GET /health
GET /knowledge
```

(`GET /graph` remains the Horizon world graph for compatibility.)
