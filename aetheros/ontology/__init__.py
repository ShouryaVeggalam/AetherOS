"""Genesis computing ontology — resources, workloads, intents, relationships."""

from aetheros.ontology.intents import INTENT_ENTITIES, IntentConcept
from aetheros.ontology.relationships import (
    SEED_RELATIONS,
    OntologyRelation,
    RelationKind,
    build_ontology_graph,
)
from aetheros.ontology.resources import RESOURCE_ENTITIES, ResourceConcept
from aetheros.ontology.workloads import WORKLOAD_ENTITIES, WorkloadConcept

__all__ = [
    "INTENT_ENTITIES",
    "RESOURCE_ENTITIES",
    "SEED_RELATIONS",
    "WORKLOAD_ENTITIES",
    "IntentConcept",
    "OntologyRelation",
    "RelationKind",
    "ResourceConcept",
    "WorkloadConcept",
    "build_ontology_graph",
]
