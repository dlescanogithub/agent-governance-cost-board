"""Small numeric helpers with a documented percentile definition."""

from __future__ import annotations

import math


def percentile(values: list[float], p: float) -> float:
    """Linear interpolation between nearest ranks. p is in [0, 100]."""
    if not values:
        raise ValueError("percentile of an empty sample")
    if p < 0 or p > 100:
        raise ValueError("p must be between 0 and 100")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * (p / 100.0)
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return ordered[low]
    weight = rank - low
    return ordered[low] * (1.0 - weight) + ordered[high] * weight
