"""Public Python SDK — graph resource helper (HTTP client side).

Read-only. Talks to ``GET /api/v1/graph``.
"""

from __future__ import annotations

from typing import Any


class GraphResource:
    """Thin wrapper around the public graph endpoint."""

    def __init__(self, request: Any) -> None:
        self._request = request

    def get(self) -> dict[str, Any]:
        """Fetch the current graph projection."""

        return self._request("GET", "/api/v1/graph")
