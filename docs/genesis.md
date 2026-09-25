# Genesis Intelligence Layer (v7.0)

Genesis is the highest-level research layer in AetherOS. It generates,
simulates, verifies, and stores operational knowledge.

## Constraints

- Research / recommendation only
- Never executes commands or controls hardware
- Never stores unsupported claims
- Humans approve any follow-up

## Packages

| Package | Role |
|---------|------|
| `aetheros.ontology` | Resources, workloads, intents, relationships |
| `aetheros.genesis` | Knowledge base, hypotheses, experiments, verifier, theorems |

## Cycle

1. **Hypothesis Engine** — propose multiple stances for a research question
2. **Experiment Engine** — virtual simulations (performance / stability / efficiency / fairness)
3. **Verifier** — accept only statistically supported claims; archive rejects
4. **Knowledge Base / Theorem Store** — persist verified discoveries (SQLite)

## Dashboard

Press **G** for Genesis. Cognitive Graph moved to **K**.

## API

```
GET /genesis
GET /genesis/knowledge
GET /genesis/theorems
GET /genesis/ontology
```
