"""Portfolio allocation helpers."""
from __future__ import annotations

from typing import Dict


def equal_weight_targets(signals: Dict[str, int], max_pos_frac: float) -> Dict[str, float]:
    """Return target allocations given signals."""
    active = [s for s, v in signals.items() if v == 1]
    if not active:
        return {s: 0.0 for s in signals}
    weight = min(1 / len(active), max_pos_frac)
    return {s: (weight if v == 1 else 0.0) for s, v in signals.items()}


__all__ = ["equal_weight_targets"]
