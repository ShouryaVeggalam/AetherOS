# Resource Graph Engine (v2.0 P4)

Immutable directed **host resource graph** — the canonical local intelligence
model for prediction, reasoning, explainability, and simulation.

Distinct from Sentinel’s service ``DependencyGraph`` (same package, different
types).

## Packages

| Module | Role |
|--------|------|
| `models.py` | `ResourceNode`, `ResourceEdge`, `ResourceGraph` |
| `builder.py` | Build from real telemetry only |
| `validator.py` | Cycles, missing nodes, invalid types, duplicate ids |
| `queries.py` | Neighbors, dependents, path, subgraph, process resources |
| `serializer.py` | Versioned JSON (`schema_version=1.0.0`), no pickle |
| `renderer.py` | Rich Tree panel |

## Dashboard

Press **Y** for Resource Graph. (**G** remains Genesis — key conflict avoided
without changing existing runtime shortcuts.)

## Public API

```python
from aetheros.graph import build_resource_graph, validate_resource_graph

graph = build_resource_graph(system_snapshot, intent_name="Coding")
assert validate_resource_graph(graph).ok
```

## Constraints

- Frozen dataclasses only
- No fake GPU/network/cluster nodes without telemetry
- Humans remain in control; graph is observation-only
