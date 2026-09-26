"""Public Python SDK — reasoning resource helper (HTTP client side)."""

from __future__ import annotations

from typing import Any


class ReasoningResource:
    """Thin wrapper around the public reasoning endpoint."""

    def __init__(self, request: Any) -> None:
        self._request = request

    def get(self, **params: Any) -> dict[str, Any]:
        """Fetch a read-only reasoning summary."""

        return self._request("GET", "/api/v1/reasoning", params=params or None)
