"""Simple moving average crossover strategy."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .base import Strategy


@dataclass
class SMACross(Strategy):
    fast: int
    slow: int

    def __post_init__(self) -> None:
        if self.fast >= self.slow:
            raise ValueError("fast must be < slow")

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        sma_fast = df["close"].rolling(self.fast).mean()
        sma_slow = df["close"].rolling(self.slow).mean()
        regime = (sma_fast > sma_slow).astype(int)
        return regime

    def name(self) -> str:
        return "sma_cross"

    def params(self) -> dict:
        return {"fast": self.fast, "slow": self.slow}


__all__ = ["SMACross"]
