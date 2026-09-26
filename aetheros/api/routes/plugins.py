"""Public API v1 — plugin catalog (read-only).

Lists Plugin SDK example packages via manifest parse. Never loads unsafe code
into the API process beyond validated discovery metadata.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from aetheros.api.schemas import V1PluginInfo, V1PluginsResponse

router = APIRouter(tags=["public-api-v1"])


@router.get("/plugins", response_model=V1PluginsResponse)
def get_plugins() -> V1PluginsResponse:
    """Return the public plugin catalog from the v5 Plugin SDK examples."""

    sdk_version = "unknown"
    plugins: list[V1PluginInfo] = []
    try:
        from plugins.sdk import SDK_VERSION, PluginLoader, PluginValidator

        sdk_version = SDK_VERSION
        root = Path(__file__).resolve().parents[3] / "plugins" / "examples"
        loader = PluginLoader()
        validator = PluginValidator()
        for path in loader.discover(root):
            result = validator.validate_directory(path)
            if not result.ok or result.manifest is None:
                continue
            m = result.manifest
            plugins.append(
                V1PluginInfo(
                    id=m.id,
                    name=m.name,
                    version=m.version,
                    description=m.description,
                    capabilities=list(m.capabilities),
                    path=str(path),
                )
            )
    except Exception:
        plugins = []

    return V1PluginsResponse(
        sdk_version=sdk_version,
        plugins=plugins,
        count=len(plugins),
    )
