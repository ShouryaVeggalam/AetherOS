"""Plugin SDK version identity — v5.0 P1.

Third-party plugins declare ``sdk: ">=5.0.0,<6"`` in their YAML manifest.
Bump ``SDK_VERSION`` only on incompatible API surface changes.
"""

from __future__ import annotations

SDK_NAME = "aetheros-plugin-sdk"
SDK_VERSION = "5.0.0"
SDK_MAJOR = 5
SDK_MINOR = 0
SDK_PATCH = 0

# Capabilities exposed by this SDK release (read-only / advisory only).
SUPPORTED_CAPABILITIES: frozenset[str] = frozenset(
    {
        "telemetry.read",
        "graph.read",
        "context.read",
        "events.subscribe",
        "dashboard.contribute",
        "policy.advise",
        "simulation.model",
        "learning.analyze",
    }
)
