"""Utility helpers for the trading bot."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Union

import pandas as pd


def now_utc() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


def to_utc(ts: Union[datetime, pd.Timestamp]) -> datetime:
    """Convert a datetime or pandas timestamp to UTC datetime."""
    if isinstance(ts, pd.Timestamp):
        ts = ts.to_pydatetime()
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def timeframe_to_per_year_bars(timeframe: str) -> int:
    """Return approximate number of bars per year for a timeframe string."""
    minutes = timeframe_to_minutes(timeframe)
    bars_per_year = int((365 * 24 * 60) / minutes)
    return bars_per_year


def timeframe_to_minutes(timeframe: str) -> int:
    unit = timeframe[-1]
    value = int(timeframe[:-1])
    if unit == "m":
        return value
    if unit == "h":
        return value * 60
    if unit == "d":
        return value * 60 * 24
    raise ValueError(f"Unsupported timeframe: {timeframe}")


def timeframe_to_seconds(timeframe: str) -> int:
    """Convert timeframe like '1h' to seconds."""
    return timeframe_to_minutes(timeframe) * 60


def apply_slippage(price: float, bps: float, side: str) -> float:
    """Apply slippage in basis points to price depending on side."""
    sign = 1 if side.upper() == "BUY" else -1
    return price * (1 + sign * bps / 10000)


def pct(value: float) -> str:
    """Return value as percentage string."""
    return f"{value * 100:.2f}%"


__all__ = [
    "now_utc",
    "to_utc",
    "timeframe_to_per_year_bars",
    "timeframe_to_minutes",
    "timeframe_to_seconds",
    "apply_slippage",
    "pct",
]
