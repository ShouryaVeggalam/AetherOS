# Knowledge vs Ontology

AetherOS keeps **two** relation catalogs on purpose. Prefer the namespaced
types in new code.

| Catalog | Type | Members | Used by |
|---------|------|---------|---------|
| Causal / cognitive | `CausalRelationKind` | CAUSES, USES, DEPENDS_ON, PREDICTS, EXPLAINS | `knowledge`, cognition causal graph, reasoning |
| Genesis ontology | `OntologyRelationKind` | CAUSES, USES, ALLOCATES, DEPENDS_ON, IMPROVES, DEGRADES | `ontology`, Genesis, kernel facade |

Compat aliases: both packages still export `RelationKind` pointing at their
namespaced type. Do not import `RelationKind` from both packages in one module.

```python
from aetheros.knowledge import CausalRelationKind
from aetheros.ontology import OntologyRelationKind
```

## Related

- [Architecture](architecture.md)
- [Cognition](cognition.md)
- [Genesis](genesis.md)
