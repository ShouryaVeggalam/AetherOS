"""Sandboxed execution gate for Plugin SDK packages.

AST load-time scan — not OS isolation. Rejects dangerous imports and
call patterns before dynamic import. See docs/plugin_sdk.md.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

FORBIDDEN_MODULES: frozenset[str] = frozenset(
    {
        "subprocess",
        "ctypes",
        "socket",
        "pty",
        "fcntl",
        "multiprocessing",
        "signal",
        "http",
        "http.client",
        "urllib",
        "urllib.request",
        "requests",
        "httpx",
        "pickle",
        "importlib",
        "shutil",
        "code",
        "codeop",
        "pathlib",  # plugins should not touch arbitrary paths at import time
    }
)

FORBIDDEN_PREFIXES: tuple[str, ...] = (
    "subprocess",
    "ctypes",
    "socket",
    "urllib",
    "http",
    "importlib",
    "pickle",
    "requests",
    "httpx",
    "shutil",
)

FORBIDDEN_STRINGS: tuple[str, ...] = (
    "sudo",
    "os.system",
    "subprocess.",
    "ctypes.",
    "__import__",
)

FORBIDDEN_CALL_NAMES: frozenset[str] = frozenset(
    {"eval", "exec", "compile", "__import__"}
)

FORBIDDEN_OS_ATTRS: frozenset[str] = frozenset(
    {
        "system",
        "popen",
        "execl",
        "execle",
        "execlp",
        "execlpe",
        "execv",
        "execve",
        "execvp",
        "execvpe",
        "spawnl",
        "spawnle",
        "spawnlp",
        "spawnlpe",
        "spawnv",
        "spawnve",
        "spawnvp",
        "spawnvpe",
        "remove",
        "unlink",
        "rmdir",
        "removedirs",
        "chmod",
        "chown",
        "kill",
        "killpg",
    }
)


@dataclass(frozen=True, slots=True)
class SandboxResult:
    """Outcome of validating one plugin path."""

    safe: bool
    reason: str
    findings: tuple[str, ...] = ()


class PluginSandbox:
    """Validate plugin source trees before they are imported."""

    def validate_path(self, plugin_dir: Path) -> SandboxResult:
        """Scan all ``.py`` files under a plugin directory."""

        findings: list[str] = []
        py_files = sorted(plugin_dir.rglob("*.py"))
        # Skip __pycache__
        py_files = [p for p in py_files if "__pycache__" not in p.parts]
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
                if module == "os":
                    for alias in node.names:
                        if alias.name in FORBIDDEN_OS_ATTRS or alias.name == "*":
                            findings.append(
                                f"{path.name}: forbidden import os.{alias.name}"
                            )
            elif isinstance(node, ast.Call):
                findings.extend(self._check_call(node, path.name))
            elif isinstance(node, ast.Attribute):
                findings.extend(self._check_attribute(node, path.name))
        return findings

    def _check_module(self, module: str, filename: str) -> list[str]:
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
        func = node.func
        if isinstance(func, ast.Name) and func.id in FORBIDDEN_CALL_NAMES:
            return [f"{filename}: forbidden call {func.id}()"]
        if isinstance(func, ast.Attribute) and func.attr in FORBIDDEN_OS_ATTRS:
            if isinstance(func.value, ast.Name) and func.value.id == "os":
                return [f"{filename}: forbidden call os.{func.attr}()"]
        return []

    def _check_attribute(self, node: ast.Attribute, filename: str) -> list[str]:
        if node.attr not in FORBIDDEN_OS_ATTRS:
            return []
        if isinstance(node.value, ast.Name) and node.value.id == "os":
            return [f"{filename}: forbidden attribute os.{node.attr}"]
        return []
