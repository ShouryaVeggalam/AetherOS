# Cognition (v3.0)

Systems reasoning engine — **not an LLM chatbot**.

## Layers

| Package | Role |
|---------|------|
| `knowledge/` | Ontology, resource types, workload graph seeds |
| `cognition/` | Memory, causal graph, hypotheses, verifier, planner, runtime |
| `reasoning/` | Abductive / deductive / causal helpers + explain |
| `api/` | FastAPI read-only endpoints |

## Loop

Observe → Hypothesize → Verify → Plan (simulate) → Explain → Recommend

Humans approve. Nothing executes.

## Dashboard

| Key | Action |
|-----|--------|
| `G` | Cognitive Graph |
| `ESC` | Leave |

## API

```bash
pip install -e .
uvicorn aetheros.api.app:app --reload
```

- `GET /health`
- `GET /knowledge/ontology`
- `GET /memory/facts`
- `POST /cognition/reason`
