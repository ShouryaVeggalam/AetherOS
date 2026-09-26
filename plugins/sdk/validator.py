"""Plugin validator — manifest + capability + SDK constraint checks.

Runs before sandbox import. Never executes plugin code.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from plugins.sdk.manifest import (
    PluginManifest,
    load_manifest,
    sdk_constraint_allows,
    unknown_capabilities,
)
from plugins.sdk.version import SDK_VERSION


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Outcome of validating a plugin package directory."""

    ok: bool
    reason: str
    manifest: PluginManifest | None = None
    findings: tuple[str, ...] = ()


class PluginValidator:
    """Validate plugin manifests and package layout."""

    MANIFEST_NAMES: tuple[str, ...] = (
        "plugin.yaml",
        "plugin.yml",
        "manifest.yaml",
        "manifest.yml",
    )

    def validate_directory(self, plugin_dir: Path | str) -> ValidationResult:
        """Validate layout + manifest for one plugin directory."""

        root = Path(plugin_dir)
        findings: list[str] = []
        if not root.is_dir():
            return ValidationResult(
                ok=False,
                reason="Not a directory.",
                findings=("missing_directory",),
            )

        manifest_path = self._find_manifest(root)
        if manifest_path is None:
            return ValidationResult(
                ok=False,
                reason="Missing plugin.yaml / manifest.yaml.",
                findings=("missing_manifest",),
            )

        try:
            manifest = load_manifest(manifest_path)
        except (OSError, ValueError) as exc:
            return ValidationResult(
                ok=False,
                reason=f"Manifest parse failed: {exc}",
                findings=("invalid_manifest",),
            )

        if not sdk_constraint_allows(manifest.sdk):
            findings.append(
                f"sdk constraint '{manifest.sdk}' incompatible with SDK {SDK_VERSION}"
            )

        unknown = unknown_capabilities(manifest.capabilities)
        for cap in unknown:
            findings.append(f"unknown capability '{cap}'")

        entry = root / manifest.entry
        if not entry.exists():
            # Allow package-style entry without suffix
            alt = root / "plugin.py"
            if not alt.exists():
                findings.append(f"missing entry '{manifest.entry}'")

        if findings:
            return ValidationResult(
                ok=False,
                reason="Plugin validation failed.",
                manifest=manifest,
                findings=tuple(findings),
            )
        return ValidationResult(
            ok=True,
            reason="Manifest and capabilities verified.",
            manifest=manifest,
            findings=(),
        )

    def _find_manifest(self, root: Path) -> Path | None:
        for name in self.MANIFEST_NAMES:
            candidate = root / name
            if candidate.is_file():
                return candidate
        return None
