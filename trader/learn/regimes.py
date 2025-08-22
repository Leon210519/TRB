"""Market regime detection."""
from __future__ import annotations

import pandas as pd


def detect_regimes(df: pd.DataFrame) -> pd.DataFrame:
    """Return DataFrame with boolean trend/range regime columns."""
    close = df["close"]
    sma200 = close.rolling(200).mean()
    slope = sma200.diff()
    tr = (df["high"] - df["low"]).rolling(14).mean()
    atr_ratio = (tr / close).fillna(0)
    trend = slope > 0
    range_ = (atr_ratio < 0.02) & (slope.abs() < 1e-3)
    return pd.DataFrame({"trend": trend, "range": range_})


__all__ = ["detect_regimes"]
