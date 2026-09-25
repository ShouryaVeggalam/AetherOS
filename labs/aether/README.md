# Aether Lab — Cognitive Architecture of CELESTRA X

Foundation models perform **inference**. Aether performs **cognition**.

```
Goal → Attention → Decomposition → Planning → Reasoning
    → Reflection → Critique → Revised Plan → Decision
```

Deterministic · explainable · observable. Not a language model. Not CoT generation. Not an agent framework.

## Module 1 — Attention Engine ✓

**Package:** `labs/aether/attention/`

| File | Role |
|------|------|
| `signals.py` | Normalize complexity / context / memory / uncertainty |
| `allocator.py` | Deterministic channel weights + budgets |
| `service.py` | `AttentionEngine` async facade + draft cognition plans |

### Inputs

- task complexity
- available context
- memory relevance
- uncertainty

### Outputs

- attention weights (`focus`, `memory`, `exploration`, `verification`)
- reasoning budget
- retrieval budget
- explainable `factors`

### API

| Method | Path | Status |
|--------|------|--------|
| `POST` | `/aether/attention` | Module 1 |
| `GET` | `/aether/attention/{id}` | Module 1 |
| `POST` | `/aether/cognition` | Attention-backed draft plan |
| `GET` | `/aether/plans/{id}` | Module 1 |
| `POST` | `/aether/decompose` | Pending |
| `POST` | `/aether/reflect` | Pending |
| `POST` | `/aether/critique` | Pending |
| `GET` | `/aether/health` | Ready |

### Observatory

Next.js 16 app: `labs/aether/observatory/web` — Attention Map page talks to `/aether/attention`.

```bash
# API
uvicorn aetheros.api:create_app --factory --reload

# Observatory
cd labs/aether/observatory/web && npm install && npm run dev
```

## Layout

```
labs/aether/
  attention/       # Module 1 ✓
  cognition/       # orchestration façade
  planning/        # Module 2+
  decomposition/   # Module 2+
  reflection/      # pending
  critique/        # pending
  observatory/     # Attention Map + replay helpers + Next.js UI
  api/             # FastAPI /aether
  models/          # frozen domain types
  repositories/    # append-only stores
  migrations/      # PostgreSQL forward schema
  tests/
```

## Persistence

Default: in-memory append-only repositories.  
Forward: PostgreSQL via `migrations/m0001_aether_attention.py`.
