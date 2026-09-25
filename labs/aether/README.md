# Aether Lab — Cognitive Architecture of CELESTRA X

Foundation models perform **inference**. Aether performs **cognition**.

```
Goal → Attention → Decomposition → Planning → Reasoning
    → Reflection → Critique → Revised Plan → Decision
```

Deterministic · explainable · observable.

## Modules

| Module | Package | Status |
|--------|---------|--------|
| 1 Attention | `attention/` | ✓ |
| 2 Decomposition | `decomposition/` | ✓ |
| 2+ Planning | `planning/` | ✓ |
| 3 Reflection | `reflection/` | ✓ |
| 4 Critique | `critique/` | ✓ |
| Cognition orchestrator | `cognition/` | ✓ |

## API

| Method | Path | Module |
|--------|------|--------|
| `POST` | `/aether/attention` | 1 |
| `GET` | `/aether/attention/{id}` | 1 |
| `POST` | `/aether/cognition` | 1–2 pipeline |
| `GET` | `/aether/plans/{id}` | 1–2 |
| `POST` | `/aether/decompose` | 2 |
| `GET` | `/aether/graphs/{id}` | 2 |
| `POST` | `/aether/reflect` | 3 |
| `POST` | `/aether/critique` | 4 |
| `GET` | `/aether/health` | all |

## Observatory

Next.js 16: `labs/aether/observatory/web`

- Cognition · Attention Map · Task Graph · Reflection · Critique

```bash
uvicorn aetheros.api:create_app --factory --reload
cd labs/aether/observatory/web && npm install && npm run dev
```

## Layout

```
labs/aether/
  attention/       # Module 1
  decomposition/   # Module 2 — DAG tasks
  planning/        # hierarchical CognitionPlan
  reflection/      # Module 3
  critique/        # Module 4
  cognition/       # orchestrator
  observatory/     # heatmap + Next.js UI
  api/             # FastAPI /aether
  models/
  repositories/
  migrations/
  tests/
```
