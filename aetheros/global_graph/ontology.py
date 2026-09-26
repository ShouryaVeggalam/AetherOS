"""Global Knowledge Graph ontology — immutable node type catalog.

v6.0 P3. Read-only Horizon intelligence model. Distinct from the Causal
Knowledge Graph (``aetheros.knowledge``) and Resource Graph catalogs.
"""

from __future__ import annotations

from typing import Literal

GlobalNodeType = Literal[
    # Infrastructure
    "Region",
    "Datacenter",
    "Cluster",
    "Node",
    "VM",
    "Container",
    "Pod",
    "Service",
    # Resources
    "CPU",
    "Memory",
    "GPU",
    "Disk",
    "Network",
    # Intelligence
    "Context",
    "Intent",
    "Pattern",
    "Discovery",
    "Simulation",
    "Consensus",
    "Research",
]

INFRASTRUCTURE_TYPES: frozenset[str] = frozenset(
    {
        "Region",
        "Datacenter",
        "Cluster",
        "Node",
        "VM",
        "Container",
        "Pod",
        "Service",
    }
)

RESOURCE_TYPES: frozenset[str] = frozenset({"CPU", "Memory", "GPU", "Disk", "Network"})

INTELLIGENCE_TYPES: frozenset[str] = frozenset(
    {
        "Context",
        "Intent",
        "Pattern",
        "Discovery",
        "Simulation",
        "Consensus",
        "Research",
    }
)

GLOBAL_NODE_TYPES: frozenset[str] = (
    INFRASTRUCTURE_TYPES | RESOURCE_TYPES | INTELLIGENCE_TYPES
)


def is_global_node_type(value: str) -> bool:
    """True when ``value`` is a supported Global Knowledge Graph node type."""

    return value in GLOBAL_NODE_TYPES
