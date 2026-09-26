# Policy / Policy Studio

v5.0 P4 **Policy Studio** lives in this package. Legacy telemetry detectors
remain available via re-exports of [`aetheros.policy_engine`](../policy_engine/).

## Policy Studio

```python
from aetheros.policy import PolicyStudio, PolicyRegistry, parse_rule

studio = PolicyStudio(PolicyRegistry())
studio.registry.create(
    id="battery-saver",
    name="Battery Saver",
    description="Reject High Performance when battery < 20%",
    rules=(parse_rule("battery < 20", action="Reject High Performance"),),
)
results = studio.evaluate({"battery": 15, "intent": "CODING"})
impact = studio.simulate(
    {"battery": 15},
    recommendations=("High Performance", "Balanced"),
)
```

Policies never control the OS — simulation / recommendation filtering only.

## Legacy API

```python
from aetheros.policy import PolicyEngine, TelemetrySnapshot, PolicyRecommendation
```

Docs: [policy_studio.md](../../docs/policy_studio.md)
