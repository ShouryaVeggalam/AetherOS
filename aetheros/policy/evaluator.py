"""Policy Studio evaluator — deterministic rule matching over a context map.

Never mutates system state. Returns immutable EvaluationResult values.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from aetheros.policy.models import EvaluationResult, Policy, Rule


def _coerce_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def evaluate_rule(rule: Rule, context: Mapping[str, Any]) -> tuple[bool, str]:
    """Evaluate one rule against ``context``.

    Returns:
        ``(matched, explanation)``.
    """

    if rule.field not in context:
        return False, f"field {rule.field!r} absent from context"
    left = context[rule.field]
    right = rule.value
    op = rule.operator

    if op in {"IN", "NOT_IN"}:
        collection = right if isinstance(right, tuple) else (right,)
        # Stringify for stable membership of mixed types
        members = tuple(collection)
        present = left in members or str(left) in {str(m) for m in members}
        matched = present if op == "IN" else not present
        expl = f"{rule.field}={left!r} {op} {members!r} → {matched}"
        return matched, expl

    if op in {">", "<", ">=", "<="}:
        ln = _coerce_number(left)
        rn = _coerce_number(right)
        if ln is None or rn is None:
            return False, f"non-numeric compare for {rule.field} {op} {right!r}"
        ops = {
            ">": ln > rn,
            "<": ln < rn,
            ">=": ln >= rn,
            "<=": ln <= rn,
        }
        matched = ops[op]
        return matched, f"{rule.field}={ln} {op} {rn} → {matched}"

    # Equality forms — coerce numbers when both numeric-ish
    ln = _coerce_number(left)
    rn = _coerce_number(right)
    if ln is not None and rn is not None:
        equal = ln == rn
    else:
        equal = left == right or str(left) == str(right)
    matched = equal if op == "==" else not equal
    return matched, f"{rule.field}={left!r} {op} {right!r} → {matched}"


def evaluate_policy(
    policy: Policy,
    context: Mapping[str, Any],
) -> EvaluationResult:
    """Evaluate all rules on ``policy`` (AND semantics).

    Disabled or archived policies never match.
    """

    if not policy.enabled or policy.status == "archived":
        return EvaluationResult(
            matched=False,
            policy=policy,
            explanation=f"policy {policy.id} inactive (enabled={policy.enabled}, status={policy.status})",
            confidence=1.0,
        )
    if not policy.rules:
        return EvaluationResult(
            matched=False,
            policy=policy,
            explanation=f"policy {policy.id} has no rules",
            confidence=1.0,
        )

    explanations: list[str] = []
    matched_rule: Rule | None = None
    for rule in policy.rules:
        ok, expl = evaluate_rule(rule, context)
        explanations.append(expl)
        if not ok:
            return EvaluationResult(
                matched=False,
                policy=policy,
                explanation="; ".join(explanations),
                confidence=0.9,
                rule=rule,
            )
        matched_rule = rule

    action = matched_rule.action if matched_rule else ""
    # Confidence scales mildly with priority (capped).
    confidence = min(0.99, 0.75 + min(policy.priority, 20) * 0.01)
    return EvaluationResult(
        matched=True,
        policy=policy,
        explanation="; ".join(explanations),
        confidence=confidence,
        action=action,
        rule=matched_rule,
    )


def evaluate_all(
    policies: tuple[Policy, ...],
    context: Mapping[str, Any],
) -> tuple[EvaluationResult, ...]:
    """Evaluate every policy; results ordered by descending priority."""

    ordered = sorted(policies, key=lambda p: (-p.priority, p.id, -p.version))
    return tuple(evaluate_policy(p, context) for p in ordered)
