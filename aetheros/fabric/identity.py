"""Fabric identity — stable node identities across the federation.

Identities are declarative labels only. Never authenticate remote hosts
or open credentials stores.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

NodeClass = Literal[
    "personal",
    "server",
    "cloud",
    "edge",
    "robot",
    "ai_cluster",
    "iot",
]


@dataclass(frozen=True, slots=True)
class FabricIdentity:
    """One immutable federated node identity.

    Attributes:
        node_id: Globally unique id.
        display_name: Human label.
        node_class: Device class.
        region_id: Hosting region label.
        version: Fabric software version string.
    """

    node_id: str
    display_name: str
    node_class: NodeClass
    region_id: str
    version: str

    def __post_init__(self) -> None:
        """Reject empty ids."""

        if not self.node_id.strip():
            raise ValueError("node_id must be non-empty")


SEED_IDENTITIES: tuple[FabricIdentity, ...] = (
    FabricIdentity(
        "node.local.pc", "Local Workstation", "personal", "region.local", "9.0.0"
    ),
    FabricIdentity("node.edge.1", "Edge Gateway-1", "edge", "region.edge", "9.0.0"),
    FabricIdentity(
        "node.cloud.gpu.1", "Cloud GPU Pool", "ai_cluster", "region.cloud", "9.0.0"
    ),
    FabricIdentity("node.robot.1", "Fleet Robot-1", "robot", "region.local", "9.0.0"),
    FabricIdentity("node.iot.hub", "IoT Hub", "iot", "region.edge", "9.0.0"),
    FabricIdentity("node.server.1", "App Server-1", "server", "region.local", "9.0.0"),
)
