"""Marketplace validator — manifest, checksum, SDK, and permission checks.

Rejects incompatible or unsafe plugin packages before install.
Does not import or execute plugin code.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from aetheros.marketplace.models import PluginManifest
from aetheros.marketplace.permissions import validate_permissions

try:
    from plugins.sdk.manifest import sdk_constraint_allows
    from plugins.sdk.version import SDK_VERSION
except Exception:  # pragma: no cover - fallback when SDK package missing
    SDK_VERSION = "5.0.0"

    def sdk_constraint_allows(constraint: str, *, major: int = 5) -> bool:
        return str(major) in constraint or constraint.strip().startswith(f"{major}.")


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Outcome of marketplace package validation."""

    ok: bool
    reasons: tuple[str, ...] = ()
    manifest: PluginManifest | None = None
    checksum: str = ""


def compute_checksum(path: Path) -> str:
    """Compute a deterministic ``sha256:<hex>`` digest for a plugin package.

    Hashes sorted relative file paths + contents for regular files under ``path``.
    """

    root = Path(path)
    digest = hashlib.sha256()
    if root.is_file():
        digest.update(root.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(root.read_bytes())
        return f"sha256:{digest.hexdigest()}"

    files = sorted(
        p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts
    )
    for file_path in files:
        rel = file_path.relative_to(root).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_path.read_bytes())
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def validate_manifest(manifest: PluginManifest) -> ValidationResult:
    """Validate a marketplace ``PluginManifest`` without touching disk."""

    reasons: list[str] = []
    try:
        validate_permissions(manifest.permissions)
    except ValueError as exc:
        reasons.append(str(exc))
    if not sdk_constraint_allows(manifest.sdk_version):
        reasons.append(
            f"SDK incompatible: manifest requires {manifest.sdk_version!r}, "
            f"host is {SDK_VERSION}"
        )
    if not manifest.checksum.startswith("sha256:"):
        reasons.append("checksum must use sha256:<hex> form")
    if reasons:
        return ValidationResult(ok=False, reasons=tuple(reasons), manifest=manifest)
    return ValidationResult(ok=True, manifest=manifest, checksum=manifest.checksum)


def validate_package(
    path: Path | str,
    *,
    expected: PluginManifest | None = None,
) -> ValidationResult:
    """Validate an on-disk package against optional catalog expectations.

    Reads ``marketplace.json`` or synthesizes from ``plugin.yaml`` metadata
    when present. Verifies checksum of package contents.
    """

    root = Path(path)
    if not root.exists():
        return ValidationResult(ok=False, reasons=(f"path not found: {root}",))

    reasons: list[str] = []
    manifest = expected
    meta_path = root / "marketplace.json" if root.is_dir() else None
    if meta_path is not None and meta_path.is_file():
        import json

        raw = json.loads(meta_path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            try:
                manifest = PluginManifest.from_dict(raw)
            except ValueError as exc:
                reasons.append(str(exc))
                return ValidationResult(ok=False, reasons=tuple(reasons))

    if manifest is None:
        # Best-effort bridge from Plugin SDK YAML when marketplace.json is absent.
        yaml_candidates = (
            "plugin.yaml",
            "plugin.yml",
            "manifest.yaml",
            "manifest.yml",
        )
        yaml_path = next(
            (root / name for name in yaml_candidates if (root / name).is_file()),
            None,
        )
        if yaml_path is None:
            return ValidationResult(
                ok=False,
                reasons=("missing marketplace.json or plugin.yaml",),
            )
        try:
            from plugins.sdk.manifest import load_manifest

            sdk_manifest = load_manifest(yaml_path)
            from aetheros.marketplace.permissions import (
                READ_CONTEXT,
                READ_GRAPH,
                READ_TELEMETRY,
            )

            cap_map = {
                "graph.read": READ_GRAPH,
                "context.read": READ_CONTEXT,
                "telemetry.read": READ_TELEMETRY,
            }
            perms = tuple(cap_map[c] for c in sdk_manifest.capabilities if c in cap_map)
            checksum = compute_checksum(root)
            manifest = PluginManifest(
                id=sdk_manifest.id,
                name=sdk_manifest.name,
                version=sdk_manifest.version,
                author=sdk_manifest.author,
                description=sdk_manifest.description,
                sdk_version=sdk_manifest.sdk,
                category="insight",
                permissions=perms or (READ_GRAPH,),
                checksum=checksum,
            )
        except Exception as exc:
            return ValidationResult(
                ok=False, reasons=(f"manifest parse failed: {exc}",)
            )

    assert manifest is not None
    base = validate_manifest(manifest)
    if not base.ok:
        return base

    actual = compute_checksum(root)
    excl = (
        compute_checksum_excluding(root, exclude_names={"marketplace.json"})
        if root.is_dir()
        else actual
    )
    acceptable = {actual, excl}

    if (
        expected is not None
        and expected.checksum
        and expected.checksum not in acceptable
    ):
        reasons.append(f"checksum mismatch: expected {expected.checksum}, got {actual}")
    if (
        manifest.checksum
        and manifest.checksum not in acceptable
        and meta_path is not None
        and meta_path.is_file()
    ):
        reasons.append(f"checksum mismatch: declared {manifest.checksum}, got {actual}")

    if reasons:
        return ValidationResult(
            ok=False,
            reasons=tuple(reasons),
            manifest=manifest,
            checksum=actual,
        )
    return ValidationResult(
        ok=True,
        manifest=manifest,
        checksum=excl if manifest.checksum == excl else actual,
    )


def compute_checksum_excluding(path: Path, *, exclude_names: set[str]) -> str:
    """Like ``compute_checksum`` but skips named files at any depth."""

    root = Path(path)
    digest = hashlib.sha256()
    files = sorted(
        p
        for p in root.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.name not in exclude_names
    )
    for file_path in files:
        rel = file_path.relative_to(root).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_path.read_bytes())
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"
