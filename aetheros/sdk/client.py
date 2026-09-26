"""AetherClient — public Python SDK for the versioned REST API.

Read-only HTTP client. Authentication header is a placeholder for future use.
"""

from __future__ import annotations

from typing import Any

import httpx

from aetheros.sdk.context import ContextResource
from aetheros.sdk.graph import GraphResource
from aetheros.sdk.reasoning import ReasoningResource
from aetheros.sdk.research import ResearchResource
from aetheros.sdk.twin import TwinResource


class AetherClient:
    """Versioned public API client (``/api/v1``).

    Example::

        from aetheros import AetherClient

        client = AetherClient()
        client.health()
        client.simulate(scenario="CPU_OVERLOAD")
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        *,
        api_key: str | None = None,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            transport=transport,
        )
        self.graph_api = GraphResource(self._request)
        self.context_api = ContextResource(self._request)
        self.reasoning_api = ReasoningResource(self._request)
        self.twin_api = TwinResource(self._request)
        self.research_api = ResearchResource(self._request)

    def close(self) -> None:
        """Close the underlying HTTP client."""

        self._client.close()

    def __enter__(self) -> AetherClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            # Placeholder auth scheme — not enforced by the server yet.
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = self._client.request(
            method,
            path,
            params=params,
            json=json,
            headers=self._headers(),
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            return {"data": data}
        return data

    def health(self) -> dict[str, Any]:
        """GET /api/v1/health."""

        return self._request("GET", "/api/v1/health")

    def context(self, **params: Any) -> dict[str, Any]:
        """GET /api/v1/context."""

        return self.context_api.get(**params)

    def graph(self) -> dict[str, Any]:
        """GET /api/v1/graph."""

        return self.graph_api.get()

    def reasoning(self, **params: Any) -> dict[str, Any]:
        """GET /api/v1/reasoning."""

        return self.reasoning_api.get(**params)

    def simulate(self, **kwargs: Any) -> dict[str, Any]:
        """POST /api/v1/twin/simulate."""

        return self.twin_api.simulate(**kwargs)

    def research(self) -> dict[str, Any]:
        """GET /api/v1/research."""

        return self.research_api.get()

    def plugins(self) -> dict[str, Any]:
        """GET /api/v1/plugins."""

        return self._request("GET", "/api/v1/plugins")
