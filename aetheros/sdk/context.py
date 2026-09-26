"""Public Python SDK — context resource helper (HTTP client side)."""

from __future__ import annotations

from typing import Any


class ContextResource:
    """Thin wrapper around the public context endpoint."""

    def __init__(self, request: Any) -> None:
        self._request = request

    def get(self, **params: Any) -> dict[str, Any]:
        """Fetch operational context (optional query params)."""

        return self._request("GET", "/api/v1/context", params=params or None)
