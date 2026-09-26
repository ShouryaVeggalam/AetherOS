"""Policy Studio rule language parser — immutable AST only.

Supports: == != > < >= <= IN NOT_IN

Examples::

    battery < 20
    intent == CODING
    region IN ["Hyderabad"]

Never executes anything. Returns frozen AST nodes.
"""

from __future__ import annotations

import ast as py_ast
import re
from dataclasses import dataclass
from typing import Any

from aetheros.policy.models import OPERATORS, Rule

# Token patterns
_OP_PATTERN = re.compile(
    r"(==|!=|>=|<=|>|<|\bIN\b|\bNOT_IN\b|\bNOT\s+IN\b)",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class Literal:
    """Immutable AST literal node."""

    value: Any


@dataclass(frozen=True, slots=True)
class FieldRef:
    """Immutable AST field reference (left-hand side)."""

    name: str


@dataclass(frozen=True, slots=True)
class Comparison:
    """Immutable binary comparison AST node."""

    field: FieldRef
    operator: str
    value: Literal

    def to_rule(self, *, action: str) -> Rule:
        """Lower this AST node into a ``Rule`` with an advisory action."""

        return Rule(
            field=self.field.name,
            operator=self.operator,
            value=self.value.value,
            action=action,
        )


def _normalize_operator(raw: str) -> str:
    text = re.sub(r"\s+", " ", raw.strip().upper())
    if text == "NOT IN":
        return "NOT_IN"
    return text.replace(" ", "")


def _parse_rhs(raw: str) -> Any:
    """Parse a RHS literal: number, string, bareword, or list."""

    text = raw.strip()
    if not text:
        raise ValueError("missing comparison value")
    # List / tuple forms
    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = py_ast.literal_eval(text)
        except (ValueError, SyntaxError) as exc:
            raise ValueError(f"invalid list literal: {text!r}") from exc
        if not isinstance(parsed, (list, tuple)):
            raise ValueError(f"expected list literal, got {type(parsed).__name__}")
        return tuple(parsed)
    # Quoted string
    if (text.startswith('"') and text.endswith('"')) or (
        text.startswith("'") and text.endswith("'")
    ):
        return text[1:-1]
    # Number
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        pass
    # Boolean-ish / bareword
    lower = text.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if lower == "null" or lower == "none":
        return None
    return text


def parse_expression(expression: str) -> Comparison:
    """Parse a rule expression into an immutable ``Comparison`` AST.

    Raises:
        ValueError: On empty input or unsupported syntax.
    """

    text = expression.strip()
    if not text:
        raise ValueError("expression must be non-empty")
    match = _OP_PATTERN.search(text)
    if match is None:
        raise ValueError(f"no operator found in expression: {expression!r}")
    field = text[: match.start()].strip()
    operator = _normalize_operator(match.group(0))
    rhs = text[match.end() :].strip()
    if not field:
        raise ValueError("missing field name")
    if operator not in OPERATORS:
        raise ValueError(f"unsupported operator: {operator!r}")
    value = _parse_rhs(rhs)
    if operator in {"IN", "NOT_IN"} and not isinstance(value, tuple):
        # Allow single value as one-element membership set
        value = (value,)
    return Comparison(
        field=FieldRef(name=field),
        operator=operator,
        value=Literal(value=value),
    )


def parse_rule(expression: str, *, action: str) -> Rule:
    """Parse ``expression`` and attach an advisory ``action``."""

    return parse_expression(expression).to_rule(action=action)


def rule_to_expression(rule: Rule) -> str:
    """Render a Rule back to a canonical expression string."""

    value = rule.value
    if isinstance(value, tuple):
        inner = ", ".join(f'"{v}"' if isinstance(v, str) else repr(v) for v in value)
        rhs = f"[{inner}]"
    elif isinstance(value, str):
        rhs = value
    else:
        rhs = repr(value)
    return f"{rule.field} {rule.operator} {rhs}"
