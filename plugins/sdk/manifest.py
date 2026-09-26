"""Plugin manifest — YAML declaration for sandboxed intelligence plugins.

Presentation / registration metadata only. Never executes plugin code.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from plugins.sdk.version import SDK_MAJOR, SUPPORTED_CAPABILITIES


@dataclass(frozen=True, slots=True)
class PluginManifest:
    """Immutable plugin identity + requested capabilities.

    Attributes:
        id: Stable plugin identifier (kebab-case recommended).
        name: Human-readable display name.
        version: Plugin semantic version.
        author: Author or organization.
        description: Short summary.
        sdk: SDK version constraint string (e.g. ``>=5.0.0,<6``).
        entry: Relative entry module (default ``plugin.py``).
        capabilities: Requested capability strings.
        events: Event topics to subscribe to.
        enabled: Whether the plugin loads enabled by default.
    """

    id: str
    name: str
    version: str
    author: str
    description: str
    sdk: str = ">=5.0.0,<6"
    entry: str = "plugin.py"
    capabilities: tuple[str, ...] = ()
    events: tuple[str, ...] = ()
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if not self.name.strip():
            raise ValueError("name must be non-empty")
        if not self.version.strip():
            raise ValueError("version must be non-empty")


def load_manifest(path: Path | str) -> PluginManifest:
    """Parse a ``plugin.yaml`` / ``manifest.yaml`` file into ``PluginManifest``."""

    file_path = Path(path)
    raw = file_path.read_text(encoding="utf-8")
    return parse_manifest(raw, source=str(file_path))


def parse_manifest(raw: str, *, source: str = "<string>") -> PluginManifest:
    """Parse YAML text into a validated ``PluginManifest``."""

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML in {source}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"manifest root must be a mapping ({source})")
    return manifest_from_dict(data)


def manifest_from_dict(data: dict[str, Any]) -> PluginManifest:
    """Build ``PluginManifest`` from a plain dict (already-parsed YAML)."""

    caps = data.get("capabilities") or ()
    events = data.get("events") or ()
    if isinstance(caps, str):
        caps = [caps]
    if isinstance(events, str):
        events = [events]
    return PluginManifest(
        id=str(data.get("id") or data.get("name") or "").strip(),
        name=str(data.get("name") or "").strip(),
        version=str(data.get("version") or "").strip(),
        author=str(data.get("author") or "unknown").strip(),
        description=str(data.get("description") or "").strip(),
        sdk=str(data.get("sdk") or ">=5.0.0,<6").strip(),
        entry=str(data.get("entry") or "plugin.py").strip(),
        capabilities=tuple(str(c).strip() for c in caps if str(c).strip()),
        events=tuple(str(e).strip() for e in events if str(e).strip()),
        enabled=bool(data.get("enabled", True)),
    )


def sdk_constraint_allows(constraint: str, *, major: int = SDK_MAJOR) -> bool:
    """Return True when ``constraint`` accepts the current SDK major.

    Supports simple forms: ``5``, ``5.x``, ``>=5.0.0,<6``, ``==5.0.0``.
    """

    text = constraint.strip()
    if not text:
        return False
    if text in {f"{major}", f"{major}.x", f"^{major}"}:
        return True
    if text.startswith("=="):
        ver = text[2:].strip()
        return ver.startswith(f"{major}.")
    # Default range style >=X,<Y
    if ">=" in text or "<" in text:
        parts = [p.strip() for p in text.split(",")]
        lower_ok = True
        upper_ok = True
        for part in parts:
            if part.startswith(">="):
                lower = part[2:].strip()
                lower_major = int(lower.split(".", 1)[0])
                lower_ok = major >= lower_major
            elif part.startswith("<"):
                upper = part[1:].strip()
                upper_major = int(upper.split(".", 1)[0])
                upper_ok = major < upper_major
        return lower_ok and upper_ok
    return text.startswith(f"{major}.")


def unknown_capabilities(requested: tuple[str, ...]) -> tuple[str, ...]:
    """Return capability names not supported by this SDK release."""

    return tuple(c for c in requested if c not in SUPPORTED_CAPABILITIES)
