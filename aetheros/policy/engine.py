"""Policy Studio engine — evaluate / validate / list / simulate.

Public facade over registry + evaluator. Never mutates OS, scheduler,
twin, or consensus runtime state — returns advisory results only.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from aetheros.policy.constraints import (
    GovernanceConstraint,
    constraints_from_results,
    filter_recommendations,
)
from aetheros.policy.evaluator import evaluate_all, evaluate_policy
from aetheros.policy.models import (
    OPERATORS,
    EvaluationResult,
    Policy,
    Rule,
    SimulationImpact,
)
from aetheros.policy.parser import rule_to_expression
from aetheros.policy.registry import PolicyRegistry


class PolicyStudio:
    """Deterministic Policy Studio engine.

    Args:
        registry: Local versioned policy registry (JSON-backed).
    """

    def __init__(self, registry: PolicyRegistry | None = None) -> None:
        self.registry = registry or PolicyRegistry()

    def list_policies(self, *, include_archived: bool = False) -> tuple[Policy, ...]:
        """Return published (and optionally archived) policy heads."""

        return self.registry.list_policies(include_archived=include_archived)

    def validate(self, policy: Policy) -> tuple[bool, tuple[str, ...]]:
        """Validate a policy document without persisting it.

        Returns:
            ``(ok, reasons)`` — empty reasons when valid.
        """

        reasons: list[str] = []
        if not policy.id.strip():
            reasons.append("id required")
        if not policy.name.strip():
            reasons.append("name required")
        if policy.priority < 0:
            reasons.append("priority must be >= 0")
        if not policy.rules:
            reasons.append("at least one rule required")
        for rule in policy.rules:
            reasons.extend(_validate_rule(rule))
        return (not reasons, tuple(reasons))

    def evaluate(
        self,
        context: Mapping[str, Any],
        *,
        policy_id: str | None = None,
    ) -> tuple[EvaluationResult, ...]:
        """Evaluate enabled published policies against ``context``."""

        if policy_id is not None:
            policy = self.registry.get_policy(policy_id)
            if policy is None:
                return ()
            return (evaluate_policy(policy, context),)
        policies = self.registry.list_policies(include_archived=False)
        active = tuple(p for p in policies if p.enabled and p.status == "published")
        return evaluate_all(active, context)

    def simulate(
        self,
        context: Mapping[str, Any],
        *,
        recommendations: tuple[str, ...] = (),
    ) -> SimulationImpact:
        """Simulate governance impact without applying anything.

        Returns filtered recommendation titles, constraints, and explanations.
        """

        results = self.evaluate(context)
        matched = tuple(r for r in results if r.matched)
        filtered = filter_recommendations(recommendations, matched)
        constraints = constraints_from_results(matched)
        explanations = tuple(r.explanation for r in matched)
        return SimulationImpact(
            matched=matched,
            filtered_recommendations=filtered,
            constraints=tuple(_constraint_label(c) for c in constraints),
            explanations=explanations,
        )


def _validate_rule(rule: Rule) -> list[str]:
    errors: list[str] = []
    if rule.operator not in OPERATORS:
        errors.append(f"unsupported operator: {rule.operator}")
    if rule.operator in {"IN", "NOT_IN"} and not isinstance(rule.value, (tuple, list)):
        errors.append(f"{rule.operator} requires a list/tuple value")
    try:
        _ = rule_to_expression(rule)
    except Exception as exc:  # pragma: no cover - defensive
        errors.append(str(exc))
    return errors


def _constraint_label(constraint: GovernanceConstraint) -> str:
    return (
        f"[{constraint.kind}] {constraint.action} "
        f"({constraint.source_policy_id}@v{constraint.source_version})"
    )
