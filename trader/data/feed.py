"""Market data helpers using ccxt."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict

import ccxt
import pandas as pd

logger = logging.getLogger(__name__)


def _exchange(name: str) -> ccxt.Exchange:
    cls = getattr(ccxt, name)
    ex = cls({"enableRateLimit": True})
    return ex


def fetch_ohlcv(exchange_name: str, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
    """Fetch OHLCV data and return DataFrame with UTC index."""
    ex = _exchange(exchange_name)
    try:
        raw = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    except Exception as exc:  # pragma: no cover
        logger.error("fetch_ohlcv failed: %s", exc)
        raise
    df = pd.DataFrame(raw, columns=["ts", "open", "high", "low", "close", "volume"])
    df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    df = df.set_index("ts")
    return df


def poll_latest(exchange_name: str, symbol: str, timeframe: str) -> pd.DataFrame:
    """Poll the latest bar for a symbol."""
    return fetch_ohlcv(exchange_name, symbol, timeframe, limit=1)


__all__ = ["fetch_ohlcv", "poll_latest"]
