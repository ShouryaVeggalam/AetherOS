"""Public Python SDK — Digital Twin simulate helper (HTTP client side)."""

from __future__ import annotations

from typing import Any


class TwinResource:
    """Thin wrapper around ``POST /api/v1/twin/simulate``."""

    def __init__(self, request: Any) -> None:
        self._request = request

    def simulate(
        self,
        *,
        scenario: str = "CPU_OVERLOAD",
        cpu_percent: float = 40.0,
        memory_percent: float = 50.0,
        disk_percent: float = 30.0,
    ) -> dict[str, Any]:
        """Run a simulation-only twin scenario via the public API."""

        return self._request(
            "POST",
            "/api/v1/twin/simulate",
            json={
                "scenario": scenario,
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_percent": disk_percent,
            },
        )
