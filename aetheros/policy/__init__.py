"""Policy package — Policy Studio (v5.0 P4) + legacy policy_engine alias.

Policy Studio defines versioned governance rules for recommendations,
Digital Twin simulations, Scheduler constraints, and research annotations.

Legacy ``PolicyEngine`` / ``TelemetrySnapshot`` re-exports remain for
backward compatibility with ``aetheros.policy_engine``.
"""

from __future__ import annotations

from aetheros.policy.constraints import (
    GovernanceConstraint,
    constraints_from_results,
    filter_recommendations,
)
from aetheros.policy.demo import seed_demo_policies
from aetheros.policy.engine import PolicyStudio
from aetheros.policy.evaluator import evaluate_all, evaluate_policy, evaluate_rule
from aetheros.policy.formatter import PolicyStudioPanel
from aetheros.policy.models import (
    OPERATORS,
    EvaluationResult,
    Policy,
    Rule,
    SimulationImpact,
)
from aetheros.policy.parser import (
    Comparison,
    FieldRef,
    Literal,
    parse_expression,
    parse_rule,
    rule_to_expression,
)
from aetheros.policy.registry import PolicyRegistry

# Legacy alias surface (policy_engine)
from aetheros.policy_engine import (
    PolicyEngine,
    PolicyRecommendation,
    TelemetrySnapshot,
)
from aetheros.policy_engine.models import SEVERITY_RANK, SeverityLevel

__all__ = [
    "OPERATORS",
    "Comparison",
    "EvaluationResult",
    "FieldRef",
    "GovernanceConstraint",
    "Literal",
    "Policy",
    "PolicyEngine",
    "PolicyRecommendation",
    "PolicyRegistry",
    "PolicyStudio",
    "PolicyStudioPanel",
    "Rule",
    "SEVERITY_RANK",
    "SeverityLevel",
    "SimulationImpact",
    "TelemetrySnapshot",
    "constraints_from_results",
    "evaluate_all",
    "evaluate_policy",
    "evaluate_rule",
    "filter_recommendations",
    "parse_expression",
    "parse_rule",
    "rule_to_expression",
    "seed_demo_policies",
]
