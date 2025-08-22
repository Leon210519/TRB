"""Strategy base class."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict

import pandas as pd


class Strategy(ABC):
    """Abstract trading strategy."""

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Return Series with 1 for long regime and 0 for flat."""

    @abstractmethod
    def name(self) -> str:
        """Return strategy name."""

    @abstractmethod
    def params(self) -> Dict[str, int | float]:
        """Return parameter dictionary."""


__all__ = ["Strategy"]
