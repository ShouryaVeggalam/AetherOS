# Python SDK — AetherOS v5.0 P2

**Package:** [`aetheros/sdk/client.py`](../aetheros/sdk/client.py) (+ resource helpers)  
**Import:** `from aetheros import AetherClient`

---

## Quickstart

```python
from aetheros import AetherClient

client = AetherClient(base_url="http://127.0.0.1:8000")
print(client.health())
print(client.context(intent_name="Balanced"))
print(client.graph())
print(client.reasoning(cpu_percent=70))
print(client.simulate(scenario="CPU_OVERLOAD"))
print(client.research())
print(client.plugins())
client.close()
```

Context manager:

```python
with AetherClient() as client:
    status = client.health()["status"]
```

---

## Methods

| Method | HTTP | Notes |
|--------|------|-------|
| `health()` | `GET /api/v1/health` | Liveness |
| `context(**params)` | `GET /api/v1/context` | Optional query params |
| `graph()` | `GET /api/v1/graph` | Graph projection |
| `reasoning(**params)` | `GET /api/v1/reasoning` | Reasoning summary |
| `simulate(...)` | `POST /api/v1/twin/simulate` | Simulation only |
| `research()` | `GET /api/v1/research` | Research summary |
| `plugins()` | `GET /api/v1/plugins` | Plugin catalog |

---

## Authentication placeholder

```python
client = AetherClient(api_key="dev-token")
# Sends: Authorization: Bearer dev-token
```

Not enforced by the server in P2.

---

## Versioning policy

- Client targets **API v1** paths exclusively.
- Breaking HTTP contracts require a new client major + `/api/v2`.
- Plugin host SDK (`AetherPlugin`, sandbox, …) remains available from
  `aetheros.sdk` alongside `AetherClient`.

---

## Resource helpers

| Module | Class |
|--------|-------|
| `aetheros.sdk.graph` | `GraphResource` |
| `aetheros.sdk.context` | `ContextResource` |
| `aetheros.sdk.reasoning` | `ReasoningResource` |
| `aetheros.sdk.twin` | `TwinResource` |
| `aetheros.sdk.research` | `ResearchResource` |
