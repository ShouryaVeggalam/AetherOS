# CELESTRA GII — General Intelligence Infrastructure

Language Intelligence **v9.0** / Phase 16.

Foundation models are interchangeable compute. This package owns cognition,
planning, learning, societies, and lifelong memory interfaces.

## Module 1 — Cognition Engine

```bash
# Create a cognition plan
curl -s -X POST http://127.0.0.1:8000/v9/cognition \
  -H 'content-type: application/json' \
  -d '{"goal":"Research latency and then implement a fix","constraints":["Stay under 100ms"]}'
```

Public API:

- `CognitionEngine.understand(goal, context, constraints) -> CognitionPlan`
- `POST /v9/cognition` · `GET /v9/cognition` · `GET /v9/cognition/{id}`
- `GET /v9/intelligence`

See [docs/PHASE16.md](../../docs/PHASE16.md).
