# Policy

Architecture alias for [`aetheros.policy_engine`](../policy_engine/).

## Public API

```python
from aetheros.policy import PolicyEngine, TelemetrySnapshot, PolicyRecommendation
```

## Architecture

```mermaid
flowchart LR
    T[TelemetrySnapshot] --> P[PolicyEngine]
    P --> R[PolicyRecommendation]
```

Advice only — never executes OS actions.
