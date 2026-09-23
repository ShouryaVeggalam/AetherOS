"""Static safety sandbox for plugin source validation.

Scans plugin Python files with the AST module before dynamic import.
Rejects unsafe imports and dangerous string patterns. This is not a
full OS sandbox — it is a load-time gate for the SDK.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

# Module roots that plugins must not import.
FORBIDDEN_MODULES: frozenset[str] = frozenset(
    {
        "subprocess",
        "ctypes",
        "socket",
        "pty",
        "fcntl",
        "multiprocessing",
        "signal",
        "http.client",
        "urllib.request",
    }
)

# Submodule prefixes that are also forbidden.
FORBIDDEN_PREFIXES: tuple[str, ...] = (
    "subprocess",
    "ctypes",
    "socket",
)

# Text patterns that indicate unsafe intent.
FORBIDDEN_STRINGS: tuple[str, ...] = (
    "sudo",
    "os.system",
    "subprocess.",
    "ctypes.",
)


@dataclass(frozen=True, slots=True)
class SandboxResult:
    """Outcome of validating one plugin path.

    Attributes:
        safe: True when the plugin passed all checks.
        reason: Human-readable explanation.
        findings: Individual rule violations (empty when safe).
    """

    safe: bool
    reason: str
    findings: tuple[str, ...] = ()


class PluginSandbox:
    """Validate plugin source trees before they are imported."""

    def validate_path(self, plugin_dir: Path) -> SandboxResult:
        """Scan all .py files under a plugin directory.

        Args:
            plugin_dir: Directory containing the plugin package.

        Returns:
            A SandboxResult describing approval or rejection.
        """

        findings: list[str] = []
        py_files = sorted(plugin_dir.rglob("*.py"))
        if not py_files:
            return SandboxResult(
                safe=False,
                reason="No Python files found in plugin directory.",
                findings=("missing_python",),
            )

        for path in py_files:
            findings.extend(self._scan_file(path))

        if findings:
            return SandboxResult(
                safe=False,
                reason="Plugin failed safety validation.",
                findings=tuple(findings),
            )
        return SandboxResult(
            safe=True,
            reason="Plugin verified — no forbidden APIs detected.",
            findings=(),
        )

    def _scan_file(self, path: Path) -> list[str]:
        """Scan one Python file for forbidden imports and strings."""

        findings: list[str] = []
        try:
            source = path.read_text(encoding="utf-8")
        except OSError as exc:
            return [f"{path.name}: unreadable ({exc})"]

        lowered = source.lower()
        for token in FORBIDDEN_STRINGS:
            if token in lowered:
                findings.append(f"{path.name}: forbidden text '{token}'")

        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            return [f"{path.name}: syntax error ({exc.msg})"]

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    findings.extend(self._check_module(alias.name, path.name))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                findings.extend(self._check_module(module, path.name))
                # from os import system
                if module == "os":
                    for alias in node.names:
                        if alias.name == "system":
                            findings.append(f"{path.name}: forbidden import os.system")
            elif isinstance(node, ast.Call):
                findings.extend(self._check_call(node, path.name))

        return findings

    def _check_module(self, module: str, filename: str) -> list[str]:
        """Return findings if a module name is forbidden."""

        if not module:
            return []
        root = module.split(".", 1)[0]
        if root in FORBIDDEN_MODULES or module in FORBIDDEN_MODULES:
            return [f"{filename}: forbidden import '{module}'"]
        for prefix in FORBIDDEN_PREFIXES:
            if module == prefix or module.startswith(prefix + "."):
                return [f"{filename}: forbidden import '{module}'"]
        return []

    def _check_call(self, node: ast.Call, filename: str) -> list[str]:
        """Detect calls like os.system(...)."""

        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "system":
            if isinstance(func.value, ast.Name) and func.value.id == "os":
                return [f"{filename}: forbidden call os.system()"]
        return []
