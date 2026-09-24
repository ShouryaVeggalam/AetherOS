"""Forecast confidence scoring from measurable quality signals.

Longer horizons and higher volatility reduce confidence. No hardcoded
per-metric confidence values.
"""

from __future__ import annotations

from aetheros.predictive.models import HorizonMinutes


def forecast_confidence(
    *,
    sample_count: int,
    horizon: HorizonMinutes,
    volatility: float,
) -> int:
    """Compute 0–100 confidence for one forecast horizon.

    Args:
        sample_count: Number of history samples used.
        horizon: Forecast horizon in minutes.
        volatility: Mean series volatility (std-dev percent points).

    Returns:
        Integer confidence in [0, 100].
    """

    if sample_count <= 0:
        return 0
    # Sample quality saturates near observatory capacity (300).
    sample_q = min(100.0, (sample_count / 300.0) * 100.0)
    # Longer horizons are inherently less certain.
    horizon_q = max(20.0, 100.0 - (horizon * 0.9))
    # High volatility erodes trust.
    vol_penalty = min(60.0, max(0.0, volatility) * 2.5)
    volatility_q = max(0.0, 100.0 - vol_penalty)
    score = sample_q * 0.45 + horizon_q * 0.30 + volatility_q * 0.25
    return int(max(0, min(100, round(score))))
