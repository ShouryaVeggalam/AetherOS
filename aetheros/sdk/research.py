"""Public Python SDK — research resource helper (HTTP client side)."""

from __future__ import annotations

from typing import Any


class ResearchResource:
    """Thin wrapper around the public research endpoint."""

    def __init__(self, request: Any) -> None:
        self._request = request

    def get(self) -> dict[str, Any]:
        """Fetch a research-grade summary."""

        return self._request("GET", "/api/v1/research")
