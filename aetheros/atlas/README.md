# Atlas (v5)

Global infrastructure reasoning facade.

Atlas maps to the existing Horizon world graph and Global Twin. It does
**not** introduce a second planetary model.

## Hierarchy

```mermaid
flowchart TD
    W[World / Earth] --> R[Regions]
    R --> D[Datacenters]
    D --> C[Clusters]
    C --> N[Nodes]
```

## Public API

```python
from aetheros.atlas import WorldGraph, HorizonRuntime, GlobalTwin
```

## Invariants

- Read-only / simulation-only
- No remote execution
- Humans approve recommendations
